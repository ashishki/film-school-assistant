import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import get_idea, get_llm_calls_today, get_project_memory, list_ideas, log_llm_call
from src.handlers.common import reply_text
from src.reviewer import review_idea
from src.user_context import get_user_context_prompt_text, refresh_user_context_summary


LOGGER = logging.getLogger(__name__)


def _format_created(created_at: str | None) -> str:
    if not created_at:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        MONTHS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
        return f"{dt.day} {MONTHS[dt.month - 1]}"
    except Exception:
        return ""


async def review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not context.args:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                ideas = await list_ideas(db, limit=10)
            if not ideas:
                await reply_text(update, context, "Нет сохранённых идей. Запиши идею — и я помогу её разобрать.")
                return
            lines = ["Идеи для разбора:\n"]
            for idea in ideas:
                date_label = _format_created(str(idea.get("created_at") or ""))
                date_suffix = f" ({date_label})" if date_label else ""
                content = str(idea.get("content") or "").strip()
                short = content[:80] + "…" if len(content) > 80 else content
                lines.append(f"#{idea['id']} — {short}{date_suffix}")
            lines.append("\nНапиши /review <id> для любой из них.")
            await reply_text(update, context, "\n".join(lines))
            return

        raw_idea_id = context.args[0].strip()
        try:
            idea_id = int(raw_idea_id)
        except ValueError:
            await reply_text(update, context, "Использование: /review <id_идеи>")
            return

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            idea = await get_idea(db, idea_id)
            project_memory_text: str | None = None
            user_context_text: str | None = None
            if idea is not None:
                if idea.get("project_id") is not None:
                    try:
                        memory_row = await get_project_memory(db, idea["project_id"])
                        project_memory_text = memory_row["summary_text"] if memory_row else None
                    except Exception:
                        LOGGER.warning("Failed to fetch project memory for review idea_id=%s", idea_id)
                        project_memory_text = None
                try:
                    await refresh_user_context_summary(db, context.bot_data["config"].daily_llm_call_limit)
                    user_context_text = await get_user_context_prompt_text(db)
                except Exception:
                    LOGGER.warning("Failed to fetch user context for review idea_id=%s", idea_id)
                    user_context_text = None
                daily_llm_call_limit = context.bot_data["config"].daily_llm_call_limit
                today_calls = await get_llm_calls_today(db)
                if today_calls >= daily_llm_call_limit:
                    await reply_text(
                        update,
                        context,
                        f"Достигнут дневной лимит LLM запросов ({daily_llm_call_limit}). Попробуй завтра.",
                    )
                    return

        if idea is None:
            await reply_text(update, context, f"Идея #{idea_id} не найдена.")
            return

        await reply_text(update, context, f"Обрабатываю идею #{idea_id}...")
        review_text = await review_idea(idea, context.bot_data["config"], project_memory_text, user_context_text)
        await reply_text(update, context, review_text)
        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                await log_llm_call(db, "review", "review")
        except aiosqlite.Error:
            LOGGER.warning("Failed to log LLM call for review idea_id=%s", idea_id)
        LOGGER.info("Completed /review for idea_id=%s", idea_id)
    except Exception:
        LOGGER.exception("Unhandled review command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
