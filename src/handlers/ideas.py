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
            await reply_text(update, context, "Использование: /idea <текст>")
            return

        chat_id = update.effective_chat.id
        user_state = get_state(chat_id)

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                idea = await create_idea(db, content=text, project_id=user_state.active_project_id)
        except aiosqlite.Error:
            LOGGER.exception("Failed to save idea for chat_id=%s", chat_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        LOGGER.info("Saved idea_id=%s for chat_id=%s", idea["id"], chat_id)
        scope = (
            f"(Проект: {user_state.active_project_name})"
            if user_state.active_project_name
            else "(Общее)"
        )
        await reply_text(
            update,
            context,
            f'Идея сохранена как идея #{idea["id"]}. {scope} Используй /review {idea["id"]} для структурного разбора.',
        )
    except Exception:
        LOGGER.exception("Unhandled idea command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
