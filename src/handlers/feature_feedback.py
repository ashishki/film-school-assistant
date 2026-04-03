from __future__ import annotations

import asyncio
import json
import logging

import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.db import (
    create_feature_feedback,
    create_user_feedback,
    get_llm_calls_today_by_prefix,
    log_llm_call,
)
from src.handlers.common import reply_text
from src.openclaw_client import LLMError, complete_json, get_model_name
from src.state import clear_feature_feedback_state, get_state


LOGGER = logging.getLogger(__name__)

FEATURE_ACCEPT_WORDS = {"да", "ага", "ок", "окей", "давай", "хочу", "согласна", "согласен"}
FEATURE_DECLINE_WORDS = {"нет", "не надо", "не нужно", "отмена", "отменить", "стоп"}
FEATURE_CAPABILITY_NEGATION_MARKERS = (
    "не могу",
    "не умею",
    "не способен",
    "не обладаю",
    "мои возможности ограничены",
    "нужно разработать отдельно",
    "сейчас такой возможности нет",
    "в настоящий момент я такой возможностью не обладаю",
)

FEATURE_CAPTURE_SYSTEM_PROMPT = (
    "Ты помогаешь оформить пожелание к новой функции ассистента в короткое ТЗ для разработчика.\n"
    "Работай только по данным пользователя. Не выдумывай деталей.\n"
    "Твоя задача: либо задать ОДИН короткий уточняющий вопрос, либо собрать черновик feature brief.\n"
    "Предпочитай быстрый переход к черновику: максимум 3 уточняющих вопроса на сессию.\n"
    "Уточняй только критично недостающие детали: что должно происходить, когда это должно срабатывать, "
    "и какой результат будет полезен.\n"
    "Формулируй кратко, по-русски, без продуктового жаргона.\n"
    'Верни только JSON: {"status":"ask|ready","question":"...","draft":{"summary_title":"...","problem":"...","desired_behavior":"...","trigger_condition":"...","success_result":"..."}}'
)

FEATURE_SPEC_SYSTEM_PROMPT = (
    "Ты превращаешь запрос пользователя на новую функцию ассистента в короткое ТЗ для разработчика.\n"
    "Используй только факты из исходного запроса и уточнений пользователя.\n"
    "Ничего не придумывай. Не добавляй архитектурные решения.\n"
    "Пиши кратко, ясно, по-русски.\n"
    'Верни только JSON: {"summary_title":"...","problem":"...","desired_behavior":"...","trigger_condition":"...","success_result":"..."}'
)


def is_incapable_response(text: str) -> bool:
    lowered = text.strip().lower()
    return bool(lowered) and any(marker in lowered for marker in FEATURE_CAPABILITY_NEGATION_MARKERS)


def feature_offer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Оформить пожелание", callback_data="feature_offer_start"),
            InlineKeyboardButton("Не надо", callback_data="feature_offer_cancel"),
        ]]
    )


def feature_draft_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Сохранить", callback_data="feature_draft_save"),
            InlineKeyboardButton("Уточнить", callback_data="feature_draft_refine"),
            InlineKeyboardButton("Отменить", callback_data="feature_draft_cancel"),
        ]]
    )


def _build_capture_prompt(session: dict, max_questions: int) -> str:
    answers = session.get("answers", [])
    answers_block = "\n".join(
        f"- Вопрос: {item['question']}\n  Ответ: {item['answer']}"
        for item in answers
    ) or "- пока без уточнений"
    refinement_notes = session.get("refinement_notes", [])
    refinement_block = "\n".join(f"- {note}" for note in refinement_notes) or "- нет"
    return (
        f"Исходный запрос пользователя:\n{session['original_request']}\n\n"
        f"Уже собранные ответы:\n{answers_block}\n\n"
        f"Правки пользователя к черновику:\n{refinement_block}\n\n"
        f"Уже задано вопросов: {session.get('questions_asked', 0)} из {max_questions}.\n"
        "Если деталей уже достаточно или лимит вопросов достигнут, верни status=ready и собери best-effort черновик."
    )


