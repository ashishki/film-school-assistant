# Engineering Patterns: What Was Non-Obvious

This document captures three implementation patterns from film-school-assistant that required more than a first obvious solution. Each pattern is documented as: the problem, why the naive approach fails, the actual solution, and what was traded off.

These patterns emerged from building a real single-user assistant, not from designing a framework first.

---

## Pattern 1 — Timezone-Aware Reminder Deduplication

### The problem

A recurring reminder fires once per day. The user is in Tbilisi (UTC+4). The system server is in Europe. A naïve implementation compares `schedule_time` (e.g. "20:00") against UTC clock time and deduplicates by calendar date — but which calendar date? UTC or local?

If the dedup key is a UTC date, a user in UTC+4 who gets their 20:00 reminder at 16:00 UTC might get a second reminder the next UTC day even though it is still the same local day. Or worse: a user in UTC−5 misses a day entirely because the reminder fired at "tomorrow" UTC while it was still today locally.

### Why the naive approach fails

```python
# BAD: dedup by UTC date
today_utc = datetime.now(timezone.utc).date().isoformat()
if already_sent(reminder_id, today_utc):
    skip()
```

This ties the dedup boundary to the server clock, not the user's day. Any timezone offset larger than the gap between the schedule time and midnight will produce double-fires or skips.

### The actual solution

Each `recurring_reminders` row stores a `timezone` column (e.g. `Asia/Tbilisi`). At delivery time, the scheduler converts UTC now to local time, computes the local calendar date, checks `schedule_time` against local clock, and uses the local date as the dedup key:

```python
# src/db.py — list_due_recurring_reminders()
reminder_tz = ZoneInfo(reminder["timezone"])
local_now = current_utc.astimezone(reminder_tz)
local_date = local_now.date().isoformat()          # dedup key
local_time = local_now.strftime("%H:%M")

if reminder["schedule_time"] > local_time:
    continue  # not yet due in user's timezone

existing = await get_log(reminder_id, local_date)
if existing:
    continue  # already sent today (user's today)
```

The dedup key lives in `recurring_reminder_log.sent_on` as a local ISO date, not a UTC timestamp. This means "already sent today" is evaluated relative to where the user wakes up, not where the server lives.

### What was traded off

- The per-reminder timezone column adds schema complexity. For a single-user system this is acceptable; for multi-user it would need to move to a user settings table.
- The scheduler is stateless — it can be called multiple times safely because dedup is in the DB, not in-process memory. This means it is safe to run as a `systemd` timer without fearing double-fires on retry.
- Timezone detection from free text ("по Тбилиси", "Moscow time") is deterministic marker matching, not NLP. Cheap and predictable, but a new city requires an explicit row in the lookup table.

**Files:** `src/db.py:914` (`list_due_recurring_reminders`), `src/db.py:839` (`update_recurring_reminder_timezone`), `scripts/send_reminders.py`

---

## Pattern 2 — False-Positive Filtering for Intent Detection Without ML

### The problem

The bot uses keyword matching to detect practice-related intents from free text (no LLM, no classifier). The user might say:

> "Напоминай утренние страницы каждый день в 10:00"

This should trigger a practice setup. But the user might also say:

> "Я сейчас в Тбилиси, напомни мне что купить в магазине"

This contains "напомни" and a city name — which would match timezone update logic if the filter is not careful.

The deeper problem: personal context messages sometimes look structurally identical to practice setup messages. A message like "по утрам я делаю страницы, это мне важно" should be stored as user context, not interpreted as a setup command.

### Why the naive approach fails

A single-level keyword check fires on coincidental co-occurrence:

```python
# BAD: fires whenever "напомни" + city appear in the same message
if "напомни" in text and any(city in text for city in CITIES):
    return timezone_update_intent()
```

This turns any reminder request with a location reference into a practice timezone update.

### The actual solution

Intent detection uses a layered gate structure. For a timezone update to trigger, three conditions must hold simultaneously:

```python
# src/practice_intents.py — parse_practice_intent()

# Gate 1: a timezone marker is present
timezone_name = detect_timezone(lowered)

# Gate 2: no explicit times were given (otherwise it's a full setup, not a tz update)
found_times = TIME_SEARCH_RE.findall(lowered)

# Gate 3: the message is actually about daily practices
def _references_daily_practice_context(text, mentioned_kinds):
    if "напомин" in text or "практик" in text or "ежеднев" in text:
        return True
    if not mentioned_kinds:
        return False
    return any(p in text for p in ("каждое утро", "каждый вечер", "каждый день"))

if timezone_name and not found_times and _references_daily_practice_context(lowered, kinds):
    return timezone_update_intent
```

