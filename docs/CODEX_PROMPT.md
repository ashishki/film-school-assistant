# Film School Assistant — Codex Session State

Last updated: 2026-04-06

---

## Project

- Name: Film School Assistant
- Root: `/srv/openclaw-her/workspace/film-school-assistant`
- Repository state: operational product; Phases 0–6 complete; Phase 7 decomposed and ready for entry check

---

## Current Phase

- Phase: 7 — Continuity Layer Improvement — PENDING
- Phase entry condition: Phase 7 decomposition pass complete (this file); human approval required before first task dispatch

--- Fix Queue --- (empty) ---

--- Phase 7 Task Status ---
[ ] P7-01 — Structured project memory format
[ ] P7-02 — Homework inclusion in project memory
[ ] P7-03 — Time-based memory staleness
[ ] P7-04 — "Returning after a gap" surface
[ ] P7-05 — Phase 7 Continuity Eval Pack

---

## Baseline

- CI: passing (ruff, smoke test)
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
- Capability profiles:
  - `RAG: OFF`
  - `Tool-Use: ON`
  - `Agentic: ON`
  - `Planning: OFF`
  - `Compliance: OFF`

Deterministic-owned areas:
- auth
- SQLite persistence
- scheduling and reminders (timezone-aware, deduplicated by local calendar date)
- recurring practice delivery and deduplication
- weekly digest triggering and dedup
- search/edit/archive flows
- local voice pipeline execution
- practice streak tracking

LLM-owned, bounded areas:
- free-text entity extraction (enriched prompt with entity-type descriptions)
- conversational tool selection
- idea critique and reflection
- user-context profile summarization (Haiku)
- project memory generation (Haiku; moving to structured four-field format in Phase 7)

---

## Product Priorities

- strengthen continuity: project memory should surface where the user left off, not just what exists
- time-awareness: staleness by time, not only by item count
- passive re-entry: "you were here" surface for returning users without requiring a command
- keep future work artifact-first, phase-based, and reviewable

---

## Active Loop Model

Use this loop:
- `Claude Orchestrator` reads this file and selects the next active phase
- `Claude` performs a Phase Decomposition Pass (already done for Phase 7)
- `Claude` performs a Phase Entry Check
- `Claude Orchestrator` dispatches one task at a time to Codex via `codex exec -s workspace-write`
- each task receives light review
- each phase ends with deep review and human approval

Do not assume a full-project Strategist rerun is required.

---

## Open Findings

- `P2` Project memory is a flat paragraph; structured fields (Фокус / Открытые вопросы / Последнее / Следующий шаг) would make it independently useful per field — addressed in P7-01
- `P2` Homework excluded from project memory context — addressed in P7-02
- `P2` Memory cache invalidation ignores time; stale memory after 3+ day gap — addressed in P7-03
- `P2` No passive re-entry surface; user must explicitly call /memory or /reflect after a gap — addressed in P7-04
- `P3` Review history injected into /reflect as raw JSON dump rather than accumulated summary — deferred to Phase 8

---

## Completed Tasks (archived — Phases 0–5)

Phase 0 (documentation clarity): D01–D05 — README, PRODUCT_OVERVIEW, ARCHITECTURE, WORKFLOW_BOUNDARIES, PHASE_PLAN, DECISIONS, spec.md, CODEX_PROMPT
Phase 1 (UX continuity): P1-01–P1-05 — UX examples pack, weekly digest rewrite, confirm flow language, edit ack, UX review pack
Phase 2 (creative memory): P2-01–P2-04 — project_memory schema + db functions, /memory command, memory injection into chat, continuity eval
Phase 3 (reflection): P3-01–P3-03 — memory context into review, /reflect command, reflection eval pack
Phase 4 (productization): P4-01–P4-03 — deployment package, /start onboarding, productization review
Phase 5 (NL quality): P5-01–P5-05 — multi-entity extraction + queue, clarifying questions, Уточнить button, NL context window, NL quality review
Audit Cycle 1 (2026-04-01): 15 findings; FIX-1 and FIX-2 (P1) resolved; all P2/P3 findings resolved

## Completed Tasks — Phase 6 (Daily Practices, User Context, NL UX)

Phase entry: Phase 5 complete; operator-driven development 2026-04-03 to 2026-04-06
Phase close artifact: none (retrospectively documented; no formal review pack)

[x] P6-01 — Daily practice reminders: recurring_reminders + recurring_reminder_log schema; timezone-aware dedup in list_due_recurring_reminders; NL setup flow via practice_intents.py; pause/resume/list
[x] P6-02 — Feature feedback capture: is_incapable_response trigger; bounded multi-step LLM clarification (max 3 questions); feature_feedback + user_feedback tables
[x] P6-03 — User context memory: user_context_entries + user_context_summary tables; SAVE_CONTEXT_MARKERS detection; Haiku profile summary; injection into chat/reflect/review system prompts
[x] P6-04 — Practice UX: practice_completions table + streak calculation; timezone inheritance from existing practice; next fire time in /practices; inline Поставить на паузу button in reminders
[x] P6-05 — NL UX: expanded NL_CAPTURE_MARKERS; multi-entity count announcement; mixed-intent routing (practice + NL in one message); enriched EXTRACTION_SYSTEM_PROMPT with entity-type descriptions and examples

---

## Compaction Protocol

When `Completed Tasks` exceeds 20 active items:
- move older phase summaries into the archive block above
- keep only current phase task list, open findings, and last 1–2 phase summaries here
