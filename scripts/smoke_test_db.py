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
    confirm_parsed_event,
    create_deadline,
    create_homework,
    create_idea,
    create_note,
    create_parsed_event,
    create_project,
    get_recent_unconfirmed_events,
    get_deadline,
    get_idea,
    get_llm_calls_today,
    get_note,
    get_project_item_count,
    get_project_by_slug,
    get_project_memory,
    get_reminder_log,
    list_due_recurring_reminders,
    list_recurring_reminders,
    init_db,
    log_recurring_reminder,
    log_reminder,
    log_llm_call,
    list_all_projects,
    list_deadlines,
    list_homework,
    list_notes,
    list_projects,
    search_ideas,
    search_notes,
    update_recurring_reminder_status,
    update_recurring_reminder_timezone,
    upsert_recurring_reminder,
    upsert_project_memory,
    update_deadline_due_date,
    update_deadline_status,
    update_deadline_title,
    update_idea_content,
    update_note_content,
    update_project_status,
)
from src.practice_intents import EVENING_KIND, MORNING_KIND, parse_practice_intent
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
    "recurring_reminders",
    "recurring_reminder_log",
    "project_memory",
    "llm_call_log",
    "user_feedback",
    "user_context_entries",
    "user_context_summary",
    "feature_feedback",
}


