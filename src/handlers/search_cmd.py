import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import search_ideas, search_memory_items_for_project, search_notes
from src.handlers.common import get_command_text, reply_text
from src.state import get_state


LOGGER = logging.getLogger(__name__)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        keyword = get_command_text(update).strip()
        if len(keyword) < 2:
            await reply_text(update, context, "Слишком короткий запрос")
            return

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            state = get_state(update.effective_chat.id)
            if state.active_project_id is not None:
                memory_results = await search_memory_items_for_project(db, state.active_project_id, keyword)
            else:
                memory_results = []
            notes = await search_notes(db, keyword)
            ideas = await search_ideas(db, keyword)

        if not memory_results and not notes and not ideas:
            await reply_text(update, context, "Ничего не найдено")
            return

        lines: list[str] = []
        if memory_results:
            lines.append("🔍 Найдено в памяти проекта:")
            for item in memory_results:
                lines.append(f"[{item['source_kind']}] {item['content']}  (source_id: {item['source_id']})")

        if notes:
            if lines:
                lines.append("")
            lines.append("Заметки:")
            for item in notes:
                lines.append(f"- #{item['id']}: {item['content']}")

        if ideas:
            if lines:
                lines.append("")
            lines.append("Идеи:")
            for item in ideas:
                lines.append(f"- Идея #{item['id']}: {item['content']}")

        LOGGER.info(
            "Search returned %s memory hits, %s notes and %s ideas",
            len(memory_results),
            len(notes),
            len(ideas),
        )
        await reply_text(update, context, "\n".join(lines))
    except Exception:
        LOGGER.exception("Unhandled search command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуйте ещё раз.")
