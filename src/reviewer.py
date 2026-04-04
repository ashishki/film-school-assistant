from __future__ import annotations

import asyncio
import json
import logging

import aiosqlite

from src.db import create_review_history, update_idea_review_status
from src.openclaw_client import LLMError, complete_json, get_model_name


LOGGER = logging.getLogger(__name__)
MISSING_REVIEW_PLACEHOLDER = "[Not provided — regenerate or add manually]"
REVIEW_SYSTEM_PROMPT = (
    "Ты — творческий советник киношколы. Ты даёшь структурный, строгий разбор киноидей.\n"
    "Правила:\n"
    '- Никакой общей похвалы ("отличная идея", "интересная концепция")\n'
    "- Определи конкретный драматический или эмоциональный механизм\n"
    "- Оцени кинематографические ставки: что именно визуально и драматически поставлено на кон в сцене или проекте\n"
    "- Оцени точку зрения: чья перспектива ведёт историю и насколько эта POV-позиция последовательна\n"
    "- Оцени двигатель сцены: что создаёт напряжение, удивление или раскрытие от сцены к сцене\n"
    "- Слабые места должны быть конкретными провалами логики, структуры, оригинальности, ставок, точки зрения или построения сцен\n"
    "- Вопросы должны быть точными и релевантными кинопроизводству\n"
    '- Следующий шаг должен быть одним конкретным действием, осуществимым в производстве (например: "Напиши сцену 3"), а не расплывчатым направлением вроде "Исследуй темы"\n'
    'Return JSON: {"core_idea": "...", "dramatic_center": "...", "weak_points": "...", "questions": ["...", "...", "..."], "next_step": "..."}'
    "Ответ на русском языке."
)


async def review_idea(
    idea: dict,
    config,
    project_memory_text: str | None = None,
    user_context_text: str | None = None,
) -> str:
    idea_id = idea["id"]
    prompt_parts: list[str] = []
    if user_context_text:
        prompt_parts.append(user_context_text)
    if project_memory_text:
        prompt_parts.append(f"Контекст проекта: {project_memory_text}")
    prompt_parts.append(f"Разбери эту киноидею:\n\n{idea['content']}")
    prompt = "\n\n".join(prompt_parts)

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
            try:
                unreviewed_count = await _fetch_unreviewed_count(db, idea.get("project_id"))
            except aiosqlite.Error:
                LOGGER.warning("Failed to fetch unreviewed idea count for idea_id=%s", idea_id, exc_info=True)
            else:
                if unreviewed_count > 0:
                    plural = _russian_plural_ideas(unreviewed_count)
                    formatted = f"{formatted}\n\n→ Ещё {unreviewed_count} {plural} без разбора в этом проекте."

        LOGGER.info("Generated review for idea_id=%s", idea_id)
        return formatted
    except aiosqlite.Error:
        LOGGER.exception("Failed to persist review history for idea_id=%s", idea_id)
        return "Could not save. Please try again. (ERR:DB)"
    except LLMError as exc:
        LOGGER.exception("Review generation failed for idea_id=%s", idea_id)
        return f"Review unavailable: {exc}"


def _format_review(response: dict) -> str:
    core_idea = _get_required_review_field(response, "core_idea")
    dramatic_center = _get_required_review_field(response, "dramatic_center")
    weak_points = _get_required_review_field(response, "weak_points")
    next_step = _get_required_review_field(response, "next_step")
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


async def _fetch_unreviewed_count(db: aiosqlite.Connection, project_id: int | None) -> int:
    if project_id is None:
        return 0
    cursor = await db.execute(
        "SELECT COUNT(*) FROM ideas WHERE project_id = ? AND review_status = 'unreviewed'",
        (project_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return int(row[0]) if row else 0


def _russian_plural_ideas(count: int) -> str:
    rem100 = count % 100
    rem10 = count % 10
    if 11 <= rem100 <= 14:
        return "идей"
    if rem10 == 1:
        return "идея"
    if 2 <= rem10 <= 4:
        return "идеи"
    return "идей"


def _get_required_review_field(response: dict, field_name: str) -> str:
    value = response.get(field_name)
    if value is None:
        LOGGER.warning("Review field '%s' missing; substituting placeholder.", field_name)
        return MISSING_REVIEW_PLACEHOLDER

    cleaned = str(value).strip()
    if not cleaned:
        LOGGER.warning("Review field '%s' empty; substituting placeholder.", field_name)
        return MISSING_REVIEW_PLACEHOLDER

    return cleaned
