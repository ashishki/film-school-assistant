from __future__ import annotations

import asyncio
import json
import logging

import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.db import create_parsed_event, get_llm_calls_today, log_llm_call
from src.handlers.common import reply_text, resolve_project_match, validate_and_parse_date
from src.handlers.confirm import _build_pending_preview, _pending_keyboard
from src.openclaw_client import LLMError, LLMSchemaError, complete_json
from src.state import get_state


LOGGER = logging.getLogger(__name__)
EXTRACTION_SYSTEM_PROMPT = (
    "Ты извлекатель сущностей для ассистента по учебному процессу киношколы. Извлеки структурированные данные из сообщения пользователя.\n"
    'Верни только JSON: {"entities": [{"entity_type": "note|idea|homework|deadline", "content": "cleaned content", '
    '"project_hint": "project name or empty string", "due_date": "YYYY-MM-DD or empty string"}]}\n'
    "Правила: entity_type должен быть одним из четырёх значений. due_date указывай только если дата явно упомянута. "
    "content не меняй. Если сущностей несколько, верни каждую отдельным объектом в массиве entities. Без пояснительного текста."
)


async def nl_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        message = update.effective_message
        chat = update.effective_chat
        if message is None or chat is None or not message.text:
            return

        state = get_state(chat.id)
        if state.pending_entity is not None:
            LOGGER.info("Skipping NL parse because a pending entity exists for chat_id=%s", chat.id)
            await reply_text(update, context, "Есть незавершённая запись. Сначала /confirm, /edit или /discard.")
            return

        user_text = message.text.strip()
        if not user_text:
            return

        daily_llm_call_limit = context.bot_data["config"].daily_llm_call_limit
        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                today_calls = await get_llm_calls_today(db)
                if today_calls >= daily_llm_call_limit:
                    await reply_text(
                        update,
                        context,
                        f"Достигнут дневной лимит LLM запросов ({daily_llm_call_limit}). Попробуй завтра.",
                    )
                    return
        except aiosqlite.Error:
            LOGGER.exception("Failed to read/write LLM call log for chat_id=%s", chat.id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        try:
            parsed = await asyncio.to_thread(
                complete_json,
                user_text,
                EXTRACTION_SYSTEM_PROMPT,
                "intent",
            )
        except (LLMError, LLMSchemaError):
            LOGGER.exception("NL extraction failed for chat_id=%s", chat.id)
            await reply_text(
                update,
                context,
                "Не совсем понял. Попробуй переформулировать или используй команду:\n"
                "/note текст, /idea текст, /deadline название due дата",
            )
            return

        if not isinstance(parsed, dict):
            LOGGER.warning("NL extraction returned non-object payload for chat_id=%s", chat.id)
            await reply_text(
                update,
                context,
                "Не совсем понял. Попробуй переформулировать или используй команду:\n"
                "/note текст, /idea текст, /deadline название due дата",
            )
            return

        entities = parsed.get("entities", [])
        if not isinstance(entities, list) or not entities:
            LOGGER.warning("NL extraction returned empty entities list for chat_id=%s", chat.id)
            await reply_text(update, context, _nl_parse_error_text())
            return

        valid_entities: list[dict[str, str | None]] = []
        for item in entities:
            normalized = _normalize_extracted_entity(item)
            if normalized is not None:
                valid_entities.append(normalized)

        if not valid_entities:
            LOGGER.warning("NL extraction returned no valid entities for chat_id=%s", chat.id)
            await reply_text(update, context, _nl_parse_error_text())
            return

        first_entity = valid_entities[0]
        entity_type = first_entity["entity_type"]
        content = first_entity["content"] or ""
        project_hint = first_entity["project_hint"] or ""
        due_date = first_entity["due_date"] or ""

        if entity_type is None:
            state.pending_nl_content = content
            state.pending_nl_due_date = due_date or None
            state.pending_nl_project_hint = project_hint or None
            await reply_text(
                update,
                context,
                f"Куда сохранить «{_content_preview(content)}»?",
                reply_markup=_type_selection_keyboard(),
            )
            return

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                pending_entity, validated_due_date = await _prepare_pending_entity_from_nl(
                    db,
                    entity_type,
                    content,
                    project_hint,
                    due_date,
                    user_text,
                )
        except aiosqlite.Error:
            LOGGER.exception("Failed to persist NL parsed event for chat_id=%s", chat.id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        state.pending_entity = pending_entity
        state.pending_entity_type = entity_type
        remaining_entities = [
            {
                "entity_type": item["entity_type"],
                "content": item["content"],
                "project_hint": item["project_hint"],
                "due_date": item["due_date"],
            }
            for item in valid_entities[1:]
            if item["entity_type"] is not None and item["content"]
        ]
        state.pending_entities = remaining_entities or None

        preview_text = _build_pending_preview(state)
        due_date_note = _build_due_date_note(entity_type, due_date, validated_due_date)
        if due_date_note:
            preview_text = f"{preview_text}{due_date_note}"
        await reply_text(update, context, preview_text, reply_markup=_pending_keyboard())
        LOGGER.info(
            "Prepared pending NL entity type=%s parsed_event_id=%s queued=%s for chat_id=%s",
            entity_type,
            pending_entity["parsed_event_id"],
            len(state.pending_entities or []),
            chat.id,
        )
    except Exception:
        LOGGER.exception("Unhandled NL handler failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


def _normalize_entity_type(raw_value: object) -> str | None:
    value = str(raw_value or "").strip().lower()
    if not value:
        return None
    if value not in {"note", "idea", "homework", "deadline"}:
        return None
    return value


def _normalize_extracted_entity(item: object) -> dict[str, str | None] | None:
    if not isinstance(item, dict):
        return None

    entity_type = _normalize_entity_type(item.get("entity_type"))
    content = str(item.get("content", "")).strip()
    project_hint = str(item.get("project_hint", "")).strip()
    due_date = str(item.get("due_date", "")).strip()
    if not content:
        return None

    return {
        "entity_type": entity_type,
        "content": content,
        "project_hint": project_hint,
        "due_date": due_date,
    }


async def _resolve_project(db: aiosqlite.Connection, project_hint: str) -> dict | None:
    if not project_hint:
        return None
    status, result = await resolve_project_match(db, project_hint)
    if status != "ok" or not isinstance(result, dict):
        return None
    return result


async def _prepare_pending_entity_from_nl(
    db: aiosqlite.Connection,
    entity_type: str,
    content: str,
    project_hint: str,
    due_date: str,
    source_text: str,
) -> tuple[dict[str, object], str | None]:
    project = await _resolve_project(db, project_hint)
    validated_due_date = validate_and_parse_date(due_date)
    pending_entity = _build_pending_entity(
        entity_type,
        content,
        validated_due_date,
        project["id"] if project else None,
    )
    parsed_event = await create_parsed_event(
        db,
        entity_type=entity_type,
        extracted_json=json.dumps(
            {
                "entity_type": entity_type,
                "content": content,
                "project_hint": project_hint,
                "project_id": project["id"] if project else None,
                "project_name": project["name"] if project else None,
                "due_date": validated_due_date,
                "source_text": source_text,
            }
        ),
    )
    await log_llm_call(db, "intent", "extraction")
    pending_entity["parsed_event_id"] = parsed_event["id"]
    return pending_entity, validated_due_date


def _build_pending_entity(entity_type: str, content: str, due_date: str | None, project_id: int | None) -> dict[str, object]:
    if entity_type == "note":
        return {
            "content": content,
            "project_id": project_id,
            "raw_transcript": content,
            "source": "text",
        }
    if entity_type == "idea":
        return {
            "content": content,
            "project_id": project_id,
            "raw_transcript": content,
            "source": "text",
        }
    if entity_type == "homework":
        return {
            "title": content,
            "description": content,
            "due_date": due_date,
            "course": None,
            "project_id": project_id,
            "source": "text",
        }
    return {
        "title": content,
        "due_date": due_date,
        "project_id": project_id,
        "source": "text",
    }


def _build_due_date_note(entity_type: str, raw_due_date: str, validated_due_date: str | None) -> str:
    if entity_type not in {"deadline", "homework"} or validated_due_date is not None:
        return ""
    if raw_due_date:
        return (
            "\n⚠️ Дата не распознана — можно добавить позже.\n"
            "Напиши: «в пятницу» или /edit due 20 апреля"
        )
    return (
        "\n⚠️ Дата не указана — можно добавить позже.\n"
        "Напиши: «до пятницы» или /edit due 20 апреля"
    )


def _nl_parse_error_text() -> str:
    return (
        "Не совсем понял. Попробуй переформулировать или используй команду:\n"
        "/note текст, /idea текст, /deadline название due дата"
    )


def _type_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📝 Заметка", callback_data="type_note"),
                InlineKeyboardButton("💡 Идея", callback_data="type_idea"),
            ],
            [
                InlineKeyboardButton("📅 Дедлайн", callback_data="type_deadline"),
                InlineKeyboardButton("📚 Домашнее", callback_data="type_homework"),
            ],
        ]
    )


def _content_preview(content: str, max_length: int = 80) -> str:
    preview = " ".join(content.split())
    if len(preview) <= max_length:
        return preview
    return f"{preview[: max_length - 3].rstrip()}..."
