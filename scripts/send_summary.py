from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import aiosqlite
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.db import create_weekly_report, get_weekly_report_by_week, update_weekly_report_sent


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


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _truncate_content(value: object, limit: int = 60) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def _format_bullets(lines: list[str], empty_text: str) -> str:
    if not lines:
        return empty_text
    return "\n".join(lines)


def _russian_plural(count: int, forms: tuple[str, str, str]) -> str:
    remainder_100 = count % 100
    remainder_10 = count % 10
    if 11 <= remainder_100 <= 14:
        return forms[2]
    if remainder_10 == 1:
        return forms[0]
    if 2 <= remainder_10 <= 4:
        return forms[1]
    return forms[2]


def _russian_month_range(week_start: date, week_end: date) -> str:
    month_names = {
        1: "января",
        2: "февраля",
        3: "марта",
        4: "апреля",
        5: "мая",
        6: "июня",
        7: "июля",
        8: "августа",
        9: "сентября",
        10: "октября",
        11: "ноября",
        12: "декабря",
    }
    start_month = month_names[week_start.month]
    end_month = month_names[week_end.month]
    if week_start.month == week_end.month:
        return f"{week_start.day}–{week_end.day} {end_month}"
    return f"{week_start.day} {start_month} – {week_end.day} {end_month}"


def _format_project_activity_summary(activity: dict[str, int]) -> str:
    parts: list[str] = []
    if activity.get("notes", 0):
        notes_count = int(activity["notes"])
        parts.append(
            f"{notes_count} {_russian_plural(notes_count, ('заметка', 'заметки', 'заметок'))}"
        )
    if activity.get("ideas", 0):
        ideas_count = int(activity["ideas"])
        parts.append(
            f"{ideas_count} {_russian_plural(ideas_count, ('идея', 'идеи', 'идей'))}"
        )
    if activity.get("homework", 0):
        homework_count = int(activity["homework"])
        parts.append(
            f"{homework_count} {_russian_plural(homework_count, ('задача', 'задачи', 'задач'))}"
        )
    return ", ".join(parts)


def _build_opening_sentence(
    week_start: date,
    week_end: date,
    project_activity: dict[str, dict[str, int]],
    new_notes: list[dict[str, object]],
    new_ideas: list[dict[str, object]],
    new_homework: list[dict[str, object]],
) -> str:
    week_label = _russian_month_range(week_start, week_end)
    total_items = len(new_notes) + len(new_ideas) + len(new_homework)
    if total_items == 0 or not project_activity:
        return f"Дайджест {week_label}\n\nТихая неделя."

    ranked_projects = sorted(
        (
            (
                project_name,
                int(activity.get("notes", 0)) + int(activity.get("ideas", 0)) + int(activity.get("homework", 0)),
                activity,
            )
            for project_name, activity in project_activity.items()
        ),
        key=lambda item: (-item[1], item[0]),
    )
    top_project_name, top_total, top_activity = ranked_projects[0]
    if top_total <= 0:
        return f"Дайджест {week_label}\n\nТихая неделя."
    if len(ranked_projects) > 1 and top_total == ranked_projects[1][1]:
        return f"Дайджест {week_label}\n\nТихая неделя."

    activity_summary = _format_project_activity_summary(top_activity)
    return (
        f"Дайджест {week_label}\n\n"
        f"{top_project_name} — основная активность недели: {activity_summary}."
    )


def _build_urgent_items(
    upcoming_deadlines: list[dict[str, object]],
    week_end: date,
) -> list[str]:
    urgent: list[str] = []
    for item in upcoming_deadlines:
        due_date_raw = str(item.get("due_date") or "")
        if not due_date_raw:
            continue
        if date.fromisoformat(due_date_raw) > week_end:
            continue
        urgent.append(f'• {item["title"]} — срок {due_date_raw}')
    return urgent


def _build_creative_momentum(
    new_notes: list[dict[str, object]],
    new_ideas: list[dict[str, object]],
) -> list[str]:
    items = [
        {"created_at": item.get("created_at"), "content": item.get("content")}
        for item in new_notes + new_ideas
    ]
    items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return [f"• {_truncate_content(item.get('content'))}" for item in items]


def _build_overdue_or_stalled(
    upcoming_deadlines: list[dict[str, object]],
    stalled_projects: list[dict[str, object]],
) -> list[str]:
    lines: list[str] = []
    overdue_items = [item for item in upcoming_deadlines if int(item.get("days_until") or 0) < 0]
    overdue_items.sort(key=lambda item: str(item.get("due_date") or ""))
    for item in overdue_items:
        lines.append(f'• {item["title"]} (просрочено с {item["due_date"]})')
    for project in stalled_projects:
        lines.append(f'• {project["name"]} (активность: {str(project["last_activity_at"])[:10]})')
    return lines


