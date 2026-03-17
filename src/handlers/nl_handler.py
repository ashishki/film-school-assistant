from __future__ import annotations

import asyncio
import json
import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import create_parsed_event
from src.handlers.common import reply_text, resolve_project_match
from src.openclaw_client import LLMError, LLMSchemaError, complete_json
from src.state import get_state


LOGGER = logging.getLogger(__name__)
EXTRACTION_SYSTEM_PROMPT = (
    "You are an entity extractor for a film school workflow assistant. Extract structured data from the user's message.\n"
    'Return JSON only: {"entity_type": "note|idea|homework|deadline", "content": "cleaned content", '
    '"project_hint": "project name or empty string", "due_date": "YYYY-MM-DD or empty string"}\n'
    "Rules: entity_type must be one of the four values. due_date only if explicitly mentioned. No explanation text."
)


async def nl_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        message = update.effective_message
        chat = update.effective_chat
        if message is None or chat is None or not message.text:
            return

        state = get_state(chat.id)
        if state.pending_entity is not None:
            LOGGER.info("Skipping NL parse because a pending entity exists for chat_id=%s", chat.id)
            await reply_text(update, context, "You have a pending item. Reply /confirm, /edit, or /discard.")
            return

        user_text = message.text.strip()
        if not user_text:
            return

        try:
            parsed = await asyncio.to_thread(
                complete_json,
                user_text,
                EXTRACTION_SYSTEM_PROMPT,
                "intent",
            )
        except (LLMError, LLMSchemaError):
            LOGGER.exception("NL extraction failed for chat_id=%s", chat.id)
            await reply_text(update, context, "Could not parse. Try a /command instead. (/help for list)")
            return

        if not isinstance(parsed, dict):
            LOGGER.warning("NL extraction returned non-object payload for chat_id=%s", chat.id)
            await reply_text(update, context, "Could not parse. Try a /command instead. (/help for list)")
            return

        try:
            entity_type = _normalize_entity_type(parsed.get("entity_type"))
            content = str(parsed.get("content", "")).strip()
            project_hint = str(parsed.get("project_hint", "")).strip()
            due_date = str(parsed.get("due_date", "")).strip()
        except ValueError:
            LOGGER.warning("NL extraction returned invalid schema for chat_id=%s", chat.id)
            await reply_text(update, context, "Could not parse. Try a /command instead. (/help for list)")
            return

        if not content:
            LOGGER.warning("NL extraction returned empty content for chat_id=%s", chat.id)
            await reply_text(update, context, "Could not parse. Try a /command instead. (/help for list)")
            return

        try:
            async with aiosqlite.connect(context.bot_data["db_path"]) as db:
                db.row_factory = aiosqlite.Row
                project = await _resolve_project(db, project_hint)
                pending_entity = _build_pending_entity(entity_type, content, due_date, project["id"] if project else None)
                parsed_event = await create_parsed_event(
                    db,
                    entity_type=entity_type,
                    extracted_json=json.dumps(
                        {
                            "entity_type": entity_type,
                            "content": content,
                            "project_hint": project_hint,
                            "project_id": project["id"] if project else None,
                            "project_name": project["name"] if project else None,
                            "due_date": due_date,
                            "source_text": user_text,
                        }
                    ),
                )
        except aiosqlite.Error:
            LOGGER.exception("Failed to persist NL parsed event for chat_id=%s", chat.id)
            await reply_text(update, context, "Could not save. Please try again. (ERR:DB)")
            return

        pending_entity["parsed_event_id"] = parsed_event["id"]
        state.pending_entity = pending_entity
        state.pending_entity_type = entity_type

        project_label = project["name"] if project else "General"
        due_line = f"\nDue date: {due_date}" if due_date else ""
        await reply_text(
            update,
            context,
            f"Detected {entity_type}: {content}\nProject: {project_label}{due_line}",
        )
        await reply_text(update, context, "Reply /confirm, /edit, or /discard.")
        LOGGER.info("Prepared pending NL entity type=%s parsed_event_id=%s for chat_id=%s", entity_type, parsed_event["id"], chat.id)
    except Exception:
        LOGGER.exception("Unhandled NL handler failure")
        await reply_text(update, context, "Something went wrong. Please try again.")


def _normalize_entity_type(raw_value: object) -> str:
    value = str(raw_value or "").strip().lower()
    if value not in {"note", "idea", "homework", "deadline"}:
        raise ValueError("Unsupported entity type")
    return value


async def _resolve_project(db: aiosqlite.Connection, project_hint: str) -> dict | None:
    if not project_hint:
        return None
    status, result = await resolve_project_match(db, project_hint)
    if status != "ok" or not isinstance(result, dict):
        return None
    return result


def _build_pending_entity(entity_type: str, content: str, due_date: str, project_id: int | None) -> dict[str, object]:
    if entity_type == "note":
        return {
            "content": content,
            "project_id": project_id,
            "raw_transcript": content,
            "source": "text",
        }
    if entity_type == "idea":
        return {
            "content": content,
            "project_id": project_id,
            "raw_transcript": content,
            "source": "text",
        }
    if entity_type == "homework":
        return {
            "title": content,
            "description": content,
            "due_date": due_date,
            "course": None,
            "project_id": project_id,
            "source": "text",
        }
    return {
        "title": content,
        "due_date": due_date,
        "project_id": project_id,
        "source": "text",
    }
