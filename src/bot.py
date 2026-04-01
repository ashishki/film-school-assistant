from __future__ import annotations

import asyncio
import json
import logging
import sys
from collections import Counter
from pathlib import Path

import aiosqlite
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    TypeHandler,
    filters,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import transcriber, voice
from src.config import load_config
from src.db import (
    create_parsed_event,
    create_transcript,
    create_voice_input,
    get_recent_unconfirmed_events,
    init_db,
    update_voice_input_processed,
)
from src.handlers.chat_handler import handle_chat
from src.handlers.confirm import _build_pending_preview, _do_confirm, _pending_keyboard, confirm_command, discard_command, edit_command
from src.handlers.edit_cmd import edit_deadline_command, edit_idea_command, edit_note_command
from src.handlers.deadlines import deadline_command, dismiss_deadline_command, done_deadline_command
from src.handlers.help_cmd import help_command
from src.handlers.homework import homework_command
from src.handlers.ideas import idea_command
from src.handlers.list_cmd import list_command
from src.handlers.memory_cmd import memory_command
from src.handlers.common import validate_and_parse_date
from src.handlers.nl_handler import _build_pending_entity as build_nl_pending_entity
from src.handlers.nl_handler import _resolve_project
from src.handlers.notes import note_command
from src.handlers.projects import archive_project_command, new_project_command, project_command, projects_command
from src.handlers.reflect_cmd import reflect_command
from src.handlers.review import review_handler
from src.handlers.search_cmd import search_command
from src.state import clear_pending, get_state


LOGGER = logging.getLogger(__name__)
CONFIRM_WORDS = {"да", "ок", "окей", "давай", "сохрани", "сохранить", "подтверждаю", "yes", "yep"}
DISCARD_WORDS = {"нет", "стоп", "удали", "удалить", "отмена", "отменить", "выброси", "no", "nope", "cancel"}


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            log_dict["exc"] = self.formatException(record.exc_info)
        return json.dumps(log_dict, ensure_ascii=False)


