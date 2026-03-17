from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import aiosqlite
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.db import create_weekly_report, update_weekly_report_sent


LOGGER = logging.getLogger(__name__)
TELEGRAM_API_TIMEOUT = 15


def configure_logging(level_name: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level_name.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def build_active_projects_section(project_activity: dict[str, dict[str, int]]) -> str:
    if not project_activity:
        return "No new activity."

    parts: list[str] = []
    for project_name, counts in sorted(project_activity.items()):
        fragments: list[str] = []
        if counts["notes"]:
            fragments.append(f'{counts["notes"]} note{"s" if counts["notes"] != 1 else ""}')
        if counts["ideas"]:
            fragments.append(f'{counts["ideas"]} idea{"s" if counts["ideas"] != 1 else ""}')
        if counts["homework"]:
            fragments.append(f'{counts["homework"]} homework item{"s" if counts["homework"] != 1 else ""}')
        parts.append(f'"{project_name}" ({", ".join(fragments)})')
    return "; ".join(parts)


def build_ideas_section(new_ideas: list[dict[str, object]]) -> str:
    if not new_ideas:
        return "No new ideas."

    reviewed = sum(1 for idea in new_ideas if idea.get("review_status") == "reviewed")
    unreviewed = len(new_ideas) - reviewed
    return f"{len(new_ideas)} ideas this week — {reviewed} reviewed, {unreviewed} unreviewed."


def build_urgent_section(upcoming_deadlines: list[dict[str, object]]) -> str:
    urgent = [deadline for deadline in upcoming_deadlines if int(deadline["days_until"]) <= 7]
    if not urgent:
        return "Nothing urgent this week."

    urgent_parts = []
    for deadline in urgent:
        days_until = int(deadline["days_until"])
        if days_until == 0:
            due_phrase = "due TODAY"
        elif days_until == 1:
            due_phrase = "due in 1 day"
        else:
            due_phrase = f"due in {days_until} days"
        urgent_parts.append(f'"{deadline["title"]}" ({due_phrase}, {deadline["due_date"]})')
    return "; ".join(urgent_parts)


def build_stalled_section(stalled_projects: list[dict[str, object]]) -> str:
    if not stalled_projects:
        return "No stalled projects."
    return "; ".join(
        f'"{project["name"]}" (last activity {project["last_activity_at"][:10]})'
        for project in stalled_projects
    )


def build_recommended_next(
    upcoming_deadlines: list[dict[str, object]],
    unreviewed_ideas: list[dict[str, object]],
) -> str:
    suggestions: list[str] = []
    urgent = [deadline for deadline in upcoming_deadlines if int(deadline["days_until"]) <= 7]
    if urgent:
        top_deadline = sorted(urgent, key=lambda item: (int(item["days_until"]), str(item["due_date"])))[0]
        suggestions.append(f'Prioritize "{top_deadline["title"]}" before {top_deadline["due_date"]}.')
    if unreviewed_ideas:
        first_idea = unreviewed_ideas[0]
        idea_preview = str(first_idea["content"]).strip().replace("\n", " ")
        if len(idea_preview) > 80:
            idea_preview = f"{idea_preview[:77]}..."
        suggestions.append(f'Review unreviewed idea #{first_idea["id"]}: "{idea_preview}".')
    if not suggestions:
        suggestions.append("Pick one active project and turn this week’s material into a concrete next draft.")
    return " ".join(suggestions[:2])


def build_summary_text(
    week_start: date,
    week_end: date,
    project_activity: dict[str, dict[str, int]],
    new_ideas: list[dict[str, object]],
    upcoming_deadlines: list[dict[str, object]],
    stalled_projects: list[dict[str, object]],
    unreviewed_ideas: list[dict[str, object]],
) -> str:
    return (
        f"WEEK IN REVIEW — {week_start.isoformat()} – {week_end.isoformat()}\n\n"
        f"URGENT: {build_urgent_section(upcoming_deadlines)}\n"
        f"ACTIVE PROJECTS: {build_active_projects_section(project_activity)}\n"
        f"RECENT IDEAS: {build_ideas_section(new_ideas)}\n"
        f"STALLED: {build_stalled_section(stalled_projects)}\n"
        f"RECOMMENDED NEXT: {build_recommended_next(upcoming_deadlines, unreviewed_ideas)}"
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
        snapshot = await fetch_snapshot(db, week_start, week_end)
        project_activity = compute_project_activity(snapshot)
        message_text = build_summary_text(
            week_start=week_start,
            week_end=week_end,
            project_activity=project_activity,
            new_ideas=snapshot["new_ideas"],
            upcoming_deadlines=snapshot["upcoming_deadlines"],
            stalled_projects=snapshot["stalled_projects"],
            unreviewed_ideas=snapshot["unreviewed_ideas"],
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
