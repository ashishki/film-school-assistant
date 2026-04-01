# Film School Assistant — Phase Plan

## 1. Planning Principle

This plan follows the AI workflow playbook:
- artifact-first
- phase-based
- role-separated
- reviewable
- minimum sufficient solution shape
- no speculative overengineering

It is not a wishlist. It is the recommended development order.

## 2. What Has Already Been Built

Implemented foundation (Phases 0–5, Audit Cycle 1):
- Telegram-first capture and management by text and voice
- structured entities: notes, ideas, deadlines, homework
- project scoping; confirmation and edit replies are project-aware
- local Whisper voice transcription
- multi-entity NL extraction — one message can produce multiple queued entities
- context-aware NL handler — last 5 messages used to resolve back-references
- targeted clarifying questions on parse failure (not generic errors)
- ✏️ Уточнить button — lets user rewrite a pending entity without retyping from scratch
- bounded chat tool use
- idea review with project-memory context injection
- `/memory` — bounded per-project state summary, injected into chat context
- `/reflect` — structured project reflection: current state, tensions, next focus
- reminders; weekly digest with project-level next-step framing
- search, edit, archive
- private VPS deployment with SQLite and `systemd`; documented in `docs/DEPLOY.md`

This foundation is substantial enough to support a real product. The next work should clarify and deepen it, not replace it.

## 3. Why This Order Is Correct

The current weakness is not infrastructure scarcity. It is:
- weak product legibility
- weak continuity feeling
- shallow memory beyond stored records
- unclear prioritization

So the correct order is:
1. documentation and product clarity
2. UX continuity inside the current surface
3. creative memory
4. higher-leverage reflection and guidance
5. packaging expansion if justified

## 4. Phase 0 — Documentation and Product Clarity Foundation

### Objective

Make the repository product-legible, architecture-coherent, and workflow-governed.

### Why now

Without this, later phases will drift into random feature work.

### Must exist before starting

- current implementation inventory
- playbook-compatible artifact set

### Scope in

- README rewrite
- product framing docs
- architecture clarity docs
- workflow boundary docs
- phase planning docs

### Scope out

- runtime feature changes
- web app work
- memory implementation

### Key artifacts

- `README.md`
- `docs/PRODUCT_OVERVIEW.md`
- `docs/ARCHITECTURE.md`
- `docs/WORKFLOW_BOUNDARIES.md`
- `docs/PHASE_PLAN.md`
- `docs/USER_EXPERIENCE.md`
- `docs/DECISIONS.md`
- updated `docs/spec.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`

### Acceptance criteria

- the repo no longer reads like a feature bundle
- current system boundaries are explicit
- next phase entry is documented and reviewable

### Evidence / review checks

- manual document consistency review
- phase decomposition pass before Phase 1 starts

### Deterministic vs LLM

- deterministic: artifact structure, task sequencing, boundary definition
- LLM: drafting and refining language only

### Risks

- over-claiming current product maturity
- inventing roadmap complexity

### Deferred

- any implementation work not required for documentation coherence

## 5. Phase 1 — Product Experience and UX Continuity

### Objective

Make the assistant feel like continuity support, not command-driven storage.

### Why it belongs now

This creates the highest user-visible value per complexity without changing architecture class.

### Must exist before starting

- approved Phase 0 artifacts
- explicit UX principles
- explicit next-phase task graph

### Scope in

- better confirmation flow language
- clearer project context and active-project awareness
- stronger weekly digest framing
- better progress feeling in replies
- sharper tone and continuity cues

### Scope out

- embeddings
- vector DB
- web interface
- multi-user behavior

### Key artifacts

- updated `docs/tasks.md`
- updated `docs/CODEX_PROMPT.md`
- UX-specific acceptance criteria
- examples of desired assistant responses
- eval notes for reply quality and continuity usefulness

### Implementation tasks

- redesign response framing for capture, confirm, and completion moments
- improve project context visibility in key flows
- tighten weekly digest into a continuity artifact rather than a generic recap
- improve "next step" guidance with deterministic context support

