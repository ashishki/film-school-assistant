# Film School Assistant — Task Graph

Status legend:
- `[ ]` not started
- `[-]` in progress
- `[x]` done
- `[!]` blocked

Current phase goal:
- complete the documentation clarity foundation so the next implementation phase is product-led, architecture-aware, and playbook-governed

---

## Phase 0 — Documentation and Product Clarity Foundation

Goal:
- turn the repository into a coherent product and implementation system before feature work resumes

Exit criteria:
- the product category is explicit and stable
- README, product docs, architecture docs, and workflow docs no longer contradict each other
- the next phase is defined in reviewable artifacts, not implied in conversation
- the immediate build order is documented with acceptance criteria

[x] D01 — Rewrite repository landing documentation
Owner: codex
Phase: 0
Type: none
Depends-On: none
Objective: |
  Reframe the landing page so the repository reads as a creative workflow assistant rather
  than a Telegram feature list while remaining honest about the current implementation.
Acceptance-Criteria:
  - id: AC-1
    description: "README defines the product in one sentence without calling it only a notes bot."
    test: "manual-doc-check"
  - id: AC-2
    description: "README explains current architecture, status, setup pointer, and roadmap pointer."
    test: "manual-doc-check"
Files:
  - README.md
Notes: |
  This is a product framing task. Do not inflate the current product into SaaS language.

[x] D02 — Add product-facing source-of-truth documents
Owner: codex
Phase: 0
Type: none
Depends-On: D01
Objective: |
  Create product-facing documents that define what the product is, who it is for, what it
  is not, and how the user experience should feel.
Acceptance-Criteria:
  - id: AC-1
    description: "PRODUCT_OVERVIEW.md defines target user, JTBD, outcomes, boundaries, and differentiation."
    test: "manual-doc-check"
  - id: AC-2
    description: "USER_EXPERIENCE.md defines tone, continuity, emotional design goals, and UX anti-goals."
    test: "manual-doc-check"
Files:
  - docs/PRODUCT_OVERVIEW.md
  - docs/USER_EXPERIENCE.md
Notes: |
  These docs are product-facing. They must not collapse into implementation detail dumps.

[x] D03 — Reframe architecture and workflow boundaries
Owner: codex
Phase: 0
Type: none
Depends-On: D02
Objective: |
  Rewrite the core architecture docs so the system shape, current runtime, governance, and
  deterministic vs LLM ownership are explicit and aligned with the product definition.
Acceptance-Criteria:
  - id: AC-1
    description: "ARCHITECTURE.md explicitly names current product category, governance level, and runtime tier."
    test: "manual-doc-check"
  - id: AC-2
    description: "WORKFLOW_BOUNDARIES.md defines deterministic ownership, LLM ownership, approval gates, and drift-prevention rules."
    test: "manual-doc-check"
Files:
  - docs/ARCHITECTURE.md
  - docs/WORKFLOW_BOUNDARIES.md
  - docs/IMPLEMENTATION_CONTRACT.md
Notes: |
  Keep the retrofit discipline. This is not a rollback away from the playbook.

[x] D04 — Define the phase plan and active product decisions
Owner: codex
Phase: 0
Type: none
Depends-On: D03
Objective: |
  Replace implied future direction with an explicit phase plan and a written record of
  what current constraints are valid, temporary, or deferred.
Acceptance-Criteria:
  - id: AC-1
    description: "PHASE_PLAN.md defines built, next, deferred, phase boundaries, exit criteria, and evidence gates."
    test: "manual-doc-check"
  - id: AC-2
    description: "DECISIONS.md records why Telegram-first, SQLite, and private VPS remain valid now."
    test: "manual-doc-check"
Files:
  - docs/PHASE_PLAN.md
  - docs/DECISIONS.md
Notes: |
  The phase plan must follow artifact-first, reviewable sequencing rather than wishlist logic.

[x] D05 — Sync implementation-facing playbook artifacts
Owner: codex
Phase: 0
Type: none
Depends-On: D04
Objective: |
  Update implementation-facing docs so future strategist, orchestrator, and validator work
  starts from the new documentation system instead of the previous hardening-only framing.
