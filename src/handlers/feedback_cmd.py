import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import create_user_feedback
from src.handlers.common import get_command_text, reply_text


LOGGER = logging.getLogger(__name__)


async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = get_command_text(update)
        if not text:
            await reply_text(
                update,
                context,
                "Напиши что хочешь передать разработчику:\n"
                "/feedback чего не хватает, что хочешь или ждёшь от ассистента",
            )
            return

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                await create_user_feedback(db, content=text, source="text")
        except aiosqlite.Error:
            LOGGER.exception("Failed to save feedback for update_id=%s", update.update_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        LOGGER.info("Saved user feedback (text) update_id=%s", update.update_id)
        await reply_text(update, context, "Принято, передам разработчику.")
    except Exception:
        LOGGER.exception("Unhandled feedback command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
