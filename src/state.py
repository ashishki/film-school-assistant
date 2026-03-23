import logging
from dataclasses import dataclass, field


LOGGER = logging.getLogger(__name__)
MAX_HISTORY_MESSAGES: int = 20


@dataclass
class UserState:
    active_project_id: int | None = None
    active_project_name: str | None = None
    pending_entity: dict | None = None
    pending_entity_type: str | None = None
    pending_nl_content: str | None = None
    pending_nl_due_date: str | None = None
    pending_nl_project_hint: str | None = None
    conversation_history: list[dict] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > MAX_HISTORY_MESSAGES:
            self.conversation_history = self.conversation_history[-MAX_HISTORY_MESSAGES:]

    def reset_history(self) -> None:
        self.conversation_history = []


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
    state.pending_nl_content = None
    state.pending_nl_due_date = None
    state.pending_nl_project_hint = None
    LOGGER.debug("Cleared pending entity for chat_id=%s", chat_id)