Acceptance-Criteria:
  - id: AC-1
    description: "spec.md reflects the product framing and immediate phase boundary."
    test: "manual-doc-check"
  - id: AC-2
    description: "CODEX_PROMPT.md reflects the active documentation foundation phase and points to the next phase correctly."
    test: "manual-doc-check"
Files:
  - docs/spec.md
  - docs/CODEX_PROMPT.md
  - docs/tasks.md
Notes: |
  Preserve playbook compatibility. Do not fabricate test or CI results.

---

## Phase 1 — Product Experience and UX Continuity

Goal:
- improve the user-visible experience inside Telegram so the assistant feels like continuity support rather than structured storage with commands

Entry condition:
- Phase 0 artifacts are approved

Exit criteria:
- confirmation flows use oriented, project-aware language
- weekly digest reads as a continuity artifact with directional framing
- active-project context is visible in relevant flows without user prompting
- reply framing at key moments (save, edit, confirm, review) feels grounded, not mechanical
- a transcript-based UX review pack validates the above across representative sessions

---

[x] P1-01 — UX Acceptance Examples Pack
Owner: claude
Phase: 1
Type: documentation
Depends-On: none
Objective: |
  Produce a concrete set of before/after examples for the four key interaction moments:
  capture confirmation, edit confirmation, active-project-context reply, and digest opening.
  These examples define what "better" means before any code changes are made.
Why-Now: |
  Coding UX improvements without agreed examples leads to subjective argument at review time.
  The examples are the eval contract for every subsequent task in this phase.
File-Scope:
  - docs/examples/ux_acceptance_examples.md (new file)
Deterministic-Owned:
  - selection of moments to cover (this list is fixed: capture confirm, edit confirm, active project reply, digest opening)
  - structure of each example (before / after / why)
LLM-Owned:
  - drafting the example language to match USER_EXPERIENCE.md tone and anti-goals
Acceptance-Criteria:
  - id: AC-1
    description: "Examples cover all four moments: capture confirmation, edit confirmation, active-project reply, weekly digest opening."
    test: "manual review against USER_EXPERIENCE.md"
  - id: AC-2
    description: "Each example contains a before (current or representative), an after (target), and a one-line rationale."
    test: "manual review"
  - id: AC-3
    description: "No after-state example uses generic AI praise, excessive length, or false-certainty language."
    test: "manual review against USER_EXPERIENCE.md section 6 anti-goals"
Dependencies: none
Review-Mode: light (documentation only)
Out-Of-Scope:
  - code changes
  - new flows not already in the current implementation
  - eval automation or scoring pipelines

---

[x] P1-02 — Weekly Digest Contract Rewrite
Owner: codex
Phase: 1
Type: doc + implementation
Depends-On: P1-01
Objective: |
  Rewrite the weekly digest output contract in docs/spec.md and implement the corresponding
  changes in scripts/send_summary.py so the digest reads as a continuity artifact rather than
  a raw activity log or generic weekly recap.
Why-Now: |
  The weekly digest is currently the highest-leverage continuity touchpoint.
  It is also where the gap between "stored data" and "useful continuity framing" is most visible.
  Improving it delivers phase value without touching the core capture or edit flows.
File-Scope:
  - docs/spec.md (section 10, UXR-3 digest contract)
  - scripts/send_summary.py
Deterministic-Owned:
  - which entity types to include and their ordering
  - grouping rules by project or type
  - deduplication state and send guard
  - delivery timing and trigger logic
LLM-Owned:
  - bounded framing sentence at digest opening, derived from actual stored project state
  - optional one-line directional pointer per active project if records exist
Acceptance-Criteria:
  - id: AC-1
    description: "Digest opens with a brief grounded framing sentence referencing actual project state, not a generic header."
    test: "manual review against P1-01 digest opening example"
  - id: AC-2
    description: "Digest includes a directional next-step pointer per active project where records support one."
    test: "manual review on representative or synthetic test data"
  - id: AC-3
    description: "Digest send trigger and dedup guard remain fully deterministic after changes."
    test: "code review of scripts/send_summary.py trigger and guard logic"
  - id: AC-4
    description: "Total digest length does not increase relative to the current version."
    test: "manual comparison on identical input data"
