# Film School Assistant — Codex Session State

Last updated: 2026-03-31

---

## Project

- Name: Film School Assistant
- Root: `/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant`
- Repository state: existing operational project with retrofit workflow infrastructure and a new product/documentation refactor

---

## Current Phase

- Phase: 4 — COMPLETE. All planned phases done.
- Phase close artifact: `docs/review/productization_review_p4.md`
- Audit Cycle 1 complete: `docs/audit/REVIEW_REPORT.md`

─── Fix Queue ─── (empty — P1 fixes resolved) ──────────────────────
✅ FIX-1 [P1] — log_llm_call moved after complete_json in nl_handler.py (2026-04-01)
✅ FIX-2 [P1] — log_llm_call moved after review_idea in review.py (2026-04-01)
─────────────────────────────────────────────────────────────────────

---

## Baseline

- Current code baseline: existing operational assistant; no new code behavior was changed in this documentation pass
- Local verification status in the current shell:
  - no product runtime checks were re-run during this documentation refactor
  - no new test claims are made
- CI status: not re-verified during this pass

Rule:
- do not claim implementation verification that did not happen

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
- scheduling
- reminders
- weekly digest triggering and dedup
- search/edit/archive flows
- local voice pipeline execution

LLM-owned, bounded areas:
- free-text entity extraction
- conversational tool selection
- idea critique and reflection

---

## Product Priorities

- stop presenting the product as a bot feature bundle
- treat Telegram as interface layer, not product identity
- strengthen continuity and clarity before expanding surfaces
- keep future work artifact-first, phase-based, and reviewable

---

## Active Loop Model

The repository is past the initial bootstrap stage.

Use this loop:
- `Claude Orchestrator` selects the next active phase
- `Claude` performs a Phase Decomposition Pass for that phase
- `Claude` performs a Phase Entry Check
- `Claude Orchestrator` dispatches one task at a time to Codex through the existing execution mechanism
- each task receives light review
- each phase ends with deep review and human approval

Do not assume that a full-project Strategist rerun or original full-repo Phase 1 Validator run is required.

---

## Open Findings

- `P1` The product foundation is real, but the main differentiation is still under-expressed unless the repo is read through the new docs set.
- `P2` UX continuity is weaker than storage capability; Phase 1 should address experience before architectural expansion.
- `P3` Creative memory is the next substantial capability, but only after continuity artifacts and UX framing are strengthened.
- `P4` Web packaging is optional and deferred; it is not a prerequisite for the next value step.

---

## Completed Tasks

- documentation system refactor:
  - rewrote `README.md`
  - added `docs/PRODUCT_OVERVIEW.md`
  - rewrote `docs/ARCHITECTURE.md`
  - added `docs/WORKFLOW_BOUNDARIES.md`
  - added `docs/PHASE_PLAN.md`
  - added `docs/USER_EXPERIENCE.md`
  - added `docs/DECISIONS.md`
  - refreshed `docs/spec.md`
  - refreshed `docs/tasks.md`
- Phase 1 Decomposition Pass:
  - decomposed Phase 1 into five tasks (P1-01 through P1-05) in `docs/tasks.md`
  - added Phase 1 UX behavioral requirements (UXR-1 through UXR-5) to `docs/spec.md` section 10
  - advanced `docs/CODEX_PROMPT.md` to Phase 1 with P1-01 as active task
- Phase 1 Implementation:
  - P1-01: `docs/examples/ux_acceptance_examples.md` — UX eval contract (7 moments, anti-pattern table)
  - P1-02: `scripts/send_summary.py` — digest rewritten with Russian locale, project-framing opening
  - P1-03: `src/handlers/confirm.py` — project name in confirmation replies, emoji removed, gender fixed
  - P1-04: `src/handlers/confirm.py`, `nl_handler.py`, `reviewer.py` — edit ack, type-select prompt, unreviewed count pointer
  - P1-05: `docs/review/ux_review_p1.md` — UX review pack; 3 low-severity gaps deferred to Phase 2
- Phase 2 Decomposition Pass:
  - decomposed Phase 2 into four tasks (P2-01 through P2-04) in `docs/tasks.md`
  - added Phase 2 memory behavioral requirements (MR-1 through MR-4) to `docs/spec.md` section 11
  - advanced `docs/CODEX_PROMPT.md` to Phase 2 with P2-01 as active task
