from __future__ import annotations

import asyncio
import aiosqlite

from src.db import (
    get_llm_calls_today,
    get_user_context_entry_count,
    get_user_context_summary,
    list_user_context_entries,
    log_llm_call,
    upsert_user_context_summary,
)
from src.openclaw_client import LLMError, complete
from src.openclaw_client import get_model_name


SAVE_CONTEXT_MARKERS = (
    "сохрани это сообщение обо мне",
    "сохрани это обо мне",
    "сохрани это как контекст обо мне",
    "сохрани контекст обо мне",
    "запомни обо мне",
    "добавь контекст обо мне",
    "это контекст обо мне",
    "это информация обо мне",
)
SELF_REFERENCE_MARKERS = (
    "обо мне",
    "о себе",
    "мой контекст",
    "контекст обо мне",
)
ASSISTANT_CONTEXT_PROMPTS = (
    "расскажи мне о себе",
    "расскажи о себе",
    "чтобы я лучше понимал твою ситуацию",
    "я готов слушать и записывать информацию о себе",
)
USER_CONTEXT_SUMMARY_SYSTEM_PROMPT = (
    "Ты собираешь краткий рабочий профиль пользователя для кино-ассистента.\n"
    "Используй только факты из входных данных.\n"
    "Сделай компактный профиль в 5-7 строках.\n"
    "Каждая строка формата: «Метка: значение».\n"
    "Нужные зоны: роль и этап, учебный контекст, творческие интересы, рабочий стиль, текущие блокировки, ближайший проект, предпочтительный тип помощи.\n"
    "Без выдумки, без советов, без повторов."
)


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def is_user_context_capture_request(text: str, last_assistant_message: str | None = None) -> bool:
    lowered = _normalize(text)
    if not lowered:
        return False

    if any(marker in lowered for marker in SAVE_CONTEXT_MARKERS):
        return True

    if "сохрани" in lowered and any(marker in lowered for marker in SELF_REFERENCE_MARKERS):
        return True

    if last_assistant_message:
        assistant_lowered = _normalize(last_assistant_message)
        if (
            any(marker in assistant_lowered for marker in ASSISTANT_CONTEXT_PROMPTS)
            and len(text.strip()) >= 160
            and any(marker in lowered for marker in ("меня зовут", "я ", "мне ", "мой "))
        ):
            return True

    return False


def extract_user_context_content(text: str) -> str:
    stripped = text.strip()
    lines = [line.strip() for line in stripped.splitlines()]
    if not lines:
        return stripped

    first_line = _normalize(lines[0])
    if any(marker in first_line for marker in SAVE_CONTEXT_MARKERS):
        remainder = "\n".join(line for line in lines[1:] if line).strip()
        if remainder:
            return remainder

    return stripped


def build_user_context_pending_entity(text: str, source: str = "text") -> dict[str, object]:
    content = extract_user_context_content(text)
    return {
        "content": content,
        "raw_transcript": text,
        "source": source,
    }


def _truncate_text(value: str, limit: int = 320) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit].rstrip()}..."


async def get_user_context_prompt_text(
    db: aiosqlite.Connection,
    limit: int = 3,
    max_chars: int = 1200,
) -> str | None:
    summary_row = await get_user_context_summary(db)
    entry_count = await get_user_context_entry_count(db)
    if summary_row is not None and int(summary_row.get("entry_count_snapshot") or 0) == entry_count:
        summary_text = str(summary_row.get("summary_text") or "").strip()
        if summary_text:
            return "Профиль пользователя:\n" + summary_text

    entries = await list_user_context_entries(db, limit=limit)
    if not entries:
        return None

    ordered_entries = list(reversed(entries))
    lines: list[str] = []
    total_chars = 0
    for entry in ordered_entries:
        content = _truncate_text(str(entry.get("content") or ""))
        if not content:
            continue
        line = f"- {content}"
        if total_chars + len(line) > max_chars:
            break
        lines.append(line)
        total_chars += len(line)

    if not lines:
        return None
    return "Контекст о пользователе:\n" + "\n".join(lines)


def _build_summary_input(entries: list[dict[str, object]]) -> str:
    ordered_entries = list(reversed(entries))
    lines = []
    for index, entry in enumerate(ordered_entries, start=1):
        content = str(entry.get("content") or "").strip()
        if not content:
            continue
        lines.append(f"{index}. {content}")
    return "\n\n".join(lines)


async def refresh_user_context_summary(db: aiosqlite.Connection, daily_llm_call_limit: int | None = None) -> str | None:
    entries = await list_user_context_entries(db, limit=10)
    if not entries:
        return None

    entry_count = await get_user_context_entry_count(db)
    existing_summary = await get_user_context_summary(db)
    if existing_summary is not None and int(existing_summary.get("entry_count_snapshot") or 0) == entry_count:
        summary_text = str(existing_summary.get("summary_text") or "").strip()
        return summary_text or None

    if daily_llm_call_limit is not None:
        calls_today = await get_llm_calls_today(db)
        if calls_today >= daily_llm_call_limit:
            return None

    input_text = _build_summary_input(entries)
    try:
        summary_text = await asyncio.to_thread(
            complete,
            input_text,
            USER_CONTEXT_SUMMARY_SYSTEM_PROMPT,
            300,
            "intent",
        )
    except LLMError:
        return None

    summary_text = summary_text.strip()
    if not summary_text:
        return None

    await log_llm_call(db, get_model_name("intent"), "user_context_summary")
    await upsert_user_context_summary(db, summary_text, entry_count, get_model_name("intent"))
    return summary_text
