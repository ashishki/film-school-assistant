import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import search_ideas, search_notes
from src.handlers.common import get_command_text, reply_text


LOGGER = logging.getLogger(__name__)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        keyword = get_command_text(update).strip()
        if len(keyword) < 2:
            await reply_text(update, context, "Слишком короткий запрос")
            return

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            notes = await search_notes(db, keyword)
            ideas = await search_ideas(db, keyword)

        if not notes and not ideas:
            await reply_text(update, context, "Ничего не найдено")
            return

        lines: list[str] = []
        if notes:
            lines.append("Заметки:")
            for item in notes:
                lines.append(f"- #{item['id']}: {item['content']}")

        if ideas:
            if lines:
                lines.append("")
            lines.append("Идеи:")
            for item in ideas:
                lines.append(f"- Идея #{item['id']}: {item['content']}")

        LOGGER.info("Search returned %s notes and %s ideas", len(notes), len(ideas))
        await reply_text(update, context, "\n".join(lines))
    except Exception:
        LOGGER.exception("Unhandled search command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуйте ещё раз.")
