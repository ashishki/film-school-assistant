import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import confirm_parsed_event, create_deadline, create_homework, create_idea, create_note
from src.handlers.common import reply_text
from src.state import clear_pending, get_state


LOGGER = logging.getLogger(__name__)


async def confirm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        state = get_state(chat_id)
        pending = state.pending_entity

        if not pending or not state.pending_entity_type:
            await reply_text(update, context, "Nothing to confirm.")
            return

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                saved_type, saved_row = await _save_pending_entity(db, state.pending_entity_type, pending)

                parsed_event_id = pending.get("parsed_event_id")
                if parsed_event_id is not None:
                    await confirm_parsed_event(db, parsed_event_id, saved_row["id"], _entity_table_name(saved_type))
        except aiosqlite.Error:
            LOGGER.exception("Failed to confirm pending entity for chat_id=%s", chat_id)
            await reply_text(update, context, "Could not save. Please try again. (ERR:DB)")
            return

        clear_pending(chat_id)
        LOGGER.info("Confirmed pending %s for chat_id=%s as id=%s", saved_type, chat_id, saved_row["id"])
        await reply_text(update, context, f"Saved as {saved_type} #{saved_row['id']}")
    except Exception:
        LOGGER.exception("Unhandled confirm command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")


async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        state = get_state(update.effective_chat.id)
        if not state.pending_entity:
            await reply_text(update, context, "Nothing to confirm.")
            return
        await reply_text(update, context, "Edit not yet implemented. Use /discard and re-enter.")
    except Exception:
        LOGGER.exception("Unhandled edit command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")


async def discard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        state = get_state(chat_id)
        if not state.pending_entity:
            await reply_text(update, context, "Nothing to confirm.")
            return

        clear_pending(chat_id)
        LOGGER.info("Discarded pending entity for chat_id=%s", chat_id)
        await reply_text(update, context, "Discarded.")
    except Exception:
        LOGGER.exception("Unhandled discard command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")


async def _save_pending_entity(db: aiosqlite.Connection, entity_type: str, pending: dict) -> tuple[str, dict]:
    if entity_type == "note":
        saved = await create_note(
            db,
            content=pending["content"],
            project_id=pending.get("project_id"),
            raw_transcript=pending.get("raw_transcript"),
            source=pending.get("source", "voice"),
        )
        return entity_type, saved

    if entity_type == "idea":
        saved = await create_idea(
            db,
            content=pending["content"],
            project_id=pending.get("project_id"),
            raw_transcript=pending.get("raw_transcript"),
            source=pending.get("source", "voice"),
        )
        return entity_type, saved

    if entity_type == "deadline":
        saved = await create_deadline(
            db,
            title=pending["title"],
            due_date=pending["due_date"],
            project_id=pending.get("project_id"),
            source=pending.get("source", "voice"),
        )
        return entity_type, saved

    if entity_type == "homework":
        saved = await create_homework(
            db,
            title=pending["title"],
            due_date=pending["due_date"],
            course=pending.get("course"),
            project_id=pending.get("project_id"),
            description=pending.get("description"),
            source=pending.get("source", "voice"),
        )
        return entity_type, saved

    raise ValueError(f"Unsupported pending entity type: {entity_type}")


def _entity_table_name(entity_type: str) -> str:
    return {
        "note": "notes",
        "idea": "ideas",
        "deadline": "deadlines",
        "homework": "homework",
    }[entity_type]
