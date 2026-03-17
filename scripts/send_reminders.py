from __future__ import annotations

import asyncio
import logging
import sys
from datetime import date
from pathlib import Path

import aiosqlite
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.db import get_reminder_log, list_active_deadlines_for_reminder, log_reminder


LOGGER = logging.getLogger(__name__)
REMINDER_BUCKETS = (7, 3, 1, 0)
TELEGRAM_API_TIMEOUT = 15


def configure_logging(level_name: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level_name.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def parse_due_date(value: str) -> date:
    return date.fromisoformat(value)


def format_due_date(due_date: date) -> str:
    return due_date.isoformat()


def build_message(deadline: dict[str, object], days_until: int, due_date: date) -> str:
    if days_until == 0:
        due_text = f'"{deadline["title"]}" is due TODAY ({format_due_date(due_date)}).'
    elif days_until == 1:
        due_text = f'"{deadline["title"]}" is due in 1 day ({format_due_date(due_date)}).'
    else:
        due_text = f'"{deadline["title"]}" is due in {days_until} days ({format_due_date(due_date)}).'

    return (
        f"⏰ REMINDER: {due_text}\n"
        f'Mark done: /done_deadline_{deadline["id"]}\n'
        f'Dismiss reminders: /dismiss_deadline_{deadline["id"]}'
    )


def send_telegram_message(bot_token: str, chat_id: int, message_text: str) -> None:
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={"chat_id": chat_id, "text": message_text},
        timeout=TELEGRAM_API_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API returned ok={payload.get('ok')}")


async def process_reminders() -> int:
    config = load_config()
    configure_logging(config.log_level)

    today = date.today()
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

            if days_until not in REMINDER_BUCKETS:
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
