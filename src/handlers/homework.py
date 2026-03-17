import logging
import re

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import create_homework
from src.handlers.common import get_command_text, parse_date_text, reply_text
from src.state import get_state


LOGGER = logging.getLogger(__name__)
HOMEWORK_RE = re.compile(
    r"^\s*(?P<title>.+?)\s+due\s+(?P<due_date>.+?)(?:\s+course:(?P<course>.+))?\s*$",
    re.IGNORECASE,
)


async def homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        command_text = get_command_text(update)
        match = HOMEWORK_RE.match(command_text)
        if match is None:
            await reply_text(update, context, "Usage: /homework <title> due <date> [course:<name>]")
            return

        title = match.group("title").strip().strip('"')
        due_date = parse_date_text(match.group("due_date"))
        course = match.group("course").strip() if match.group("course") else None
        if not title or due_date is None:
            await reply_text(update, context, "Could not parse that date. Usage: /homework <title> due <date> [course:<name>]")
            return

        chat_id = update.effective_chat.id
        user_state = get_state(chat_id)

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                await create_homework(
                    db,
                    title=title,
                    due_date=due_date,
                    course=course,
                    project_id=user_state.active_project_id,
                )
        except aiosqlite.Error:
            LOGGER.exception("Failed to save homework for chat_id=%s", chat_id)
            await reply_text(update, context, "Could not save. Please try again. (ERR:DB)")
            return

        LOGGER.info("Saved homework for chat_id=%s project_id=%s", chat_id, user_state.active_project_id)
        await reply_text(update, context, f'Homework saved: "{title}" due {due_date}.')
    except Exception:
        LOGGER.exception("Unhandled homework command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")
