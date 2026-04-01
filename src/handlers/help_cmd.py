import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.handlers.common import reply_text


LOGGER = logging.getLogger(__name__)


HELP_TEXT = """Режим разговора:
Просто напиши что хочешь — я пойму и помогу.
Пример: «сохрани заметку про освещение» или «покажи дедлайны»
/chat_reset - Очистить историю разговора

Команды (быстрый ввод):
/note <текст> - Сохранить заметку
/idea <текст> - Сохранить идею
/deadline <название> due <дата> - Сохранить дедлайн
/homework <название> due <дата> [course:<курс>] - Сохранить домашнее задание
/projects - Показать все проекты
/project <название> - Выбрать активный проект
/project clear - Сбросить активный проект
/new_project <название> - Создать новый проект
/archive_project <название> - Архивировать проект
/review <id_идеи> - Получить структурный разбор идеи
/memory - Показать или обновить память активного проекта
/reflect - Рефлексия по активному проекту (состояние, напряжения, фокус)
/list notes [project:<название>] - Показать недавние заметки
/list ideas [project:<название>] - Показать идеи
/list deadlines - Показать дедлайны
/list homework - Показать домашние задания
/search <запрос> - Поиск по заметкам и идеям
/confirm - Подтвердить черновик
/edit - Изменить поля черновика
/discard - Удалить черновик
/done_deadline_<id> - Отметить дедлайн как выполненный
/dismiss_deadline_<id> - Отключить напоминания по дедлайну
/help - Показать эту справку"""


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        LOGGER.info("Served help for chat_id=%s", update.effective_chat.id)
        await reply_text(update, context, HELP_TEXT)
    except Exception:
        LOGGER.exception("Unhandled help command failure")
        await reply_text(update, context, "Что-то пошло не так. Попробуй ещё раз.")