Dependencies: P1-01
Review-Mode: light (doc + code)
Out-Of-Scope:
  - multi-project comparative ranking
  - semantic summary generation beyond one bounded framing sentence
  - digest scheduling or delivery window changes

---

[x] P1-03 — Active Project Visibility and Orientation
Owner: codex
Phase: 1
Type: implementation
Depends-On: P1-01
Objective: |
  Make the active project visible in capture confirmations and key replies without the user
  needing to ask or invoke project-specific commands. Project context should surface
  deterministically at save time.
Why-Now: |
  The current confirmation flow does not orient the user to project context.
  The assistant feels like generic storage even when the user has a clear active project.
  Adding project name to confirmation replies closes this gap with minimal code change
  and no new LLM path.
File-Scope:
  - src/handlers/nl_handler.py
  - src/handlers/chat_handler.py (if project context is surfaced through chat tool confirmation responses)
Deterministic-Owned:
  - reading project association from DB at confirmation time
  - including project name in reply template when association exists
  - fallback wording when no project is associated (no error, no prompt to set project)
LLM-Owned:
  - none; project-name inclusion is fully deterministic
Acceptance-Criteria:
  - id: AC-1
    description: "Confirmation replies for capture actions include the project name when a project is associated."
    test: "manual test: save a note with active project set; verify reply includes project name"
  - id: AC-2
    description: "When no project is associated, confirmation reply does not include a placeholder, error, or unsolicited prompt to set a project."
    test: "manual test: save a note with no project set"
  - id: AC-3
    description: "Project name appears before or alongside the entity description, not as an afterthought at the end."
    test: "manual review against P1-01 examples"
Dependencies: P1-01
Review-Mode: light
Out-Of-Scope:
  - project-switching commands
  - project listing, creation, or archiving changes
  - any new entity types or flows

---

[x] P1-04 — Reply Framing Rewrite for Core Moments
Owner: codex
Phase: 1
Type: implementation
Depends-On: P1-01, P1-03
Objective: |
  Rewrite the response templates for save, edit, confirm, and review-completion moments
  so they feel grounded and directional rather than mechanical. Tone and wording must match
  USER_EXPERIENCE.md principles and the P1-01 accepted examples.
Why-Now: |
  These are the most frequent interaction moments across every session.
  Improving template wording here improves product feel without new features or new architecture.
File-Scope:
  - src/handlers/nl_handler.py
  - src/handlers/chat_handler.py
  - src/reviewer.py (review completion wording only)
Deterministic-Owned:
  - template structure for save, edit, and confirm moments (project name, entity type, action taken)
  - fallback wording for all deterministic paths
LLM-Owned:
  - bounded one-line next-step suggestion appended to review-completion reply, if stored project data supports it
  - save, edit, and confirm templates must not use LLM for wording
Acceptance-Criteria:
  - id: AC-1
    description: "Save, edit, and confirm reply templates match the P1-01 after-state examples in wording and length."
    test: "manual review against P1-01 examples"
  - id: AC-2
    description: "No template contains generic AI praise phrases (great, awesome, perfect, etc.)."
    test: "grep over template strings in nl_handler.py and chat_handler.py"
  - id: AC-3
    description: "Review completion reply ends with a bounded one-sentence next-step pointer where stored data supports it."
    test: "manual test on a representative review session"
  - id: AC-4
    description: "No reply is longer after changes than before, except where project name was absent before."
    test: "manual length comparison on representative flows"
Dependencies: P1-01, P1-03
Review-Mode: light
Out-Of-Scope:
  - changing which commands trigger which flows
  - new entity types
  - LLM use for save, edit, or confirm templates

---

[x] P1-05 — Transcript-Based UX Review Pack
Owner: claude
Phase: 1
Type: documentation / eval
Depends-On: P1-02, P1-03, P1-04
Objective: |
  Review representative session transcripts (real or synthetic) against the P1-01 examples
  and USER_EXPERIENCE.md principles. Produce a structured UX review pack that documents
  what improved, what gaps remain, and whether any items warrant rework before Phase 1 closes.
Why-Now: |
  Phase 1 should not close on code review alone. Transcript review is the evidence gate
  for whether UX continuity actually improved in practice. It is the deep review artifact
  for this phase.
