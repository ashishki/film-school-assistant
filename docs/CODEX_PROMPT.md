# Film School Assistant — Codex Session State

Last updated: 2026-04-08

---

## Project

- Name: Film School Assistant
- Root: `/srv/openclaw-her/workspace/film-school-assistant`
- Repository state: operational product; Phases 0–11 complete; Audit Cycle 3 complete

---

## Current Phase

- Phase: 11 — Natural Language Access to Memory and Reflection — CLOSED
- Phase entry condition: Phase 10 complete; Audit Cycle 3 complete; human approval received 2026-04-08
- Phase close artifact: `docs/review/nl_access_eval_p11.md`

--- Fix Queue --- (empty) ---

--- Phase 11 Task Status ---
[x] P11-01 — Extract shared reflect logic: run_project_reflect in reflect_cmd.py
[x] P11-02 — Add recall_memory tool to TOOLS catalog and execute_tool
[x] P11-03 — Add reflect_project tool to TOOLS catalog and execute_tool
[x] P11-04 — Phase 11 eval pack

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

Audit Cycle 3 (2026-04-08) — Phases 8–10:

P2 (in fix queue above):
- CODE-16: reflect_cmd log_llm_call inside outer aiosqlite.Error handler — swallows valid reflection on DB failure
- CODE-17: search_memory_items_all_projects has no smoke test

P3 (carry-forward, non-blocking):
- CODE-3: due_date not validated before DB write (src/tools.py)
- CODE-4: chat_handler bypasses openclaw_client retry (src/handlers/chat_handler.py)
- CODE-5: reflect_cmd no total cap on assembled input text (downgraded from P2; next_steps[:200] now present)
- CODE-6: REVIEW_SYSTEM_PROMPT in English (src/reviewer.py)
- CODE-7: send_summary.py English section headers (scripts/send_summary.py)
- CODE-8: memory cap inconsistent across spec/prompt/API (src/handlers/memory_cmd.py)
- CODE-11..15: minor UX/naming issues from Cycle 1
- CODE-18: no UNIQUE constraint on memory_items(source_kind, source_id) — dedup is application-level only
- CODE-19: no end-to-end smoke test for recall_cmd or gap-surface evidence paths
- `P3` Gap surface fires only in chat_handler_wrapper (text messages); voice/commands don't update last_active — deferred
- `P3` Review history thin-parsed in /reflect; full review text not in evidence — deferred
- `P3` _extract_focus finds "Фокус:" only in new structured format — expected behavior

---

## Phase 10 Close Note

Phase 10 added explicit opt-in cross-project recall. All defaults (search, recall, reflect, gap surface) remain project-scoped. Cross-project paths require explicit user action only.

Phase entry: Phase 9 complete; 2026-04-08
Phase close artifact: `docs/review/cross_project_eval_p10.md`

[x] P10-01 — All-project memory search helper and /search all: mode
[x] P10-02 — Named-project recall in /recall
[x] P10-03 — Provenance labeling with project name in cross-project results
[x] P10-04 — Phase 10 cross-project eval pack

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
