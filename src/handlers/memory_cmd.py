import asyncio
import logging
import os
from datetime import datetime, timezone

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import get_llm_calls_today, get_project_item_count, get_project_memory, log_llm_call, upsert_project_memory
from src.handlers.common import reply_text
from src.openclaw_client import LLMError, complete
from src.state import get_state


LOGGER = logging.getLogger(__name__)

MEMORY_SYSTEM_PROMPT = (
    "Ты — помощник режиссёра. Опиши текущее состояние проекта, основываясь ТОЛЬКО на данных ниже.\n"
    "Не выдумывай ничего, чего нет в данных. Не давай советов.\n"
    "Используй ровно этот формат — четыре поля, каждое с новой строки:\n"
    "Фокус: {одно предложение о текущем творческом или практическом центре проекта}\n"
    "Открытые вопросы: {2–3 активных нерешённых вопроса через точку с запятой}\n"
    "Последнее: {что появилось или изменилось в последней активности}\n"
    "Следующий шаг: {одно конкретное действие для следующей сессии}\n"
    "Если данных недостаточно для поля — напиши «нет данных»."
)


async def _fetch_records(
    db: aiosqlite.Connection,
    project_id: int,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    notes_cursor = await db.execute(
        """
        SELECT content, created_at
        FROM notes
        WHERE project_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (project_id,),
    )
    note_rows = await notes_cursor.fetchall()
    await notes_cursor.close()

    ideas_cursor = await db.execute(
        """
        SELECT content, created_at
        FROM ideas
        WHERE project_id = ?
        ORDER BY created_at DESC
        LIMIT 10
        """,
        (project_id,),
    )
    idea_rows = await ideas_cursor.fetchall()
    await ideas_cursor.close()

    deadlines_cursor = await db.execute(
        """
        SELECT title, due_date, status
        FROM deadlines
        WHERE project_id = ? AND status = 'active'
        ORDER BY due_date ASC
        LIMIT 10
        """,
        (project_id,),
    )
    deadline_rows = await deadlines_cursor.fetchall()
    await deadlines_cursor.close()

    homework_cursor = await db.execute(
        """
        SELECT title, due_date
        FROM homework
        WHERE project_id = ? AND status = 'pending'
        ORDER BY due_date ASC
        LIMIT 10
        """,
        (project_id,),
    )
    homework_rows = await homework_cursor.fetchall()
    await homework_cursor.close()

    return (
        [dict(row) for row in note_rows],
        [dict(row) for row in idea_rows],
        [dict(row) for row in deadline_rows],
        [dict(row) for row in homework_rows],
    )


def _truncate_text(value: str, limit: int = 100) -> str:
    return value[:limit]


def _build_input_text(
    project_name: str,
    notes: list[dict],
    ideas: list[dict],
    deadlines: list[dict],
    homework: list[dict],
) -> str:
    return (
        f"Проект: {project_name}\n\n"
        + (
            f"Заметки ({len(notes)}):\n"
            + "\n".join(f"- {_truncate_text(note['content'])}" for note in notes)
            + "\n\n"
            if notes
            else ""
        )
        + (
            f"Идеи ({len(ideas)}):\n"
            + "\n".join(f"- {_truncate_text(idea['content'])}" for idea in ideas)
            + "\n\n"
            if ideas
            else ""
        )
        + (
            f"Активные дедлайны ({len(deadlines)}):\n"
            + "\n".join(
                f"- {deadline['title']} (срок: {deadline['due_date'] or 'не указан'})"
                for deadline in deadlines
            )
            + "\n\n"
            if deadlines
            else ""
        )
        + (
            f"Домашние задания ({len(homework)}):\n"
            + "\n".join(
                f"- {hw['title']} (срок: {hw['due_date'] or 'не указан'})"
                for hw in homework
            )
            if homework
            else ""
        )
    )


def _check_summary_staleness(
    existing_memory: dict | None,
    current_count: int,
    staleness_days: int,
) -> tuple[bool, str]:
    """Return (is_stale, reason). reason is logged and shown in debug output."""
    if existing_memory is None:
        return True, "no_summary_exists"
    if existing_memory["item_count_snapshot"] != current_count:
        return True, f"item_count_changed:{existing_memory['item_count_snapshot']}->{current_count}"
    try:
        generated_at = datetime.fromisoformat(existing_memory["generated_at"].replace("Z", "+00:00"))
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - generated_at).days
    except (ValueError, TypeError):
        return True, "generated_at_parse_error"
    if age_days >= staleness_days:
        return True, f"age_exceeded:{age_days}d>={staleness_days}d"
    return False, f"fresh:age={age_days}d,count={current_count}"


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat = update.effective_chat
        if chat is None:
            LOGGER.warning("Received /memory without effective chat")
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

                current_count = await get_project_item_count(db, project_id)
                existing_memory = await get_project_memory(db, project_id)
                staleness_days = context.bot_data["config"].memory_staleness_days
                is_stale, stale_reason = _check_summary_staleness(
                    existing_memory,
                    current_count,
                    staleness_days,
                )
                LOGGER.info(
                    "summary staleness check project_id=%s: stale=%s reason=%s",
                    project_id,
                    is_stale,
                    stale_reason,
                )

                if not is_stale and existing_memory is not None:
                    await reply_text(
                        update,
                        context,
                        f"Память проекта «{project_name}»:\n\n{existing_memory['summary_text']}\n\n_(актуально, обновлено: {existing_memory['generated_at'][:10]})_",
                    )
                    LOGGER.info("memory_path=summary_cached project_id=%s reason=%s", project_id, stale_reason)
                    return

                if current_count == 0:
                    await reply_text(
                        update,
                        context,
                        "В проекте пока нет заметок, идей или дедлайнов. Добавь материал и повтори /memory.",
                    )
                    return

                notes, ideas, deadlines, homework = await _fetch_records(db, project_id)

                daily_llm_call_limit = context.bot_data["config"].daily_llm_call_limit
                today_calls = await get_llm_calls_today(db)
                if today_calls >= daily_llm_call_limit:
                    await reply_text(update, context, "Дневной лимит запросов исчерпан. Попробуй завтра.")
                    return

                input_text = _build_input_text(project_name, notes, ideas, deadlines, homework)

                try:
                    summary_text = await asyncio.to_thread(
                        complete,
                        input_text,
                        MEMORY_SYSTEM_PROMPT,
                        350,
                        "intent",
                    )
                except LLMError:
                    LOGGER.exception("Failed to generate project memory for project_id=%s", project_id)
                    await reply_text(update, context, "Не удалось сгенерировать память. Попробуй ещё раз.")
                    return

                summary_text = summary_text.strip()
                await log_llm_call(db, "intent", "memory_generation")

                model_name = os.environ.get("LLM_MODEL_INTENT", "claude-haiku-4-5")
                await upsert_project_memory(db, project_id, summary_text, current_count, model_name)
                LOGGER.info("memory_path=summary_refreshed project_id=%s reason=%s", project_id, stale_reason)

        except aiosqlite.Error:
            LOGGER.exception("Database failure during /memory for project_id=%s", project_id)
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        await reply_text(update, context, f"Память проекта «{project_name}» обновлена:\n\n{summary_text}")
        LOGGER.info("Completed /memory for project_id=%s", project_id)
    except Exception:
        LOGGER.exception("Unhandled memory command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
