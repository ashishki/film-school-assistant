import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import (
    get_deadline,
    get_idea,
    get_note,
    update_deadline_due_date,
    update_deadline_title,
    update_idea_content,
    update_note_content,
)
from src.handlers.common import get_command_text, reply_text, validate_and_parse_date


LOGGER = logging.getLogger(__name__)

_ERR_NOT_FOUND = "Запись не найдена"
_ERR_INVALID_DATE = "Неверный формат даты"


def _parse_id_and_rest(text: str) -> tuple[int, str] | None:
    """Parse '<id> <rest>' from command text. Returns None if id is missing or non-integer."""
    parts = text.split(maxsplit=1)
    if not parts:
        return None
    try:
        entity_id = int(parts[0])
    except ValueError:
        return None
    rest = parts[1].strip() if len(parts) > 1 else ""
    return entity_id, rest


async def edit_deadline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /edit_deadline <id> title <new title> or /edit_deadline <id> due <new date>."""
    try:
        text = get_command_text(update)
        parsed = _parse_id_and_rest(text)
        if parsed is None:
            await reply_text(update, context, "Использование: /edit_deadline <id> title <новое название> или /edit_deadline <id> due <дата>")
            return

        deadline_id, rest = parsed
        if not rest:
            await reply_text(update, context, "Использование: /edit_deadline <id> title <новое название> или /edit_deadline <id> due <дата>")
            return

        field_parts = rest.split(maxsplit=1)
        field = field_parts[0].lower()
        value = field_parts[1].strip() if len(field_parts) > 1 else ""

        if field not in ("title", "due"):
            await reply_text(update, context, "Использование: /edit_deadline <id> title <новое название> или /edit_deadline <id> due <дата>")
            return

        if not value:
            await reply_text(update, context, "Использование: /edit_deadline <id> title <новое название> или /edit_deadline <id> due <дата>")
            return

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                existing = await get_deadline(db, deadline_id)
                if existing is None:
                    await reply_text(update, context, _ERR_NOT_FOUND)
                    return

                if field == "title":
                    updated = await update_deadline_title(db, deadline_id, value)
                    if not updated:
                        await reply_text(update, context, _ERR_NOT_FOUND)
                        return
                    await reply_text(update, context, f"Дедлайн #{deadline_id}: название обновлено.")
                else:
                    parsed_date = validate_and_parse_date(value)
                    if parsed_date is None:
                        await reply_text(update, context, _ERR_INVALID_DATE)
                        return
                    updated = await update_deadline_due_date(db, deadline_id, parsed_date)
                    if not updated:
                        await reply_text(update, context, _ERR_NOT_FOUND)
                        return
                    await reply_text(update, context, f"Дедлайн #{deadline_id}: дата обновлена на {parsed_date}.")

        except aiosqlite.Error:
            LOGGER.exception("DB error editing deadline_id=%s", deadline_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")

    except Exception:
        LOGGER.exception("Unhandled edit_deadline failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


async def edit_note_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /edit_note <id> <new content>."""
    try:
        text = get_command_text(update)
        parsed = _parse_id_and_rest(text)
        if parsed is None or not parsed[1]:
            await reply_text(update, context, "Использование: /edit_note <id> <новый текст>")
            return

        note_id, new_content = parsed

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                existing = await get_note(db, note_id)
                if existing is None:
                    await reply_text(update, context, _ERR_NOT_FOUND)
                    return
                updated = await update_note_content(db, note_id, new_content)
                if not updated:
                    await reply_text(update, context, _ERR_NOT_FOUND)
                    return
            await reply_text(update, context, f"Заметка #{note_id} обновлена.")

        except aiosqlite.Error:
            LOGGER.exception("DB error editing note_id=%s", note_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")

    except Exception:
        LOGGER.exception("Unhandled edit_note failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


async def edit_idea_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /edit_idea <id> <new content>."""
    try:
        text = get_command_text(update)
        parsed = _parse_id_and_rest(text)
        if parsed is None or not parsed[1]:
            await reply_text(update, context, "Использование: /edit_idea <id> <новый текст>")
            return

        idea_id, new_content = parsed

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                existing = await get_idea(db, idea_id)
                if existing is None:
                    await reply_text(update, context, _ERR_NOT_FOUND)
                    return
                updated = await update_idea_content(db, idea_id, new_content)
                if not updated:
                    await reply_text(update, context, _ERR_NOT_FOUND)
                    return
            await reply_text(update, context, f"Идея #{idea_id} обновлена.")

        except aiosqlite.Error:
            LOGGER.exception("DB error editing idea_id=%s", idea_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")

    except Exception:
        LOGGER.exception("Unhandled edit_idea failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
