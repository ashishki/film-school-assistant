# Film School Assistant — Codex Session State

Last updated: 2026-04-07

---

## Project

- Name: Film School Assistant
- Root: `/srv/openclaw-her/workspace/film-school-assistant`
- Repository state: operational product; Phases 0–6 complete; Phase 7 memory-architecture alignment complete in docs; Phase 8 ready for implementation planning

---

## Current Phase

- Phase: 8 — MVP Evidence Memory Foundation — PENDING
- Phase entry condition: Phase 7 docs approved; human approval required before first implementation task dispatch

--- Fix Queue --- (empty) ---

--- Phase 8 Task Status ---
[ ] P8-01 — Evidence memory schema and migration
[ ] P8-02 — Deterministic memory-item ingestion from existing sources
[ ] P8-03 — Summary refresh rules v2
[ ] P8-04 — Project-first evidence retrieval helper
[ ] P8-05 — Memory observability and migration validation

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

---

## Compaction Protocol

When `Completed Tasks` exceeds 20 active items:
- move older phase summaries into the archive block above
- keep only current phase task list, open findings, and last 1–2 phase summaries here
