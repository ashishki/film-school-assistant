import logging

import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.db import confirm_parsed_event, create_deadline, create_homework, create_idea, create_note
from src.handlers.common import reply_text, validate_and_parse_date
from src.state import UserState, clear_pending, get_state


LOGGER = logging.getLogger(__name__)


async def confirm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        state = get_state(chat_id)

        if not state.pending_entity or not state.pending_entity_type:
            await reply_text(update, context, "Нет записи для сохранения. Сначала надиктуй или напиши что-нибудь.")
            return

        result_text = await _do_confirm(chat_id, context)
        await reply_text(update, context, result_text)
    except Exception:
        LOGGER.exception("Unhandled confirm command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat = update.effective_chat
        if chat is None:
            return

        state = get_state(chat.id)
        if not state.pending_entity:
            await reply_text(update, context, "Нет записи для сохранения. Сначала надиктуй или напиши что-нибудь.")
            return

        args = context.args or []
        if len(args) < 2:
            await reply_text(update, context, _edit_usage_text())
            return

        field = args[0].lower()
        value = " ".join(args[1:]).strip()
        if not value:
            await reply_text(update, context, _edit_usage_text())
            return

        pending = state.pending_entity
        entity_type = state.pending_entity_type or ""

        if field == "due":
            if entity_type not in {"deadline", "homework"}:
                await reply_text(update, context, _edit_usage_text())
                return
            due_date = validate_and_parse_date(value)
            if due_date is None:
                await reply_text(
                    update,
                    context,
                    "Не понял дату. Попробуй написать иначе:\n"
                    "«следующая пятница», «20 апреля», «2026-04-20»",
                )
                return
            pending["due_date"] = due_date
        elif field in {"title", "content"}:
            target_key = _editable_text_field(entity_type, field)
            if target_key is None:
                await reply_text(update, context, _edit_usage_text())
                return
            pending[target_key] = value
            if entity_type == "homework" and target_key == "title":
                pending["description"] = value
        else:
            await reply_text(update, context, _edit_usage_text())
            return

        await reply_text(update, context, _build_pending_preview(state), reply_markup=_pending_keyboard())
    except Exception:
        LOGGER.exception("Unhandled edit command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


async def discard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        state = get_state(chat_id)
        if not state.pending_entity:
            await reply_text(update, context, "Нечего удалять.")
            return

        clear_pending(chat_id)
        LOGGER.info("Discarded pending entity for chat_id=%s", chat_id)
        await reply_text(update, context, "Запись удалена.")
    except Exception:
        LOGGER.exception("Unhandled discard command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


async def _do_confirm(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    state = get_state(chat_id)
    pending = state.pending_entity
    entity_type = state.pending_entity_type

    if not pending or not entity_type:
        return "Нет записи для сохранения. Сначала надиктуй или напиши что-нибудь."

    if entity_type in {"deadline", "homework"} and not pending.get("due_date"):
        return (
            "Не хватает даты. Когда это нужно сдать?\n\n"
            "Напиши например: «в пятницу» или «15 апреля»\n"
            "или: /edit due 2026-04-20"
        )

    try:
        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            saved_type, saved_row = await _save_pending_entity(db, entity_type, pending)

            parsed_event_id = pending.get("parsed_event_id")
            if parsed_event_id is not None:
                await confirm_parsed_event(db, parsed_event_id, saved_row["id"], _entity_table_name(saved_type))
    except aiosqlite.Error:
        LOGGER.exception("Failed to confirm pending entity for chat_id=%s", chat_id)
        return "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)"

    clear_pending(chat_id)
    LOGGER.info("Confirmed pending %s for chat_id=%s as id=%s", saved_type, chat_id, saved_row["id"])
    return _confirm_success_text(saved_type)


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


def _edit_usage_text() -> str:
    return (
        "Что изменить?\n"
        "• /edit due пятница — изменить дату\n"
        "• /edit title Новый заголовок — изменить название\n"
        "• /edit content Новый текст — изменить содержание"
    )


def _pending_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Сохранить", callback_data="confirm"),
            InlineKeyboardButton("❌ Удалить", callback_data="discard"),
        ]]
    )


def _editable_text_field(entity_type: str, field: str) -> str | None:
    if field == "title":
        return "title" if entity_type in {"deadline", "homework"} else "content"
    if field == "content":
        return "title" if entity_type in {"deadline", "homework"} else "content"
    return None


def _build_pending_preview(state: UserState) -> str:
    pending = state.pending_entity or {}
    entity_type = state.pending_entity_type or "item"
    text_value = pending.get("title") if entity_type in {"deadline", "homework"} else pending.get("content")
    due_date = pending.get("due_date")
    project_id = pending.get("project_id")

    if project_id is None:
        project_label = "Общее"
    elif project_id == state.active_project_id and state.active_project_name:
        project_label = state.active_project_name
    else:
        project_label = f"#{project_id}"

    entity_labels = {
        "note": "заметка",
        "idea": "идея",
        "deadline": "дедлайн",
        "homework": "домашнее задание",
        "item": "запись",
    }
    preview = [f"Черновик ({entity_labels.get(entity_type, 'запись')}): {text_value}", f"Проект: {project_label}"]
    if due_date:
        preview.insert(1, f"Срок: {due_date}")
    return "\n".join(preview)


def _confirm_success_text(entity_type: str) -> str:
    return {
        "note": "✅ Заметка сохранена.",
        "idea": "✅ Идея сохранена.",
        "deadline": "✅ Дедлайн сохранён.",
        "homework": "✅ Домашнее задание сохранено.",
    }[entity_type]
