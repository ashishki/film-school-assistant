#!/usr/bin/env python3
import asyncio
import logging
import os
import pathlib
import sys

import aiosqlite

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db import (
    create_deadline,
    create_homework,
    create_idea,
    create_note,
    create_project,
    get_deadline,
    get_idea,
    get_project_by_slug,
    init_db,
    list_homework,
    list_notes,
)


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
DB_PATH = "/tmp/smoke_test.db"
EXPECTED_TABLES = {
    "projects",
    "notes",
    "ideas",
    "homework",
    "deadlines",
    "voice_inputs",
    "transcripts",
    "parsed_events",
    "reminder_log",
    "review_history",
    "weekly_reports",
}


async def run_smoke_test() -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    try:
        await init_db(DB_PATH)
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            project = await create_project(db, "Documentary", "documentary", "Main film project")
            note = await create_note(db, "Opening frame note", project_id=project["id"])
            idea = await create_idea(db, "Silence before image", project_id=project["id"])
            deadline = await create_deadline(db, "Final cut submission", "2026-04-15", project_id=project["id"])
            homework = await create_homework(
                db,
                "Color grading worksheet",
                "2026-03-27",
                course="Color Grading",
                project_id=project["id"],
            )

            fetched_project = await get_project_by_slug(db, "documentary")
            fetched_note = (await list_notes(db, project_id=project["id"], limit=1))[0]
            fetched_idea = await get_idea(db, idea["id"])
            fetched_deadline = await get_deadline(db, deadline["id"])
            fetched_homework = (await list_homework(db, status="pending"))[0]

            for value in (project, note, idea, deadline, homework, fetched_project, fetched_note, fetched_idea, fetched_deadline, fetched_homework):
                if not isinstance(value, dict):
                    raise AssertionError("CRUD function returned non-dict result")

            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            table_rows = await cursor.fetchall()
            await cursor.close()
            actual_tables = {row["name"] for row in table_rows}

            missing_tables = EXPECTED_TABLES - actual_tables
            if missing_tables:
                raise AssertionError(f"Missing tables: {sorted(missing_tables)}")

        print("PASS")
        sys.exit(0)
    except Exception as exc:
        LOGGER.exception("Smoke test failed")
        print(f"FAIL: {exc}")
        sys.exit(1)
    finally:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
