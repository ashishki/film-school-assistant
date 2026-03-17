import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import get_idea
from src.handlers.common import reply_text
from src.reviewer import review_idea


LOGGER = logging.getLogger(__name__)


async def review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not context.args:
            await reply_text(update, context, "Usage: /review <idea_id>")
            return

        raw_idea_id = context.args[0].strip()
        try:
            idea_id = int(raw_idea_id)
        except ValueError:
            await reply_text(update, context, "Usage: /review <idea_id>")
            return

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            idea = await get_idea(db, idea_id)

        if idea is None:
            await reply_text(update, context, f"Idea #{idea_id} not found.")
            return

        await reply_text(update, context, f"Reviewing Idea #{idea_id}...")
        review_text = await review_idea(idea, context.bot_data["config"])
        await reply_text(update, context, review_text)
        LOGGER.info("Completed /review for idea_id=%s", idea_id)
    except Exception:
        LOGGER.exception("Unhandled review command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")
