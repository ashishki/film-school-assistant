import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import get_deadline, get_homework, get_idea, get_note
from src.handlers.common import reply_text

LOGGER = logging.getLogger(__name__)

_MONTHS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]


def _fmt_date(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return f"{dt.day} {_MONTHS[dt.month - 1]} {dt.year}"
    except Exception:
        return iso[:10]


async def get_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await reply_text(update, context, "Использование: /get <id>\nНапример: /get 12")
        return

    try:
        item_id = int(context.args[0].strip())
    except ValueError:
        await reply_text(update, context, "ID должен быть числом. Пример: /get 12")
        return

    async with aiosqlite.connect(context.bot_data["db_path"]) as db:
        db.row_factory = aiosqlite.Row

        note = await get_note(db, item_id)
        if note:
            project_id = note.get("project_id")
            project_name = ""
            if project_id:
                row = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
                p = await row.fetchone()
                project_name = p[0] if p else ""
            lines = [
                f"Заметка #{item_id}",
                f"Дата: {_fmt_date(str(note.get('created_at') or ''))}",
            ]
            if project_name:
                lines.append(f"Проект: {project_name}")
            lines.append(f"\n{note['content']}")
            await reply_text(update, context, "\n".join(lines))
            return

        idea = await get_idea(db, item_id)
        if idea:
            project_id = idea.get("project_id")
            project_name = ""
            if project_id:
                row = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
                p = await row.fetchone()
                project_name = p[0] if p else ""
            lines = [
                f"Идея #{item_id}",
                f"Дата: {_fmt_date(str(idea.get('created_at') or ''))}",
            ]
            if project_name:
                lines.append(f"Проект: {project_name}")
            lines.append(f"\n{idea['content']}")
            await reply_text(update, context, "\n".join(lines))
            return

        deadline = await get_deadline(db, item_id)
        if deadline:
            project_id = deadline.get("project_id")
            project_name = ""
            if project_id:
                row = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
                p = await row.fetchone()
                project_name = p[0] if p else ""
            lines = [
                f"Дедлайн #{item_id}",
                f"Срок: {_fmt_date(str(deadline.get('due_date') or ''))}",
                f"Статус: {deadline.get('status') or '—'}",
            ]
            if project_name:
                lines.append(f"Проект: {project_name}")
            lines.append(f"\n{deadline['title']}")
            await reply_text(update, context, "\n".join(lines))
            return

        hw = await get_homework(db, item_id)
        if hw:
            project_id = hw.get("project_id")
            project_name = ""
            if project_id:
                row = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
                p = await row.fetchone()
                project_name = p[0] if p else ""
            lines = [
                f"Домашнее задание #{item_id}",
                f"Срок: {_fmt_date(str(hw.get('due_date') or ''))}",
            ]
            if hw.get("course"):
                lines.append(f"Курс: {hw['course']}")
            if project_name:
                lines.append(f"Проект: {project_name}")
            lines.append(f"\n{hw['title']}")
            if hw.get("description"):
                lines.append(str(hw["description"]))
            await reply_text(update, context, "\n".join(lines))
            return

    await reply_text(update, context, f"Запись #{item_id} не найдена. Проверь ID через /list.")
