import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone
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


def _utcnow_minus_hours_iso(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).replace(microsecond=0).isoformat()


def get_recent_unconfirmed_events(db_path: str, hours: int = 2) -> list[dict[str, Any]]:
    cutoff = _utcnow_minus_hours_iso(hours)
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        cursor = db.execute(
            """
            SELECT *
            FROM parsed_events
            WHERE confirmed = ? AND created_at > ?
            ORDER BY created_at DESC
            """,
            (0, cutoff),
        )
        rows = cursor.fetchall()
        cursor.close()
    return [dict(row) for row in rows]


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
    "recurring_reminders", "recurring_reminder_log",
    "project_memory", "user_feedback", "feature_feedback",
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


async def get_llm_calls_today(db: aiosqlite.Connection) -> int:
    """Return count of LLM API calls made today (UTC)."""
    today = datetime.now(timezone.utc).date().isoformat()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM llm_call_log WHERE date(called_at) = date(?)",
        (today,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return int(row[0]) if row else 0


async def get_llm_calls_today_by_prefix(db: aiosqlite.Connection, call_type_prefix: str) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM llm_call_log WHERE date(called_at) = date(?) AND call_type LIKE ?",
        (today, f"{call_type_prefix}%"),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return int(row[0]) if row else 0


async def log_llm_call(db: aiosqlite.Connection, model: str, call_type: str) -> None:
    """Log an LLM API call for cost tracking."""
    called_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    await db.execute(
        "INSERT INTO llm_call_log (model, call_type, called_at) VALUES (?, ?, ?)",
        (model, call_type, called_at),
    )
    await db.commit()


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


async def list_projects(db: aiosqlite.Connection, status: str = "active") -> list[dict[str, Any]]:
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC",
        (status,),
    )


async def list_all_projects(db: aiosqlite.Connection) -> list[dict[str, Any]]:
    return await _fetch_all_dicts(db, "SELECT * FROM projects ORDER BY created_at DESC")


async def update_project_status(db: aiosqlite.Connection, project_id: int, status: str) -> bool:
    cursor = await db.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
    await db.commit()
    return (cursor.rowcount or 0) > 0


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


