import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import create_idea
from src.handlers.common import get_command_text, reply_text
from src.state import get_state


LOGGER = logging.getLogger(__name__)


async def idea_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = get_command_text(update)
        if not text:
            await reply_text(update, context, "Usage: /idea <text>")
            return

        chat_id = update.effective_chat.id
        user_state = get_state(chat_id)

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                idea = await create_idea(db, content=text, project_id=user_state.active_project_id)
        except aiosqlite.Error:
            LOGGER.exception("Failed to save idea for chat_id=%s", chat_id)
            await reply_text(update, context, "Could not save. Please try again. (ERR:DB)")
            return

        LOGGER.info("Saved idea_id=%s for chat_id=%s", idea["id"], chat_id)
        await reply_text(update, context, f'Idea saved as Idea #{idea["id"]}. Use /review {idea["id"]} for structured feedback.')
    except Exception:
        LOGGER.exception("Unhandled idea command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")