### Acceptance criteria

- the assistant feels more oriented and less mechanical in common flows
- weekly output gives clearer continuity and prioritization
- the user can tell what project and state they are in without friction

### Evidence / evals / review checks

- transcript-based UX review on representative conversations
- validator check against `docs/USER_EXPERIENCE.md`
- light implementation review per task
- deep review at phase boundary

### Deterministic vs LLM

- deterministic: flow state, project context, triggers, summary inputs
- LLM: wording, bounded reflection, tone-sensitive summaries where justified

### Major risks

- polishing language without improving orientation
- making responses longer instead of clearer

### Deferred

- persistent creative memory layer

## 6. Phase 2 — Creative Memory Layer

### Objective

Add bounded creative memory that helps the assistant maintain project continuity across time.

### Why it belongs here

Continuity should improve before higher-level guidance. Otherwise guidance will still be shallow.

### Must exist before starting

- stronger Phase 1 UX continuity
- clear definition of memory artifacts
- explicit eval criteria for memory usefulness

### Scope in

- project state summaries
- continuity notes
- creative thread tracking
- stable "current state of project" artifacts

### Scope out

- generalized RAG
- large document retrieval
- autonomous planning from memory

### Key artifacts

- memory model update in `docs/ARCHITECTURE.md`
- eval artifact for continuity quality
- implementation contract update if storage rules expand

### Implementation tasks

- define memory artifacts and write/update rules
- choose deterministic and bounded-LLM responsibilities
- add retrieval and refresh paths for project continuity
- add review prompts that use memory artifacts safely

### Acceptance criteria

- the assistant can surface recent project state coherently
- memory outputs reduce repetition and re-explanation for the user
- memory remains bounded, inspectable, and non-magical

### Evidence / evals / review checks

- continuity eval on real or synthetic project histories
- regression check for false continuity claims
- deep review mandatory

### Deterministic vs LLM

- deterministic: storage structure, refresh triggers, retrieval selection
- LLM: synthesis of bounded continuity summaries

### Major risks

- jumping to embeddings before memory artifacts are defined
- inventing continuity rather than grounding it in stored state

### Deferred

- open-ended semantic search platform

## 7. Phase 3 — Higher-Leverage Reflection and Guidance

### Objective

Turn the memory-backed system into a more useful reflective assistant for creative development.

### Why it belongs here

Reflection quality depends on continuity quality.

### Must exist before starting

- Phase 2 memory artifacts
- eval contract for reflection usefulness

### Scope in

- stronger idea development guidance
- project-level reflection prompts
- continuity-aware weekly or milestone guidance

### Scope out

- autonomous planning
- persistent agent roles

### Key artifacts

- updated product and architecture docs
- eval artifact for guidance quality

### Acceptance criteria

- reflection is materially more useful than current single-idea critique
- outputs remain grounded in stored project context

### Evidence / evals / review checks

- side-by-side usefulness review on representative prompts
- deep review mandatory

### Deterministic vs LLM

- deterministic: context assembly, guardrails, output triggers
- LLM: reflective synthesis and critique

### Major risks

- vague inspirational language instead of actionable guidance

### Deferred

- collaborative review workflows

## 8. Phase 5 — NL Interaction Quality

### Objective

Make free-text capture smarter: handle multi-item messages, recover gracefully from parse failures, and let the user correct a pending entity with minimal friction.

### Why it belongs here

Phases 1–4 improved continuity, memory, and reflection. Phase 5 closes the gap in the most frequent interaction — free-text capture — where users regularly send compound messages, get unhelpful generic errors, or have no way to fix a misread entity without discarding it.

### What was built

- multi-entity extraction — one message → `{"entities": [...]}` → queued per-entity confirmation
- NL context window — last 5 raw messages passed to extraction so back-references resolve
- targeted clarifying questions — 4 distinct failure modes each get a specific message
- ✏️ Уточнить button — third keyboard option; sets re-extraction mode on next free-text message

