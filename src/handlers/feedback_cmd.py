import logging

import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from src.db import create_user_feedback
from src.handlers.common import get_command_text, reply_text


LOGGER = logging.getLogger(__name__)

_FEEDBACK_KEYWORDS = (
    "не хватает",
    "хотелось бы",
    "хочу чтобы",
    "хочу чтоб",
    "жду от",
    "ожидаю от",
    "хотел бы",
    "хотела бы",
    "было бы круто",
    "было бы здорово",
    "сделай так чтобы",
    "разработчику",
    "фидбек",
    "обратная связь",
    "feedback",
    "wish",
    "suggestion",
)

_FUTURE_FEATURE_PATTERNS = (
    "я хочу такую возможность",
    "хочу такую возможность",
    "такую возможность в будущем",
    "эту возможность в будущем",
    "хочу это в будущем",
    "добавьте такую возможность",
    "добавь такую возможность",
    "добавь возможность",
    "добавьте возможность",
)


def is_feedback_message(text: str, last_assistant_message: str | None = None) -> bool:
    lowered = text.strip().lower()
    if not lowered:
        return False

    if any(keyword in lowered for keyword in _FEEDBACK_KEYWORDS):
        return True

    if any(pattern in lowered for pattern in _FUTURE_FEATURE_PATTERNS):
        return True

    if last_assistant_message:
        assistant_lowered = last_assistant_message.lower()
        if (
            "не могу" in assistant_lowered
            or "не обладаю" in assistant_lowered
            or "нужно разработать отдельно" in assistant_lowered
            or "предложи эту идею разработчикам" in assistant_lowered
        ) and (
            "в будущем" in lowered
            or "хочу" in lowered
            or "нужна" in lowered
            or "нужно" in lowered
        ):
            return True

    return False


async def save_feedback_text(db_path: str, text: str) -> bool:
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            await create_user_feedback(db, content=text, source="text")
        return True
    except aiosqlite.Error:
        LOGGER.exception("Failed to save feedback text")
        return False


async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = get_command_text(update)
        if not text:
            await reply_text(
                update,
                context,
                "Напиши что хочешь передать разработчику:\n"
                "/feedback чего не хватает, что хочешь или ждёшь от ассистента",
            )
            return

        saved = await save_feedback_text(context.bot_data["db_path"], text)
        if not saved:
            await reply_text(update, context, "Не удалось сохранить. Попробуй ещё раз. (ERR:DB)")
            return

        LOGGER.info("Saved user feedback (text) update_id=%s", update.update_id)
        await reply_text(update, context, "Принято, передам разработчику.")
    except Exception:
        LOGGER.exception("Unhandled feedback command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
