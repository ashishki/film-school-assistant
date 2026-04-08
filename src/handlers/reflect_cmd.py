import asyncio
import json
import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.config import Config
from src.db import get_llm_calls_today, get_memory_items_for_project, get_project_memory, log_llm_call
from src.handlers.common import reply_text
from src.openclaw_client import LLMError, complete_json
from src.state import get_state
from src.user_context import get_user_context_prompt_text, refresh_user_context_summary


LOGGER = logging.getLogger(__name__)

REFLECT_SYSTEM_PROMPT = (
    "Ты — творческий советник режиссёра. Проанализируй состояние проекта на основе данных ниже.\n"
    "Правила:\n"
    "- Используй ТОЛЬКО данные из контекста. Не выдумывай.\n"
    "- Никаких общих советов («доверяй интуиции», «исследуй темы»).\n"
    "- Творческие напряжения — конкретные, из идей и разборов, не абстрактные.\n"
    "- Фокус — одно конкретное действие на следующую рабочую сессию.\n"
    'Return JSON: {"project_standing": "...", "tensions": "...", "focus_recommendation": "..."}\n'
    "Ответ на русском языке."
)


async def _fetch_recent_review_rows(db: aiosqlite.Connection, project_id: int) -> list[dict]:
    cursor = await db.execute(
        """
        SELECT rh.response_json, rh.created_at
        FROM review_history rh
        JOIN ideas i ON i.id = rh.idea_id
        WHERE i.project_id = ?
        ORDER BY rh.created_at DESC
        LIMIT 5
        """,
        (project_id,),
    )
    rows = await cursor.fetchall()
    await cursor.close()
    return [dict(row) for row in rows]


async def _fetch_active_deadlines(db: aiosqlite.Connection, project_id: int) -> list[dict]:
    cursor = await db.execute(
        """
        SELECT title, due_date
        FROM deadlines
        WHERE project_id = ? AND status = 'active'
        ORDER BY due_date ASC
        LIMIT 5
        """,
        (project_id,),
    )
    rows = await cursor.fetchall()
    await cursor.close()
    return [dict(row) for row in rows]


def _extract_next_steps(review_rows: list[dict]) -> list[str]:
    next_steps: list[str] = []
    for row in review_rows:
        raw_response = row.get("response_json")
        if not raw_response:
            continue

        try:
            parsed = json.loads(str(raw_response))
        except (TypeError, ValueError):
            continue

        if not isinstance(parsed, dict):
            continue

        next_step = str(parsed.get("next_step", "")).strip()
        next_step = next_step[:200]
        if next_step:
            next_steps.append(next_step)

    return next_steps


def _build_input_text(
    project_name: str,
    summary_text: str,
    next_steps: list[str],
    deadlines: list[dict],
    user_context_text: str | None,
    evidence_snippets: list[dict] | None = None,
) -> str:
    parts: list[str] = []
    if user_context_text:
        parts.append(user_context_text)
    parts.append(f"Проект: {project_name}")
    parts.append(f"Текущее состояние (из памяти проекта):\n{summary_text}")
    if evidence_snippets:
        lines = ["Verbatim evidence (последние записи с провенансом):"]
        for item in evidence_snippets:
            kind = item.get("source_kind", "запись")
            src_id = item.get("source_id", "?")
            text = str(item.get("content", "")).strip()
            if len(text) > 200:
                text = text[:200].rstrip() + "..."
            lines.append(f"[{kind}#{src_id}] {text}")
        parts.append("\n".join(lines))
    if next_steps:
        parts.append(
            "Рекомендации из последних разборов идей:\n"
            + "\n".join(f"- {step}" for step in next_steps)
        )
    if deadlines:
        parts.append(
            "Активные дедлайны:\n"
            + "\n".join(f"- {d['title']} (срок: {d['due_date'] or 'не указан'})" for d in deadlines)
        )
    return "\n\n".join(parts)


def _format_reflection(response: dict) -> str:
    standing = str(response.get("project_standing", "")).strip() or "[нет данных]"
    tensions = str(response.get("tensions", "")).strip() or "[нет данных]"
    focus = str(response.get("focus_recommendation", "")).strip() or "[нет данных]"
    return (
        f"Состояние проекта:\n{standing}\n\n"
        f"Творческие напряжения:\n{tensions}\n\n"
        f"Фокус:\n{focus}"
    )


async def run_project_reflect(
    db: aiosqlite.Connection,
    project_id: int,
    project_name: str,
    config: Config,
) -> str | None:
    memory_row = await get_project_memory(db, project_id)
    if memory_row is None:
        LOGGER.info("No project memory found for reflection project_id=%s", project_id)
        return None

    try:
        evidence_snippets = await get_memory_items_for_project(db, project_id, limit=5)
    except Exception:
        LOGGER.warning("Failed to fetch evidence snippets for project reflection project_id=%s", project_id)
        evidence_snippets = []

    review_rows = await _fetch_recent_review_rows(db, project_id)
    next_steps = _extract_next_steps(review_rows)
    deadlines = await _fetch_active_deadlines(db, project_id)

    try:
        await refresh_user_context_summary(db, config.daily_llm_call_limit)
        user_context_text = await get_user_context_prompt_text(db)
    except Exception:
        LOGGER.warning("Failed to fetch user context for project reflection project_id=%s", project_id)
        user_context_text = None

    input_text = _build_input_text(
        project_name,
        memory_row["summary_text"],
        next_steps,
        deadlines,
        user_context_text,
        evidence_snippets=evidence_snippets or None,
    )

    try:
        response = await asyncio.to_thread(
            complete_json,
            input_text,
            REFLECT_SYSTEM_PROMPT,
            "review",
        )
    except LLMError:
        LOGGER.exception("Failed to generate reflection for project_id=%s", project_id)
        return None

    if not isinstance(response, dict):
        LOGGER.warning("Reflection response was not a JSON object for project_id=%s", project_id)
        return None

    return _format_reflection(response)


async def reflect_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat = update.effective_chat
        if chat is None:
            LOGGER.warning("Received /reflect without effective chat")
            return

        chat_id = chat.id
        state = get_state(chat_id)
        if state.active_project_id is None:
            await reply_text(update, context, "Сначала выбери проект: /project <название>")
            return

        project_id = state.active_project_id
        project_name = state.active_project_name or f"#{project_id}"

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row

                daily_llm_call_limit = context.bot_data["config"].daily_llm_call_limit
                today_calls = await get_llm_calls_today(db)
                if today_calls >= daily_llm_call_limit:
                    await reply_text(update, context, "Дневной лимит запросов исчерпан. Попробуй завтра.")
                    return

                result = await run_project_reflect(
                    db,
                    project_id,
                    project_name,
                    context.bot_data["config"],
                )
                if result is None:
                    await reply_text(update, context, "Не удалось сформировать рефлексию. Попробуй ещё раз.")
                    return

                try:
                    await log_llm_call(db, "review", "reflect")
                except aiosqlite.Error:
                    LOGGER.warning(
                        "Failed to log LLM call for /reflect project_id=%s",
                        project_id,
                        exc_info=True,
                    )

        except aiosqlite.Error:
            LOGGER.exception("Database failure during /reflect for project_id=%s", project_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        await reply_text(update, context, result)
        LOGGER.info("Completed /reflect for project_id=%s", project_id)
    except Exception:
        LOGGER.exception("Unhandled reflect command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
