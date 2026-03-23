import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from src.config import Config


LOGGER = logging.getLogger(__name__)
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_db_path(config: Config | None = None) -> str:
    if config is not None:
        return config.db_path
    return os.environ.get("DB_PATH", "data/assistant.db")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row_to_dict(row: aiosqlite.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def _rows_to_dicts(rows: list[aiosqlite.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


async def _fetch_one_dict(db: aiosqlite.Connection, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    cursor = await db.execute(query, params)
    row = await cursor.fetchone()
    await cursor.close()
    return _row_to_dict(row)


async def _fetch_all_dicts(db: aiosqlite.Connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    await cursor.close()
    return _rows_to_dicts(rows)


_ALLOWED_TABLES = frozenset({
    "projects", "notes", "ideas", "homework", "deadlines",
    "voice_inputs", "transcripts", "parsed_events",
    "reminder_log", "review_history", "weekly_reports",
})


async def _insert_and_fetch(
    db: aiosqlite.Connection,
    query: str,
    params: tuple[Any, ...],
    table_name: str,
) -> dict[str, Any]:
    if table_name not in _ALLOWED_TABLES:
        raise ValueError(f"Unknown table: {table_name!r}")
    cursor = await db.execute(query, params)
    row_id = cursor.lastrowid
    await cursor.close()
    await db.commit()
    created = await _fetch_one_dict(db, f"SELECT * FROM {table_name} WHERE id = ?", (row_id,))  # noqa: S608 — table_name whitelisted above
    if created is None:
        raise RuntimeError(f"Failed to fetch created row from {table_name}")
    return created


async def init_db(db_path: str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(schema)
        await db.commit()
    LOGGER.info("Database initialized at %s", path)


async def create_project(db: aiosqlite.Connection, name: str, slug: str, description: str | None = None) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO projects (name, slug, description, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, slug, description, "active", _utcnow_iso()),
        "projects",
    )


async def get_project_by_slug(db: aiosqlite.Connection, slug: str) -> dict[str, Any] | None:
    return await _fetch_one_dict(db, "SELECT * FROM projects WHERE slug = ?", (slug,))


async def list_projects(db: aiosqlite.Connection) -> list[dict[str, Any]]:
    return await _fetch_all_dicts(db, "SELECT * FROM projects ORDER BY created_at DESC")


async def create_note(
    db: aiosqlite.Connection,
    content: str,
    project_id: int | None = None,
    raw_transcript: str | None = None,
    source: str = "text",
) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO notes (project_id, content, raw_transcript, source, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (project_id, content, raw_transcript, source, _utcnow_iso()),
        "notes",
    )


async def list_notes(db: aiosqlite.Connection, project_id: int | None = None, limit: int = 20) -> list[dict[str, Any]]:
    if project_id is None:
        return await _fetch_all_dicts(
            db,
            "SELECT * FROM notes ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM notes WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
        (project_id, limit),
    )


async def create_idea(
    db: aiosqlite.Connection,
    content: str,
    project_id: int | None = None,
    raw_transcript: str | None = None,
    source: str = "text",
) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO ideas (project_id, content, raw_transcript, source, review_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (project_id, content, raw_transcript, source, "unreviewed", _utcnow_iso()),
        "ideas",
    )


async def get_idea(db: aiosqlite.Connection, idea_id: int) -> dict[str, Any] | None:
    return await _fetch_one_dict(db, "SELECT * FROM ideas WHERE id = ?", (idea_id,))


async def list_ideas(db: aiosqlite.Connection, project_id: int | None = None) -> list[dict[str, Any]]:
    if project_id is None:
        return await _fetch_all_dicts(db, "SELECT * FROM ideas ORDER BY created_at DESC")
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM ideas WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    )


async def update_idea_review_status(db: aiosqlite.Connection, idea_id: int, status: str) -> None:
    await db.execute("UPDATE ideas SET review_status = ? WHERE id = ?", (status, idea_id))
    await db.commit()


async def create_homework(
    db: aiosqlite.Connection,
    title: str,
    due_date: str,
    course: str | None = None,
    project_id: int | None = None,
    description: str | None = None,
    source: str = "text",
) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO homework (project_id, course, title, description, due_date, status, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (project_id, course, title, description, due_date, "pending", source, _utcnow_iso()),
        "homework",
    )


async def list_homework(db: aiosqlite.Connection, status: str | None = None) -> list[dict[str, Any]]:
    if status is None:
        return await _fetch_all_dicts(
            db,
            "SELECT * FROM homework ORDER BY due_date ASC, created_at DESC",
        )
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM homework WHERE status = ? ORDER BY due_date ASC, created_at DESC",
        (status,),
    )


async def create_deadline(
    db: aiosqlite.Connection,
    title: str,
    due_date: str,
    project_id: int | None = None,
    source: str = "text",
) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO deadlines (project_id, title, due_date, status, reminded_count, last_reminded_at, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (project_id, title, due_date, "active", 0, None, source, _utcnow_iso()),
        "deadlines",
    )


async def get_deadline(db: aiosqlite.Connection, deadline_id: int) -> dict[str, Any] | None:
    return await _fetch_one_dict(db, "SELECT * FROM deadlines WHERE id = ?", (deadline_id,))


async def list_deadlines(db: aiosqlite.Connection, status: str | None = None) -> list[dict[str, Any]]:
    if status is None:
        return await _fetch_all_dicts(
            db,
            "SELECT * FROM deadlines ORDER BY due_date ASC, created_at DESC",
        )
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM deadlines WHERE status = ? ORDER BY due_date ASC, created_at DESC",
        (status,),
    )


async def update_deadline_status(db: aiosqlite.Connection, deadline_id: int, status: str) -> None:
    await db.execute("UPDATE deadlines SET status = ? WHERE id = ?", (status, deadline_id))
    await db.commit()


async def update_deadline_title(db: aiosqlite.Connection, deadline_id: int, title: str) -> bool:
    cursor = await db.execute("UPDATE deadlines SET title = ? WHERE id = ?", (title, deadline_id))
    await db.commit()
    return (cursor.rowcount or 0) > 0


async def update_deadline_due_date(db: aiosqlite.Connection, deadline_id: int, due_date: str) -> bool:
    cursor = await db.execute("UPDATE deadlines SET due_date = ? WHERE id = ?", (due_date, deadline_id))
    await db.commit()
    return (cursor.rowcount or 0) > 0


async def get_note(db: aiosqlite.Connection, note_id: int) -> dict[str, Any] | None:
    return await _fetch_one_dict(db, "SELECT * FROM notes WHERE id = ?", (note_id,))


async def update_note_content(db: aiosqlite.Connection, note_id: int, content: str) -> bool:
    cursor = await db.execute("UPDATE notes SET content = ? WHERE id = ?", (content, note_id))
    await db.commit()
    return (cursor.rowcount or 0) > 0


async def update_idea_content(db: aiosqlite.Connection, idea_id: int, content: str) -> bool:
    cursor = await db.execute("UPDATE ideas SET content = ? WHERE id = ?", (content, idea_id))
    await db.commit()
    return (cursor.rowcount or 0) > 0


async def create_voice_input(
    db: aiosqlite.Connection,
    telegram_file_id: str,
    local_path: str,
    duration_seconds: int,
    telegram_message_id: int,
) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO voice_inputs (telegram_file_id, local_path, duration_seconds, telegram_message_id, created_at, processed_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (telegram_file_id, local_path, duration_seconds, telegram_message_id, _utcnow_iso(), None),
        "voice_inputs",
    )


async def update_voice_input_processed(db: aiosqlite.Connection, voice_input_id: int) -> None:
    await db.execute(
        "UPDATE voice_inputs SET processed_at = ? WHERE id = ?",
        (_utcnow_iso(), voice_input_id),
    )
    await db.commit()


async def create_transcript(
    db: aiosqlite.Connection,
    voice_input_id: int,
    raw_text: str,
    model_used: str,
) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO transcripts (voice_input_id, raw_text, model_used, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (voice_input_id, raw_text, model_used, _utcnow_iso()),
        "transcripts",
    )


async def create_parsed_event(
    db: aiosqlite.Connection,
    entity_type: str,
    extracted_json: str,
    transcript_id: int | None = None,
) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO parsed_events (transcript_id, entity_type, extracted_json, confirmed, entity_id, entity_table, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (transcript_id, entity_type, extracted_json, 0, None, None, _utcnow_iso()),
        "parsed_events",
    )


async def confirm_parsed_event(db: aiosqlite.Connection, parsed_event_id: int, entity_id: int, entity_table: str) -> None:
    await db.execute(
        """
        UPDATE parsed_events
        SET confirmed = ?, entity_id = ?, entity_table = ?
        WHERE id = ?
        """,
        (1, entity_id, entity_table, parsed_event_id),
    )
    await db.commit()


async def log_reminder(db: aiosqlite.Connection, deadline_id: int, message_text: str, days_before: int) -> dict[str, Any]:
    sent_at = _utcnow_iso()
    cursor = await db.execute(
        """
        INSERT INTO reminder_log (deadline_id, sent_at, message_text, days_before)
        VALUES (?, ?, ?, ?)
        """,
        (deadline_id, sent_at, message_text, days_before),
    )
    await cursor.close()
    await db.execute(
        """
        UPDATE deadlines
        SET reminded_count = reminded_count + 1, last_reminded_at = ?
        WHERE id = ?
        """,
        (sent_at, deadline_id),
    )
    await db.commit()
    return await _fetch_one_dict(
        db,
        """
        SELECT * FROM reminder_log
        WHERE deadline_id = ? AND days_before = ?
        """,
        (deadline_id, days_before),
    ) or {}


async def get_reminder_log(db: aiosqlite.Connection, deadline_id: int) -> list[dict[str, Any]]:
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM reminder_log WHERE deadline_id = ? ORDER BY sent_at DESC",
        (deadline_id,),
    )


async def create_review_history(
    db: aiosqlite.Connection,
    idea_id: int,
    prompt_used: str,
    response_json: str,
    model_used: str,
) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO review_history (idea_id, prompt_used, response_json, model_used, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (idea_id, prompt_used, response_json, model_used, _utcnow_iso()),
        "review_history",
    )


async def create_weekly_report(
    db: aiosqlite.Connection,
    week_start: str,
    content_json: str,
    message_text: str | None = None,
) -> dict[str, Any]:
    cursor = await db.execute(
        """
        INSERT OR IGNORE INTO weekly_reports (week_start, generated_at, content_json, sent_at, message_text)
        VALUES (?, ?, ?, ?, ?)
        """,
        (week_start, _utcnow_iso(), content_json, None, message_text),
    )
    await cursor.close()
    await db.commit()
    report = await get_weekly_report_by_week(db, week_start)
    if report is None:
        raise RuntimeError(f"Failed to fetch weekly report for week_start={week_start}")
    return report


async def get_weekly_report_by_week(db: aiosqlite.Connection, week_start: str) -> dict[str, Any] | None:
    return await _fetch_one_dict(
        db,
        "SELECT * FROM weekly_reports WHERE week_start = ?",
        (week_start,),
    )


async def update_weekly_report_sent(db: aiosqlite.Connection, report_id: int, sent_at: str) -> None:
    await db.execute(
        "UPDATE weekly_reports SET sent_at = ? WHERE id = ?",
        (sent_at, report_id),
    )
    await db.commit()


async def list_active_deadlines_for_reminder(db: aiosqlite.Connection) -> list[dict[str, Any]]:
    return await _fetch_all_dicts(
        db,
        """
        SELECT *
        FROM deadlines
        WHERE status = 'active'
          AND due_date IS NOT NULL
          AND CAST(julianday(date(due_date)) - julianday(date('now')) AS INTEGER) BETWEEN 0 AND 30
        ORDER BY due_date ASC, created_at DESC
        """,
    )
