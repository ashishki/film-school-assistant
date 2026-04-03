from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from anthropic import Anthropic, APIConnectionError, APIStatusError, APITimeoutError, RateLimitError


LOGGER = logging.getLogger(__name__)
DEFAULT_INTENT_MODEL = "claude-haiku-4-5"
DEFAULT_REVIEW_MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 3


class LLMError(Exception):
    pass


class LLMSchemaError(LLMError):
    pass


def _get_api_key() -> str:
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("LLM_API_KEY is missing")
    return api_key


def _require_api_key() -> str:
    try:
        return _get_api_key()
    except ValueError as exc:
        raise LLMError("LLM_API_KEY is not set. OpenClaw is unavailable.") from exc


def _get_client() -> Anthropic:
    return Anthropic(api_key=_require_api_key())


def _get_model(category: str) -> str:
    if category == "review":
        return os.environ.get("LLM_MODEL_REVIEW", DEFAULT_REVIEW_MODEL)
    if category == "feature_capture":
        return os.environ.get("LLM_MODEL_FEATURE_CAPTURE", DEFAULT_INTENT_MODEL)
    if category == "feature_spec":
        return os.environ.get("LLM_MODEL_FEATURE_SPEC", DEFAULT_REVIEW_MODEL)
    return os.environ.get("LLM_MODEL_INTENT", DEFAULT_INTENT_MODEL)


def get_model_name(category: str) -> str:
    return _get_model(category)


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (APIConnectionError, APITimeoutError, RateLimitError)):
        return True
    return isinstance(exc, APIStatusError) and exc.status_code >= 500


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def complete(prompt: str, system: str = "", max_tokens: int = 2048, category: str = "unknown") -> str:
    client = _get_client()
    model = _get_model(category)
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=model,
                system=system,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(block.text for block in response.content if block.type == "text").strip()
            LOGGER.info("LLM completion succeeded category=%s model=%s attempt=%s", category, model, attempt)
            return text
        except Exception as exc:
            last_error = exc
            if not _is_retryable(exc) or attempt >= MAX_RETRIES:
                LOGGER.exception("LLM completion failed category=%s model=%s attempt=%s", category, model, attempt)
                break
            LOGGER.warning(
                "Retrying LLM completion category=%s model=%s attempt=%s error=%s",
                category,
                model,
                attempt,
                exc.__class__.__name__,
            )
            time.sleep(0.5 * attempt)

    if last_error is None:
        raise LLMError("LLM completion failed without an error.")
    raise LLMError(f"LLM completion failed for category '{category}': {last_error}") from last_error


def complete_json(prompt: str, system: str = "", category: str = "unknown") -> dict[str, Any] | list[Any]:
    raw_text = complete(prompt=prompt, system=system, max_tokens=2048, category=category)
    cleaned = _strip_code_fences(raw_text)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        LOGGER.warning("LLM returned invalid JSON for category=%s", category)
        raise LLMSchemaError(f"LLM returned invalid JSON for category '{category}'") from exc

    if not isinstance(parsed, (dict, list)):
        raise LLMSchemaError(f"LLM returned unexpected JSON type for category '{category}'")
    return parsed