async def list_notes(db: aiosqlite.Connection, project_id: int | None = None, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    if project_id is None:
        return await _fetch_all_dicts(
            db,
            "SELECT * FROM notes ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM notes WHERE project_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (project_id, limit, offset),
    )


async def search_notes(db: aiosqlite.Connection, keyword: str) -> list[dict[str, Any]]:
    return await _fetch_all_dicts(
        db,
        """
        SELECT *
        FROM notes
        WHERE content LIKE ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (f"%{keyword}%",),
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


async def list_ideas(db: aiosqlite.Connection, project_id: int | None = None, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    if project_id is None:
        return await _fetch_all_dicts(db, "SELECT * FROM ideas ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM ideas WHERE project_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (project_id, limit, offset),
    )


async def search_ideas(db: aiosqlite.Connection, keyword: str) -> list[dict[str, Any]]:
    return await _fetch_all_dicts(
        db,
        """
        SELECT *
        FROM ideas
        WHERE content LIKE ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (f"%{keyword}%",),
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


async def list_homework(
    db: aiosqlite.Connection,
    status: str | None = None,
    project_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    conditions = []
    params: list[Any] = []

    if status is not None:
        conditions.append("status = ?")
        params.append(status)
    if project_id is not None:
        conditions.append("project_id = ?")
        params.append(project_id)

    query = "SELECT * FROM homework"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY due_date ASC, created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    return await _fetch_all_dicts(db, query, tuple(params))


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


async def list_deadlines(
    db: aiosqlite.Connection,
    status: str | None = None,
    project_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    conditions = []
    params: list[Any] = []

    if status is not None:
        conditions.append("status = ?")
        params.append(status)
    if project_id is not None:
        conditions.append("project_id = ?")
        params.append(project_id)

    query = "SELECT * FROM deadlines"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY due_date ASC, created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    return await _fetch_all_dicts(db, query, tuple(params))


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


async def upsert_project_memory(
    db: aiosqlite.Connection,
    project_id: int,
    summary_text: str,
    item_count_snapshot: int,
    model_used: str,
) -> dict[str, Any]:
    generated_at = _utcnow_iso()
    await db.execute(
        """
        INSERT INTO project_memory (project_id, summary_text, generated_at, item_count_snapshot, model_used)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET
            summary_text = excluded.summary_text,
            generated_at = excluded.generated_at,
            item_count_snapshot = excluded.item_count_snapshot,
            model_used = excluded.model_used
        """,
        (project_id, summary_text, generated_at, item_count_snapshot, model_used),
    )
    await db.commit()
    result = await _fetch_one_dict(db, "SELECT * FROM project_memory WHERE project_id = ?", (project_id,))
    if result is None:
        raise RuntimeError(f"Failed to fetch project_memory for project_id={project_id}")
    return result


async def get_project_memory(db: aiosqlite.Connection, project_id: int) -> dict[str, Any] | None:
    return await _fetch_one_dict(
        db, "SELECT * FROM project_memory WHERE project_id = ?", (project_id,)
    )


async def get_project_item_count(db: aiosqlite.Connection, project_id: int) -> int:
    cursor = await db.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM notes WHERE project_id = ?) +
            (SELECT COUNT(*) FROM ideas WHERE project_id = ?) +
            (SELECT COUNT(*) FROM deadlines WHERE project_id = ? AND status = 'active') +
            (SELECT COUNT(*) FROM review_history rh JOIN ideas i ON i.id = rh.idea_id WHERE i.project_id = ?)
        """,
        (project_id, project_id, project_id, project_id),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return int(row[0]) if row else 0


async def create_user_feedback(
    db: aiosqlite.Connection,
    content: str,
    raw_transcript: str | None = None,
    source: str = "text",
) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO user_feedback (content, raw_transcript, source, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (content, raw_transcript, source, _utcnow_iso()),
        "user_feedback",
    )


async def list_user_feedback(db: aiosqlite.Connection, limit: int = 200) -> list[dict[str, Any]]:
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM user_feedback ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )


async def create_feature_feedback(
    db: aiosqlite.Connection,
    source: str,
    original_request: str,
    summary_title: str,
    problem: str,
    desired_behavior: str,
    trigger_condition: str,
    success_result: str,
    conversation_json: str,
) -> dict[str, Any]:
    return await _insert_and_fetch(
        db,
        """
        INSERT INTO feature_feedback (
            source,
            original_request,
            summary_title,
            problem,
            desired_behavior,
            trigger_condition,
            success_result,
            conversation_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source,
            original_request,
            summary_title,
            problem,
            desired_behavior,
            trigger_condition,
            success_result,
            conversation_json,
            _utcnow_iso(),
        ),
        "feature_feedback",
    )


async def list_feature_feedback(db: aiosqlite.Connection, limit: int = 200) -> list[dict[str, Any]]:
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM feature_feedback ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )


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


async def upsert_recurring_reminder(
    db: aiosqlite.Connection,
    kind: str,
    title: str,
    prompt_text: str,
    schedule_time: str,
    status: str = "active",
) -> dict[str, Any]:
    now = _utcnow_iso()
    await db.execute(
        """
        INSERT INTO recurring_reminders (kind, title, prompt_text, schedule_time, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(kind) DO UPDATE SET
            title = excluded.title,
            prompt_text = excluded.prompt_text,
            schedule_time = excluded.schedule_time,
            status = excluded.status,
            updated_at = excluded.updated_at
        """,
        (kind, title, prompt_text, schedule_time, status, now, now),
    )
    await db.commit()
    result = await _fetch_one_dict(db, "SELECT * FROM recurring_reminders WHERE kind = ?", (kind,))
    if result is None:
        raise RuntimeError(f"Failed to fetch recurring_reminders row for kind={kind}")
    return result


async def list_recurring_reminders(
    db: aiosqlite.Connection,
    status: str | None = None,
) -> list[dict[str, Any]]:
    if status is None:
        return await _fetch_all_dicts(
            db,
            "SELECT * FROM recurring_reminders ORDER BY schedule_time ASC, id ASC",
        )
    return await _fetch_all_dicts(
        db,
        "SELECT * FROM recurring_reminders WHERE status = ? ORDER BY schedule_time ASC, id ASC",
        (status,),
    )


async def update_recurring_reminder_status(db: aiosqlite.Connection, kind: str, status: str) -> bool:
    cursor = await db.execute(
        "UPDATE recurring_reminders SET status = ?, updated_at = ? WHERE kind = ?",
        (status, _utcnow_iso(), kind),
    )
    await db.commit()
    return (cursor.rowcount or 0) > 0


async def list_due_recurring_reminders(
    db: aiosqlite.Connection,
    sent_on: str,
    current_time: str,
) -> list[dict[str, Any]]:
    return await _fetch_all_dicts(
        db,
        """
        SELECT rr.*
        FROM recurring_reminders rr
        LEFT JOIN recurring_reminder_log rrl
            ON rrl.recurring_reminder_id = rr.id AND rrl.sent_on = ?
        WHERE rr.status = 'active'
          AND rr.schedule_time <= ?
          AND rrl.id IS NULL
        ORDER BY rr.schedule_time ASC, rr.id ASC
        """,
        (sent_on, current_time),
    )


async def log_recurring_reminder(
    db: aiosqlite.Connection,
    recurring_reminder_id: int,
    sent_on: str,
    message_text: str,
) -> dict[str, Any]:
    sent_at = _utcnow_iso()
    cursor = await db.execute(
        """
        INSERT INTO recurring_reminder_log (recurring_reminder_id, sent_on, sent_at, message_text)
        VALUES (?, ?, ?, ?)
        """,
        (recurring_reminder_id, sent_on, sent_at, message_text),
    )
    await cursor.close()
    await db.commit()
    result = await _fetch_one_dict(
        db,
        """
        SELECT * FROM recurring_reminder_log
        WHERE recurring_reminder_id = ? AND sent_on = ?
        """,
        (recurring_reminder_id, sent_on),
    )
    if result is None:
        raise RuntimeError(f"Failed to fetch recurring_reminder_log row for reminder_id={recurring_reminder_id}")
    return result
