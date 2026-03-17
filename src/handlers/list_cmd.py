import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import list_deadlines, list_homework, list_ideas, list_notes
from src.handlers.common import extract_project_filter, get_command_text, reply_text, resolve_project_match


LOGGER = logging.getLogger(__name__)


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        command_text = get_command_text(update)
        item_type, project_name = extract_project_filter(command_text)
        normalized_type = item_type.strip().lower()

        if normalized_type not in {"notes", "ideas", "deadlines", "homework"}:
            await reply_text(update, context, "Usage: /list notes|ideas|deadlines|homework [project:<name>]")
            return

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            project_id = None
            project_label = None

            if project_name:
                status, result = await resolve_project_match(db, project_name)
                if status == "missing":
                    await reply_text(update, context, 'Project not found. Use /projects to see available projects.')
                    return
                if status == "ambiguous":
                    assert isinstance(result, list)
                    names = ", ".join(project["name"] for project in result)
                    await reply_text(update, context, f"Project name is ambiguous. Matches: {names}.")
                    return
                assert isinstance(result, dict)
                project_id = result["id"]
                project_label = result["name"]

            if normalized_type == "notes":
                items = await list_notes(db, project_id=project_id)
                text = _format_notes(items, project_label)
            elif normalized_type == "ideas":
                items = await list_ideas(db, project_id=project_id)
                text = _format_ideas(items, project_label)
            elif normalized_type == "deadlines":
                items = await list_deadlines(db)
                text = _format_deadlines(items)
            else:
                items = await list_homework(db)
                text = _format_homework(items)

        LOGGER.info("Listed %s items for type=%s", len(items), normalized_type)
        await reply_text(update, context, text)
    except Exception:
        LOGGER.exception("Unhandled list command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")


def _format_notes(items: list[dict], project_label: str | None) -> str:
    if not items:
        return "No notes found."
    heading = f"Notes for {project_label}:" if project_label else "Notes:"
    lines = [heading]
    for item in items:
        lines.append(f"- #{item['id']}: {item['content']}")
    return "\n".join(lines)


def _format_ideas(items: list[dict], project_label: str | None) -> str:
    if not items:
        return "No ideas found."
    heading = f"Ideas for {project_label}:" if project_label else "Ideas:"
    lines = [heading]
    for item in items:
        lines.append(f"- Idea #{item['id']}: {item['content']}")
    return "\n".join(lines)


def _format_deadlines(items: list[dict]) -> str:
    if not items:
        return "No deadlines found."
    lines = ["Deadlines:"]
    for item in items:
        lines.append(f"- Deadline #{item['id']}: {item['title']} — {item['due_date']} [{item['status']}]")
    return "\n".join(lines)


def _format_homework(items: list[dict]) -> str:
    if not items:
        return "No homework found."
    lines = ["Homework:"]
    for item in items:
        course = f" ({item['course']})" if item.get("course") else ""
        lines.append(f"- Homework #{item['id']}: {item['title']}{course} — due {item['due_date']}")
    return "\n".join(lines)
