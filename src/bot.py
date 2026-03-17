from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

import aiosqlite
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ApplicationHandlerStop,
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
from src.db import create_parsed_event, create_transcript, create_voice_input, init_db, update_voice_input_processed
from src.handlers.confirm import confirm_command, discard_command, edit_command
from src.handlers.deadlines import deadline_command, dismiss_deadline_command, done_deadline_command
from src.handlers.help_cmd import help_command
from src.handlers.homework import homework_command
from src.handlers.ideas import idea_command
from src.handlers.list_cmd import list_command
from src.handlers.common import validate_and_parse_date
from src.handlers.nl_handler import nl_handler
from src.handlers.notes import note_command
from src.handlers.projects import project_command, projects_command
from src.handlers.review import review_handler
from src.state import get_state


LOGGER = logging.getLogger(__name__)


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
        await message.reply_text("Something went wrong. Please try again.")
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
        await message.reply_text("You have a pending item. /confirm, /edit, or /discard first.")
        return

    await message.reply_text("Transcribing...")

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
        await message.reply_text("Could not save. Please try again. (ERR:DB)")
        return

    try:
        downloaded_ogg_path = await voice.download_voice(update, context, config)
    except Exception:
        LOGGER.exception("Voice download failed for voice_input_id=%s", voice_input["id"])
        await message.reply_text("Could not download audio. Please try again.")
        return

    try:
        wav_path = await voice.convert_to_wav(downloaded_ogg_path)
    except Exception:
        LOGGER.exception("Voice conversion failed for voice_input_id=%s", voice_input["id"])
        await message.reply_text("Audio conversion failed. Send as text if urgent.")
        return

    try:
        transcript_text = await asyncio.to_thread(transcriber.transcribe, wav_path)
    except Exception:
        LOGGER.exception("Voice transcription failed for voice_input_id=%s", voice_input["id"])
        await message.reply_text("Transcription failed. Your audio has been saved for retry.")
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
        await message.reply_text("Could not save. Please try again. (ERR:DB)")
        return

    pending_entity["parsed_event_id"] = parsed_event["id"]
    state.pending_entity = pending_entity
    state.pending_entity_type = detected_type

    await message.reply_text(f"Transcript: {transcript_text}")
    await message.reply_text(
        f"I think this is a {detected_type}. Save as: {_preview_text(transcript_text)}\n"
        "Reply /confirm, /edit, or /discard."
    )
    LOGGER.info(
        "Prepared pending voice entity type=%s parsed_event_id=%s for chat_id=%s",
        detected_type,
        parsed_event["id"],
        chat.id,
    )


def configure_logging(level_name: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level_name.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def build_application() -> Application:
    config = load_config()
    configure_logging(config.log_level)
    asyncio.run(init_db(config.db_path))

    application = ApplicationBuilder().token(config.telegram_bot_token).build()
    application.bot_data["config"] = config
    application.bot_data["db_path"] = config.db_path
    application.bot_data["allowed_chat_id"] = config.telegram_allowed_chat_id

    application.add_handler(TypeHandler(Update, chat_guard), group=-1000)
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    application.add_handler(CommandHandler("note", note_command))
    application.add_handler(CommandHandler("idea", idea_command))
    application.add_handler(CommandHandler("deadline", deadline_command))
    application.add_handler(CommandHandler("homework", homework_command))
    application.add_handler(CommandHandler("projects", projects_command))
    application.add_handler(CommandHandler("project", project_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("review", review_handler))
    application.add_handler(CommandHandler("confirm", confirm_command))
    application.add_handler(CommandHandler("edit", edit_command))
    application.add_handler(CommandHandler("discard", discard_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Regex(r"^/done_deadline_\d+(?:@\w+)?$"), done_deadline_command))
    application.add_handler(MessageHandler(filters.Regex(r"^/dismiss_deadline_\d+(?:@\w+)?$"), dismiss_deadline_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, nl_handler))
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
