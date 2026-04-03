import logging
import re

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import list_recurring_reminders, update_recurring_reminder_status, upsert_recurring_reminder
from src.handlers.common import get_command_text, reply_text


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

DEFAULT_MORNING_TIME = "09:00"
DEFAULT_EVENING_TIME = "21:00"
MORNING_KIND = "morning_pages"
EVENING_KIND = "evening_review"

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

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            await upsert_recurring_reminder(
                db,
                kind=MORNING_KIND,
                title=MORNING_TITLE,
                prompt_text=MORNING_PROMPT,
                schedule_time=morning_time,
            )
            await upsert_recurring_reminder(
                db,
                kind=EVENING_KIND,
                title=EVENING_TITLE,
                prompt_text=EVENING_PROMPT,
                schedule_time=evening_time,
            )

        await reply_text(
            update,
            context,
            (
                "Ежедневные практики включены.\n"
                f"Утренние страницы — {morning_time}\n"
                f"Неснятый фильм дня — {evening_time}\n"
                "Список: /practices"
            ),
        )
    except aiosqlite.Error:
        LOGGER.exception("Failed to configure daily practices")
        await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
    except Exception:
        LOGGER.exception("Unhandled setup_daily_practice failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")


async def practices_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            reminders = await list_recurring_reminders(db)

        if not reminders:
            await reply_text(update, context, "Ежедневные практики пока не настроены. Используй /setup_daily_practice.")
            return

        lines = []
        for item in reminders:
            status = "включено" if item["status"] == "active" else "пауза"
            alias = "morning" if item["kind"] == MORNING_KIND else "evening"
            lines.append(f"- {item['title']} — {item['schedule_time']} ({status}, ключ: {alias})")
        await reply_text(update, context, "Ежедневные практики:\n" + "\n".join(lines))
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

        async with aiosqlite.connect(context.bot_data["db_path"]) as db:
            db.row_factory = aiosqlite.Row
            if raw_target == "all":
                changed = 0
                for kind in (MORNING_KIND, EVENING_KIND):
                    if await update_recurring_reminder_status(db, kind, target_status):
                        changed += 1
            else:
                kind = _resolve_practice_kind(raw_target)
                if kind is None:
                    await reply_text(update, context, "Используй: morning, evening или all.")
                    return
                changed = 1 if await update_recurring_reminder_status(db, kind, target_status) else 0

        if changed == 0:
            await reply_text(update, context, "Не нашла такую practice. Проверь /practices.")
            return

        if target_status == "paused":
            await reply_text(update, context, "Ежедневная практика поставлена на паузу.")
        else:
            await reply_text(update, context, "Ежедневная практика снова включена.")
    except aiosqlite.Error:
        LOGGER.exception("Failed to change daily practice status")
        await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
    except Exception:
        LOGGER.exception("Unhandled daily practice status change failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
