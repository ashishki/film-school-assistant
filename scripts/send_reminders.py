from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from datetime import date, datetime
from pathlib import Path

import aiosqlite
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.db import (
    get_reminder_log,
    list_active_deadlines_for_reminder,
    list_due_recurring_reminders,
    log_recurring_reminder,
    log_reminder,
)


LOGGER = logging.getLogger(__name__)
TELEGRAM_API_TIMEOUT = 15
TELEGRAM_MAX_RETRIES = 3


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            log_dict["exc"] = self.formatException(record.exc_info)
        return json.dumps(log_dict, ensure_ascii=False)


def configure_logging(level_name: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    logging.basicConfig(
        level=getattr(logging, level_name.upper(), logging.INFO),
        handlers=[handler],
        force=True,
    )


def parse_due_date(value: str) -> date:
    return date.fromisoformat(value)


def format_due_date(due_date: date) -> str:
    return due_date.isoformat()


def build_message(deadline: dict[str, object], days_until: int, due_date: date) -> str:
    project_name = str(deadline.get("project_name") or "").strip()
    project_line = f"\nProject: {project_name}" if project_name else ""
    return (
        f'Reminder: "{deadline["title"]}" is due {format_due_date(due_date)} ({days_until} day(s) away).{project_line}\n'
        f'Reply /done_deadline_{deadline["id"]} when complete, or /dismiss_deadline_{deadline["id"]} to dismiss.'
    )


def build_recurring_message(reminder: dict[str, object]) -> str:
    kind = str(reminder.get("kind") or "")
    pause_hint = "morning" if kind == "morning_pages" else "evening"
    return (
        f"{reminder['prompt_text']}\n"
        f"Если хочешь поставить на паузу, напиши /pause_daily_practice {pause_hint}."
    )


def send_telegram_message(bot_token: str, chat_id: int, message_text: str) -> None:
    last_error: Exception | None = None

    for attempt in range(1, TELEGRAM_MAX_RETRIES + 1):
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": message_text},
                timeout=TELEGRAM_API_TIMEOUT,
            )
            if response.status_code >= 500:
                response.raise_for_status()
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                raise RuntimeError(f"Telegram API returned ok={payload.get('ok')}")
            return
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_error = exc
        except requests.HTTPError as exc:
            last_error = exc
            response = exc.response
            if response is None or response.status_code < 500:
                LOGGER.error("Telegram send failed after attempt=%s: %s", attempt, exc)
                raise
        if attempt >= TELEGRAM_MAX_RETRIES:
            break
        LOGGER.warning("Telegram send attempt=%s failed, retrying: %s", attempt, last_error)
        time.sleep(0.5 * attempt)

    if last_error is None:
        last_error = RuntimeError("Telegram send failed without an exception.")
    LOGGER.error("Telegram send failed after attempt=%s: %s", TELEGRAM_MAX_RETRIES, last_error)
    raise last_error


async def process_reminders() -> int:
    config = load_config()
    configure_logging(config.log_level)

    now = datetime.now()
    today = now.date()
    current_time = now.strftime("%H:%M")
    sent_count = 0

    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        deadlines = await list_active_deadlines_for_reminder(db)

        for deadline in deadlines:
            due_date_raw = deadline.get("due_date")
            if not isinstance(due_date_raw, str):
                LOGGER.warning("Skipping deadline without ISO due date: id=%s", deadline.get("id"))
                continue

            due_date = parse_due_date(due_date_raw)
            days_until = (due_date - today).days
            if days_until > 30:
                continue

            if days_until not in config.reminder_buckets:
                continue

            reminder_log = await get_reminder_log(db, int(deadline["id"]))
            if any(entry.get("days_before") == days_until for entry in reminder_log):
                LOGGER.debug("Reminder already sent for deadline_id=%s bucket=%s", deadline["id"], days_until)
                continue

            message_text = build_message(deadline, days_until, due_date)
            try:
                send_telegram_message(config.telegram_bot_token, config.telegram_allowed_chat_id, message_text)
            except requests.RequestException:
                LOGGER.warning(
                    "Telegram API request failed for deadline_id=%s; skipping reminder send",
                    deadline["id"],
                    exc_info=True,
                )
                continue
            except RuntimeError:
                LOGGER.warning(
                    "Telegram API returned unsuccessful payload for deadline_id=%s; skipping reminder send",
                    deadline["id"],
                    exc_info=True,
                )
                continue
            await log_reminder(db, int(deadline["id"]), message_text, days_until)
            sent_count += 1
            LOGGER.info(
                "Sent reminder for deadline_id=%s title=%r days_before=%s due_date=%s",
                deadline["id"],
                deadline["title"],
                days_until,
                due_date.isoformat(),
            )

        recurring_reminders = await list_due_recurring_reminders(db, today.isoformat(), current_time)
        for reminder in recurring_reminders:
            message_text = build_recurring_message(reminder)
            try:
                send_telegram_message(config.telegram_bot_token, config.telegram_allowed_chat_id, message_text)
            except requests.RequestException:
                LOGGER.warning(
                    "Telegram API request failed for recurring_reminder_id=%s; skipping send",
                    reminder["id"],
                    exc_info=True,
                )
                continue
            except RuntimeError:
                LOGGER.warning(
                    "Telegram API returned unsuccessful payload for recurring_reminder_id=%s; skipping send",
                    reminder["id"],
                    exc_info=True,
                )
                continue
            await log_recurring_reminder(db, int(reminder["id"]), today.isoformat(), message_text)
            sent_count += 1
            LOGGER.info(
                "Sent recurring reminder kind=%s id=%s schedule_time=%s",
                reminder["kind"],
                reminder["id"],
                reminder["schedule_time"],
            )

    LOGGER.info("Reminder run complete: sent=%s", sent_count)
    return sent_count


def main() -> None:
    try:
        asyncio.run(process_reminders())
    except Exception:
        LOGGER.exception("Reminder run failed")
        raise


if __name__ == "__main__":
    main()
