from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "telegram" not in sys.modules:
    telegram_module = ModuleType("telegram")
    telegram_error_module = ModuleType("telegram.error")
    telegram_ext_module = ModuleType("telegram.ext")

    class _Update:
        ALL_TYPES = ()

    class _TelegramError(Exception):
        pass

    class _Application:
        pass

    class _ApplicationBuilder:
        def token(self, *_args, **_kwargs):
            return self

        def post_init(self, *_args, **_kwargs):
            return self

        def build(self):
            return _Application()

    class _ApplicationHandlerStop(Exception):
        pass

    class _InlineKeyboardButton:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class _InlineKeyboardMarkup:
        def __init__(self, inline_keyboard):
            self.inline_keyboard = inline_keyboard

    telegram_module.Update = _Update
    telegram_module.InlineKeyboardButton = _InlineKeyboardButton
    telegram_module.InlineKeyboardMarkup = _InlineKeyboardMarkup
    telegram_error_module.TelegramError = _TelegramError
    telegram_ext_module.Application = _Application
    telegram_ext_module.ApplicationBuilder = _ApplicationBuilder
    telegram_ext_module.ApplicationHandlerStop = _ApplicationHandlerStop
    telegram_ext_module.CallbackQueryHandler = object
    telegram_ext_module.CommandHandler = object
    telegram_ext_module.ContextTypes = SimpleNamespace(DEFAULT_TYPE=object)
    telegram_ext_module.MessageHandler = object
    telegram_ext_module.TypeHandler = object
    telegram_ext_module.filters = SimpleNamespace(
        VOICE=object(),
        TEXT=object(),
        COMMAND=object(),
        Regex=lambda _pattern: object(),
    )

    sys.modules["telegram"] = telegram_module
    sys.modules["telegram.error"] = telegram_error_module
    sys.modules["telegram.ext"] = telegram_ext_module

if "whisper" not in sys.modules:
    whisper_module = ModuleType("whisper")

    class _WhisperModel:
        def transcribe(self, _wav_path):
            return {"text": ""}

    def _load_model(_model_name):
        return _WhisperModel()

    whisper_module.load_model = _load_model
    sys.modules["whisper"] = whisper_module

if "dateutil" not in sys.modules:
    dateutil_module = ModuleType("dateutil")
    dateutil_parser_module = ModuleType("dateutil.parser")

    def _parse(value, default=None, fuzzy=False):
        del fuzzy
        if default is not None:
            return default
        return datetime.fromisoformat(value)

    dateutil_parser_module.parse = _parse
    dateutil_module.parser = dateutil_parser_module
    sys.modules["dateutil"] = dateutil_module
    sys.modules["dateutil.parser"] = dateutil_parser_module

if "anthropic" not in sys.modules:
    anthropic_module = ModuleType("anthropic")

    class _Anthropic:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class _APIConnectionError(Exception):
        pass

    class _APIStatusError(Exception):
        status_code = 500

    class _APITimeoutError(Exception):
        pass

    class _RateLimitError(Exception):
        pass

    anthropic_module.Anthropic = _Anthropic
    anthropic_module.APIConnectionError = _APIConnectionError
    anthropic_module.APIStatusError = _APIStatusError
    anthropic_module.APITimeoutError = _APITimeoutError
    anthropic_module.RateLimitError = _RateLimitError
    sys.modules["anthropic"] = anthropic_module

if "dotenv" not in sys.modules:
    dotenv_module = ModuleType("dotenv")

    def _load_dotenv(*_args, **_kwargs):
        return False

    dotenv_module.load_dotenv = _load_dotenv
    sys.modules["dotenv"] = dotenv_module

# Must import after path setup
from src import db as db_module
from src.bot import voice_handler
from src.state import get_state, clear_pending

logging.basicConfig(level=logging.WARNING)
LOGGER = logging.getLogger(__name__)

CHAT_ID = 999
FILE_ID = "test_file_id_abc123"
TRANSCRIPT = "Записал идею про новый фильм"


def _make_update():
    """Build a minimal fake Update with a voice message."""
    voice = MagicMock()
    voice.file_id = FILE_ID
    voice.duration = 5

    message = MagicMock()
    message.voice = voice
    message.message_id = 42
    message.reply_text = AsyncMock()

    chat = MagicMock()
    chat.id = CHAT_ID

    update = MagicMock()
    update.effective_message = message
    update.effective_chat = chat
    return update


def _make_context(db_path: str):
    """Build a minimal fake ContextTypes.DEFAULT_TYPE."""
    config = MagicMock()
    config.audio_path = tempfile.mkdtemp()

    context = MagicMock()
    context.bot_data = {
        "config": config,
        "db_path": db_path,
    }
    return context


async def run_test() -> None:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # Initialize the database schema
        await db_module.init_db(db_path)

        update = _make_update()
        context = _make_context(db_path)

        # Clear any leftover state
        clear_pending(CHAT_ID)

        # Patch: voice.download_voice → return a fake OGG path (file doesn't need to exist)
        fake_ogg = str(Path(context.bot_data["config"].audio_path) / f"{FILE_ID}.ogg")
        # Patch: voice.convert_to_wav → return a fake WAV path
        fake_wav = fake_ogg.replace(".ogg", ".wav")

        with (
            patch("src.bot.voice.download_voice", new=AsyncMock(return_value=fake_ogg)),
            patch("src.bot.voice.convert_to_wav", new=AsyncMock(return_value=fake_wav)),
            patch("src.bot.voice.delete_wav", return_value=None),
            patch("src.bot.transcriber.transcribe", return_value=TRANSCRIPT),
        ):
            await voice_handler(update, context)

        # Assertions:
        # 1. State has pending_entity set
        state = get_state(CHAT_ID)
        assert state.pending_entity is not None, "pending_entity must be set after voice_handler"
        assert state.pending_entity_type is not None, "pending_entity_type must be set after voice_handler"

        # 2. voice_inputs row created
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM voice_inputs WHERE telegram_file_id=?", (FILE_ID,))
            voice_row = await cursor.fetchone()
            await cursor.close()
            assert voice_row is not None, "voice_inputs row must be created"
            assert voice_row["processed_at"] is not None, "voice_inputs.processed_at must be set"

            # 3. transcript row created
            cursor = await db.execute("SELECT * FROM transcripts WHERE voice_input_id=?", (voice_row["id"],))
            transcript_row = await cursor.fetchone()
            await cursor.close()
            assert transcript_row is not None, "transcripts row must be created"
            assert transcript_row["raw_text"] == TRANSCRIPT, "transcript raw_text must match"

            # 4. parsed_event row created
            cursor = await db.execute("SELECT * FROM parsed_events WHERE transcript_id=?", (transcript_row["id"],))
            event_row = await cursor.fetchone()
            await cursor.close()
            assert event_row is not None, "parsed_events row must be created"
            assert event_row["confirmed"] == 0, "parsed_event must start unconfirmed"

        print("PASS")
        sys.exit(0)

    except Exception as exc:
        LOGGER.exception("Voice pipeline test failed")
        print(f"FAIL: {exc}")
        sys.exit(1)
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    asyncio.run(run_test())
