import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.handlers.common import reply_text


LOGGER = logging.getLogger(__name__)


HELP_TEXT = """Я твой личный ассистент для учёбы в киношколе 🎬

Просто пиши или говори — я сам разберусь, что нужно сделать.
Никаких команд запоминать не нужно.

📝 Сохранить мысль или заметку
«Запиши, что хочу снять короткий метр про бабушкин двор»
«Заметка: в сцене с дождём нужен живой звук, не студийный»
«Сохрани идею — хроника одного съёмочного дня глазами реквизитора»

📅 Дедлайны и домашние задания
«Напомни сдать монтаж до пятницы»
«Домашнее по звукорежиссуре — до 15 апреля»
«Когда у меня ближайшие дедлайны?»

📁 Проекты
«Создай проект Дипломный фильм»
«Переключи на проект Документалка»
«Покажи все мои проекты»

🔍 Найти или показать
«Покажи мои последние идеи»
«Что я записывал про звук?»
«Покажи все домашние задания»

🧠 Разобраться глубже
«Разбери мою идею про рынок — есть ли в ней потенциал»
«Как сейчас обстоят дела с проектом?»
«Помоги понять, на чём сейчас сосредоточиться»

⏰ Ежедневные практики
`/setup_daily_practice 09:00 21:00` — включить утреннее и вечернее напоминание
`/practices` — показать текущие практики
`/pause_daily_practice morning`
`/resume_daily_practice evening`

✅ Когда я предлагаю сохранить
Я покажу что понял и спрошу подтверждение.
Можешь сказать «да», «сохрани», «не то» или «отмени» — пойму в любом виде."""


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        LOGGER.info("Served help for chat_id=%s", update.effective_chat.id)
        await reply_text(update, context, HELP_TEXT)
    except Exception:
        LOGGER.exception("Unhandled help command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
