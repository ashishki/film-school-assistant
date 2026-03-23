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
    get_note,
    get_project_by_slug,
    init_db,
    list_deadlines,
    list_homework,
    list_notes,
    search_ideas,
    search_notes,
    update_deadline_due_date,
    update_deadline_title,
    update_idea_content,
    update_note_content,
)
import re


def _make_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = slug.replace(" ", "-")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-")


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

            # T-F1: slug generation
            assert _make_slug("Film Noir") == "film-noir", "_make_slug('Film Noir') must return 'film-noir'"
            assert _make_slug("Film  Noir") == "film-noir", "_make_slug collapses multiple spaces"

            # T-F1: create_project stores correct slug and status
            film_noir = await create_project(db, "Film Noir", _make_slug("Film Noir"))
            assert film_noir["slug"] == "film-noir", "slug must be 'film-noir'"
            assert film_noir["status"] == "active", "status must be 'active'"

            # T-F1: duplicate name must raise IntegrityError (not crash silently)
            duplicate_raised = False
            try:
                await create_project(db, "Film Noir", _make_slug("Film Noir"))
            except aiosqlite.IntegrityError:
                duplicate_raised = True
            if not duplicate_raised:
                raise AssertionError("Duplicate create_project must raise IntegrityError")

            # T-F2: edit deadline title
            title_updated = await update_deadline_title(db, deadline["id"], "Updated Final Cut")
            assert title_updated, "update_deadline_title must return True for existing id"
            fetched_dl_after_title = await get_deadline(db, deadline["id"])
            assert fetched_dl_after_title["title"] == "Updated Final Cut", "deadline title must be updated"

            # T-F2: edit deadline due_date
            date_updated = await update_deadline_due_date(db, deadline["id"], "2026-05-01")
            assert date_updated, "update_deadline_due_date must return True for existing id"
            fetched_dl_after_date = await get_deadline(db, deadline["id"])
            assert fetched_dl_after_date["due_date"] == "2026-05-01", "deadline due_date must be updated"

            # T-F2: edit deadline with unknown id returns False
            missing_dl = await update_deadline_title(db, 99999, "Ghost")
            assert not missing_dl, "update_deadline_title must return False for unknown id"

            # T-F2: get_note returns correct row
            fetched_note_by_id = await get_note(db, note["id"])
            assert fetched_note_by_id is not None, "get_note must return the row"
            assert fetched_note_by_id["content"] == "Opening frame note", "note content must match"

            # T-F2: edit note content
            note_updated = await update_note_content(db, note["id"], "Revised opening frame")
            assert note_updated, "update_note_content must return True for existing id"
            fetched_note_after = await get_note(db, note["id"])
            assert fetched_note_after["content"] == "Revised opening frame", "note content must be updated"

            # T-F2: edit note with unknown id returns False
            missing_note = await update_note_content(db, 99999, "Ghost note")
            assert not missing_note, "update_note_content must return False for unknown id"

            # T-F4: list_notes(limit, offset) paginates correctly
            isolated_db_path = "/tmp/smoke_test_pagination.db"
            if os.path.exists(isolated_db_path):
                os.remove(isolated_db_path)

            try:
                await init_db(isolated_db_path)
                async with aiosqlite.connect(isolated_db_path) as pagination_db:
                    pagination_db.row_factory = aiosqlite.Row
                    await create_note(pagination_db, "Pagination note 1")
                    await create_note(pagination_db, "Pagination note 2")
                    await create_note(pagination_db, "Pagination note 3")
                    page1 = await list_notes(pagination_db, limit=2, offset=0)
                    page2 = await list_notes(pagination_db, limit=2, offset=2)
                    assert len(page1) == 2, "isolated list_notes(limit=2, offset=0) must return 2 items"
                    assert len(page2) == 1, "isolated list_notes(limit=2, offset=2) must return 1 item"
            finally:
                if os.path.exists(isolated_db_path):
                    os.remove(isolated_db_path)

            # T-F2: edit idea content
            idea_updated = await update_idea_content(db, idea["id"], "Revised silence before image")
            assert idea_updated, "update_idea_content must return True for existing id"
            fetched_idea_after = await get_idea(db, idea["id"])
            assert fetched_idea_after["content"] == "Revised silence before image", "idea content must be updated"

            # T-F2: edit idea with unknown id returns False
            missing_idea = await update_idea_content(db, 99999, "Ghost idea")
            assert not missing_idea, "update_idea_content must return False for unknown id"

            # T-F5: search_notes/search_ideas search content across all projects
            search_note = await create_note(db, "черновик сцены в метро")
            search_idea = await create_idea(db, "черновик финального образа")
            note_matches = await search_notes(db, "черн")
            idea_matches = await search_ideas(db, "черн")
            assert search_note["id"] in {item["id"] for item in note_matches}, \
                "search_notes('черн') must return the created note"
            assert search_idea["id"] in {item["id"] for item in idea_matches}, \
                "search_ideas('черн') must return the created idea"
            assert await search_notes(db, "xyz_no_match") == [], \
                "search_notes('xyz_no_match') must return empty list"
            assert await search_ideas(db, "xyz_no_match") == [], \
                "search_ideas('xyz_no_match') must return empty list"

            # T-F3: list_homework(status='pending') returns only pending items
            hw_done = await create_homework(db, "Done assignment", "2026-03-20", course="History")
            await db.execute("UPDATE homework SET status = 'done' WHERE id = ?", (hw_done["id"],))
            await db.commit()

            pending_items = await list_homework(db, status="pending")
            assert all(item["status"] == "pending" for item in pending_items), \
                "list_homework(status='pending') must return only pending items"
            pending_ids = {item["id"] for item in pending_items}
            assert hw_done["id"] not in pending_ids, \
                "done homework must not appear in pending list"

            all_hw = await list_homework(db)
            assert len(all_hw) >= 2, \
                "list_homework() with no filter must return all homework items"
            all_hw_ids = {item["id"] for item in all_hw}
            assert hw_done["id"] in all_hw_ids, \
                "done homework must appear in unfiltered list"
            assert homework["id"] in all_hw_ids, \
                "pending homework must appear in unfiltered list"

            # T-F3: list_deadlines(status='active') returns only active items
            dl_done = await create_deadline(db, "Past submission", "2026-01-01")
            await db.execute("UPDATE deadlines SET status = 'done' WHERE id = ?", (dl_done["id"],))
            await db.commit()

            active_items = await list_deadlines(db, status="active")
            assert all(item["status"] == "active" for item in active_items), \
                "list_deadlines(status='active') must return only active items"
            active_ids = {item["id"] for item in active_items}
            assert dl_done["id"] not in active_ids, \
                "done deadline must not appear in active list"

            all_dl = await list_deadlines(db)
            assert len(all_dl) >= 2, \
                "list_deadlines() with no filter must return all deadline items"
            all_dl_ids = {item["id"] for item in all_dl}
            assert dl_done["id"] in all_dl_ids, \
                "done deadline must appear in unfiltered list"

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