- Phase 2 Implementation:
  - P2-01: `src/schema.sql`, `src/db.py` — project_memory table + upsert/get/item_count
  - P2-02: `src/handlers/memory_cmd.py` — /memory command, bounded LLM generation, staleness cache
  - P2-03: `src/handlers/chat_handler.py` — memory injection into system prompt
  - P2-04: `docs/review/continuity_eval_p2.md` — continuity eval; 3 low-severity findings deferred to Phase 3
- Phase 3 Decomposition Pass:
  - decomposed Phase 3 into three tasks (P3-01 through P3-03) in `docs/tasks.md`
  - added Phase 3 reflection behavioral requirements (RR-1 through RR-3) to `docs/spec.md` section 12
  - advanced `docs/CODEX_PROMPT.md` to Phase 3 with P3-01 as active task
- Phase 3 Implementation:
  - P3-01: `src/reviewer.py`, `src/handlers/review.py` — inject project memory context into idea review prompt
  - P3-02: `src/handlers/reflect_cmd.py`, `src/bot.py`, `src/handlers/help_cmd.py` — /reflect command for project-level structured reflection
  - P3-03: `docs/review/reflection_eval_p3.md` — reflection eval pack; all findings low/low-medium severity, phase CLOSED
- Phase 4 Implementation:
  - P4-01: `systemd/film-school-bot.service`, `.env.example`, `docs/DEPLOY.md` — deployment package
  - P4-02: `src/bot.py` (start_command) — onboarding flow: emoji removed, first-project hint added
  - P4-03: `docs/review/productization_review_p4.md` — productization review pack; no regressions, phase CLOSED

---

## Phase History

- Earlier retrofit work: aligned the project with the AI workflow playbook artifact system
- Current pass: integrated product framing, architecture clarity, UX principles, and phased next-step planning into that artifact system

---

## Open Findings (Audit Cycle 1 — 2026-04-01)

| ID | Sev | Description | Files | Status |
|----|-----|-------------|-------|--------|
| CODE-1 | P1 | log_llm_call fires before LLM in nl_handler | src/handlers/nl_handler.py | ✅ Fixed 2026-04-01 |
| CODE-2 | P1 | log_llm_call fires before LLM in review.py | src/handlers/review.py | ✅ Fixed 2026-04-01 |
| CODE-3 | P2 | due_date not validated before DB write | src/tools.py | ✅ Fixed 2026-04-01 |
| CODE-4 | P2 | chat_handler bypasses openclaw_client retry | src/handlers/chat_handler.py | ✅ Fixed 2026-04-01 |
| CODE-5 | P2 | reflect input text no per-item cap | src/handlers/reflect_cmd.py | ✅ Fixed 2026-04-01 |
| CODE-6 | P2 | REVIEW_SYSTEM_PROMPT in English (mixed with Russian context) | src/reviewer.py | ✅ Fixed 2026-04-01 |
| CODE-7 | P2 | send_summary emoji + English section headers | scripts/send_summary.py | ✅ Fixed 2026-04-01 |
| CODE-8 | P2 | Memory cap inconsistent: spec/prompt/API disagree | src/handlers/memory_cmd.py | ✅ Fixed 2026-04-01 |
| CODE-9 | P2 | smoke_test EXPECTED_TABLES missing project_memory, llm_call_log | scripts/smoke_test_db.py | ✅ Fixed 2026-04-01 |
| CODE-10 | P2 | smoke_test no Phase 2/3 DB function coverage | scripts/smoke_test_db.py | ✅ Fixed 2026-04-01 |
| CODE-11 | P3 | confirm.py project name edge case (G3) | src/handlers/confirm.py | ✅ Fixed 2026-04-01 |
| CODE-12 | P3 | /memory cache-hit no staleness date (F1) | src/handlers/memory_cmd.py | ✅ Fixed 2026-04-01 |
| CODE-13 | P3 | memory injection no user indicator on fail (F2) | src/handlers/chat_handler.py | ✅ Fixed 2026-04-01 |
| CODE-14 | P3 | review_history excluded from staleness counter (F3) | src/db.py | ✅ Fixed 2026-04-01 |
| CODE-15 | P3 | get_status unbounded scan limit=1_000_000 | src/tools.py | ✅ Fixed 2026-04-01 |

---

## Compaction Protocol

When `Completed Tasks` exceeds 20 items or `Phase History` exceeds 5 summaries:
- move older entries into an archive summary block
- keep only the active phase, open findings, and recent history here
