import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import list_projects
from src.handlers.common import get_command_text, reply_text, resolve_project_match
from src.state import get_state


LOGGER = logging.getLogger(__name__)


async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        state = get_state(update.effective_chat.id)
        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            projects = await list_projects(db)

        if not projects:
            await reply_text(update, context, "No projects found.")
            return

        lines = ["Projects:"]
        for project in projects:
            slug = f" ({project['slug']})" if project.get("slug") else ""
            is_active = project["id"] == state.active_project_id
            marker = "* " if is_active else "- "
            active_label = " (active)" if is_active else ""
            lines.append(f"{marker}{project['name']}{slug}{active_label}")

        LOGGER.info("Listed %s projects", len(projects))
        await reply_text(update, context, "\n".join(lines))
    except Exception:
        LOGGER.exception("Unhandled projects command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")


async def project_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        raw_name = get_command_text(update)
        if not raw_name:
            await reply_text(update, context, "Usage: /project <name>")
            return

        if raw_name.strip().lower() == "clear":
            state = get_state(update.effective_chat.id)
            state.active_project_id = None
            state.active_project_name = None
            LOGGER.info("Cleared active project for chat_id=%s", update.effective_chat.id)
            await reply_text(update, context, "Active project cleared.")
            return

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            status, result = await resolve_project_match(db, raw_name)

        if status == "missing":
            await reply_text(update, context, 'Project not found. Use /projects to see available projects.')
            return

        if status == "ambiguous":
            assert isinstance(result, list)
            names = ", ".join(project["name"] for project in result)
            await reply_text(update, context, f"Project name is ambiguous. Matches: {names}.")
            return

        assert isinstance(result, dict)
        state = get_state(update.effective_chat.id)
        state.active_project_id = result["id"]
        state.active_project_name = result["name"]

        LOGGER.info("Set active project_id=%s for chat_id=%s", result["id"], update.effective_chat.id)
        await reply_text(update, context, f"Active project set to: {result['name']}")
    except Exception:
        LOGGER.exception("Unhandled project command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")