async def chat_guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed_chat_id = context.bot_data["allowed_chat_id"]
    chat = update.effective_chat
    if chat is None:
        return
    if chat.id != allowed_chat_id:
        LOGGER.debug("Dropped update from unauthorized chat_id=%s", chat.id)
        raise ApplicationHandlerStop


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.error("Unhandled Telegram bot error", exc_info=context.error)

    if not isinstance(update, Update):
        return

    message = update.effective_message
    if message is None:
        return

    try:
        await message.reply_text("Что-то пошло не так. Попробуй ещё раз.")
    except TelegramError:
        LOGGER.warning("Failed to send generic error reply", exc_info=True)


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    config = context.bot_data["config"]
    if message is None or chat is None or message.voice is None:
        LOGGER.warning("Received voice handler invocation without a voice message")
        return

    state = get_state(chat.id)
    if state.pending_entity is not None:
        await message.reply_text("Есть незавершённая запись. Сначала /confirm, /edit или /discard.")
        return

    await message.reply_text("Расшифровываю...")

    voice_info = message.voice
    ogg_path = str(Path(config.audio_path) / f"{voice_info.file_id}.ogg")

    try:
        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            voice_input = await create_voice_input(
                db,
                telegram_file_id=voice_info.file_id,
                local_path=ogg_path,
                duration_seconds=voice_info.duration,
                telegram_message_id=message.message_id,
            )
    except aiosqlite.Error:
        LOGGER.exception("Failed to create voice_inputs row for message_id=%s", message.message_id)
        await message.reply_text("Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
        return

    try:
        downloaded_ogg_path = await voice.download_voice(update, context, config)
    except Exception:
        LOGGER.exception("Voice download failed for voice_input_id=%s", voice_input["id"])
        await message.reply_text("Не удалось скачать аудио. Попробуй ещё раз.")
        return

    try:
        wav_path = await voice.convert_to_wav(downloaded_ogg_path)
    except Exception:
        LOGGER.exception("Voice conversion failed for voice_input_id=%s", voice_input["id"])
        voice.delete_wav(downloaded_ogg_path)
        await message.reply_text("Ошибка конвертации аудио. Отправь текстом если срочно.")
        return

    try:
        transcript_text = await asyncio.to_thread(transcriber.transcribe, wav_path)
    except Exception:
        LOGGER.exception("Voice transcription failed for voice_input_id=%s", voice_input["id"])
        await message.reply_text("Ошибка расшифровки. Аудио сохранено для повтора.")
        return

    voice.delete_wav(wav_path)

    try:
        detected_type = _detect_entity_type(transcript_text)
        pending_entity = _build_pending_entity(detected_type, transcript_text, state.active_project_id)
        if detected_type in {"deadline", "homework"} and not validate_and_parse_date(str(pending_entity.get("due_date") or "")):
            pending_entity["due_date"] = None

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            transcript = await create_transcript(
                db,
                voice_input_id=voice_input["id"],
                raw_text=transcript_text,
                model_used="small",
            )
            parsed_event = await create_parsed_event(
                db,
                entity_type=detected_type,
                extracted_json=json.dumps(
                    {
                        "suggested_type": detected_type,
                        "project_id": pending_entity.get("project_id"),
                        "content": pending_entity.get("content"),
                        "title": pending_entity.get("title"),
                        "description": pending_entity.get("description"),
                        "raw_transcript": transcript_text,
                    }
                ),
                transcript_id=transcript["id"],
            )
            await update_voice_input_processed(db, voice_input["id"])
    except aiosqlite.Error:
        LOGGER.exception("Failed to persist transcript flow for voice_input_id=%s", voice_input["id"])
        await message.reply_text("Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
        return

    pending_entity["parsed_event_id"] = parsed_event["id"]
    state.pending_entity = pending_entity
    state.pending_entity_type = detected_type

    await message.reply_text(f"Расшифровка: {transcript_text}")
    await message.reply_text(_build_pending_preview(state), reply_markup=_pending_keyboard())
    LOGGER.info(
        "Prepared pending voice entity type=%s parsed_event_id=%s for chat_id=%s",
        detected_type,
        parsed_event["id"],
        chat.id,
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return
    await message.reply_text(
        "Привет.\n\n"
        "Я помогаю режиссёрам и студентам хранить идеи, заметки, дедлайны "
        "и домашние задания — и возвращаться к ним без потерь.\n\n"
        "Для начала создай проект:\n"
        "/new_project <название>\n\n"
        "Потом просто пиши или диктуй — я разберусь сам. "
        "/help покажет все команды."
    )


async def natural_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    if chat is None or message is None:
        return

    state = get_state(chat.id)
    if state.pending_entity is None:
        return

    text = (message.text or "").strip().lower()
    if text in CONFIRM_WORDS:
        await confirm_command(update, context)
        raise ApplicationHandlerStop
    elif text in DISCARD_WORDS:
        await discard_command(update, context)
        raise ApplicationHandlerStop


async def chat_handler_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None or not message.text:
        return
    config = context.bot_data["config"]
    state = get_state(chat.id)
    text = message.text.strip()
    try:
        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            result = await handle_chat(text, db, config, state)
        await message.reply_text(result)
    except Exception:
        LOGGER.exception("chat_handler_wrapper failed for chat_id=%s", chat.id)
        await message.reply_text("Что-то пошло не так. Попробуй ещё раз.")


async def chat_reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None:
        return
    state = get_state(chat.id)
    state.reset_history()
    await message.reply_text("История разговора очищена.")


async def inline_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.message is None:
        return

    await query.answer()
    chat_id = query.message.chat_id
    state = get_state(chat_id)

    if query.data == "confirm":
        if state.pending_entity is None:
            await query.edit_message_text("Нечего сохранять.")
            return
        result_text = await _do_confirm(chat_id, context)
        await query.edit_message_text(result_text)
        return

    if query.data == "discard":
        if state.pending_entity is None:
            await query.edit_message_text("Нечего удалять.")
            return
        clear_pending(chat_id)
        await query.edit_message_text("Запись удалена.")
        return

    if query.data in {"type_note", "type_idea", "type_deadline", "type_homework"}:
        content = state.pending_nl_content
        if not content:
            await query.edit_message_text("Не понял, что сохранять. Напиши это ещё раз.")
            return

        raw_due_date = state.pending_nl_due_date
        due_date = validate_and_parse_date(raw_due_date)
        project_hint = state.pending_nl_project_hint or ""
        entity_type = query.data.removeprefix("type_")

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                project = await _resolve_project(db, project_hint)
                pending_entity = build_nl_pending_entity(entity_type, content, due_date, project["id"] if project else None)
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
                            "due_date": due_date,
                            "source_text": content,
                        }
                    ),
                )
        except aiosqlite.Error:
            LOGGER.exception("Failed to prepare NL pending entity after type selection for chat_id=%s", chat_id)
            await query.edit_message_text("Не получилось подготовить запись. Попробуй ещё раз.")
            return

        pending_entity["parsed_event_id"] = parsed_event["id"]
        state.pending_entity = pending_entity
        state.pending_entity_type = entity_type
        state.pending_nl_content = None
        state.pending_nl_due_date = None
        state.pending_nl_project_hint = None

        preview_text = _build_pending_preview(state)
        if entity_type in {"deadline", "homework"} and due_date is None:
            if raw_due_date:
                preview_text = (
                    f"{preview_text}\n⚠️ Дата не распознана — можно добавить позже.\n"
                    "Напиши: «в пятницу» или /edit due 20 апреля"
                )
            else:
                preview_text = (
                    f"{preview_text}\n⚠️ Дата не указана — можно добавить позже.\n"
                    "Напиши: «до пятницы» или /edit due 20 апреля"
                )
        await query.edit_message_text(preview_text, reply_markup=_pending_keyboard())