### Key artifacts

- `src/state.py` — `pending_entities`, `pending_clarify`, `nl_context`, `add_nl_context()`
- `src/handlers/nl_handler.py` — multi-entity schema, context prompt, clarifying messages
- `src/handlers/confirm.py` — `_queue_next_pending_entity()`, 3-button keyboard
- `src/bot.py` — clarify callback handler
- `docs/review/nl_quality_review_p5.md` — phase review pack; all NR-1..4 met

### Acceptance criteria met

- single-entity path unchanged (backward compatible)
- multi-entity queuing confirmed in code and review
- ruff passes on all tasks; no regressions

### Deferred (low severity)

- R1-F1: save/restore pattern for `pending_entities` around `clear_pending` in `_do_confirm`
- R3-F1: clarify flow leaves old message in `nl_context`

---

## 9. Phase 4 — Productization and Optional Surface Expansion

### Objective

Improve packaging, onboarding, and optional additional surfaces if earlier phases prove the product value.

### Why last

Packaging a weakly differentiated product surface earlier would amplify the wrong thing.

### Must exist before starting

- strong continuity story
- proven memory usefulness
- stable reflective value

### Scope in

- deployment simplification
- onboarding clarity
- optional web review layer for browsing or editing

### Scope out

- premature team SaaS repositioning
- multi-tenant platform complexity

### Acceptance criteria

- added packaging increases usability without distorting product identity

### Evidence / evals / review checks

- adoption and usability review
- architecture review before any new surface becomes primary

### Deterministic vs LLM

- depends on chosen packaging work

### Major risks

- mistaking surface expansion for product progress

### Deferred

- multi-user product unless evidence clearly demands it

## 10. Current Development Status

Phases 0–5 and Audit Cycle 1 are complete. There is no active phase.

If development resumes, the recommended next areas (in order of leverage):
1. Voice capture improvement — voice notes currently enter the same extraction path but lose the multi-entity and context benefits; aligning voice + text capture would close that gap.
2. Second audit cycle — now that NL extraction is significantly more complex, a targeted code audit of the queue and clarify paths would be valuable before any further expansion.
3. Web review layer — deferred per DECISIONS.md; condition not yet met but closer now that capture quality has improved.

## 10. Active Development Loop

The active loop for this repository is not the original project-bootstrap loop.

Because the product phases and architectural direction are already defined, the correct loop is:

1. `Claude Orchestrator` selects the next phase from this document.
2. `Claude` runs a **Phase Decomposition Pass** for that phase.
3. `Claude` updates `docs/tasks.md`, `docs/CODEX_PROMPT.md`, and any directly affected source-of-truth docs.
4. `Claude` runs a **Phase Entry Check**.
5. If the phase package passes, `Claude Orchestrator` dispatches one task at a time to Codex.
6. Each task gets light review after implementation.
7. The phase ends with deep review and a human phase gate.

Definitions:
- **Phase Decomposition Pass**: a narrow strategist function for one upcoming phase only. It does not redefine the whole product or architecture from scratch.
- **Phase Entry Check**: a narrow validator function that checks the current phase package for internal consistency, scope correctness, reviewability, and drift against source-of-truth artifacts.

This project does **not** need:
- a full-project strategist rerun before each phase
- the original project-bootstrap `Phase 1 Validator` flow for the whole repository

## 11. Documentation That Must Be Updated Before Coding Starts

Before Phase 1 coding starts, update:
- `docs/tasks.md`
- `docs/CODEX_PROMPT.md`
- `docs/spec.md`
- `docs/USER_EXPERIENCE.md`
- `docs/ARCHITECTURE.md` if the phase introduces any new bounded AI path

## 12. What Should Go Into `docs/tasks.md`

`docs/tasks.md` should contain:
- concrete UX continuity tasks
- exact file scope
- deterministic vs LLM ownership notes
- explicit acceptance criteria
- review and eval references

It should not contain:
- vague product aspirations
- speculative later-phase ideas
- mixed implementation and roadmap prose