Gate 3 is the key. "Я сейчас в Тбилиси, напомни купить молоко" fails gate 3 because "напомни" alone does not imply a recurring daily practice without the practice-domain vocabulary.

For the false-positive protection specifically (personal context vs. intent), the routing order in `bot.py` matters as much as the filter itself. User context capture is checked before practice intent parsing. A message with "запомни обо мне" never reaches the practice parser regardless of what other keywords it contains.

### What was traded off

- Domain vocabulary is hardcoded (Russian, film-school context). Adding a new language or domain requires extending the marker lists; there is no general solution.
- The layered gate approach fails silently if none of the gates fire — the message falls through to the chat handler. This is the correct fallback: the LLM handles whatever the deterministic layer does not catch, rather than forcing a bad intent match.
- The correction flow ("нет, только утренние страницы") uses a leading-word check (`startswith("нет ", "исправь", ...)`) rather than semantic understanding. This works for the most common correction patterns but will miss creative phrasings.

**Files:** `src/practice_intents.py:114` (`parse_practice_intent`), `src/practice_intents.py:106` (`_references_daily_practice_context`), `src/bot.py:392` (routing order in `chat_handler_wrapper`)

---

## Pattern 3 — Streak Calculation Against Insertion-Only Storage

### The problem

Track a "current streak" of consecutive days a practice was completed. The completions table is append-only (`INSERT OR IGNORE`). The streak must handle:

- today's completion not yet recorded (streak in progress)
- yesterday's completion recorded but today not yet (streak intact, should count)
- a gap two days ago (streak broken)

The naive "count consecutive rows" approach breaks as soon as any row is missing.

### Why the naive approach fails

```python
# BAD: assumes rows are consecutive, breaks on any gap
streak = len(recent_rows)
```

A user who completed a practice every day for a week but missed three days ago has a current streak of 3, not 7, not 0. Counting rows without checking adjacency gives the wrong number.

### The actual solution

Fetch all completion dates as a set, then walk backwards from today checking membership:

```python
# src/db.py — get_practice_streak()
completed_dates = {date.fromisoformat(str(row[0])) for row in rows}
streak = 0
check = today

while check in completed_dates:
    streak += 1
    check -= timedelta(days=1)

# Streak is still valid if today is not yet done but yesterday was
if streak == 0:
    check = today - timedelta(days=1)
    while check in completed_dates:
        streak += 1
        check -= timedelta(days=1)
```

The "today not yet done" branch preserves the streak through the day until the user marks the practice complete. Without it, the streak would appear broken every morning.

The storage layer uses `INSERT OR IGNORE` with a unique index on `(recurring_reminder_id, completed_on)`:

```sql
CREATE UNIQUE INDEX idx_practice_completions_on
    ON practice_completions(recurring_reminder_id, completed_on);
```

This makes completion recording idempotent — calling `log_practice_completion` twice on the same day is safe and produces no duplicate rows, which matters because the "Выполнено" button in a reminder message can be tapped multiple times.

### What was traded off

- The set-lookup walk is O(n) where n is the total number of completion records ever. For a single user doing one practice per day for a year, that is ~365 rows — fast enough to not matter. For a multi-user system with millions of rows, you would want a SQL streak query instead.
- The "yesterday counts" rule means the streak shown in the morning before completing the practice is the same as the streak shown after. Some apps reset to 0 at midnight and rebuild only after completion. The current choice is gentler and matches user expectation better for a low-stakes creative habit.
- Completions are stored in UTC date (`date.today()` in the scheduler) rather than the user's local date. For practices that fire late in the evening (e.g. 23:00 in a UTC+5 timezone), the UTC date and local date can diverge. This is a known imprecision; fixing it properly would require passing the user's local date into the completion logger the same way it is passed into the dedup check in Pattern 1.

**Files:** `src/db.py:856` (`log_practice_completion`), `src/db.py:871` (`get_practice_streak`), `src/schema.sql:196` (`practice_completions` table)
