import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import get_memory_items_for_project, get_memory_items_for_user, get_project_by_slug
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


def _format_items(items: list[dict], project_label: str | None = None) -> list[str]:
    lines: list[str] = []
    for item in items:
        kind = item.get("source_kind", "запись")
        label = _SOURCE_KIND_LABEL.get(kind, kind)
        src_id = item.get("source_id", "?")
        text = str(item.get("content", "")).strip()
        if len(text) > 200:
            text = text[:200].rstrip() + "..."
        date = str(item.get("source_created_at") or item.get("created_at") or "")[:10]
        prefix = f"[{project_label} / {label} #{src_id}]" if project_label else f"[{label} #{src_id}]"
        lines.append(f"\n{prefix} {date}\n{text}")
    return lines


async def recall_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat = update.effective_chat
        if chat is None:
            return

        arg = get_command_text(update).strip()
        arg_lower = arg.lower()
        state = get_state(chat.id)

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row

            if arg_lower == "user":
                # User-scoped recall
                items = await get_memory_items_for_user(db, limit=10)
                scope_label = "твоём профиле"
                project_label = None
                scope_key = "user"

            elif arg and arg_lower != "user":
                # Named-project recall: /recall <slug>
                project = await get_project_by_slug(db, arg)
                if project is None:
                    await reply_text(update, context, f"Проект «{arg}» не найден.")
                    return
                items = await get_memory_items_for_project(db, project["id"], limit=10)
                project_name = str(project.get("name") or arg)
                scope_label = f"проекте «{project_name}»"
                project_label = project_name
                scope_key = f"project:{arg}"

            elif state.active_project_id is not None:
                # Default: active project
                items = await get_memory_items_for_project(db, state.active_project_id, limit=10)
                project_name = str(state.active_project_name or state.active_project_id)
                scope_label = f"проекте «{project_name}»"
                project_label = None  # single-project, no need to repeat project in each item
                scope_key = "project:active"

            else:
                await reply_text(update, context, "Сначала выбери проект: /project <название>")
                return

        if not items:
            await reply_text(update, context, "Нет материалов в памяти.")
            return

        lines = [f"Материалы в {scope_label}:"]
        lines.extend(_format_items(items, project_label=project_label))

        await reply_text(update, context, "\n".join(lines))
        LOGGER.info(
            "recall_command scope=%s items=%d chat_id=%s",
            scope_key,
            len(items),
            chat.id,
        )
    except Exception:
        LOGGER.exception("Unhandled recall command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
