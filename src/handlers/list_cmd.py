import logging
import re

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import list_deadlines, list_homework, list_ideas, list_notes
from src.handlers.common import extract_project_filter, get_command_text, reply_text, resolve_project_match


LOGGER = logging.getLogger(__name__)

_STATUS_FILTER_RE = re.compile(r"\bstatus:(\S+)", re.IGNORECASE)
_PAGE_FILTER_RE = re.compile(r"\bpage:(\S+)", re.IGNORECASE)

_VALID_HOMEWORK_STATUSES = {"pending", "done"}
_VALID_DEADLINE_STATUSES = {"active", "done"}
_PAGE_SIZE = 20


def _extract_status_filter(text: str) -> tuple[str, str | None]:
    """Return (text_without_status_token, status_value_or_None)."""
    match = _STATUS_FILTER_RE.search(text)
    if match is None:
        return text, None
    status_value = match.group(1).lower()
    cleaned = (text[: match.start()] + text[match.end() :]).strip()
    return cleaned, status_value


def _extract_page_filter(text: str) -> tuple[str, int]:
    """Return (text_without_page_token, page_number)."""
    match = _PAGE_FILTER_RE.search(text)
    if match is None:
        return text, 1

    page_value = match.group(1)
    cleaned = (text[: match.start()] + text[match.end() :]).strip()

    try:
        page = int(page_value)
    except ValueError as exc:
        raise ValueError("invalid_page") from exc

    if page <= 0:
        raise ValueError("invalid_page")

    return cleaned, page


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        command_text = get_command_text(update)
        command_text, status_filter = _extract_status_filter(command_text)
        command_text, page = _extract_page_filter(command_text)
        item_type, project_name = extract_project_filter(command_text)
        normalized_type = item_type.strip().lower()
        offset = (page - 1) * _PAGE_SIZE

        if normalized_type not in {"notes", "ideas", "deadlines", "homework"}:
            await reply_text(
                update,
                context,
                "Использование: /list notes|ideas|deadlines|homework [project:<name>] [status:<value>] [page:<номер>]",
            )
            return

        if status_filter is not None:
            if normalized_type == "homework" and status_filter not in _VALID_HOMEWORK_STATUSES:
                await reply_text(update, context, "Неверный статус")
                return
            if normalized_type == "deadlines" and status_filter not in _VALID_DEADLINE_STATUSES:
                await reply_text(update, context, "Неверный статус")
                return
            if normalized_type in {"notes", "ideas"}:
                await reply_text(update, context, "Неверный статус")
                return

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            project_id = None
            project_label = None

            if project_name:
                status, result = await resolve_project_match(db, project_name)
                if status == "missing":
                    await reply_text(update, context, "Проект не найден. Используйте /projects для списка проектов.")
                    return
                if status == "ambiguous":
                    assert isinstance(result, list)
                    names = ", ".join(project["name"] for project in result)
                    await reply_text(update, context, f"Название проекта неоднозначно. Совпадения: {names}.")
                    return
                assert isinstance(result, dict)
                project_id = result["id"]
                project_label = result["name"]

            if normalized_type == "notes":
                items = await list_notes(db, project_id=project_id, limit=_PAGE_SIZE, offset=offset)
                text = _format_notes(items, project_label)
            elif normalized_type == "ideas":
                items = await list_ideas(db, project_id=project_id, limit=_PAGE_SIZE, offset=offset)
                text = _format_ideas(items, project_label)
            elif normalized_type == "deadlines":
                items = await list_deadlines(db, status=status_filter)
                items = items[offset : offset + _PAGE_SIZE]
                text = _format_deadlines(items)
            else:
                items = await list_homework(db, status=status_filter)
                items = items[offset : offset + _PAGE_SIZE]
                text = _format_homework(items)

        LOGGER.info("Listed %s items for type=%s", len(items), normalized_type)
        await reply_text(update, context, text)
    except ValueError as exc:
        if str(exc) == "invalid_page":
            await reply_text(update, context, "Неверный номер страницы")
            return
        LOGGER.exception("Unhandled list command validation failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуйте ещё раз.")
    except Exception:
        LOGGER.exception("Unhandled list command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуйте ещё раз.")


def _format_notes(items: list[dict], project_label: str | None) -> str:
    if not items:
        return "Больше записей нет"
    heading = f"Заметки по проекту {project_label}:" if project_label else "Заметки:"
    lines = [heading]
    for item in items:
        lines.append(f"- #{item['id']}: {item['content']}")
    return "\n".join(lines)


def _format_ideas(items: list[dict], project_label: str | None) -> str:
    if not items:
        return "Больше записей нет"
    heading = f"Идеи по проекту {project_label}:" if project_label else "Идеи:"
    lines = [heading]
    for item in items:
        lines.append(f"- Идея #{item['id']}: {item['content']}")
    return "\n".join(lines)


def _format_deadlines(items: list[dict]) -> str:
    if not items:
        return "Больше записей нет"
    lines = ["Дедлайны:"]
    for item in items:
        lines.append(f"- Дедлайн #{item['id']}: {item['title']} — {item['due_date']} [{item['status']}]")
    return "\n".join(lines)


def _format_homework(items: list[dict]) -> str:
    if not items:
        return "Больше записей нет"
    lines = ["Домашние задания:"]
    for item in items:
        course = f" ({item['course']})" if item.get("course") else ""
        lines.append(f"- Домашнее задание #{item['id']}: {item['title']}{course} — срок {item['due_date']}")
    return "\n".join(lines)
