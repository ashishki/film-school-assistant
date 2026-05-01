# Film School Assistant — Audit Cycle 2

**Date:** 2026-04-06
**Scope:** Phase 5 additions — multi-entity queue, clarify flow, nl_context; voice handler; type_selection path
**Reviewer:** Claude Orchestrator
**Status:** FINDINGS COMPLETE — fixes pending

---

## Summary

4 P2 findings and 3 P3 findings. No P1 (critical data loss or security) issues.
P2 findings require fix tasks before Phase 6 / voice expansion work begins.

---

## Findings

### AC2-F1 [P2] — log_llm_call overcounting for multi-entity queue

**File:** `src/handlers/confirm.py:_queue_next_pending_entity` → `src/handlers/nl_handler.py:_prepare_pending_entity_from_nl`

**Problem:**
`_prepare_pending_entity_from_nl` always calls `log_llm_call(db, "intent", "extraction")`. This function is called once in `nl_handler` for the first entity (correct — one LLM call was made). But for each subsequent queued entity, `_queue_next_pending_entity` also calls `_prepare_pending_entity_from_nl`, which again calls `log_llm_call`. For an N-entity message, the LLM quota counter is incremented N times, but only 1 LLM call was made.

**Impact:** Daily LLM quota depletes faster than actual usage. A 3-entity message counts as 3 LLM calls.

**Fix:** Move `log_llm_call` out of `_prepare_pending_entity_from_nl`. Call it explicitly in `nl_handler` after `complete_json` succeeds (before or after `_prepare_pending_entity_from_nl`). `_queue_next_pending_entity` must not trigger `log_llm_call`.

---

### AC2-F2 [P2] — LLM call not logged for type_selection path

**File:** `src/handlers/nl_handler.py` (entity_type is None branch); `src/bot.py:inline_action_handler` (type_* callbacks)

**Problem:**
When the LLM returns an entity with an unknown or empty `entity_type`, `nl_handler` shows the type_selection keyboard and returns early — before calling `_prepare_pending_entity_from_nl`. The `complete_json` LLM call was made and counted against real token usage, but `log_llm_call` is never called. When the user then picks a type via the inline keyboard, `bot.py` creates a `parsed_event` but also does not call `log_llm_call`.

**Impact:** A small but regular class of LLM calls goes untracked. Daily quota check (`get_llm_calls_today`) becomes inaccurate for this path.

**Fix:** Call `log_llm_call` in `nl_handler` after `complete_json` succeeds and after `valid_entities` is confirmed non-empty, but before the early return for `entity_type is None`. This ensures one log entry per LLM call regardless of path.

---

### AC2-F3 [P2] — /start emoji regression

**File:** `src/bot.py:start_command` line 222

**Problem:**
`start_command` text begins with `"Привет! Я твой ассистент для учёбы в киношколе 🎬\n\n"`. P4-02 acceptance criterion AC-1 explicitly requires: `/start reply contains no emoji`. The CODEX_PROMPT.md records P4-02 as complete: `"emoji removed, first-project hint added"`. The emoji was not removed.

**Impact:** Spec regression. Minor UX inconsistency but breaks the documented acceptance criterion.

**Fix:** Remove the `🎬` emoji from the start_command reply text.

---

### AC2-F4 [P2] — discard silently drops entire entity queue

**File:** `src/bot.py:inline_action_handler` (discard branch); `src/handlers/confirm.py:discard_command`

**Problem:**
When the user presses ❌ Удалить (or sends a discard word), `clear_pending` is called, which clears `pending_entities` along with the current entity. If the message produced 3 entities and the user discards the first, the remaining 2 are silently lost with no notification. The reply says only "Запись удалена."

**Impact:** User loses queued entities without knowing it. This is especially surprising for multi-entity messages where the user intended to discard only one entry.

**Fix:** Before calling `clear_pending`, check if `state.pending_entities` is non-empty. If so, append a note to the reply: e.g., `"Запись удалена. Ещё {N} из той же очереди не сохранено."` This informs the user without blocking the discard.

---

### AC2-F5 [P3] — clarify flow silently drops queued entities

**File:** `src/handlers/nl_handler.py` (pending_clarify check at handler entry)

**Problem:**
When the user taps ✏️ Уточнить on a multi-entity confirmation, `pending_clarify=True` is set but `pending_entities` is preserved. On the next text message, `nl_handler` calls `clear_pending` (which clears `pending_entities`) and re-runs extraction — silently discarding the queue. Similar to AC2-F4 but less likely since clarify is used to correct a specific entity.

**Impact:** Low severity. User who taps Уточнить while in a multi-entity queue loses remaining entities silently.

**Fix (deferred):** Either notify about dropped queue at clarify prompt time, or preserve `pending_entities` through the clarify re-extraction (more complex). Defer to post-AC2 pass.

---

### AC2-F6 [P3] — queue source_text uses extracted content, not original user message

**File:** `src/handlers/confirm.py:_queue_next_pending_entity`

**Problem:**
When preparing a queued entity via `_prepare_pending_entity_from_nl`, `source_text` is passed as `content` (the extracted entity text) rather than the original user message. The `parsed_events` table stores this as provenance. For traceability, the original full user message would be more informative.

**Impact:** Low traceability impact. Not visible to the user, only affects `parsed_events` audit log.

**Fix (deferred):** Store original user_text in `pending_entities` items during nl_handler queueing, pass it through to `_queue_next_pending_entity`. Low priority — no functional impact.

---

### AC2-F7 [P3] — voice entity type detection uses English keywords only

**File:** `src/bot.py:_detect_entity_type`

**Problem:**
The voice path uses a simple keyword match against English terms (`"deadline"`, `"homework"`, `"idea"`, etc.). Russian voice messages will almost never match, causing all Russian voice input to be classified as `"note"`. This is a pre-existing limitation, not introduced in Phase 5.

**Impact:** Russian voice messages are all classified as notes. Users who intend to dictate a deadline or idea get a note instead.

**Fix (deferred):** This is the core issue behind PHASE_PLAN.md recommendation #1 (voice capture improvement). The fix requires routing voice transcripts through the same NL extraction path as text, which is a full Phase 6 task, not a targeted fix.

---

## Fix Queue

| ID | Sev | Description | Status |
|----|-----|-------------|--------|
| AC2-F1 | P2 | log_llm_call overcounting in entity queue | [ ] |
| AC2-F2 | P2 | LLM call not logged for type_selection path | [ ] |
| AC2-F3 | P2 | /start emoji regression | [ ] |
| AC2-F4 | P2 | discard silently drops queued entities | [ ] |
| AC2-F5 | P3 | clarify drops queue silently | deferred |
| AC2-F6 | P3 | queue source_text not original message | deferred |
| AC2-F7 | P3 | voice entity type detection English-only | deferred to Phase 6 |

---

## Phase Entry Gate

- P2 fixes (AC2-F1 through AC2-F4) must be resolved before Phase 6 (voice expansion) begins.
- P3 findings are explicitly deferred.
- After P2 fixes: update this document with `[x]` status and add CODEX_PROMPT.md entry.
