import logging
import re
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import (
    get_recurring_reminder,
    list_recurring_reminders,
    update_recurring_reminder_status,
    update_recurring_reminder_timezone,
    upsert_recurring_reminder,
)
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


def _default_timezone() -> str:
    return os.environ.get("DEFAULT_TIMEZONE", "Europe/Berlin").strip() or "Europe/Berlin"


def _resolve_timezone_name(raw_value: object) -> str:
    candidate = str(raw_value or "").strip() or _default_timezone()
    try:
        ZoneInfo(candidate)
    except ZoneInfoNotFoundError:
        return _default_timezone()
    return candidate


def _format_timezone_suffix(timezone_name: str) -> str:
    return f" ({timezone_name})"


def _practice_title(kind: str) -> str:
    return MORNING_TITLE if kind == MORNING_KIND else EVENING_TITLE


def _build_practice_line(kind: str, schedule_time: str, timezone_name: str) -> str:
    return f"{_practice_title(kind)} — {schedule_time}{_format_timezone_suffix(timezone_name)}"


def _next_fire_label(schedule_time: str, timezone_name: str) -> str:
    """Return 'сегодня' or 'завтра' based on whether the reminder has already fired today."""
    try:
        tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ""
    local_now = datetime.now(timezone.utc).astimezone(tz)
    local_time_str = local_now.strftime("%H:%M")
    if schedule_time > local_time_str:
        return " · следующее: сегодня"
    return " · следующее: завтра"


async def execute_practice_intent(db_path: str, intent: dict[str, object]) -> str:
    action = str(intent.get("action") or "")
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # Resolve timezone: use explicit intent value, else inherit from existing practices, else default
        raw_tz = intent.get("timezone")
        if raw_tz:
            timezone_name = _resolve_timezone_name(raw_tz)
        else:
            existing_for_tz = await list_recurring_reminders(db)
            if existing_for_tz:
                timezone_name = _resolve_timezone_name(existing_for_tz[0].get("timezone"))
            else:
                timezone_name = _default_timezone()

        if action == "list":
            reminders = await list_recurring_reminders(db)
            if not reminders:
                return (
                    "Ежедневные практики пока не настроены.\n"
                    "Напиши, например: «Напоминай утренние страницы в 10:00 по Тбилиси»."
                )
            lines = []
            for item in reminders:
                status = "включено" if item["status"] == "active" else "пауза"
                alias = "morning" if item["kind"] == MORNING_KIND else "evening"
                tz_name = str(item.get("timezone") or _default_timezone())
                timezone_suffix = _format_timezone_suffix(tz_name)
                next_label = _next_fire_label(str(item["schedule_time"]), tz_name) if item["status"] == "active" else ""
                lines.append(
                    f"- {item['title']} — {item['schedule_time']}{timezone_suffix}{next_label}"
                    f" ({status}, ключ: {alias})"
                )
            return "Ежедневные практики:\n" + "\n".join(lines)

        if action == "setup":
            kinds = set(intent.get("kinds", []))
            is_correction = bool(intent.get("is_correction"))
            only_selected = bool(intent.get("only_selected"))
            morning_time = str(intent.get("morning_time") or DEFAULT_MORNING_TIME)
            evening_time = str(intent.get("evening_time") or DEFAULT_EVENING_TIME)
            existing_items = await list_recurring_reminders(db)
            existing_by_kind = {str(item["kind"]): item for item in existing_items}
            if MORNING_KIND in kinds:
                await upsert_recurring_reminder(
                    db,
                    kind=MORNING_KIND,
                    title=MORNING_TITLE,
                    prompt_text=MORNING_PROMPT,
                    schedule_time=morning_time,
                    timezone_name=timezone_name,
                )
            if EVENING_KIND in kinds:
                await upsert_recurring_reminder(
                    db,
                    kind=EVENING_KIND,
                    title=EVENING_TITLE,
                    prompt_text=EVENING_PROMPT,
                    schedule_time=evening_time,
                    timezone_name=timezone_name,
                )
            paused_kinds: list[str] = []
            if only_selected:
                for other_kind in (MORNING_KIND, EVENING_KIND):
                    if other_kind in kinds:
                        continue
                    if other_kind in existing_by_kind:
                        if await update_recurring_reminder_status(db, other_kind, "paused"):
                            paused_kinds.append(other_kind)
            enabled_lines = []
            if MORNING_KIND in kinds:
                enabled_lines.append(_build_practice_line(MORNING_KIND, morning_time, timezone_name))
            if EVENING_KIND in kinds:
                enabled_lines.append(_build_practice_line(EVENING_KIND, evening_time, timezone_name))
            had_existing_selected = any(kind in existing_by_kind for kind in kinds)
            if is_correction or had_existing_selected or only_selected:
                header = "Обновила ежедневные практики."
            else:
                header = "Ежедневные практики включены."
            if paused_kinds:
                paused_titles = ", ".join(_practice_title(kind) for kind in paused_kinds)
                return f"{header}\n" + "\n".join(enabled_lines) + f"\nНа паузе: {paused_titles}"
            return f"{header}\n" + "\n".join(enabled_lines)

        if action == "update_timezone":
            kinds = list(dict.fromkeys(intent.get("kinds", []))) or [MORNING_KIND, EVENING_KIND]
            changed = 0
            for kind in kinds:
                if await update_recurring_reminder_timezone(db, str(kind), timezone_name):
                    changed += 1
            if changed == 0:
                return "Сначала настрой ежедневные практики, а потом уже меняй timezone."
            target_scope = "для выбранных практик" if len(kinds) < 2 else "для ежедневных практик"
            updated_lines = []
            for kind in kinds:
                row = await get_recurring_reminder(db, kind)
                if row is None:
                    continue
                updated_lines.append(_build_practice_line(kind, str(row["schedule_time"]), timezone_name))
            if updated_lines:
                return f"Timezone обновлён {target_scope}.\n" + "\n".join(updated_lines)
            return f"Timezone обновлён {target_scope}: {_format_timezone_suffix(timezone_name).strip()}."

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
