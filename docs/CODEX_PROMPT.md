# Film School Assistant — Codex Session State

Last updated: 2026-04-07

---

## Project

- Name: Film School Assistant
- Root: `/srv/openclaw-her/workspace/film-school-assistant`
- Repository state: operational product; Phases 0–8 complete; Phase 9 ready for implementation

---

## Current Phase

- Phase: 9 — Continuity Surfaces And Evidence Use — PENDING
- Phase entry condition: Phase 8 complete; human approval received 2026-04-08

--- Fix Queue --- (empty) ---

--- Phase 9 Task Status ---
[x] P9-01 — Returning-after-gap continuity surface
[x] P9-02 — Evidence-grounded reflection path
[x] P9-03 — Explicit recall command or equivalent bounded tool surface
[x] P9-04 — Continuity eval pack

---

## Baseline

- CI: do not claim passing unless re-run
- Bot: running in production on VPS as `film-school-bot.service`
- DB: `/srv/openclaw-her/workspace/film-school-assistant/data/assistant.db`
- Rule: do not claim implementation verification that did not happen

---

## Declared Architecture Snapshot

- Product category now: `Single-user AI creative workflow assistant for directors, delivered through Telegram`
- Product category later: `AI continuity assistant for directors and creative project development`
- Solution shape: `Hybrid`
- Governance: `Standard`
- Runtime tier: `T1`

Memory model:
- structured state is canonical
- bounded summaries are fast working context
- next memory layer is project-first evidence recall with provenance
- cross-project recall is explicit, not default

Deterministic-owned areas:
- auth
- SQLite persistence
- scheduling and reminders
- search/edit/archive flows
- summary refresh rules
- memory scope resolution
- provenance-preserving retrieval formatting

LLM-owned, bounded areas:
- free-text entity extraction
- conversational tool selection
- idea critique and reflection
- bounded project and user summaries

---

## Product Priorities

- strengthen continuity without importing a generic memory platform
- add verbatim evidence recall where summaries are too lossy
- keep retrieval narrow before widening it
- preserve privacy, inspectability, and low operational complexity

---

## Active Loop Model

Use this loop:
- `Claude Orchestrator` selects the next phase from the current docs
- `Claude` updates source-of-truth docs for the selected phase if needed
- `Claude` performs a Phase Entry Check
- `Claude Orchestrator` dispatches one implementation task at a time to Codex
- each task receives light review
- each phase ends with deep review and human approval

Do not assume a full-project Strategist rerun is required.

---

## Open Findings

- Current project continuity relies too heavily on `project_memory.summary_text`
- `src/handlers/memory_cmd.py` still generates a flat paragraph from notes, ideas, and active deadlines only
- `src/db.py:get_project_item_count` is a weak long-term freshness signal for summary reuse
- chat, review, and reflect inject summary text but have no explicit evidence-memory retrieval path
- `/search` and the chat search tool are not project-first by default
- transcript storage exists, but transcript recall is not yet part of the memory architecture
- `P3` Review history injected into /reflect as raw JSON dump rather than accumulated summary — deferred to Phase 8
- `P3` Gap surface fires only in chat_handler_wrapper (text messages); voice messages and commands don't update last_active — deferred
- `P3` _extract_focus finds "Фокус:" only in new structured format; users with old flat-paragraph memory see no gap surface until they regenerate with /memory — expected behavior, not a bug

---

## Completed Tasks — Phase 8 (MVP Evidence Memory Foundation)

Phase entry: Phase 7 complete; 2026-04-08
Phase close artifact: `docs/review/continuity_eval_p8.md`
Also includes: R1-FIX (confirm.py inline logging), R2-FIX (dedup memory_cmd log)

[x] P8-01 — Evidence memory schema: memory_items table, scope CHECK, FK, two indexes, migration file
[x] P8-02 — Deterministic ingestion: note/idea/homework → project scope; user_context → user scope; fire-and-forget
[x] P8-03 — Summary refresh rules v2: _check_summary_staleness (count-changed / age-exceeded), reason logging
[x] P8-04 — Project-first retrieval: search_memory_items_for_project; /search and chat tool project-first
[x] P8-05 — Observability: smoke tests T-M1..T-M5 (PASS), memory_path logs, continuity_eval_p8.md

---

## Completed Tasks (archived — Phases 0–6)

Phase 0 (documentation clarity): D01–D05
Phase 1 (UX continuity): P1-01–P1-05
Phase 2 (creative memory): P2-01–P2-04
Phase 3 (reflection): P3-01–P3-03
Phase 4 (productization): P4-01–P4-03
Phase 5 (NL quality): P5-01–P5-05
Phase 6 (daily practices, user context, feature feedback, NL UX): P6-01–P6-05
Audit Cycle 1: FIX-1 and FIX-2 resolved

---

## Phase 7 Close Note

Phase 7 was a documentation-first memory architecture alignment pass.

Artifacts updated:
- `docs/MEMORY_ARCHITECTURE.md`
- `docs/ARCHITECTURE.md`
- `docs/PHASE_PLAN.md`
- `docs/tasks.md`
- `docs/spec.md`
- `docs/IMPLEMENTATION_CONTRACT.md`

Outcome:
- the next implementation phase is no longer "make the summary paragraph better"
- it is now "add a small evidence-memory layer with project-first retrieval and provenance"

## Completed Tasks — Phase 7 (Continuity Layer Improvement)

Phase entry: Phase 6 complete; 2026-04-07
Phase close artifact: `docs/review/continuity_eval_p7.md`
Also includes: AC2-FIX-1/2 (log_llm_call overcounting in entity queue; unlogged LLM calls in type_selection path)

[x] P7-01 — Structured project memory format: MEMORY_SYSTEM_PROMPT rewritten to 4-field format (Фокус / Открытые вопросы / Последнее / Следующий шаг)
[x] P7-02 — Homework inclusion: _fetch_records + _build_input_text + get_project_item_count updated; homework WHERE status='pending' included
[x] P7-03 — Time-based memory staleness: memory_staleness_days in Config (default 3, env MEMORY_STALENESS_DAYS); cache-hit checks age not only count
[x] P7-04 — Gap surface: last_active in UserState; gap_days in Config; chat_handler_wrapper prepends "Последний раз ты работала над..." on re-entry after gap
[x] P7-05 — Phase 7 Continuity Eval Pack: docs/review/continuity_eval_p7.md — all findings low, phase CLOSED

---

## Compaction Protocol

When `Completed Tasks` exceeds 20 active items:
- move older phase summaries into the archive block above
- keep only current phase task list, open findings, and last 1–2 phase summaries here
