import logging
import re
from datetime import datetime
from typing import Any

import aiosqlite
from dateutil import parser as date_parser
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from src.db import list_projects


LOGGER = logging.getLogger(__name__)
PROJECT_FILTER_RE = re.compile(r"\s+project:(?P<project>.+)$", re.IGNORECASE)


def get_command_text(update: Update) -> str:
    message = update.effective_message
    if message is None or not message.text:
        return ""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return ""
    return parts[1].strip()


def format_project_scope(project_name: str | None) -> str:
    if project_name:
        return f"в проекте {project_name}"
    return "в общем списке"


def parse_date_text(raw_value: str) -> str | None:
    return validate_and_parse_date(raw_value)


def validate_and_parse_date(date_str: str | None) -> str | None:
    if date_str is None:
        return None

    candidate = date_str.strip()
    if not candidate:
        return None

    try:
        return datetime.strptime(candidate, "%Y-%m-%d").date().isoformat()
    except ValueError:
        pass

    try:
        parsed = date_parser.parse(candidate, default=datetime(2000, 1, 1), fuzzy=True)
    except (ValueError, OverflowError) as exc:
        LOGGER.debug("Failed to parse date %r: %s", candidate, exc)
        return None

    return parsed.date().isoformat()


async def resolve_project_match(db: aiosqlite.Connection, raw_name: str) -> tuple[str, dict | list[dict] | None]:
    target = raw_name.strip().lower()
    if not target:
        return "missing", None

    projects = await list_projects(db)
    if not projects:
        return "missing", None

    exact_matches = [
        project
        for project in projects
        if (project.get("name") or "").lower() == target or (project.get("slug") or "").lower() == target
    ]
    if len(exact_matches) == 1:
        return "ok", exact_matches[0]
    if len(exact_matches) > 1:
        return "ambiguous", exact_matches

    partial_matches = [
        project
        for project in projects
        if target in (project.get("name") or "").lower() or target in (project.get("slug") or "").lower()
    ]
    if len(partial_matches) == 1:
        return "ok", partial_matches[0]
    if len(partial_matches) > 1:
        return "ambiguous", partial_matches
    return "missing", None


def extract_project_filter(text: str) -> tuple[str, str | None]:
    match = PROJECT_FILTER_RE.search(text)
    if match is None:
        return text.strip(), None
    item_type = text[: match.start()].strip()
    project_name = match.group("project").strip()
    return item_type, project_name or None


async def reply_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup: Any | None = None,
) -> None:
    message = update.effective_message
    if message is None:
        LOGGER.debug("Skipping reply because update has no message")
        return
    try:
        await context.bot.send_message(chat_id=message.chat_id, text=text, reply_markup=reply_markup)
    except TelegramError:
        LOGGER.warning("Failed to send Telegram reply for chat_id=%s", message.chat_id, exc_info=True)
