import asyncio
import logging
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from src.config import Config


LOGGER = logging.getLogger(__name__)


async def download_voice(update: Update, context: ContextTypes.DEFAULT_TYPE, config: Config) -> str:
    message = update.effective_message
    if message is None or message.voice is None:
        raise ValueError("Voice message is missing from update")

    telegram_file_id = message.voice.file_id
    audio_dir = Path(config.audio_path)
    audio_dir.mkdir(parents=True, exist_ok=True)
    ogg_path = audio_dir / f"{telegram_file_id}.ogg"

    try:
        telegram_file = await context.bot.get_file(telegram_file_id)
        await telegram_file.download_to_drive(custom_path=str(ogg_path))
    except Exception as exc:
        LOGGER.exception("Failed to download Telegram voice file id=%s", telegram_file_id)
        raise RuntimeError(f"Failed to download voice file {telegram_file_id}") from exc

    LOGGER.info("Downloaded voice input file=%s", ogg_path.name)
    return str(ogg_path)


async def convert_to_wav(ogg_path: str) -> str:
    if not ogg_path.endswith(".ogg"):
        raise ValueError(f"Expected .ogg input path, got {ogg_path}")

    ogg_name = Path(ogg_path).name
    wav_path = ogg_path.replace(".ogg", ".wav")
    wav_name = Path(wav_path).name
    command = ["ffmpeg", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path]

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        LOGGER.exception("ffmpeg executable not found while converting file=%s", ogg_name)
        raise RuntimeError("ffmpeg executable not found") from exc
    except OSError as exc:
        LOGGER.exception("Failed to start ffmpeg for file=%s", ogg_name)
        raise RuntimeError(f"Failed to start ffmpeg for {ogg_name}: {exc}") from exc

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        stderr_text = stderr.decode("utf-8", errors="replace").strip()
        LOGGER.error(
            "ffmpeg conversion failed for file=%s with exit code %s: %s",
            ogg_name,
            process.returncode,
            stderr_text,
        )
        raise RuntimeError(stderr_text or f"ffmpeg exited with status {process.returncode}")

    if stdout:
        LOGGER.debug("ffmpeg stdout for file=%s: %s", ogg_name, stdout.decode("utf-8", errors="replace").strip())

    LOGGER.info("Converted voice input to file=%s", wav_name)
    return wav_path
