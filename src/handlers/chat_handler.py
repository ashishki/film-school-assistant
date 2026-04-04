from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import aiosqlite
import anthropic
from anthropic import AsyncAnthropic

from src.config import Config
from src.db import get_llm_calls_today, get_project_memory, log_llm_call
from src.state import UserState
from src.tools import TOOLS, execute_tool
from src.user_context import get_user_context_prompt_text, refresh_user_context_summary


LOGGER = logging.getLogger(__name__)

_BASE_SYSTEM_PROMPT: str = (
    "Ты — помощник студента кинематографического факультета. "
    "Отвечаешь всегда на русском языке. "
    "Для сохранения и получения данных используй только инструменты (tools). "
    "Не выдумывай сущности, которых ты не получал через инструменты."
)
CHAT_SYSTEM_PROMPT = _BASE_SYSTEM_PROMPT  # backward-compat alias
MAX_TOOL_ROUNDS: int = 5


def _build_system_prompt(memory_text: str | None, user_context_text: str | None) -> str:
    sections = [_BASE_SYSTEM_PROMPT]
    if user_context_text:
        sections.append(user_context_text)
    if memory_text:
        sections.append(f"Контекст проекта: {memory_text}")
    return "\n\n".join(sections)


def _extract_text_blocks(response: Any) -> str:
    parts: list[str] = []
    for block in response.content:
        if getattr(block, "type", None) == "text" and getattr(block, "text", ""):
            parts.append(block.text)
    return "".join(parts).strip()


async def handle_chat(
    message_text: str,
    db: aiosqlite.Connection,
    config: Config,
    user_state: UserState,
) -> str:
    calls_today = await get_llm_calls_today(db)
    if calls_today >= config.daily_llm_call_limit:
        return "Дневной лимит запросов исчерпан. Попробуй завтра."

    project_id = user_state.active_project_id
    if project_id is not None:
        try:
            memory_row = await get_project_memory(db, project_id)
            memory_text = memory_row["summary_text"] if memory_row else None
        except Exception:
            LOGGER.warning(
                "memory injection failed: could not read project memory for project_id=%s, proceeding without it",
                project_id,
            )
            memory_text = None
    else:
        memory_text = None

    try:
        await refresh_user_context_summary(db, config.daily_llm_call_limit)
        user_context_text = await get_user_context_prompt_text(db)
    except Exception:
        LOGGER.warning("user context injection failed, proceeding without it", exc_info=True)
        user_context_text = None

    system_prompt = _build_system_prompt(memory_text, user_context_text)

    messages: list[dict[str, Any]] = user_state.conversation_history[:] + [
        {"role": "user", "content": message_text}
    ]

    api_key = os.environ.get("LLM_API_KEY", "")
    if not api_key:
        return "Ошибка: API ключ не настроен."

    model = os.environ.get("LLM_MODEL_INTENT", "claude-haiku-4-5")
    client = AsyncAnthropic(api_key=api_key)

    round_counter = 0
    last_response: Any | None = None
    last_assistant_message = ""

    while True:
        try:
            for attempt in range(1, 4):
                try:
                    response = await client.messages.create(
                        model=model,
                        system=system_prompt,
                        max_tokens=1024,
                        messages=messages,
                        tools=TOOLS,
                    )
                    break
                except (
                    anthropic.APIConnectionError,
                    anthropic.APITimeoutError,
                    anthropic.RateLimitError,
                ):
                    if attempt >= 3:
                        raise
                    await asyncio.sleep(0.5 * attempt)
            await log_llm_call(db, model, "chat")
        except Exception:
            LOGGER.exception("Claude chat request failed")
            return "Произошла ошибка при обращении к Claude. Попробуй ещё раз."

        last_response = response
        current_text = _extract_text_blocks(response)
        if current_text:
            last_assistant_message = current_text

        if response.stop_reason != "tool_use":
            break

        tool_blocks = [block for block in response.content if getattr(block, "type", None) == "tool_use"]
        tool_results: list[str] = []
        for block in tool_blocks:
            result = await execute_tool(block.name, block.input, db, config, user_state)
            tool_results.append(result)

        messages.append({"role": "assistant", "content": response.content})
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                    for block, result in zip(tool_blocks, tool_results, strict=True)
                ],
            }
        )

        round_counter += 1
        if round_counter >= MAX_TOOL_ROUNDS:
            LOGGER.warning("Chat tool-use loop guard fired after %s rounds", round_counter)
            break

    final_text = _extract_text_blocks(last_response) if last_response is not None else ""
    if not final_text:
        final_text = last_assistant_message
    if not final_text:
        return "Нет ответа от Claude."

    user_state.add_message("user", message_text)
    user_state.add_message("assistant", final_text)
    return final_text