async def run_smoke_test() -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    try:
        recent_unconfirmed_id: int | None = None
        confirmed_event_id: int | None = None
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

            # T-F6: archive project is a soft-delete and active listing hides it
            archived_project = await create_project(db, "Archive Me", _make_slug("Archive Me"))
            archived_updated = await update_project_status(db, archived_project["id"], "archived")
            assert archived_updated, "update_project_status must return True for existing id"

            active_projects = await list_projects(db)
            active_project_ids = {item["id"] for item in active_projects}
            assert archived_project["id"] not in active_project_ids, \
                "list_projects() must exclude archived projects by default"

            all_projects = await list_all_projects(db)
            archived_rows = [item for item in all_projects if item["id"] == archived_project["id"]]
            assert len(archived_rows) == 1, "list_all_projects() must include archived projects"
            assert archived_rows[0]["status"] == "archived", \
                "archived project status must remain 'archived'"

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

            other_project = await create_project(db, "Animation", "animation")
            other_deadline = await create_deadline(db, "Storyboard delivery", "2026-04-20", project_id=other_project["id"])
            filtered_deadlines = await list_deadlines(db, project_id=project["id"], limit=20, offset=0)
            filtered_deadline_ids = {item["id"] for item in filtered_deadlines}
            assert deadline["id"] in filtered_deadline_ids, \
                "list_deadlines(project_id=...) must include deadlines for the selected project"
            assert other_deadline["id"] not in filtered_deadline_ids, \
                "list_deadlines(project_id=...) must exclude deadlines from other projects"

            all_dl = await list_deadlines(db)
            assert len(all_dl) >= 2, \
                "list_deadlines() with no filter must return all deadline items"
            all_dl_ids = {item["id"] for item in all_dl}
            assert dl_done["id"] in all_dl_ids, \
                "done deadline must appear in unfiltered list"

            # T-P2: upsert_project_memory/get_project_memory round-trip updates existing row
            memory_project = await create_project(db, "Memory Project", "memory-project")
            memory_inserted = await upsert_project_memory(
                db,
                memory_project["id"],
                "first summary",
                0,
                "test-model-v1",
            )
            assert memory_inserted["summary_text"] == "first summary", \
                "upsert_project_memory must insert the initial summary_text"

            memory_updated = await upsert_project_memory(
                db,
                memory_project["id"],
                "updated summary",
                1,
                "test-model-v2",
            )
            fetched_memory = await get_project_memory(db, memory_project["id"])
            assert fetched_memory is not None, "get_project_memory must return the stored row"
            assert memory_updated["id"] == memory_inserted["id"], \
                "upsert_project_memory must update the existing UNIQUE project_id row"
            assert fetched_memory["summary_text"] == "updated summary", \
                "upsert_project_memory must persist the latest summary_text"

            # T-P2: log_llm_call/get_llm_calls_today round-trip counts logged calls
            calls_before = await get_llm_calls_today(db)
            await log_llm_call(db, "smoke-test-model", "chat")
            calls_after = await get_llm_calls_today(db)
            assert calls_after >= 1, "get_llm_calls_today must return at least 1 after logging a call"
            assert calls_after >= calls_before + 1, \
                "log_llm_call must increase today's llm_call_log count"

            recurring = await upsert_recurring_reminder(
                db,
                kind="morning_pages",
                title="Morning Pages",
                prompt_text="Write the morning pages",
                schedule_time="09:00",
            )
            assert recurring["status"] == "active", "upsert_recurring_reminder must default status to active"
            updated_recurring = await upsert_recurring_reminder(
                db,
                kind="morning_pages",
                title="Morning Pages Updated",
                prompt_text="Updated prompt",
                schedule_time="09:30",
                status="active",
            )
            assert updated_recurring["id"] == recurring["id"], "upsert_recurring_reminder must update by kind"
            recurring_items = await list_recurring_reminders(db, status="active")
            assert updated_recurring["id"] in {item["id"] for item in recurring_items}, \
                "list_recurring_reminders(status='active') must include active reminders"
            due_recurring = await list_due_recurring_reminders(db, "2026-04-03", "10:00")
            assert updated_recurring["id"] in {item["id"] for item in due_recurring}, \
                "list_due_recurring_reminders must return reminders due before current_time"
            recurring_log = await log_recurring_reminder(db, updated_recurring["id"], "2026-04-03", "Morning reminder")
            assert recurring_log["sent_on"] == "2026-04-03", \
                "log_recurring_reminder must persist sent_on date"
            due_after_send = await list_due_recurring_reminders(db, "2026-04-03", "10:00")
            assert updated_recurring["id"] not in {item["id"] for item in due_after_send}, \
                "already sent recurring reminders must not be returned again on the same day"
            paused = await update_recurring_reminder_status(db, "morning_pages", "paused")
            assert paused, "update_recurring_reminder_status must return True for existing kind"
            paused_items = await list_recurring_reminders(db, status="paused")
            assert updated_recurring["id"] in {item["id"] for item in paused_items}, \
                "paused recurring reminder must appear in paused listing"
            timezone_updated = await update_recurring_reminder_timezone(db, "morning_pages", "Asia/Tbilisi")
            assert timezone_updated, "update_recurring_reminder_timezone must return True for existing kind"
            recurring_after_tz = await list_recurring_reminders(db)
            updated_tz_row = next(item for item in recurring_after_tz if item["kind"] == "morning_pages")
            assert updated_tz_row["timezone"] == "Asia/Tbilisi", \
                "update_recurring_reminder_timezone must persist timezone change"

            nl_practice_intent = parse_practice_intent(
                "Присылай мне напоминания каждое утро про утренние страницы и каждый вечер про итоги дня"
            )
            assert nl_practice_intent is not None, "parse_practice_intent must detect free-text daily practice setup"
            assert nl_practice_intent["action"] == "setup", \
                "free-text daily practice request must parse as setup action"
            assert MORNING_KIND in nl_practice_intent["kinds"], \
                "free-text daily practice request must include morning practice"
            assert EVENING_KIND in nl_practice_intent["kinds"], \
                "free-text daily practice request must include evening practice"
            tz_update_intent = parse_practice_intent("Переведи напоминания на Тбилисское время")
            assert tz_update_intent is not None, "parse_practice_intent must detect timezone update request"
            assert tz_update_intent["action"] == "update_timezone", \
                "timezone update request must parse as update_timezone action"
            assert tz_update_intent["timezone"] == "Asia/Tbilisi", \
                "timezone update request must resolve Tbilisi timezone"
            correction_intent = parse_practice_intent("Нет, только утренние страницы в 10:00 по Тбилисскому времени")
            assert correction_intent is not None, "parse_practice_intent must detect correction request for practices"
            assert correction_intent["action"] == "setup", \
                "correction with updated practice time must still parse as setup"
            assert correction_intent["is_correction"] is True, \
                "correction request must set is_correction flag"
            assert correction_intent["only_selected"] is True, \
                "correction request with 'только' must set only_selected flag"
            assert correction_intent["kinds"] == [MORNING_KIND], \
                "correction request for only morning practice must target morning kind only"
            assert correction_intent["morning_time"] == "10:00", \
                "correction request must extract updated morning time"
            assert correction_intent["timezone"] == "Asia/Tbilisi", \
                "correction request must preserve timezone"
            false_positive_text = (
                "Сохрани это сообщение обо мне, чтобы ты использовал его в релевантных ответах. "
                "У меня есть групповой психолог каждый месяц, я хочу вглубь себя посмотреть, "
                "прожить сложные внутренние эмоции и кажется это можно сделать только будучи в походе."
            )
            false_positive_intent = parse_practice_intent(false_positive_text)
            assert false_positive_intent is None, \
                "personal context text must not be misparsed as a daily practice intent"

            # T-P3: get_project_item_count counts notes and ideas for a project
            count_project = await create_project(db, "Count Project", "count-project")
            await create_note(db, "Counted note", project_id=count_project["id"])
            await create_idea(db, "Counted idea", project_id=count_project["id"])
            project_item_count = await get_project_item_count(db, count_project["id"])
            assert project_item_count == 2, \
                "get_project_item_count must count 1 note + 1 idea as 2 items"

            # T-B1/T-O4: restart notification source query returns only recent unconfirmed parsed_events
            recent_unconfirmed = await create_parsed_event(
                db,
                entity_type="idea",
                extracted_json='{"content":"recent pending idea"}',
            )
            confirmed_event = await create_parsed_event(
                db,
                entity_type="note",
                extracted_json='{"content":"confirmed note"}',
            )
            await confirm_parsed_event(db, confirmed_event["id"], entity_id=note["id"], entity_table="notes")

            recent_unconfirmed_id = recent_unconfirmed["id"]
            confirmed_event_id = confirmed_event["id"]

            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            table_rows = await cursor.fetchall()
            await cursor.close()
            actual_tables = {row["name"] for row in table_rows}

            missing_tables = EXPECTED_TABLES - actual_tables
            if missing_tables:
                raise AssertionError(f"Missing tables: {sorted(missing_tables)}")

            # T-T1: deadline status update
            await update_deadline_status(db, deadline["id"], "completed")
            updated_deadline = await get_deadline(db, deadline["id"])
            assert updated_deadline is not None, "get_deadline must return the updated row"
            assert updated_deadline["status"] == "completed", "deadline status must be updated to completed"
            await update_deadline_status(db, deadline["id"], "active")

            # T-T1: reminder_log dedup
            reminder_deadline = await create_deadline(db, "Reminder test deadline", "2026-06-01")
            await log_reminder(db, reminder_deadline["id"], "test reminder", days_before=3)
            reminder_rows = await get_reminder_log(db, reminder_deadline["id"])
            assert len(reminder_rows) == 1, "first log_reminder call must create one reminder_log row"

            duplicate_reminder_raised = False
            try:
                await log_reminder(db, reminder_deadline["id"], "duplicate reminder", days_before=3)
            except aiosqlite.IntegrityError:
                duplicate_reminder_raised = True
            assert duplicate_reminder_raised, "duplicate log_reminder must raise IntegrityError"

            reminder_rows_after_duplicate = await get_reminder_log(db, reminder_deadline["id"])
            assert len(reminder_rows_after_duplicate) == 1, \
                "duplicate log_reminder must not create an extra reminder_log row"

            # T-T1: parsed_event confirmation
            homework_event = await create_parsed_event(
                db,
                entity_type="homework",
                extracted_json='{"title":"Lens test homework"}',
            )
            assert homework_event["confirmed"] == 0, "new parsed_event must start with confirmed=0"
            await confirm_parsed_event(db, homework_event["id"], entity_id=1, entity_table="homework")
            cursor = await db.execute(
                "SELECT confirmed, entity_id, entity_table FROM parsed_events WHERE id=?",
                (homework_event["id"],),
            )
            confirmed_homework_event = await cursor.fetchone()
            await cursor.close()
            assert confirmed_homework_event is not None, "confirmed parsed_event row must exist"
            assert confirmed_homework_event["confirmed"] == 1, "confirmed parsed_event must set confirmed=1"
            assert confirmed_homework_event["entity_id"] == 1, "confirmed parsed_event must set entity_id=1"
            assert confirmed_homework_event["entity_table"] == "homework", \
                "confirmed parsed_event must set entity_table='homework'"

        recent_events = get_recent_unconfirmed_events(DB_PATH, hours=2)
        recent_event_ids = {item["id"] for item in recent_events}
        assert recent_unconfirmed_id is not None and recent_unconfirmed_id in recent_event_ids, \
            "get_recent_unconfirmed_events() must include recent confirmed=0 rows"
        assert confirmed_event_id is not None and confirmed_event_id not in recent_event_ids, \
            "get_recent_unconfirmed_events() must exclude confirmed=1 rows"

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
