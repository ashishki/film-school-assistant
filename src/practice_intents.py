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


def parse_practice_times(text: str) -> tuple[str | None, str | None]:
    lowered = " ".join(text.strip().lower().split())
    found_times = TIME_SEARCH_RE.findall(lowered)
    if len(found_times) >= 2:
        return found_times[0], found_times[1]
    if len(found_times) == 1:
        if lowered == found_times[0]:
            return found_times[0], found_times[0]
        if any(marker in lowered for marker in MORNING_MARKERS) and not any(marker in lowered for marker in EVENING_MARKERS):
            return found_times[0], None
        if any(marker in lowered for marker in EVENING_MARKERS) and not any(marker in lowered for marker in MORNING_MARKERS):
            return None, found_times[0]
    return None, None


def parse_practice_intent(text: str) -> dict[str, object] | None:
    lowered = " ".join(text.strip().lower().split())
    if not lowered:
        return None
    is_correction = lowered.startswith(("нет ", "нет,", "исправь", "точнее", "вернее")) or any(
        marker in lowered for marker in CORRECTION_MARKERS
    )
    only_selected = any(marker in lowered for marker in ONLY_MARKERS)

    timezone_name = None
    for marker, zone in TIMEZONE_MARKERS:
        if marker in lowered:
            timezone_name = zone
            break

    if any(marker in lowered for marker in LIST_MARKERS):
        return {"action": "list"}

    mentioned_kinds: list[str] = []
    if any(marker in lowered for marker in MORNING_MARKERS):
        mentioned_kinds.append(MORNING_KIND)
    if any(marker in lowered for marker in EVENING_MARKERS):
        mentioned_kinds.append(EVENING_KIND)

    if any(marker in lowered for marker in PAUSE_MARKERS):
        if not mentioned_kinds:
            mentioned_kinds = [MORNING_KIND, EVENING_KIND]
        return {"action": "pause", "kinds": mentioned_kinds}

    if any(marker in lowered for marker in RESUME_MARKERS):
        if not mentioned_kinds:
            mentioned_kinds = [MORNING_KIND, EVENING_KIND]
        return {"action": "resume", "kinds": mentioned_kinds}

    found_times = TIME_SEARCH_RE.findall(lowered)

    if timezone_name is not None and not found_times and (
        "напомин" in lowered
        or "практик" in lowered
        or bool(mentioned_kinds)
    ) and any(marker in lowered for marker in TIMEZONE_UPDATE_MARKERS):
        if not mentioned_kinds:
            mentioned_kinds = [MORNING_KIND, EVENING_KIND]
        return {
            "action": "update_timezone",
            "kinds": mentioned_kinds,
            "timezone": timezone_name,
            "is_correction": is_correction,
            "only_selected": only_selected,
        }

    has_enable_marker = any(marker in lowered for marker in ENABLE_MARKERS)
    references_daily_practice = bool(mentioned_kinds) and ("напомин" in lowered or "ежеднев" in lowered or "кажд" in lowered)
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
