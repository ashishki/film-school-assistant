import logging
import re

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import list_recurring_reminders, update_recurring_reminder_status, upsert_recurring_reminder
from src.handlers.common import get_command_text, reply_text
from src.practice_intents import (
    DEFAULT_EVENING_TIME,
    DEFAULT_MORNING_TIME,
    EVENING_KIND,
    MORNING_KIND,
)


LOGGER = logging.getLogger(__name__)
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
PRACTICE_KIND_ALIASES = {
    "morning": "morning_pages",
    "утро": "morning_pages",
    "morning_pages": "morning_pages",
    "evening": "evening_review",
    "вечер": "evening_review",
    "evening_review": "evening_review",
}

MORNING_TITLE = "Утренние страницы"
MORNING_PROMPT = "Утренние страницы. О чем был утренний кофе сегодня? Если хочешь, просто ответь сюда."
EVENING_TITLE = "Неснятый фильм дня"
EVENING_PROMPT = "Вечерняя заметка. Что случилось за день и какие моменты были неснятым фильмом? Если хочешь, просто ответь сюда."


def _parse_hhmm(value: str) -> str | None:
    candidate = value.strip()
    if not TIME_RE.fullmatch(candidate):
        return None
    return candidate


def _resolve_practice_kind(raw_value: str) -> str | None:
    return PRACTICE_KIND_ALIASES.get(raw_value.strip().lower())


async def execute_practice_intent(db_path: str, intent: dict[str, object]) -> str:
    action = str(intent.get("action") or "")
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        if action == "list":
            reminders = await list_recurring_reminders(db)
            if not reminders:
                return "Ежедневные практики пока не настроены. Напиши, например: «Напоминай мне утром и вечером каждый день»."
            lines = []
            for item in reminders:
                status = "включено" if item["status"] == "active" else "пауза"
                alias = "morning" if item["kind"] == MORNING_KIND else "evening"
                lines.append(f"- {item['title']} — {item['schedule_time']} ({status}, ключ: {alias})")
            return "Ежедневные практики:\n" + "\n".join(lines)

        if action == "setup":
            kinds = set(intent.get("kinds", []))
            morning_time = str(intent.get("morning_time") or DEFAULT_MORNING_TIME)
            evening_time = str(intent.get("evening_time") or DEFAULT_EVENING_TIME)
            if MORNING_KIND in kinds:
                await upsert_recurring_reminder(
                    db,
                    kind=MORNING_KIND,
                    title=MORNING_TITLE,
                    prompt_text=MORNING_PROMPT,
                    schedule_time=morning_time,
                )
            if EVENING_KIND in kinds:
                await upsert_recurring_reminder(
                    db,
                    kind=EVENING_KIND,
                    title=EVENING_TITLE,
                    prompt_text=EVENING_PROMPT,
                    schedule_time=evening_time,
                )
            enabled_lines = []
            if MORNING_KIND in kinds:
                enabled_lines.append(f"Утренние страницы — {morning_time}")
            if EVENING_KIND in kinds:
                enabled_lines.append(f"Неснятый фильм дня — {evening_time}")
            return "Ежедневные практики включены.\n" + "\n".join(enabled_lines)

        if action in {"pause", "resume"}:
            target_status = "paused" if action == "pause" else "active"
            kinds = list(dict.fromkeys(intent.get("kinds", []))) or [MORNING_KIND, EVENING_KIND]
            changed = 0
            for kind in kinds:
                if await update_recurring_reminder_status(db, str(kind), target_status):
                    changed += 1
            if changed == 0:
                return "Не нашла такую practice. Проверь /practices."
            return "Ежедневная практика поставлена на паузу." if action == "pause" else "Ежедневная практика снова включена."

    return "Не поняла запрос по ежедневным практикам."


async def setup_daily_practice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        command_text = get_command_text(update)
        args = command_text.split() if command_text else []
        if len(args) not in {0, 2}:
            await reply_text(
                update,
                context,
                "Использование: /setup_daily_practice [утро_HH:MM вечер_HH:MM]\n"
                "Пример: /setup_daily_practice 09:00 21:00",
            )
            return

        morning_time = DEFAULT_MORNING_TIME
        evening_time = DEFAULT_EVENING_TIME
        if len(args) == 2:
            parsed_morning = _parse_hhmm(args[0])
            parsed_evening = _parse_hhmm(args[1])
            if parsed_morning is None or parsed_evening is None:
                await reply_text(update, context, "Время должно быть в формате HH:MM, например 09:00 21:00.")
                return
            morning_time = parsed_morning
            evening_time = parsed_evening

        result = await execute_practice_intent(
            context.bot_data["db_path"],
            {
                "action": "setup",
                "kinds": [MORNING_KIND, EVENING_KIND],
                "morning_time": morning_time,
                "evening_time": evening_time,
            },
        )
        await reply_text(update, context, f"{result}\nСписок: /practices")
    except aiosqlite.Error:
        LOGGER.exception("Failed to configure daily practices")
        await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
    except Exception:
        LOGGER.exception("Unhandled setup_daily_practice failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


async def practices_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        result = await execute_practice_intent(context.bot_data["db_path"], {"action": "list"})
        await reply_text(update, context, result)
    except aiosqlite.Error:
        LOGGER.exception("Failed to list daily practices")
        await reply_text(update, context, "Не удалось прочитать список. Попробуй ещё раз. (ERR:DB)")
    except Exception:
        LOGGER.exception("Unhandled practices_command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


async def pause_daily_practice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _change_practice_status(update, context, "paused")


async def resume_daily_practice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _change_practice_status(update, context, "active")


async def _change_practice_status(update: Update, context: ContextTypes.DEFAULT_TYPE, target_status: str) -> None:
    try:
        command_text = get_command_text(update)
        raw_target = command_text.strip().lower()
        if not raw_target:
            action = "паузы" if target_status == "paused" else "включения"
            await reply_text(
                update,
                context,
                f"Укажи practice для {action}: morning, evening или all.",
            )
            return

        kinds = [MORNING_KIND, EVENING_KIND] if raw_target == "all" else [_resolve_practice_kind(raw_target)]
        if any(kind is None for kind in kinds):
            await reply_text(update, context, "Используй: morning, evening или all.")
            return

        result = await execute_practice_intent(
            context.bot_data["db_path"],
            {"action": "pause" if target_status == "paused" else "resume", "kinds": kinds},
        )
        await reply_text(update, context, result)
    except aiosqlite.Error:
        LOGGER.exception("Failed to change daily practice status")
        await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
    except Exception:
        LOGGER.exception("Unhandled daily practice status change failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
