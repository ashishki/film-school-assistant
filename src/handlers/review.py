import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import get_idea, get_llm_calls_today, get_project_memory, log_llm_call
from src.handlers.common import reply_text
from src.reviewer import review_idea


LOGGER = logging.getLogger(__name__)


async def review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not context.args:
            await reply_text(update, context, "Использование: /review <id_идеи>")
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
            if idea is not None:
                if idea.get("project_id") is not None:
                    try:
                        memory_row = await get_project_memory(db, idea["project_id"])
                        project_memory_text = memory_row["summary_text"] if memory_row else None
                    except Exception:
                        LOGGER.warning("Failed to fetch project memory for review idea_id=%s", idea_id)
                        project_memory_text = None
                daily_llm_call_limit = context.bot_data["config"].daily_llm_call_limit
                today_calls = await get_llm_calls_today(db)
                if today_calls >= daily_llm_call_limit:
                    await reply_text(
                        update,
                        context,
                        f"Достигнут дневной лимит LLM запросов ({daily_llm_call_limit}). Попробуй завтра.",
                    )
                    return
                await log_llm_call(db, "review", "review")

        if idea is None:
            await reply_text(update, context, f"Идея #{idea_id} не найдена.")
            return

        await reply_text(update, context, f"Обрабатываю идею #{idea_id}...")
        review_text = await review_idea(idea, context.bot_data["config"], project_memory_text)
        await reply_text(update, context, review_text)
        LOGGER.info("Completed /review for idea_id=%s", idea_id)
    except Exception:
        LOGGER.exception("Unhandled review command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