File-Scope:
  - docs/review/ux_review_p1.md (new file)
Deterministic-Owned:
  - which moments to review (fixed: the four moments from P1-01)
  - review structure per moment: moment name / before / after / verdict / notes
LLM-Owned:
  - drafting the review commentary and verdict prose from transcript evidence
Acceptance-Criteria:
  - id: AC-1
    description: "Review covers all four moments from P1-01."
    test: "doc structure check"
  - id: AC-2
    description: "Each moment has a verdict (improved / unchanged / regressed) with supporting evidence."
    test: "manual review"
  - id: AC-3
    description: "Gaps or rework items are listed explicitly, not folded into vague commentary."
    test: "manual review"
  - id: AC-4
    description: "Phase 1 close decision in CODEX_PROMPT.md references this review pack."
    test: "CODEX_PROMPT.md update at phase close"
Dependencies: P1-02, P1-03, P1-04
Review-Mode: deep (phase-close artifact; human approval required before Phase 2 entry)
Out-Of-Scope:
  - automated eval pipelines or benchmark scoring
  - Phase 2 feature proposals (belong in Phase 2 decomposition pass)
  - new transcript capture tooling

---

## Phase 2 — Creative Memory Layer

Goal:
- give the assistant bounded memory of each project's current state so it can maintain continuity across sessions without requiring the user to re-explain context

Entry condition:
- Phase 1 artifacts approved (phase gate passed)

Exit criteria:
- project_memory table exists and is populated via /memory command
- chat handler injects active project memory into system prompt when available
- memory generation is bounded LLM, input assembly is deterministic
- continuity eval pack confirms chat quality improvement

---

[ ] P2-01 — project_memory Schema and DB Layer
Owner: codex
Phase: 2
Type: schema + implementation
Depends-On: none
Objective: |
  Add the project_memory table to the schema and the corresponding db.py functions.
  This is the storage layer for Phase 2 — no LLM involved in this task.
Why-Now: |
  All other Phase 2 tasks depend on having a stable storage layer first.
  Defining the schema and DB API before generation or retrieval prevents drift.
File-Scope:
  - src/schema.sql
  - src/db.py
Deterministic-Owned:
  - table definition, constraints, indexes
  - upsert, get, and list functions
  - _ALLOWED_TABLES whitelist update
LLM-Owned:
  - none
Acceptance-Criteria:
  - id: AC-1
    description: "project_memory table created with: id, project_id (FK projects), summary_text, generated_at, item_count_snapshot, model_used."
    test: "smoke test passes; schema inspect confirms table"
  - id: AC-2
    description: "db.py exposes: upsert_project_memory, get_project_memory(project_id), list_projects_without_memory."
    test: "functions importable; smoke test passes"
  - id: AC-3
    description: "project_memory added to _ALLOWED_TABLES."
    test: "code review"
  - id: AC-4
    description: "UNIQUE constraint on project_id (one memory row per project)."
    test: "schema review"
Dependencies: none
Review-Mode: light
Out-Of-Scope:
  - memory generation logic
  - chat injection
  - any LLM calls

---

[ ] P2-02 — Project Memory Generation Command
Owner: codex
Phase: 2
Type: implementation
Depends-On: P2-01
Objective: |
  Add a /memory command that generates a bounded LLM summary of the active project
  from its stored records and saves it to project_memory. The command also displays
  the current memory to the user if one exists.
Why-Now: |
  Memory must be generated before it can be injected into chat context.
  The command gives the user explicit control over when memory is refreshed.
File-Scope:
  - src/handlers/memory_cmd.py (new file)
  - src/bot.py (register /memory command handler)
  - src/handlers/help_cmd.py (add /memory to help text)
Deterministic-Owned:
  - project resolution (use active project from state, or first arg as project name/slug)
  - input assembly: fetch recent notes, ideas, deadlines, review_history for the project
  - storage: upsert_project_memory after generation
  - staleness check: if memory exists and item_count_snapshot matches current count, return cached
  - LLM call log entry
LLM-Owned:
  - bounded summary generation: one paragraph, max 200 tokens, grounded in assembled records
  - model: Haiku-class (intent path)
  - system prompt: factual summary only; no invention; no advice
