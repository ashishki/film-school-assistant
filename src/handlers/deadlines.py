import logging
import re

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import create_deadline, update_deadline_status
from src.handlers.common import get_command_text, parse_date_text, reply_text
from src.state import get_state


LOGGER = logging.getLogger(__name__)
DEADLINE_RE = re.compile(r"^\s*(?P<title>.+?)\s+due\s+(?P<due_date>.+?)\s*$", re.IGNORECASE)
DONE_RE = re.compile(r"^/done_deadline_(?P<deadline_id>\d+)(?:@\w+)?$", re.IGNORECASE)
DISMISS_RE = re.compile(r"^/dismiss_deadline_(?P<deadline_id>\d+)(?:@\w+)?$", re.IGNORECASE)


async def deadline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        command_text = get_command_text(update)
        match = DEADLINE_RE.match(command_text)
        if match is None:
            await reply_text(update, context, "Использование: /deadline <название> due <дата>")
            return

        title = match.group("title").strip().strip('"')
        due_date = parse_date_text(match.group("due_date"))
        if not title or due_date is None:
            await reply_text(update, context, "Не удалось разобрать дату.")
            return

        chat_id = update.effective_chat.id
        user_state = get_state(chat_id)

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                deadline = await create_deadline(db, title=title, due_date=due_date, project_id=user_state.active_project_id)
        except aiosqlite.Error:
            LOGGER.exception("Failed to save deadline for chat_id=%s", chat_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        LOGGER.info("Saved deadline_id=%s for chat_id=%s", deadline["id"], chat_id)
        await reply_text(
            update,
            context,
            (
                f'Дедлайн сохранён. "{title}" — {due_date}. Напоминания: за 7, 3 и 1 день.\n'
                f"/done_deadline_{deadline['id']}\n"
                f"/dismiss_deadline_{deadline['id']}"
            ),
        )
    except Exception:
        LOGGER.exception("Unhandled deadline command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


async def done_deadline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        deadline_id = _extract_deadline_id(update, DONE_RE)
        if deadline_id is None:
            return

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                await update_deadline_status(db, deadline_id, "done")
        except aiosqlite.Error:
            LOGGER.exception("Failed to mark deadline_id=%s done", deadline_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        LOGGER.info("Marked deadline_id=%s as done", deadline_id)
        await reply_text(update, context, f"Дедлайн #{deadline_id} отмечен как выполненный.")
    except Exception:
        LOGGER.exception("Unhandled done deadline failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


async def dismiss_deadline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        deadline_id = _extract_deadline_id(update, DISMISS_RE)
        if deadline_id is None:
            return

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                await update_deadline_status(db, deadline_id, "dismissed")
        except aiosqlite.Error:
            LOGGER.exception("Failed to dismiss deadline_id=%s", deadline_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        LOGGER.info("Dismissed deadline_id=%s", deadline_id)
        await reply_text(update, context, f"Напоминания по дедлайну #{deadline_id} отключены.")
    except Exception:
        LOGGER.exception("Unhandled dismiss deadline failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


def _extract_deadline_id(update: Update, pattern: re.Pattern[str]) -> int | None:
    message = update.effective_message
    text = message.text if message else ""
    match = pattern.match(text or "")
    if match is None:
        LOGGER.debug("Dynamic deadline command did not match expected pattern: %r", text)
        return None
    return int(match.group("deadline_id"))
