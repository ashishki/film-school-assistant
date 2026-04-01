import asyncio
import json
import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import get_llm_calls_today, get_project_memory, log_llm_call
from src.handlers.common import reply_text
from src.openclaw_client import LLMError, complete_json
from src.state import get_state


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
        if next_step:
            next_steps.append(next_step)

    return next_steps


def _build_input_text(
    project_name: str,
    summary_text: str,
    next_steps: list[str],
    deadlines: list[dict],
) -> str:
    return (
        f"Проект: {project_name}\n\n"
        f"Текущее состояние (из памяти проекта):\n{summary_text}\n\n"
        + (
            "Рекомендации из последних разборов идей:\n"
            + "\n".join(f"- {step}" for step in next_steps)
            + "\n\n"
            if next_steps
            else ""
        )
        + (
            "Активные дедлайны:\n"
            + "\n".join(f"- {deadline['title']} (срок: {deadline['due_date'] or 'не указан'})" for deadline in deadlines)
            if deadlines
            else ""
        )
    )


def _format_reflection(response: dict) -> str:
    standing = str(response.get("project_standing", "")).strip() or "[нет данных]"
    tensions = str(response.get("tensions", "")).strip() or "[нет данных]"
    focus = str(response.get("focus_recommendation", "")).strip() or "[нет данных]"
    return (
        f"Состояние проекта:\n{standing}\n\n"
        f"Творческие напряжения:\n{tensions}\n\n"
        f"Фокус:\n{focus}"
    )


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

                memory_row = await get_project_memory(db, project_id)
                if memory_row is None:
                    await reply_text(update, context, "Нет памяти для этого проекта. Сначала выполни /memory.")
                    return

                review_rows = await _fetch_recent_review_rows(db, project_id)
                next_steps = _extract_next_steps(review_rows)
                deadlines = await _fetch_active_deadlines(db, project_id)

                daily_llm_call_limit = context.bot_data["config"].daily_llm_call_limit
                today_calls = await get_llm_calls_today(db)
                if today_calls >= daily_llm_call_limit:
                    await reply_text(update, context, "Дневной лимит запросов исчерпан. Попробуй завтра.")
                    return

                input_text = _build_input_text(project_name, memory_row["summary_text"], next_steps, deadlines)

                try:
                    response = await asyncio.to_thread(
                        complete_json,
                        input_text,
                        REFLECT_SYSTEM_PROMPT,
                        "review",
                    )
                except LLMError:
                    LOGGER.exception("Failed to generate reflection for project_id=%s", project_id)
                    await reply_text(update, context, "Не удалось сформировать рефлексию. Попробуй ещё раз.")
                    return

                if not isinstance(response, dict):
                    LOGGER.warning("Reflection response was not a JSON object for project_id=%s", project_id)
                    await reply_text(update, context, "Не удалось сформировать рефлексию. Попробуй ещё раз.")
                    return

                await log_llm_call(db, "review", "reflect")

        except aiosqlite.Error:
            LOGGER.exception("Database failure during /reflect for project_id=%s", project_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        await reply_text(update, context, _format_reflection(response))
        LOGGER.info("Completed /reflect for project_id=%s", project_id)
    except Exception:
        LOGGER.exception("Unhandled reflect command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
