import re


TIME_SEARCH_RE = re.compile(r"\b(?:[01]\d|2[0-3]):[0-5]\d\b")
MORNING_KIND = "morning_pages"
EVENING_KIND = "evening_review"
DEFAULT_MORNING_TIME = "09:00"
DEFAULT_EVENING_TIME = "21:00"

MORNING_MARKERS = (
    "утро",
    "утрен",
    "утренние страницы",
    "утренний кофе",
)
EVENING_MARKERS = (
    "вечер",
    "в конце дня",
    "конце дня",
    "за день",
    "неснятым фильмом",
    "неснятый фильм",
)
ENABLE_MARKERS = (
    "напомин",
    "присылай",
    "напоминай",
    "каждое утро",
    "каждый вечер",
    "ежедневно",
    "ежедневные",
    "каждый день",
)
PAUSE_MARKERS = ("пауза", "поставь на паузу", "выключи", "отключи", "останови")
RESUME_MARKERS = ("возобнови", "включи", "снова включи", "верни", "продолжи")
LIST_MARKERS = ("какие практики", "какие напоминания", "покажи практики", "покажи напоминания", "статус практик")
CORRECTION_MARKERS = ("нет", "исправь", "исправим", "точнее", "вернее", "не это")
ONLY_MARKERS = ("только", "лишь")
TIMEZONE_UPDATE_MARKERS = (
    "по ",
    "время",
    "часовой пояс",
    "таймзон",
    "timezone",
    "переведи",
    "смени",
    "поменяй",
)
TIMEZONE_MARKERS = (
    ("тбилис", "Asia/Tbilisi"),
    ("tbilisi", "Asia/Tbilisi"),
    ("моск", "Europe/Moscow"),
    ("moscow", "Europe/Moscow"),
    ("берлин", "Europe/Berlin"),
    ("berlin", "Europe/Berlin"),
    ("utc", "UTC"),
)

WORD_RE = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)


def parse_practice_times(text: str) -> tuple[str | None, str | None]:
    lowered = " ".join(text.strip().lower().split())
    found_times = TIME_SEARCH_RE.findall(lowered)
    if len(found_times) >= 2:
        return found_times[0], found_times[1]
    if len(found_times) == 1:
        if lowered == found_times[0]:
            return found_times[0], found_times[0]
        if _contains_any_phrase(lowered, MORNING_MARKERS) and not _contains_any_phrase(lowered, EVENING_MARKERS):
            return found_times[0], None
        if _contains_any_phrase(lowered, EVENING_MARKERS) and not _contains_any_phrase(lowered, MORNING_MARKERS):
            return None, found_times[0]
    return None, None


def _tokenize(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def _contains_any_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _has_daily_marker(text: str) -> bool:
    return _contains_any_phrase(text, ENABLE_MARKERS)


def _has_morning_reference(text: str) -> bool:
    return _contains_any_phrase(text, MORNING_MARKERS)


def _has_evening_reference(text: str) -> bool:
    return _contains_any_phrase(text, EVENING_MARKERS)


def _has_only_marker(text: str) -> bool:
    tokens = _tokenize(text)
    return any(marker in tokens for marker in ONLY_MARKERS)


def _references_daily_practice_context(text: str, mentioned_kinds: list[str]) -> bool:
    if "напомин" in text or "практик" in text or "ежеднев" in text:
        return True
    if not mentioned_kinds:
        return False
    return any(phrase in text for phrase in ("каждое утро", "каждый вечер", "каждый день"))


def parse_practice_intent(text: str) -> dict[str, object] | None:
    lowered = " ".join(text.strip().lower().split())
    if not lowered:
        return None
    is_correction = lowered.startswith(("нет ", "нет,", "исправь", "точнее", "вернее")) or any(
        marker in lowered for marker in CORRECTION_MARKERS
    )
    only_selected = _has_only_marker(lowered)

    timezone_name = None
    for marker, zone in TIMEZONE_MARKERS:
        if marker in lowered:
            timezone_name = zone
            break

    if _contains_any_phrase(lowered, LIST_MARKERS):
        return {"action": "list"}

    mentioned_kinds: list[str] = []
    if _has_morning_reference(lowered):
        mentioned_kinds.append(MORNING_KIND)
    if _has_evening_reference(lowered):
        mentioned_kinds.append(EVENING_KIND)

    if _contains_any_phrase(lowered, PAUSE_MARKERS):
        if not mentioned_kinds:
            mentioned_kinds = [MORNING_KIND, EVENING_KIND]
        return {"action": "pause", "kinds": mentioned_kinds}

    if _contains_any_phrase(lowered, RESUME_MARKERS):
        if not mentioned_kinds:
            mentioned_kinds = [MORNING_KIND, EVENING_KIND]
        return {"action": "resume", "kinds": mentioned_kinds}

    found_times = TIME_SEARCH_RE.findall(lowered)

    if timezone_name is not None and not found_times and (
        _references_daily_practice_context(lowered, mentioned_kinds)
    ) and _contains_any_phrase(lowered, TIMEZONE_UPDATE_MARKERS):
        if not mentioned_kinds:
            mentioned_kinds = [MORNING_KIND, EVENING_KIND]
        return {
            "action": "update_timezone",
            "kinds": mentioned_kinds,
            "timezone": timezone_name,
            "is_correction": is_correction,
            "only_selected": only_selected,
        }

    has_enable_marker = _has_daily_marker(lowered)
    references_daily_practice = _references_daily_practice_context(lowered, mentioned_kinds)
    if has_enable_marker or references_daily_practice or (mentioned_kinds and found_times):
        morning_time = found_times[0] if len(found_times) >= 1 else DEFAULT_MORNING_TIME
        evening_time = found_times[1] if len(found_times) >= 2 else DEFAULT_EVENING_TIME
        requires_time_confirmation = not found_times and (
            "каждое утро" in lowered
            or "каждый вечер" in lowered
            or "утро" in lowered
            or "вечер" in lowered
        )
        if not mentioned_kinds:
            mentioned_kinds = [MORNING_KIND, EVENING_KIND]
        return {
            "action": "setup",
            "kinds": mentioned_kinds,
            "morning_time": morning_time,
            "evening_time": evening_time,
            "timezone": timezone_name,
            "requires_time_confirmation": requires_time_confirmation,
            "is_correction": is_correction,
            "only_selected": only_selected,
        }

    return None


def build_practice_time_question(intent: dict[str, object]) -> str:
    kinds = set(intent.get("kinds", []))
    if kinds == {MORNING_KIND, EVENING_KIND}:
        return (
            "Во сколько присылать эти напоминания?\n"
            "Напиши двумя временами в формате HH:MM HH:MM, например: 09:00 21:00"
        )
    if MORNING_KIND in kinds:
        return "Во сколько присылать утреннее напоминание? Напиши время в формате HH:MM, например 09:00."
    return "Во сколько присылать вечернее напоминание? Напиши время в формате HH:MM, например 21:00."