def configure_logging(level_name: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    logging.basicConfig(
        level=getattr(logging, level_name.upper(), logging.INFO),
        handlers=[handler],
        force=True,
    )


async def notify_restart_if_pending(application: Application) -> None:
    db_path = application.bot_data["db_path"]
    allowed_chat_id = application.bot_data["allowed_chat_id"]

    try:
        recent_events = await asyncio.to_thread(get_recent_unconfirmed_events, db_path, 2)
    except Exception:
        LOGGER.exception("Failed to query recent unconfirmed parsed events during startup")
        return

    if not recent_events:
        return

    counts = Counter(str(event.get("entity_type") or "unknown") for event in recent_events)
    summary = ", ".join(f"[{entity_type}, {count}]" for entity_type, count in sorted(counts.items()))
    text = f"Бот перезапустился. Незавершённые записи потеряны: {summary}. Повторите ввод."

    try:
        await application.bot.send_message(chat_id=allowed_chat_id, text=text)
    except TelegramError:
        LOGGER.warning("Failed to send restart pending-entity notification", exc_info=True)
        return

    LOGGER.info(
        "Sent restart pending-entity notification to chat_id=%s for %s unconfirmed events",
        allowed_chat_id,
        len(recent_events),
    )


def build_application() -> Application:
    config = load_config()
    configure_logging(config.log_level)
    asyncio.run(init_db(config.db_path))

    application = ApplicationBuilder().token(config.telegram_bot_token).post_init(notify_restart_if_pending).build()
    application.bot_data["config"] = config
    application.bot_data["db_path"] = config.db_path
    application.bot_data["allowed_chat_id"] = config.telegram_allowed_chat_id

    application.add_handler(TypeHandler(Update, chat_guard), group=-1000)
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    application.add_handler(CallbackQueryHandler(inline_action_handler))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("note", note_command))
    application.add_handler(CommandHandler("idea", idea_command))
    application.add_handler(CommandHandler("deadline", deadline_command))
    application.add_handler(CommandHandler("homework", homework_command))
    application.add_handler(CommandHandler("projects", projects_command))
    application.add_handler(CommandHandler("project", project_command))
    application.add_handler(CommandHandler("new_project", new_project_command))
    application.add_handler(CommandHandler("archive_project", archive_project_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("review", review_handler))
    application.add_handler(CommandHandler("memory", memory_command))
    application.add_handler(CommandHandler("reflect", reflect_command))
    application.add_handler(CommandHandler("confirm", confirm_command))
    application.add_handler(CommandHandler("edit", edit_command))
    application.add_handler(CommandHandler("discard", discard_command))
    application.add_handler(CommandHandler("edit_deadline", edit_deadline_command))
    application.add_handler(CommandHandler("edit_note", edit_note_command))
    application.add_handler(CommandHandler("edit_idea", edit_idea_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Regex(r"^/done_deadline_\d+(?:@\w+)?$"), done_deadline_command))
    application.add_handler(MessageHandler(filters.Regex(r"^/dismiss_deadline_\d+(?:@\w+)?$"), dismiss_deadline_command))
    application.add_handler(CommandHandler("chat_reset", chat_reset_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, natural_confirm_handler), group=1)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler_wrapper), group=2)
    application.add_error_handler(error_handler)

    LOGGER.info("Bot application configured")
    return application


def _detect_entity_type(transcript_text: str) -> str:
    lowered = transcript_text.lower()
    if any(keyword in lowered for keyword in ("deadline", "due", "submit")):
        return "deadline"
    if any(keyword in lowered for keyword in ("homework", "assignment")):
        return "homework"
    if any(keyword in lowered for keyword in ("idea", "what if", "imagine")):
        return "idea"
    return "note"


def _build_pending_entity(detected_type: str, transcript_text: str, project_id: int | None) -> dict[str, object]:
    if detected_type == "idea":
        return {
            "content": transcript_text,
            "project_id": project_id,
            "raw_transcript": transcript_text,
            "source": "voice",
        }
    if detected_type == "deadline":
        return {
            "title": transcript_text,
            "due_date": None,
            "project_id": project_id,
            "source": "voice",
        }
    if detected_type == "homework":
        return {
            "title": transcript_text,
            "description": transcript_text,
            "due_date": None,
            "course": None,
            "project_id": project_id,
            "source": "voice",
        }
    return {
        "content": transcript_text,
        "project_id": project_id,
        "raw_transcript": transcript_text,
        "source": "voice",
    }


def _preview_text(text: str, max_length: int = 120) -> str:
    preview = " ".join(text.split())
    if len(preview) <= max_length:
        return preview
    return f"{preview[: max_length - 3].rstrip()}..."


def main() -> None:
    application = build_application()
    LOGGER.info("Starting Telegram bot with long polling")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)
    except (KeyboardInterrupt, SystemExit):
        LOGGER.info("Telegram bot shutdown requested")


if __name__ == "__main__":
    main()
