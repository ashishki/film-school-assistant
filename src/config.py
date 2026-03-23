import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    telegram_allowed_chat_id: int
    db_path: str = "data/assistant.db"
    audio_path: str = "data/audio/"
    audio_retention_days: int = 30
    daily_llm_call_limit: int = 20
    reminder_buckets: tuple[int, ...] = (7, 3, 1, 0)
    log_level: str = "INFO"


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_config() -> Config:
    load_dotenv()

    telegram_bot_token = _require_env("TELEGRAM_BOT_TOKEN")
    allowed_chat_id_raw = _require_env("TELEGRAM_ALLOWED_CHAT_ID")

    try:
        telegram_allowed_chat_id = int(allowed_chat_id_raw)
    except ValueError as exc:
        raise ValueError("TELEGRAM_ALLOWED_CHAT_ID must be an integer") from exc

    reminder_buckets_raw = os.environ.get("REMINDER_BUCKETS", "")
    if not reminder_buckets_raw.strip():
        reminder_buckets = (7, 3, 1, 0)
    else:
        try:
            reminder_buckets = tuple(int(x.strip()) for x in reminder_buckets_raw.split(",") if x.strip())
        except ValueError as exc:
            raise ValueError(
                "REMINDER_BUCKETS must be comma-separated integers, e.g. '7,3,1,0'"
            ) from exc

    config = Config(
        telegram_bot_token=telegram_bot_token,
        telegram_allowed_chat_id=telegram_allowed_chat_id,
        db_path=os.environ.get("DB_PATH", "data/assistant.db"),
        audio_path=os.environ.get("AUDIO_PATH", "data/audio/"),
        audio_retention_days=int(os.environ.get("AUDIO_RETENTION_DAYS", "30")),
        daily_llm_call_limit=int(os.environ.get("DAILY_LLM_CALL_LIMIT", "20")),
        reminder_buckets=reminder_buckets,
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )
    LOGGER.debug("Configuration loaded with db_path=%s audio_path=%s", config.db_path, config.audio_path)
    return config