def _normalize_draft(data: dict) -> dict[str, str]:
    draft = data.get("draft", {}) if isinstance(data, dict) else {}
    if not isinstance(draft, dict):
        draft = {}
    return {
        "summary_title": str(draft.get("summary_title", "")).strip() or "Новая функция для ассистента",
        "problem": str(draft.get("problem", "")).strip() or "Пользователь описал неудовлетворённый сценарий.",
        "desired_behavior": str(draft.get("desired_behavior", "")).strip() or "Нужно новое поведение ассистента.",
        "trigger_condition": str(draft.get("trigger_condition", "")).strip() or "Условие не уточнено.",
        "success_result": str(draft.get("success_result", "")).strip() or "Пользователь получает ожидаемый результат без ручных обходных путей.",
    }


def _format_draft(draft: dict[str, str]) -> str:
    return (
        "Черновик пожелания к функции:\n\n"
        f"Коротко: {draft['summary_title']}\n"
        f"Проблема: {draft['problem']}\n"
        f"Нужно: {draft['desired_behavior']}\n"
        f"Когда это срабатывает: {draft['trigger_condition']}\n"
        f"Полезный результат: {draft['success_result']}\n\n"
        "Сохранить для разработчика?"
    )


def _raw_feedback_from_draft(draft: dict[str, str], original_request: str) -> str:
    return (
        f"[feature] {draft['summary_title']}\n"
        f"Исходный запрос: {original_request}\n"
        f"Проблема: {draft['problem']}\n"
        f"Нужно: {draft['desired_behavior']}\n"
        f"Когда: {draft['trigger_condition']}\n"
        f"Результат: {draft['success_result']}"
    )


