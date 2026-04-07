# Film School Assistant — Phase 7 Continuity Eval Pack

**Date:** 2026-04-07
**Phase:** 7 — Continuity Layer Improvement
**Reviewer:** Claude Orchestrator
**Tasks covered:** P7-01, P7-02, P7-03, P7-04

---

## Evaluation Structure

Each dimension: before / after / verdict / evidence / findings

---

## Dimension 1 — Structured Project Memory Format (P7-01)

**Before:**
`MEMORY_SYSTEM_PROMPT` instructed the LLM to produce a single flat paragraph ("Один абзац"). The output was prose that mixed focus, tensions, and next steps into undifferentiated text. Each field was independently unreadable — injection into chat and reflect meant the LLM received a wall of text.

**After:**
`MEMORY_SYSTEM_PROMPT` now instructs the LLM to produce exactly four labeled fields:
- `Фокус:` — current creative or practical center of gravity
- `Открытые вопросы:` — 2–3 active unresolved threads
- `Последнее:` — most recent activity
- `Следующий шаг:` — one concrete action for next session

The output still lives in `summary_text` (no schema change). Each field is independently readable. The "Фокус:" line is directly parseable for gap surface (P7-04).

**Verdict:** IMPROVED

**Evidence:**
- `src/handlers/memory_cmd.py:17-25` — MEMORY_SYSTEM_PROMPT rewritten
- Format is unambiguous: four labeled lines, "нет данных" fallback per field
- Injection into chat system prompt unchanged; richer content passes through

**Findings:**
- None. No schema migration needed since `summary_text` stores labeled text.
- Existing memory rows will display as flat paragraphs until user runs `/memory` again. This is expected and not a regression.

---

## Dimension 2 — Homework Inclusion in Project Memory (P7-02)

**Before:**
`_fetch_records` returned 3 tuple elements: notes, ideas, deadlines. Homework was absent from project memory context. For film students, homework is a core continuity artifact (assignments from instructors with deadlines).

**After:**
`_fetch_records` returns 4 elements: notes, ideas, deadlines, homework.
- Homework query: `status = 'pending'` only (active assignments)
- Limit: 10 items, ordered by `due_date ASC`
- `_build_input_text` adds "Домашние задания (N):" section when non-empty
- `get_project_item_count` now includes `homework WHERE status = 'pending'` in the count sum — staleness tracking is homework-aware

**Verdict:** IMPROVED

**Evidence:**
- `src/handlers/memory_cmd.py:29-80` — _fetch_records and _build_input_text
- `src/db.py:613-626` — get_project_item_count SQL updated
- Completed homework (`status != 'pending'`) correctly excluded from memory

**Findings:**
- None. Change is additive; projects without homework get unchanged output.

---

## Dimension 3 — Time-Based Memory Staleness (P7-03)

**Before:**
Cache-hit condition: `existing_memory["item_count_snapshot"] == current_count`. If the user added no items but edited existing ones, re-reviewed ideas, or simply returned after several days, the cache always hit and the user received stale memory.

**After:**
Cache-hit condition: `item_count_snapshot == current_count AND age_days < memory_staleness_days`.
- `memory_staleness_days` comes from `Config.memory_staleness_days` (default 3, env `MEMORY_STALENESS_DAYS`)
- `age_days` computed from `generated_at` ISO string vs `datetime.now(timezone.utc)`
- Parse error fallback: sets `age_days = staleness_days + 1` (forces regeneration on malformed timestamp)

**Verdict:** IMPROVED

**Evidence:**
- `src/handlers/memory_cmd.py:136-153` — staleness check with time component
- `src/config.py:23, 72` — `memory_staleness_days` field and env override
- Error path is safe: malformed `generated_at` triggers regeneration, not crash

**Findings:**
- Low: `generated_at` format from `_utcnow_iso()` in db.py may not include timezone info. The `.replace("Z", "+00:00")` handles UTC "Z" suffix, and `tzinfo is None` fallback pins it to UTC. This is correct for the current implementation. No issue.

---

## Dimension 4 — "Returning After a Gap" Surface (P7-04)

**Before:**
No passive re-entry surface. A user returning after 3+ days saw no orientation cue. They had to explicitly call `/memory` or `/reflect` to recall project state, or simply re-state context in chat.

**After:**
`chat_handler_wrapper` checks `last_active` at each message:
- `last_active: datetime | None` added to `UserState` (in-process only; resets on bot restart)
- On each text message: if `last_active` is set and `elapsed_days >= gap_days` and `active_project_id` is set, reads `project_memory` from DB and extracts the `Фокус:` line
- If focus found, sends one-line snippet before proceeding: `"Последний раз ты работала над «{project_name}»: {focus}"`
- `last_active` is then updated to `now` → second message in same session does not re-surface

**Verdict:** IMPROVED

**Evidence:**
- `src/state.py:25` — `last_active: datetime | None = None`
- `src/bot.py:102-120` — gap detection in chat_handler_wrapper
- `src/bot.py:95-100` — `_extract_focus()` helper: parses "Фокус:" from structured text
- `src/config.py:24, 73` — `gap_days` field and env override `GAP_DAYS`

**Findings:**
- Low: gap detection lives in `chat_handler_wrapper` only. Voice messages and command handlers do not update `last_active`. This means a voice message after a gap does not surface orientation, and the next text message will surface it instead. Acceptable for now.
- Low: `_extract_focus` only finds "Фокус:" in the new four-field format (P7-01). Users with old flat-paragraph memory will see no surface until they regenerate with `/memory`. This is the correct and expected behavior — old memory is flat prose, not structured.

---

## Hallucination Check

All four changes are either:
- deterministic (staleness check, homework query, gap detection, config fields)
- prompt rewrites with explicit output format constraints and "нет данных" fallback

The LLM-touching change (P7-01 prompt rewrite) instructs the model to produce only four labeled fields from provided input, prohibits invention, and specifies a fallback. The structured format reduces hallucination risk compared to free prose since each field is narrow-scope.

**Verdict:** No hallucination regression. Risk is equivalent to or lower than Phase 2 baseline.

---

## Regression Check

- ruff: all checks passed on all modified files
- smoke test: PASS
- `/memory` backward compatibility: projects with no homework get unchanged output (empty section skipped)
- Cache behavior: existing memory with matching count but old `generated_at` will regenerate on next `/memory` call — this is the desired behavior, not a regression
- `_prepare_pending_entity_from_nl` no longer calls `log_llm_call` — fixes overcounting bug from Phase 5; no functional regression

---

## Phase 7 Close Decision

**CLOSED.** All four implementation tasks delivered and verified. No P0/P1 findings. Low-severity findings noted, all deferred.

Next recommended phase: Phase 8 — deferred finding from Phase 7: review history injected into /reflect as raw JSON dump rather than accumulated summary.