def _build_next_step(upcoming_deadlines: list[dict[str, object]]) -> str:
    overdue_items = [item for item in upcoming_deadlines if int(item.get("days_until") or 0) < 0]
    overdue_items.sort(key=lambda item: (str(item.get("due_date") or ""), str(item.get("title") or "")))
    if overdue_items:
        return f'Дедлайн: {overdue_items[0]["title"]}'

    upcoming_items = [item for item in upcoming_deadlines if int(item.get("days_until") or 0) >= 0]
    upcoming_items.sort(key=lambda item: (int(item.get("days_until") or 0), str(item.get("due_date") or "")))
    if upcoming_items:
        return f'Дедлайн: {upcoming_items[0]["title"]}'

    return "Ничего срочного."


def build_summary_text(
    week_start: date,
    week_end: date,
    project_activity: dict[str, dict[str, int]],
    new_notes: list[dict[str, object]],
    new_ideas: list[dict[str, object]],
    new_homework: list[dict[str, object]],
    upcoming_deadlines: list[dict[str, object]],
    stalled_projects: list[dict[str, object]],
) -> str:
    week_label = _russian_month_range(week_start, week_end)
    opening_sentence = _build_opening_sentence(
        week_start,
        week_end,
        project_activity,
        new_notes,
        new_ideas,
        new_homework,
    )
    urgent_items = _build_urgent_items(upcoming_deadlines, week_end)
    creative_momentum = _build_creative_momentum(new_notes, new_ideas)
    overdue_or_stalled = _build_overdue_or_stalled(upcoming_deadlines, stalled_projects)
    next_step = _build_next_step(upcoming_deadlines)

    if not urgent_items and not creative_momentum and not overdue_or_stalled:
        nearest_deadline = min(
            (
                item for item in upcoming_deadlines
                if int(item.get("days_until") or 0) >= 0
            ),
            key=lambda item: (int(item.get("days_until") or 0), str(item.get("due_date") or ""), str(item.get("title") or "")),
            default=None,
        )
        if nearest_deadline is not None:
            return (
                f"Дайджест {week_label}\n\n"
                f'Тихая неделя. Ближайший дедлайн: «{nearest_deadline["title"]}» '
                f'через {nearest_deadline["days_until"]} дн.'
            )
        return f"Дайджест {week_label}\n\nТихая неделя — ничего не зафиксировано."

    return (
        f"{opening_sentence}\n\n"
        f"Срочно (срок на этой неделе):\n"
        f"{_format_bullets(urgent_items, 'Ничего срочного на этой неделе.')}\n\n"
        f"Активные идеи:\n"
        f"{_format_bullets(creative_momentum, 'Новых заметок и идей нет.')}\n\n"
        f"Без активности:\n"
        f"{_format_bullets(overdue_or_stalled, 'Ничего зависшего.')}\n\n"
        f"Что дальше:\n"
        f"{next_step}"
    )


async def fetch_all_dicts(db: aiosqlite.Connection, query: str, params: tuple[object, ...]) -> list[dict[str, object]]:
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    await cursor.close()
    return [dict(row) for row in rows]


