from __future__ import annotations

import asyncio
import json
import logging

import aiosqlite

from src.db import create_review_history, update_idea_review_status
from src.openclaw_client import LLMError, complete_json, get_model_name


LOGGER = logging.getLogger(__name__)
REVIEW_SYSTEM_PROMPT = (
    "You are a film school creative advisor. You provide structured, rigorous critique of film ideas.\n"
    "Rules:\n"
    '- No generic praise ("great idea", "interesting concept")\n'
    "- Identify the specific dramatic or emotional mechanism\n"
    "- Weak points must be concrete failures of logic, structure, or originality\n"
    "- Questions must be precise and filmmaking-relevant\n"
    "- Next step must be one actionable thing\n"
    'Return JSON: {"core_idea": "...", "dramatic_center": "...", "weak_points": "...", "questions": ["...", "...", "..."], "next_step": "..."}'
)


async def review_idea(idea: dict, config) -> str:
    idea_id = idea["id"]
    prompt = f"Review this film idea:\n\n{idea['content']}"

    try:
        response = await asyncio.to_thread(
            complete_json,
            prompt,
            REVIEW_SYSTEM_PROMPT,
            "review",
        )
        if not isinstance(response, dict):
            raise LLMError("Review response was not a JSON object.")

        formatted = _format_review(response)

        async with aiosqlite.connect(config.db_path) as db:
            db.row_factory = aiosqlite.Row
            await create_review_history(
                db,
                idea_id=idea_id,
                prompt_used=prompt,
                response_json=json.dumps(response),
                model_used=get_model_name("review"),
            )
            await update_idea_review_status(db, idea_id, "reviewed")

        LOGGER.info("Generated review for idea_id=%s", idea_id)
        return formatted
    except aiosqlite.Error:
        LOGGER.exception("Failed to persist review history for idea_id=%s", idea_id)
        return "Could not save. Please try again. (ERR:DB)"
    except LLMError as exc:
        LOGGER.exception("Review generation failed for idea_id=%s", idea_id)
        return f"Review unavailable: {exc}"


def _format_review(response: dict) -> str:
    core_idea = str(response.get("core_idea", "")).strip()
    dramatic_center = str(response.get("dramatic_center", "")).strip()
    weak_points = str(response.get("weak_points", "")).strip()
    next_step = str(response.get("next_step", "")).strip()
    questions_raw = response.get("questions", [])
    if not isinstance(questions_raw, list):
        raise LLMError("Review questions field is invalid.")

    questions = [str(item).strip() for item in questions_raw if str(item).strip()]
    while len(questions) < 3:
        questions.append("Need a more precise development question.")

    return (
        f"CORE IDEA: {core_idea}\n"
        f"DRAMATIC CENTER: {dramatic_center}\n"
        f"WEAK POINTS: {weak_points}\n"
        "QUESTIONS:\n"
        f"  1. {questions[0]}\n"
        f"  2. {questions[1]}\n"
        f"  3. {questions[2]}\n"
        f"NEXT STEP: {next_step}"
    )
