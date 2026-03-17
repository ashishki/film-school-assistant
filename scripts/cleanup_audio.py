from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config


LOGGER = logging.getLogger(__name__)
TARGET_SUFFIXES = {".ogg", ".wav"}


def configure_logging(level_name: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level_name.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def cleanup_audio_files() -> int:
    config = load_config()
    configure_logging(config.log_level)

    audio_dir = Path(config.audio_path)
    if not audio_dir.exists() or not audio_dir.is_dir():
        LOGGER.warning("Audio directory is missing or not a directory: %s", audio_dir)
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.audio_retention_days)
    deleted_count = 0

    for file_path in audio_dir.iterdir():
        if not file_path.is_file() or file_path.suffix.lower() not in TARGET_SUFFIXES:
            continue

        modified_at = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
        if modified_at >= cutoff:
            continue

        file_path.unlink()
        deleted_count += 1
        LOGGER.info("Deleted expired audio file=%s", file_path.name)

    LOGGER.info("Audio cleanup complete: deleted=%s", deleted_count)
    return deleted_count


def main() -> None:
    try:
        cleanup_audio_files()
    except Exception:
        LOGGER.exception("Audio cleanup run failed")
        raise


if __name__ == "__main__":
    main()