async def fetch_snapshot(db: aiosqlite.Connection, week_start: date, week_end: date) -> dict[str, object]:
    week_start_iso = week_start.isoformat()
    week_end_exclusive = (week_end + timedelta(days=1)).isoformat()
    today_iso = date.today().isoformat()
    upcoming_cutoff = (date.today() + timedelta(days=30)).isoformat()
    stalled_before = (date.today() - timedelta(days=14)).isoformat()

    new_notes = await fetch_all_dicts(
        db,
        """
        SELECT notes.*, COALESCE(projects.name, 'General') AS project_name
        FROM notes
        LEFT JOIN projects ON projects.id = notes.project_id
        WHERE date(notes.created_at) >= date(?)
          AND date(notes.created_at) < date(?)
        ORDER BY notes.created_at DESC
        """,
        (week_start_iso, week_end_exclusive),
    )
    new_ideas = await fetch_all_dicts(
        db,
        """
        SELECT ideas.*, COALESCE(projects.name, 'General') AS project_name
        FROM ideas
        LEFT JOIN projects ON projects.id = ideas.project_id
        WHERE date(ideas.created_at) >= date(?)
          AND date(ideas.created_at) < date(?)
        ORDER BY ideas.created_at DESC
        """,
        (week_start_iso, week_end_exclusive),
    )
    new_homework = await fetch_all_dicts(
        db,
        """
        SELECT homework.*, COALESCE(projects.name, COALESCE(homework.course, 'General')) AS project_name
        FROM homework
        LEFT JOIN projects ON projects.id = homework.project_id
        WHERE date(homework.created_at) >= date(?)
          AND date(homework.created_at) < date(?)
        ORDER BY homework.created_at DESC
        """,
        (week_start_iso, week_end_exclusive),
    )
    upcoming_deadlines = await fetch_all_dicts(
        db,
        """
        SELECT deadlines.*, COALESCE(projects.name, 'General') AS project_name,
               CAST(julianday(date(deadlines.due_date)) - julianday(date(?)) AS INTEGER) AS days_until
        FROM deadlines
        LEFT JOIN projects ON projects.id = deadlines.project_id
        WHERE deadlines.status = 'active'
          AND date(deadlines.due_date) >= date(?)
          AND date(deadlines.due_date) <= date(?)
        ORDER BY date(deadlines.due_date) ASC, deadlines.created_at DESC
        """,
        (today_iso, today_iso, upcoming_cutoff),
    )
    stalled_projects = await fetch_all_dicts(
        db,
        """
        SELECT p.id, p.name, activity.last_activity_at
        FROM projects p
        JOIN (
            SELECT project_id, MAX(activity_at) AS last_activity_at
            FROM (
                SELECT project_id, created_at AS activity_at FROM notes WHERE project_id IS NOT NULL
                UNION ALL
                SELECT project_id, created_at AS activity_at FROM ideas WHERE project_id IS NOT NULL
            ) activity_union
            GROUP BY project_id
        ) activity ON activity.project_id = p.id
        WHERE date(activity.last_activity_at) < date(?)
        ORDER BY activity.last_activity_at ASC, p.name ASC
        """,
        (stalled_before,),
    )
    unreviewed_ideas = await fetch_all_dicts(
        db,
        """
        SELECT ideas.*, COALESCE(projects.name, 'General') AS project_name
        FROM ideas
        LEFT JOIN projects ON projects.id = ideas.project_id
        WHERE ideas.review_status = 'unreviewed'
        ORDER BY ideas.created_at DESC
        """,
        (),
    )

    return {
        "week_range": {"start": week_start_iso, "end": week_end.isoformat()},
        "new_notes": new_notes,
        "new_ideas": new_ideas,
        "new_homework": new_homework,
        "upcoming_deadlines": upcoming_deadlines,
        "stalled_projects": stalled_projects,
        "unreviewed_ideas": unreviewed_ideas,
    }


def compute_project_activity(snapshot: dict[str, object]) -> dict[str, dict[str, int]]:
    project_activity: dict[str, dict[str, int]] = {}
    for collection_name, key in (("new_notes", "notes"), ("new_ideas", "ideas"), ("new_homework", "homework")):
        for item in snapshot[collection_name]:
            project_name = str(item.get("project_name") or "General")
            project_counts = project_activity.setdefault(project_name, {"notes": 0, "ideas": 0, "homework": 0})
            project_counts[key] += 1
    return project_activity


async def generate_and_send_summary() -> int:
    config = load_config()
    configure_logging(config.log_level)

    week_end = date.today()
    week_start = week_end - timedelta(days=6)

    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        existing_report = await get_weekly_report_by_week(db, week_start.isoformat())
        if existing_report is not None and existing_report["sent_at"] is not None:
            LOGGER.info("Weekly summary already sent for week_start=%s", week_start.isoformat())
            return int(existing_report["id"])

        snapshot = await fetch_snapshot(db, week_start, week_end)
        project_activity = compute_project_activity(snapshot)
        # Note: build_summary_text is pure Python - no LLM call. T-B2 N/A.
        message_text = build_summary_text(
            week_start=week_start,
            week_end=week_end,
            project_activity=project_activity,
            new_notes=snapshot["new_notes"],
            new_ideas=snapshot["new_ideas"],
            new_homework=snapshot["new_homework"],
            upcoming_deadlines=snapshot["upcoming_deadlines"],
            stalled_projects=snapshot["stalled_projects"],
        )

        report = await create_weekly_report(
            db,
            week_start=week_start.isoformat(),
            content_json=json.dumps(snapshot, ensure_ascii=True),
            message_text=message_text,
        )
        try:
            send_telegram_message(config.telegram_bot_token, config.telegram_allowed_chat_id, message_text)
        except requests.RequestException:
            LOGGER.warning("Telegram API request failed for weekly summary report_id=%s", report["id"], exc_info=True)
            return 0
        except RuntimeError:
            LOGGER.warning("Telegram API returned unsuccessful payload for weekly summary report_id=%s", report["id"], exc_info=True)
            return 0
        sent_at = utcnow_iso()
        await update_weekly_report_sent(db, int(report["id"]), sent_at)

    LOGGER.info("Weekly summary generated and sent for week_start=%s report_id=%s", week_start.isoformat(), report["id"])
    return int(report["id"])


def main() -> None:
    try:
        asyncio.run(generate_and_send_summary())
    except Exception:
        LOGGER.exception("Weekly summary run failed")
        raise


if __name__ == "__main__":
    main()
