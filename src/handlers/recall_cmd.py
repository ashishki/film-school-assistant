import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import get_memory_items_for_project, get_memory_items_for_user
from src.handlers.common import get_command_text, reply_text
from src.state import get_state


LOGGER = logging.getLogger(__name__)

_SOURCE_KIND_LABEL = {
    "note": "заметка",
    "idea": "идея",
    "homework": "задание",
    "user_context": "контекст",
    "transcript": "запись",
}


async def recall_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat = update.effective_chat
        if chat is None:
            return

        arg = get_command_text(update).strip().lower()
        state = get_state(chat.id)

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            if arg == "user":
                items = await get_memory_items_for_user(db, limit=10)
                scope_label = "твоём профиле"
            elif state.active_project_id is not None:
                items = await get_memory_items_for_project(db, state.active_project_id, limit=10)
                scope_label = f"проекте «{state.active_project_name or state.active_project_id}»"
            else:
                await reply_text(update, context, "Сначала выбери проект: /project <название>")
                return

        if not items:
            await reply_text(update, context, "Нет материалов в памяти.")
            return

        lines = [f"Материалы в {scope_label}:"]
        for item in items:
            kind = item.get("source_kind", "запись")
            label = _SOURCE_KIND_LABEL.get(kind, kind)
            src_id = item.get("source_id", "?")
            text = str(item.get("content", "")).strip()
            if len(text) > 200:
                text = text[:200].rstrip() + "..."
            date = str(item.get("source_created_at") or item.get("created_at") or "")[:10]
            lines.append(f"\n[{label} #{src_id}] {date}\n{text}")

        await reply_text(update, context, "\n".join(lines))
        LOGGER.info(
            "recall_command scope=%s items=%d chat_id=%s",
            "user" if arg == "user" else "project",
            len(items),
            chat.id,
        )
    except Exception:
        LOGGER.exception("Unhandled recall command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
