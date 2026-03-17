import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import create_note
from src.handlers.common import format_project_scope, get_command_text, reply_text
from src.state import get_state


LOGGER = logging.getLogger(__name__)


async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = get_command_text(update)
        if not text:
            await reply_text(update, context, "Usage: /note <text>")
            return

        chat_id = update.effective_chat.id
        user_state = get_state(chat_id)

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                await create_note(db, content=text, project_id=user_state.active_project_id)
        except aiosqlite.Error:
            LOGGER.exception("Failed to save note for chat_id=%s", chat_id)
            await reply_text(update, context, "Could not save. Please try again. (ERR:DB)")
            return

        scope = format_project_scope(user_state.active_project_name)
        LOGGER.info("Saved note for chat_id=%s project_id=%s", chat_id, user_state.active_project_id)
        await reply_text(update, context, f"Note saved. {scope}.")
    except Exception:
        LOGGER.exception("Unhandled note command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")
