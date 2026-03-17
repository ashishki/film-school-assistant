import logging
from dataclasses import dataclass


LOGGER = logging.getLogger(__name__)


@dataclass
class UserState:
    active_project_id: int | None = None
    active_project_name: str | None = None
    pending_entity: dict | None = None
    pending_entity_type: str | None = None


_STATE_BY_CHAT_ID: dict[int, UserState] = {}


def get_state(chat_id: int) -> UserState:
    state = _STATE_BY_CHAT_ID.get(chat_id)
    if state is None:
        state = UserState()
        _STATE_BY_CHAT_ID[chat_id] = state
        LOGGER.debug("Created new user state for chat_id=%s", chat_id)
    return state


def clear_pending(chat_id: int) -> None:
    state = get_state(chat_id)
    state.pending_entity = None
    state.pending_entity_type = None
    LOGGER.debug("Cleared pending entity for chat_id=%s", chat_id)