async def _check_feature_capture_quota(context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            used = await get_llm_calls_today_by_prefix(db, "feature_")
    except aiosqlite.Error:
        LOGGER.exception("Failed to read feature-capture quota")
        return False
    limit = context.bot_data["config"].feature_capture_daily_llm_limit
    return used < limit


async def _capture_step(context: ContextTypes.DEFAULT_TYPE, session: dict) -> dict:
    max_questions = context.bot_data["config"].feature_capture_max_questions
    prompt = _build_capture_prompt(session, max_questions)
    response = await asyncio.to_thread(
        complete_json,
        prompt,
        FEATURE_CAPTURE_SYSTEM_PROMPT,
        "feature_capture",
    )
    if not isinstance(response, dict):
        raise LLMError("Feature capture response was not a JSON object.")

    async with aiosqlite.connect(context.bot_data["db_path"]) as db:
        db.row_factory = aiosqlite.Row
        await log_llm_call(db, get_model_name("feature_capture"), "feature_capture_turn")

    return response


async def _build_final_draft(context: ContextTypes.DEFAULT_TYPE, session: dict) -> dict[str, str]:
    prompt = _build_capture_prompt(session, context.bot_data["config"].feature_capture_max_questions)
    response = await asyncio.to_thread(
        complete_json,
        prompt,
        FEATURE_SPEC_SYSTEM_PROMPT,
        "feature_spec",
    )
    if not isinstance(response, dict):
        raise LLMError("Feature spec response was not a JSON object.")

    async with aiosqlite.connect(context.bot_data["db_path"]) as db:
        db.row_factory = aiosqlite.Row
        await log_llm_call(db, get_model_name("feature_spec"), "feature_spec_turn")

    return {
        "summary_title": str(response.get("summary_title", "")).strip() or "Новая функция для ассистента",
        "problem": str(response.get("problem", "")).strip() or "Пользователь описал неудовлетворённый сценарий.",
        "desired_behavior": str(response.get("desired_behavior", "")).strip() or "Нужно новое поведение ассистента.",
        "trigger_condition": str(response.get("trigger_condition", "")).strip() or "Условие не уточнено.",
        "success_result": str(response.get("success_result", "")).strip() or "Пользователь получает ожидаемый результат без ручных обходных путей.",
    }


async def _build_or_ask(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    state = get_state(chat_id)
    session = state.feature_capture_session
    if session is None:
        await reply_text(update, context, "Не вижу активного сбора пожелания. Опиши запрос ещё раз.")
        return

    if not await _check_feature_capture_quota(context):
        clear_feature_feedback_state(chat_id)
        await reply_text(
            update,
            context,
            "Лимит на сбор пожеланий через LLM сегодня исчерпан. Могу пока сохранить это как обычный /feedback.",
        )
        return

    try:
        response = await _capture_step(context, session)
    except (LLMError, aiosqlite.Error):
        LOGGER.exception("Feature capture step failed for chat_id=%s", chat_id)
        clear_feature_feedback_state(chat_id)
        await reply_text(update, context, "Не удалось оформить пожелание. Попробуй ещё раз позже.")
        return

    status = str(response.get("status", "")).strip().lower()
    questions_asked = int(session.get("questions_asked", 0))
    max_questions = context.bot_data["config"].feature_capture_max_questions
    if status == "ask" and questions_asked < max_questions:
        question = str(response.get("question", "")).strip()
        if question:
            session["current_question"] = question
            session["questions_asked"] = questions_asked + 1
            await reply_text(update, context, question)
            return

    try:
        draft = await _build_final_draft(context, session)
    except (LLMError, aiosqlite.Error):
        LOGGER.exception("Feature spec build failed for chat_id=%s", chat_id)
        clear_feature_feedback_state(chat_id)
        await reply_text(update, context, "Не удалось собрать черновик пожелания. Попробуй ещё раз позже.")
        return

    state.pending_feature_draft = {
        "source": session.get("source", "text"),
        "original_request": session["original_request"],
        "answers": session.get("answers", []),
        "refinement_notes": session.get("refinement_notes", []),
        "draft": draft,
    }
    state.feature_capture_session = None
    await reply_text(update, context, _format_draft(draft), reply_markup=feature_draft_keyboard())


async def start_feature_capture(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    original_request: str,
    source: str = "text",
) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    state = get_state(chat.id)
    state.pending_feature_offer = None
    state.pending_feature_draft = None
    state.feature_capture_session = {
        "source": source,
        "original_request": original_request.strip(),
        "answers": [],
        "questions_asked": 0,
        "current_question": None,
        "refinement_notes": [],
    }
    await _build_or_ask(update, context, chat.id)


async def continue_feature_capture(update: Update, context: ContextTypes.DEFAULT_TYPE, answer_text: str) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    state = get_state(chat.id)
    session = state.feature_capture_session
    if session is None:
        await reply_text(update, context, "Не вижу активного сбора пожелания.")
        return

    current_question = str(session.get("current_question") or "").strip()
    if session.get("awaiting_refinement"):
        session.setdefault("refinement_notes", []).append(answer_text.strip())
        session["awaiting_refinement"] = False
    else:
        session.setdefault("answers", []).append(
            {
                "question": current_question or "Уточнение",
                "answer": answer_text.strip(),
            }
        )
    session["current_question"] = None
    await _build_or_ask(update, context, chat.id)


async def save_feature_draft(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, str]:
    state = get_state(chat_id)
    pending = state.pending_feature_draft
    if pending is None:
        return False, "Нечего сохранять."

    draft = pending["draft"]
    conversation_json = json.dumps(
        {
            "answers": pending.get("answers", []),
            "refinement_notes": pending.get("refinement_notes", []),
        },
        ensure_ascii=False,
    )
    raw_feedback_text = _raw_feedback_from_draft(draft, pending["original_request"])

    try:
        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            await create_feature_feedback(
                db,
                source=str(pending.get("source", "text")),
                original_request=pending["original_request"],
                summary_title=draft["summary_title"],
                problem=draft["problem"],
                desired_behavior=draft["desired_behavior"],
                trigger_condition=draft["trigger_condition"],
                success_result=draft["success_result"],
                conversation_json=conversation_json,
            )
            await create_user_feedback(
                db,
                content=raw_feedback_text,
                source=str(pending.get("source", "text")),
            )
    except aiosqlite.Error:
        LOGGER.exception("Failed to save structured feature feedback for chat_id=%s", chat_id)
        return False, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)"

    clear_feature_feedback_state(chat_id)
    return True, "Пожелание к функции сохранено для разработчика."


async def start_feature_refinement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    state = get_state(chat.id)
    pending = state.pending_feature_draft
    if pending is None:
        await reply_text(update, context, "Нечего уточнять.")
        return

    state.feature_capture_session = {
        "source": pending.get("source", "text"),
        "original_request": pending["original_request"],
        "answers": pending.get("answers", []),
        "questions_asked": context.bot_data["config"].feature_capture_max_questions,
        "current_question": "Что именно поправить в этом описании?",
        "refinement_notes": pending.get("refinement_notes", []),
        "awaiting_refinement": True,
    }
    state.pending_feature_draft = None
    await reply_text(update, context, "Что именно поправить в этом описании?")
