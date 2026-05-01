# Film School Assistant — Phase 9 Continuity Eval Pack

**Date:** 2026-04-08
**Phase:** 9 — Continuity Surfaces And Evidence Use
**Reviewer:** Claude Orchestrator
**Tasks covered:** P9-01, P9-02, P9-03

---

## Evaluation Structure

Each dimension: before / after / verdict / evidence / findings

---

## Dimension 1 — Returning-after-gap Continuity Surface (P9-01)

**Before:**
`chat_handler_wrapper` in `src/bot.py` surfaced only one line on re-entry after a gap:
`"Последний раз ты работала над «project»: {focus}"` extracted from the summary's `Фокус:` field.
No verbatim evidence was shown. If summary was missing or had no focus, nothing was shown.

**After:**
`chat_handler_wrapper` now fetches up to 3 recent `memory_items` for the active project
(via `get_memory_items_for_project(db, project_id, limit=3)`) in the same `async with` block
as `get_project_memory`. If evidence exists, a "Последние материалы:" block is appended
with `[source_kind] text (truncated to 120 chars)` per item.

Fallback chain preserved:
- no focus → no gap message
- no evidence items → focus-only message (original behavior)
- aiosqlite.Error → exception logged, gap block skipped

**Verdict:** IMPROVED

**Evidence:**
- `src/bot.py`: `get_memory_items_for_project` added to db import block
- `src/bot.py:~335`: `recent_items = await get_memory_items_for_project(db, project_id, limit=3)` inside `async with` block
- Gap message now builds `lines` list, appends evidence block if non-empty

**Findings:**
- F1: `last_active` is still only updated in `chat_handler_wrapper` (text messages). Voice messages and commands do not update it. Deferred — noted in Phase 7 and unchanged in Phase 9.

---

## Dimension 2 — Evidence-Grounded Reflection Path (P9-02)

**Before:**
`/reflect` in `src/handlers/reflect_cmd.py` injected into the LLM prompt:
- user context summary
- `summary_text` from `project_memory`
- `next_steps` from recent review history
- active deadlines

No verbatim evidence was used. The reflection was constrained by what the summary captured.

**After:**
`reflect_command` now fetches up to 5 `memory_items` for the active project
(via `get_memory_items_for_project(db, project_id, limit=5)`) before building the input text.
`_build_input_text` accepts an `evidence_snippets` parameter (list[dict] | None).
When provided, a `Verbatim evidence` block is inserted between the summary and next_steps:

```
Verbatim evidence (последние записи с провенансом):
[note#42] Текст заметки (до 200 символов)...
[idea#17] Текст идеи...
```

Failure handling: if evidence fetch raises, `evidence_snippets = []` and reflection continues
without evidence (degraded but functional).

**Verdict:** IMPROVED

**Evidence:**
- `src/handlers/reflect_cmd.py:9`: `get_memory_items_for_project` added to db import
- `src/handlers/reflect_cmd.py:~155`: evidence fetch with try/except before LLM call
- `src/handlers/reflect_cmd.py:_build_input_text`: refactored to `parts: list[str]`, evidence block inserted conditionally
- Provenance format: `[{source_kind}#{source_id}]` — inspectable

**Findings:**
- F2: Review history is still extracted as `next_steps` only (thin parse from JSON). The full review text is not included in evidence. This is the deferred P3 finding — still acceptable for Phase 9 scope.

---

## Dimension 3 — Explicit Recall Command (P9-03)

**Before:**
No explicit user-facing recall path existed. The user could use `/search <keyword>` which now
shows project-first evidence, but there was no command to browse recent project memory items.

**After:**
`/recall` command added (`src/handlers/recall_cmd.py`).

Behavior:
- `/recall` → fetches last 10 project-scoped `memory_items` for active project
- `/recall user` → fetches last 10 user-scoped `memory_items`
- No active project + no `user` arg → prompts to select a project first
- No items → "Нет материалов в памяти."
- Output: `[label #source_id] date\ntext (up to 200 chars)`

Provenance is explicit per item: source kind, source id, date from `source_created_at` or `created_at`.

Registered in `src/bot.py` as `CommandHandler("recall", recall_command)`.

**Verdict:** ADDED

**Evidence:**
- `src/handlers/recall_cmd.py` — new file, 65 lines
- `src/bot.py:~85`: `from src.handlers.recall_cmd import recall_command`
- `src/bot.py:~769`: `application.add_handler(CommandHandler("recall", recall_command))`
- `ruff check src/handlers/recall_cmd.py src/bot.py` → All checks passed

**Findings:**
- F3: `/recall` uses `get_memory_items_for_user` for user scope, but `save_user_context_entry`
  in `user_context.py` is still not called from confirm.py (user_context entries still go through
  the inline upsert in confirm.py). User-scoped items are populated correctly from confirm.py,
  so `/recall user` will work. The helper is unused but not harmful. Deferred to future cleanup.

---

## Phase 9 Summary

| Task | Verdict |
|------|---------|
| P9-01 — Gap surface with evidence | IMPROVED |
| P9-02 — Evidence in /reflect | IMPROVED |
| P9-03 — /recall command | ADDED |

**Open findings (low severity, deferred):**
- F1: `last_active` not updated on voice/command paths (known since Phase 7)
- F2: Review history still thin-parsed in /reflect (known P3 deferred)
- F3: `save_user_context_entry` helper unused (known F1 from Phase 8)

**Phase 9 verdict: CLOSED — all tasks complete, no P0/P1 findings.**
