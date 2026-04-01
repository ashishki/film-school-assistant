import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.handlers.common import reply_text


LOGGER = logging.getLogger(__name__)


HELP_TEXT = """Вот всё, что я умею 🎬

💬 Просто напиши мне
Не нужно запоминать команды — просто пиши как другу, голосом или текстом:
«Идея: снять документалку про ночной рынок»
«Напомни сдать сценарий до пятницы»
«Домашнее по монтажу — до 15 апреля»
Я сам пойму, что нужно сохранить, и уточню если надо.

📁 Проекты
/new_project Название — создать новый проект
/projects — список всех проектов
/project Название — переключиться на проект
/project clear — сбросить активный проект
/archive_project Название — архивировать проект

📝 Сохранение (быстрые команды)
/note текст — сохранить заметку
/idea текст — сохранить идею
/deadline название due дата — сохранить дедлайн
/homework название due дата [course:курс] — домашнее задание

📋 Просмотр
/list notes [project:название] — недавние заметки
/list ideas [project:название] — идеи
/list deadlines — все дедлайны
/list homework — домашние задания
/search запрос — поиск по заметкам и идеям

🧠 Анализ и рефлексия
/review id_идеи — структурный разбор идеи с помощью ИИ
/memory — посмотреть или обновить память проекта
/reflect — рефлексия: что происходит, где напряжение, куда двигаться

✅ Работа с черновиками
Когда я предлагаю сохранить что-то, ты можешь:
/confirm — сохранить
/edit поле значение — изменить поле черновика
/discard — отменить

⏰ Дедлайны
/done_deadline_id — отметить дедлайн как выполненный
/dismiss_deadline_id — отключить напоминания

/help — показать эту справку"""


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        LOGGER.info("Served help for chat_id=%s", update.effective_chat.id)
        await reply_text(update, context, HELP_TEXT)
    except Exception:
        LOGGER.exception("Unhandled help command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