Acceptance-Criteria:
  - id: AC-1
    description: "/memory with active project set generates and stores a summary, returns it to the user."
    test: "manual test with active project and at least one note/idea"
  - id: AC-2
    description: "/memory with no active project returns a clear prompt to set a project first."
    test: "manual test with no active project"
  - id: AC-3
    description: "If item_count_snapshot matches current count, returns cached memory without LLM call."
    test: "code review of staleness check; call log count before/after"
  - id: AC-4
    description: "LLM call is logged in llm_call_log."
    test: "code review"
  - id: AC-5
    description: "Memory summary contains no invented facts — only references to stored records."
    test: "manual review of output against actual DB state"
Dependencies: P2-01
Review-Mode: light
Out-Of-Scope:
  - automatic background memory refresh
  - memory for multiple projects in one command
  - embeddings or semantic indexing

---

[ ] P2-03 — Memory Injection into Chat Context
Owner: codex
Phase: 2
Type: implementation
Depends-On: P2-01, P2-02
Objective: |
  When the chat handler is invoked and the active project has a memory entry,
  inject the project memory summary into the system prompt so the LLM has
  project context without the user needing to re-explain it.
Why-Now: |
  Without injection, generated memory is only useful when the user explicitly reads it.
  Injection is the step that makes memory act as continuity rather than just storage.
File-Scope:
  - src/handlers/chat_handler.py
  - src/db.py (get_project_memory — already added in P2-01)
Deterministic-Owned:
  - reading project_id from user_state.active_project_id
  - DB lookup of project memory
  - constructing the augmented system prompt
  - fallback to base system prompt when no memory exists
LLM-Owned:
  - none new; the LLM receives the injected context but does not manage it
Acceptance-Criteria:
  - id: AC-1
    description: "When active project has memory, system prompt includes a 'Project context:' block with the summary."
    test: "code review of handle_chat; verify prompt construction"
  - id: AC-2
    description: "When no active project or no memory exists, system prompt is unchanged from current base."
    test: "code review; no regression on existing chat behaviour"
  - id: AC-3
    description: "Memory injection is a DB read only — no LLM call added in this task."
    test: "code review; llm_call_log count unchanged for injection-only path"
  - id: AC-4
    description: "If DB read fails, chat proceeds with base system prompt (no crash, no silent wrong state)."
    test: "code review of error path"
Dependencies: P2-01, P2-02
Review-Mode: light
Out-Of-Scope:
  - dynamic memory update during a chat session
  - injecting memory for multiple projects
  - vector similarity retrieval

---

[ ] P2-04 — Continuity Eval Pack
Owner: claude
Phase: 2
Type: documentation / eval
Depends-On: P2-02, P2-03
Objective: |
  Review representative sessions (real or synthetic) with and without memory injection
  active. Produce a structured eval pack that documents whether memory improved
  continuity quality, and whether any issues (hallucination, noise, over-injection) were
  observed.
Why-Now: |
  Phase 2 should not close on code review alone. Memory is an LLM-touching feature
  and its quality must be verified before Phase 3 builds on top of it.
File-Scope:
  - docs/review/continuity_eval_p2.md (new file)
Deterministic-Owned:
  - eval structure: session, without-memory response, with-memory response, verdict, notes
  - which dimensions to evaluate: continuity accuracy, hallucination risk, response relevance
LLM-Owned:
  - drafting verdict prose from session evidence
Acceptance-Criteria:
  - id: AC-1
    description: "Eval covers at least 3 interaction types: project-context question, capture confirmation, idea review."
    test: "doc structure check"
  - id: AC-2
    description: "Each dimension has a verdict: improved / unchanged / regressed, with evidence."
    test: "manual review"
  - id: AC-3
    description: "Any hallucination or over-injection findings are listed explicitly."
    test: "manual review"
  - id: AC-4
    description: "Phase 2 close decision references this eval pack."
    test: "CODEX_PROMPT.md update at phase close"
Dependencies: P2-02, P2-03
Review-Mode: deep (phase-close artifact; human approval required before Phase 3 entry)
Out-Of-Scope:
  - automated benchmark pipelines
  - Phase 3 feature proposals
