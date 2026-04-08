import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import search_ideas, search_memory_items_all_projects, search_memory_items_for_project, search_notes
from src.handlers.common import get_command_text, reply_text
from src.state import get_state


LOGGER = logging.getLogger(__name__)

_ALL_PREFIX = "all:"


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        raw = get_command_text(update).strip()
        if len(raw) < 2:
            await reply_text(update, context, "Слишком короткий запрос")
            return

        # Explicit all-project mode via "all:" prefix
        all_projects_mode = raw.lower().startswith(_ALL_PREFIX)
        keyword = raw[len(_ALL_PREFIX):].strip() if all_projects_mode else raw
        if len(keyword) < 2:
            await reply_text(update, context, "Слишком короткий запрос")
            return

        state = get_state(update.effective_chat.id)

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            if all_projects_mode:
                memory_results = await search_memory_items_all_projects(db, keyword)
            elif state.active_project_id is not None:
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
            header = "🔍 Найдено во всех проектах:" if all_projects_mode else "🔍 Найдено в памяти проекта:"
            lines.append(header)
            for item in memory_results:
                kind = item["source_kind"]
                src_id = item["source_id"]
                text = str(item["content"]).strip()
                if len(text) > 150:
                    text = text[:150].rstrip() + "..."
                if all_projects_mode and item.get("project_name"):
                    lines.append(f"[{item['project_name']} / {kind}#{src_id}] {text}")
                else:
                    lines.append(f"[{kind}#{src_id}] {text}")

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
            "Search mode=%s returned %s memory hits, %s notes and %s ideas",
            "all_projects" if all_projects_mode else "project_first",
            len(memory_results),
            len(notes),
            len(ideas),
        )
        await reply_text(update, context, "\n".join(lines))
    except Exception:
        LOGGER.exception("Unhandled search command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуйте ещё раз.")
