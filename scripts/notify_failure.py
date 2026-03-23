from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config


LOGGER = logging.getLogger(__name__)
TELEGRAM_API_TIMEOUT = 15
TELEGRAM_MAX_RETRIES = 3


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


def send_telegram_message(bot_token: str, chat_id: int, message_text: str) -> None:
    last_error: Exception | None = None

    for attempt in range(1, TELEGRAM_MAX_RETRIES + 1):
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": message_text},
                timeout=TELEGRAM_API_TIMEOUT,
            )
            if response.status_code >= 500:
                response.raise_for_status()
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                raise RuntimeError(f"Telegram API returned ok={payload.get('ok')}")
            return
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_error = exc
        except requests.HTTPError as exc:
            last_error = exc
            response = exc.response
            if response is None or response.status_code < 500:
                raise
        if attempt >= TELEGRAM_MAX_RETRIES:
            break
        time.sleep(0.5 * attempt)

    if last_error is None:
        last_error = RuntimeError("Telegram send failed without an exception.")
    raise last_error


def main() -> int:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

    try:
        config = load_config()
        unit_name = os.environ.get("FAILED_UNIT", "").strip()
        if not unit_name:
            unit_name = "unknown"
        message_text = (
            f"⚠️ Systemd unit failed: {unit_name}\n"
            f"Check: journalctl -u {unit_name} -n 50"
        )
        send_telegram_message(config.telegram_bot_token, config.telegram_allowed_chat_id, message_text)
        return 0
    except Exception:
        LOGGER.exception("Failure notification failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
