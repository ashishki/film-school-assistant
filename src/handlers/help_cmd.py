import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.handlers.common import reply_text


LOGGER = logging.getLogger(__name__)


HELP_TEXT = """Commands:
/note <text> - Save a note
/idea <text> - Save an idea
/deadline <title> due <date> - Save a deadline
/homework <title> due <date> [course:<name>] - Save a homework item
/projects - List all projects
/project <name> - Set active project context
/project clear - Clear active project context
/review <idea_id> - Get structured creative review of an idea
/list notes [project:<name>] - List recent notes
/list ideas [project:<name>] - List ideas
/list deadlines - List upcoming deadlines
/list homework - List homework items
/confirm - Confirm pending entity
/edit - Edit pending entity fields
/discard - Discard pending entity
/done_deadline_<id> - Mark a deadline as done
/dismiss_deadline_<id> - Dismiss reminders for a deadline
/help - Show this help text"""


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        LOGGER.info("Served help for chat_id=%s", update.effective_chat.id)
        await reply_text(update, context, HELP_TEXT)
    except Exception:
        LOGGER.exception("Unhandled help command failure")
        await reply_text(update, context, "Something went wrong. Please try again.")
