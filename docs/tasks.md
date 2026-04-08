# Film School Assistant — Task Graph

Status legend:
- `[ ]` not started
- `[-]` in progress
- `[x]` done
- `[!]` blocked

Current phase goal:
- enter Phase 8 with an execution-ready memory upgrade plan built around project-first evidence recall, provenance, and low operational complexity

---

## Fix Queue — Audit Cycle 1 (resolve before any new phase)

[x] FIX-1 — log_llm_call ordering fix in nl_handler.py
Owner: codex
Phase: fix
Type: implementation
Depends-On: none
Objective: |
  Move log_llm_call to after complete_json succeeds so the daily quota
  counter is not incremented on transient LLM failures.
File-Scope:
  - src/handlers/nl_handler.py
Acceptance-Criteria:
  - id: AC-1
    description: "log_llm_call is called only after complete_json returns without raising."
    test: "code review"
  - id: AC-2
    description: "On LLMError, llm_call_log row count is unchanged."
    test: "code review of error path"
Review-Mode: light

---

[x] FIX-2 — log_llm_call ordering fix in review.py
Owner: codex
Phase: fix
Type: implementation
Depends-On: none
Objective: |
  Move log_llm_call to after review_idea() succeeds so the daily quota
  counter is not incremented on transient LLM or DB failures.
File-Scope:
  - src/handlers/review.py
Acceptance-Criteria:
  - id: AC-1
    description: "log_llm_call is called only after review_idea returns without raising."
    test: "code review"
  - id: AC-2
    description: "On LLMError in review_idea, llm_call_log row count is unchanged."
    test: "code review of error path"
Review-Mode: light

---

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

[x] P2-01 — project_memory Schema and DB Layer
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

[x] P2-02 — Project Memory Generation Command
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

[x] P2-03 — Memory Injection into Chat Context
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

[x] P2-04 — Continuity Eval Pack
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

---

## Phase 4 — Productization

Goal:
- simplify deployment and improve first-run onboarding so the assistant is easier to set up and orient within

Entry condition:
- Phase 3 artifacts approved (phase gate passed)

Exit criteria:
- VPS deployment is documented with a clean step-by-step guide and a working .env.example
- systemd service file uses venv python, not system python
- /start flow guides a new user toward creating their first project
- emoji removed from /start (consistent with Phase 1 UX rules)
- productization review pack confirms no regressions

Web layer: deferred — DECISIONS.md condition not yet met (continuity inspectable via /memory + /reflect in chat)

---

[x] P4-01 — Deployment Package
Owner: codex
Phase: 4
Type: config + documentation
Depends-On: none
Objective: |
  Fix the systemd service file to use the venv Python binary, add a .env.example
  template so new deployments have a clear starting point, and write a
  docs/DEPLOY.md guide covering fresh VPS setup end-to-end.
Why-Now: |
  The current service file hard-codes /usr/bin/python3 (bypasses venv) and has no
  env template. Anyone deploying fresh has no documented path.
File-Scope:
  - systemd/film-school-bot.service
  - .env.example (new file)
  - docs/DEPLOY.md (new file)
Deterministic-Owned:
  - service file ExecStart (use relative venv path placeholder)
  - .env.example keys list (all keys from config loading code, no real values)
  - DEPLOY.md structure: prerequisites, clone, venv, env setup, schema init, systemd install, smoke test
LLM-Owned:
  - none; all outputs are config and documentation
Acceptance-Criteria:
  - id: AC-1
    description: "film-school-bot.service ExecStart uses .venv/bin/python3 (or documented venv path placeholder)."
    test: "code review"
  - id: AC-2
    description: ".env.example lists all required env keys with placeholder values and a one-line comment per key."
    test: "cross-check against config loading in src/config.py or equivalent"
  - id: AC-3
    description: "docs/DEPLOY.md covers: prerequisites, clone, venv setup, .env configuration, schema init, systemd unit install, verify/smoke-test."
    test: "manual doc review"
  - id: AC-4
    description: "No real secrets or personal paths appear in any committed file."
    test: "code review"
Dependencies: none
Review-Mode: light
Out-Of-Scope:
  - Docker or docker-compose
  - multi-user deployment
  - CI/CD pipeline setup

---

[x] P4-02 — Onboarding Flow Polish
Owner: codex
Phase: 4
Type: implementation
Depends-On: P4-01
Objective: |
  Improve /start to give a new user a grounded first-run orientation: remove emoji,
  explain what the assistant does in one sentence, and hint at creating a first project
  as the recommended next step.
Why-Now: |
  /start currently uses emoji (inconsistent with Phase 1 UX rules) and doesn't guide
  the user toward the first meaningful action (creating a project).
File-Scope:
  - src/bot.py (start_command)
Deterministic-Owned:
  - welcome text (static template — no LLM)
  - first-action pointer: suggest /new_project <название>
LLM-Owned:
  - none
Acceptance-Criteria:
  - id: AC-1
    description: "/start reply contains no emoji."
    test: "code review of start_command text"
  - id: AC-2
    description: "/start reply describes what the assistant does in one or two sentences without generic AI praise."
    test: "manual review"
  - id: AC-3
    description: "/start reply ends with a concrete first-step hint: /new_project <название> to create a project."
    test: "code review"
  - id: AC-4
    description: "Reply stays under 10 lines."
    test: "manual review"
Dependencies: P4-01
Review-Mode: light
Out-Of-Scope:
  - multi-step onboarding wizard
  - interactive project creation from /start
  - any new commands or flows

---

[x] P4-03 — Phase 4 Productization Review Pack
Owner: claude
Phase: 4
Type: documentation / eval
Depends-On: P4-01, P4-02
Objective: |
  Deep review of Phase 4 outputs: deployment package completeness, onboarding
  flow quality, and regression check against Phase 1 UX rules. Produce a structured
  review pack that closes Phase 4.
File-Scope:
  - docs/review/productization_review_p4.md (new file)
Deterministic-Owned:
  - review structure: deployment / onboarding / regression check / close decision
LLM-Owned:
  - verdict prose
Acceptance-Criteria:
  - id: AC-1
    description: "Review covers deployment package, onboarding flow, and UX regression check."
    test: "doc structure check"
  - id: AC-2
    description: "Each section has a verdict with evidence."
    test: "manual review"
  - id: AC-3
    description: "Phase 4 close decision is explicit."
    test: "CODEX_PROMPT.md update at phase close"
Dependencies: P4-01, P4-02
Review-Mode: deep (phase-close artifact; final phase)
Out-Of-Scope:
  - Phase 5 proposals
  - web layer work

---

## Phase 3 — Higher-Leverage Reflection and Guidance

Goal:
- use the memory layer from Phase 2 to make reflection and guidance materially more useful than single-idea critique in isolation

Entry condition:
- Phase 2 artifacts approved (phase gate passed)

Exit criteria:
- idea review uses project memory as context, improving critique specificity
- /reflect command produces grounded project-level guidance from stored state
- reflection eval pack confirms quality improvement without hallucination regression

---

[x] P3-01 — Enhanced Idea Review with Project Context
Owner: codex
Phase: 3
Type: implementation
Depends-On: none
Objective: |
  Inject the active project's memory summary into the idea review prompt so the LLM
  can critique the idea in the context of where the project currently stands,
  rather than in isolation.
Why-Now: |
  Phase 2 generated project memory but review.py never uses it.
  Connecting the two is the minimum step to make review meaningfully project-aware.
File-Scope:
  - src/reviewer.py
  - src/handlers/review.py
Deterministic-Owned:
  - fetching project_memory from DB before LLM call (in review.py)
  - passing memory_text to review_idea as optional parameter
  - fallback when no memory exists: proceed with original prompt unchanged
LLM-Owned:
  - the review itself (Sonnet-class, unchanged); now receives richer context
Acceptance-Criteria:
  - id: AC-1
    description: "review_idea accepts project_memory_text: str | None parameter."
    test: "code review"
  - id: AC-2
    description: "When project_memory_text is provided, prompt includes 'Контекст проекта: {text}' before the idea."
    test: "code review of prompt construction"
  - id: AC-3
    description: "When project_memory_text is None, prompt is identical to the pre-Phase-3 baseline."
    test: "code review"
  - id: AC-4
    description: "review.py fetches get_project_memory(db, idea['project_id']) before calling review_idea."
    test: "code review"
  - id: AC-5
    description: "If get_project_memory fails, review proceeds without context — no crash."
    test: "code review of error path"
Dependencies: none
Review-Mode: light
Out-Of-Scope:
  - changing the review JSON schema or output format
  - adding memory to bulk review flows
  - any new LLM model path

---

[x] P3-02 — /reflect Command
Owner: codex
Phase: 3
Type: implementation
Depends-On: P3-01
Objective: |
  Add a /reflect command that generates a project-level reflection from stored state:
  current project standing, creative tensions identified in ideas and reviews, and
  one concrete recommended focus for the next work session.
Why-Now: |
  Single-idea review gives tactical critique. /reflect gives the user a wider view
  of where the project is and what deserves attention — a higher-leverage output
  only possible because Phase 2 memory now exists.
File-Scope:
  - src/handlers/reflect_cmd.py (new file)
  - src/bot.py (register /reflect)
  - src/handlers/help_cmd.py (add /reflect to help text)
Deterministic-Owned:
  - project resolution from active state
  - input assembly: project memory + up to 5 most recent review summaries + active deadlines
  - LLM call guard (daily limit check)
  - LLM call logging
LLM-Owned:
  - structured reflection output (Sonnet-class): project_standing, tensions, focus
  - system prompt: grounded in provided data only; no invented state; Russian output
  - output format: JSON with keys project_standing, tensions, focus_recommendation
Acceptance-Criteria:
  - id: AC-1
    description: "/reflect with active project and memory returns structured reflection with project_standing, tensions, focus_recommendation."
    test: "manual test"
  - id: AC-2
    description: "/reflect with no active project returns a prompt to set project first."
    test: "manual test"
  - id: AC-3
    description: "/reflect with active project but no memory returns a prompt to run /memory first."
    test: "code review"
  - id: AC-4
    description: "LLM call uses Sonnet-class (review model path), is logged in llm_call_log."
    test: "code review"
  - id: AC-5
    description: "Output contains no facts not traceable to input data."
    test: "manual review of output against DB state"
Dependencies: P3-01
Review-Mode: light
Out-Of-Scope:
  - autonomous planning or multi-session scheduling
  - persistent agent roles
  - reflect without active project memory

---

[x] P3-03 — Reflection Eval Pack
Owner: claude
Phase: 3
Type: documentation / eval
Depends-On: P3-01, P3-02
Objective: |
  Evaluate reflection quality across three dimensions: enhanced review with context,
  /reflect command output, and hallucination risk. Produce a structured eval pack
  that determines whether Phase 3 outputs are materially more useful than Phase 2
  and whether any regression or fabrication occurred.
Why-Now: |
  Phase 3 uses Sonnet-class LLM with richer context input — higher hallucination risk
  than Phase 2 memory generation. Eval is the evidence gate before phase close.
File-Scope:
  - docs/review/reflection_eval_p3.md (new file)
Deterministic-Owned:
  - eval structure: dimension / without-context / with-context / verdict / findings
  - which dimensions: enhanced review, /reflect output, hallucination check
LLM-Owned:
  - verdict prose from session evidence
Acceptance-Criteria:
  - id: AC-1
    description: "Eval covers three dimensions: enhanced review, /reflect output, hallucination risk."
    test: "doc structure check"
  - id: AC-2
    description: "Each dimension has a verdict with evidence."
    test: "manual review"
  - id: AC-3
    description: "Any fabrication findings are listed explicitly with severity."
    test: "manual review"
  - id: AC-4
    description: "Phase 3 close decision references this eval pack."
    test: "CODEX_PROMPT.md update at phase close"
Dependencies: P3-01, P3-02
Review-Mode: deep (phase-close artifact; human approval required before Phase 4 entry)
Out-Of-Scope:
  - automated scoring pipelines
  - Phase 4 feature proposals

---

## Phase 5 — NL Interaction Quality

Goal:
- make free-text capture smarter: handle multi-item messages, recover gracefully from parse failures, and let the user refine a pending entity without retyping from scratch

Entry condition:
- Audit Cycle 1 all findings resolved (✅ done)

Exit criteria:
- one user message can produce multiple queued entities, each confirmed individually
- parse failure returns a targeted clarifying question, not a generic error
- confirmation keyboard has a third "Уточнить ✏️" button that lets the user rewrite the input
- nl_handler has access to the last few raw messages so references like "а ещё добавь к этому дедлайн" resolve correctly
- phase review pack confirms no regressions

---

[x] P5-01 — Multi-entity extraction and queued confirmation
Owner: codex
Phase: 5
Type: implementation
Depends-On: none
Objective: |
  Change the NL extraction schema to return an array of entities. When more than one
  entity is extracted from a single message, queue them: present the first as the current
  pending entity, store the rest in state. After each confirmation, auto-present the next
  queued entity until the queue is empty.
Why-Now: |
  Users naturally send compound messages ("сдать короткий метр в пятницу и позвонить
  продюсеру насчёт бюджета"). Currently only one entity is extracted and the second is
  lost. The fix is a schema change plus a small state queue — no new LLM model needed.
File-Scope:
  - src/state.py
  - src/handlers/nl_handler.py
  - src/handlers/confirm.py
Deterministic-Owned:
  - queue storage in UserState (pending_entities: list[dict] | None)
  - clear_pending clears pending_entities
  - after each confirm: pop next from pending_entities and present it, or finish normally
  - single-entity path unchanged (backward compatible)
LLM-Owned:
  - extraction schema change: {"entities": [{"entity_type":..., "content":..., "project_hint":..., "due_date":...}]}
  - EXTRACTION_SYSTEM_PROMPT updated to return entities array
Acceptance-Criteria:
  - id: AC-1
    description: "UserState has pending_entities: list[dict] | None = None; clear_pending resets it."
    test: "code review of state.py"
  - id: AC-2
    description: "EXTRACTION_SYSTEM_PROMPT returns {\"entities\": [...]} array."
    test: "code review of nl_handler.py prompt"
  - id: AC-3
    description: "Single-entity messages work identically to before the change."
    test: "code review of single-entity path"
  - id: AC-4
    description: "Multi-entity message: first entity shown as pending; after confirm, next entity shown automatically."
    test: "code review of confirm flow"
  - id: AC-5
    description: "Ruff passes; no import errors."
    test: "CI: ruff check src/"
Dependencies: none
Review-Mode: light
Out-Of-Scope:
  - bulk save without per-entity confirmation
  - entity type inference changes
  - UI changes beyond queue presentation

---

[x] P5-02 — Clarifying questions on parse failure
Owner: codex
Phase: 5
Type: implementation
Depends-On: none
Objective: |
  Replace all four generic "Не совсем понял" error branches in nl_handler.py with
  specific clarifying questions that tell the user exactly what was unclear and how
  to fix it, without listing the full command menu.
Why-Now: |
  The current error messages are identical across all failure modes (LLM error, non-dict
  response, bad schema, empty content). Each mode has a different root cause and a
  different most-helpful clarification. Targeted messages reduce confusion and abandonment.
File-Scope:
  - src/handlers/nl_handler.py
Deterministic-Owned:
  - mapping each failure mode to its own specific message
  - message must be a question or actionable prompt, under two lines
  - no full command menu appended (keep it brief)
LLM-Owned:
  - none; all messages are static strings
Acceptance-Criteria:
  - id: AC-1
    description: "LLMError branch: message asks the user to rephrase as a question (не команду)."
    test: "code review of LLMError path"
  - id: AC-2
    description: "non-dict branch: message clarifies the response was unparseable and suggests a specific entity command."
    test: "code review"
  - id: AC-3
    description: "empty content branch: message asks what exactly to save."
    test: "code review"
  - id: AC-4
    description: "No branch still uses the old generic 4-line message with the command list."
    test: "grep check: old message string not present"
  - id: AC-5
    description: "Ruff passes."
    test: "CI: ruff check src/"
Dependencies: none
Review-Mode: light
Out-Of-Scope:
  - LLM-driven clarification generation
  - multi-turn clarification dialogue

---

[x] P5-03 — Уточнить button and re-extraction flow
Owner: codex
Phase: 5
Type: implementation
Depends-On: P5-01
Objective: |
  Add a third button to the pending entity keyboard: "✏️ Уточнить" (callback_data="clarify").
  When tapped, the bot replies asking the user to rewrite their input. The next free-text
  message clears the current pending entity and re-runs NL extraction on the new text,
  effectively replacing the draft.
Why-Now: |
  Currently the only options after a bad extraction are to discard (lose everything) or
  accept and use /edit (requires knowing the command syntax). A clarify button gives a
  low-friction correction path that matches how users naturally fix mistakes.
File-Scope:
  - src/handlers/confirm.py
  - src/state.py
  - src/bot.py
Deterministic-Owned:
  - pending_clarify: bool = False added to UserState; clear_pending resets it
  - _pending_keyboard() adds third button: InlineKeyboardButton("✏️ Уточнить", callback_data="clarify")
  - clarify callback handler: sets state.pending_clarify = True, replies "Напиши исправленный вариант — переработаю."
  - nl_handler: at entry, if state.pending_clarify is True, set it to False, call clear_pending, then continue normally
LLM-Owned:
  - none; clarify entry re-uses existing extraction path
Acceptance-Criteria:
  - id: AC-1
    description: "UserState has pending_clarify: bool = False; clear_pending sets it to False."
    test: "code review of state.py"
  - id: AC-2
    description: "_pending_keyboard() returns three buttons: Сохранить, Удалить, Уточнить."
    test: "code review of confirm.py"
  - id: AC-3
    description: "Pressing Уточнить sets pending_clarify=True and sends a reply prompting rewrite."
    test: "code review of clarify callback"
  - id: AC-4
    description: "Next free-text message after pending_clarify=True clears old pending entity and re-runs extraction."
    test: "code review of nl_handler entry check"
  - id: AC-5
    description: "Ruff passes."
    test: "CI: ruff check src/"
Dependencies: P5-01
Review-Mode: light
Out-Of-Scope:
  - multi-turn guided correction dialogue
  - preserving any field from the old pending entity into the re-extraction
  - clarify for voice messages

---

[x] P5-04 — NL context window for reference resolution
Owner: codex
Phase: 5
Type: implementation
Depends-On: none
Objective: |
  Add a short rolling context window of the last 5 raw user messages to UserState.
  When nl_handler calls the LLM for extraction, prepend the context window to the
  extraction prompt so the model can resolve references like "а ещё добавь к этому
  дедлайн" without re-explanation.
Why-Now: |
  nl_handler currently processes every message in isolation. Short back-references
  that rely on a previous message are silently lost. Adding the last 5 messages as
  context to the extraction prompt resolves this with minimal code change and no new
  LLM call.
File-Scope:
  - src/state.py
  - src/handlers/nl_handler.py
Deterministic-Owned:
  - nl_context: list[str] = field(default_factory=list) added to UserState; max 5 items
  - clear_pending does NOT clear nl_context (context survives confirms/discards)
  - after each NL extraction attempt (success or failure), append user_text to nl_context; cap at 5
  - prompt construction: if nl_context non-empty, prepend context block before user_text
  - context block format: "Предыдущие сообщения:\n- {msg1}\n- {msg2}\n\nТекущее сообщение: {user_text}"
LLM-Owned:
  - none new; existing extraction LLM now receives richer prompt
Acceptance-Criteria:
  - id: AC-1
    description: "UserState has nl_context: list[str] = field(default_factory=list); not cleared by clear_pending."
    test: "code review of state.py and clear_pending"
  - id: AC-2
    description: "After each NL extraction attempt, user_text is appended to nl_context; list capped at 5."
    test: "code review of nl_handler"
  - id: AC-3
    description: "When nl_context is non-empty, extraction prompt includes a context block before user_text."
    test: "code review of prompt construction"
  - id: AC-4
    description: "When nl_context is empty, extraction prompt is identical to before the change."
    test: "code review"
  - id: AC-5
    description: "Ruff passes."
    test: "CI: ruff check src/"
Dependencies: none
Review-Mode: light
Out-Of-Scope:
  - context window for chat_handler (it has its own conversation_history)
  - semantic or vector-based context retrieval
  - persisting nl_context to DB

---

[x] P5-05 — Phase 5 NL Quality Review Pack
Owner: claude
Phase: 5
Type: documentation / eval
Depends-On: P5-01, P5-02, P5-03, P5-04
Objective: |
  Review Phase 5 implementation against the NR-1..NR-4 behavioral requirements.
  Produce a structured review pack that confirms multi-entity queuing, clarifying
  questions, the Уточнить button, and context window each work as specified, and
  documents any regressions or deferred findings.
File-Scope:
  - docs/review/nl_quality_review_p5.md (new file)
Deterministic-Owned:
  - review structure: feature / spec-ref / verdict / evidence / findings
  - which features: multi-entity, clarify questions, Уточнить button, context window
LLM-Owned:
  - verdict prose from code review evidence
Acceptance-Criteria:
  - id: AC-1
    description: "Review covers all four NR requirements."
    test: "doc structure check"
  - id: AC-2
    description: "Each feature has a verdict (met / partial / not met) with evidence."
    test: "manual review"
  - id: AC-3
    description: "Any regression findings are listed with severity."
    test: "manual review"
  - id: AC-4
    description: "Phase 5 close decision references this review pack."
    test: "CODEX_PROMPT.md update at phase close"
Dependencies: P5-01, P5-02, P5-03, P5-04
Review-Mode: deep (phase-close artifact; human approval required)
Out-Of-Scope:
  - automated test pipelines
  - Phase 6 proposals

---

## Phase 6 — Daily Practices, User Context, and NL UX

Goal:
- add recurring daily practice infrastructure, personal user-context memory, and NL UX improvements that make the assistant feel more intelligent and less command-driven

Entry condition:
- Phase 5 complete (✅ done)

Exit criteria:
- recurring daily practices fire timezone-correctly and deduplicate by local calendar date
- user can save personal context ("запомни обо мне") and it is injected into chat/reflect/review
- practice streak is tracked and visible
- one message can contain multiple tasks and the assistant announces the split upfront
- NL capture triggers on natural phrasings without explicit command keywords
- phase shipped and verified in production; retrospectively documented

Note: Phase 6 was shipped outside the normal loop (operator-driven). Documented here for artifact continuity.

---

[x] P6-01 — Daily practice reminders
Owner: codex
Phase: 6
Type: schema + implementation
Depends-On: none
Objective: |
  Add recurring_reminders table and delivery logic. Users configure morning/evening
  practices via natural language or /practices command. send_reminders.py delivers
  them timezone-correctly with deduplication by local calendar date.
File-Scope:
  - src/schema.sql
  - src/db.py
  - src/practice_intents.py
  - src/handlers/practice_cmd.py
  - scripts/send_reminders.py
  - src/bot.py
Deterministic-Owned:
  - recurring_reminders schema (kind, title, prompt_text, schedule_time, timezone, status)
  - timezone-aware deduplication: sent_on keyed to local date, not UTC date
  - pause/resume/list/setup actions parsed deterministically from text
  - requires_time_confirmation flow when no HH:MM given
LLM-Owned:
  - none; all practice logic is deterministic
Acceptance-Criteria:
  - id: AC-1
    description: "recurring_reminders and recurring_reminder_log tables exist in schema.sql."
    test: "smoke test"
  - id: AC-2
    description: "send_reminders delivers each practice once per local calendar day, not UTC day."
    test: "code review of list_due_recurring_reminders"
  - id: AC-3
    description: "Natural language setup ('Напоминай утренние страницы каждый день в 10:00 по Тбилиси') configures both kind and timezone correctly."
    test: "manual test"
  - id: AC-4
    description: "Pause/resume/list work without commands."
    test: "manual test"
Review-Mode: light

---

[x] P6-02 — Feature feedback capture
Owner: codex
Phase: 6
Type: implementation
Depends-On: none
Objective: |
  When the assistant cannot satisfy a request, offer to convert the gap into structured
  developer feedback. Bounded multi-step LLM clarification flow, stored in feature_feedback
  and user_feedback tables.
File-Scope:
  - src/handlers/feature_feedback.py
  - src/db.py
  - src/schema.sql
  - src/bot.py
Deterministic-Owned:
  - offer trigger: assistant response matches is_incapable_response() patterns
  - bounded question limit (max 3 clarifying questions)
  - draft storage and confirm/discard flow
LLM-Owned:
  - clarifying questions (Haiku)
  - brief assembly: summary_title, problem, desired_behavior, trigger_condition, success_result (Sonnet)
Acceptance-Criteria:
  - id: AC-1
    description: "When assistant says it cannot do something, offer keyboard appears."
    test: "manual test"
  - id: AC-2
    description: "Flow is bounded: max 3 questions before draft is assembled."
    test: "code review"
  - id: AC-3
    description: "Draft saved to feature_feedback and user_feedback tables."
    test: "code review"
Review-Mode: light

---

[x] P6-03 — User context memory
Owner: codex
Phase: 6
Type: schema + implementation
Depends-On: none
Objective: |
  Allow user to save personal context ("запомни обо мне — ..."). Entries stored in
  user_context_entries. LLM generates a bounded 5-7 line profile summary stored in
  user_context_summary. Summary injected into chat, reflect, and review system prompts.
File-Scope:
  - src/schema.sql
  - src/db.py
  - src/user_context.py
  - src/handlers/chat_handler.py
  - src/handlers/reflect_cmd.py
  - src/handlers/review.py
  - src/bot.py
Deterministic-Owned:
  - capture trigger: keyword markers ("запомни обо мне", "сохрани это как контекст")
  - summary cache invalidation: regenerate only if entry_count_snapshot changed
  - injection into system prompts for chat, reflect, review
LLM-Owned:
  - profile summary generation (Haiku): compact 5-7 line labeled profile
Acceptance-Criteria:
  - id: AC-1
    description: "user_context_entries and user_context_summary tables exist."
    test: "smoke test"
  - id: AC-2
    description: "Message matching capture markers creates pending user_context entity."
    test: "code review"
  - id: AC-3
    description: "Summary is injected into chat system prompt when available."
    test: "code review of chat_handler"
Review-Mode: light

---

[x] P6-04 — Practice UX: streak, timezone inheritance, pause button, next fire time
Owner: codex
Phase: 6
Type: implementation
Depends-On: P6-01
Objective: |
  Improve recurring practice experience: track daily completions (streak), inherit
  timezone from existing practice when user doesn't specify one, show next scheduled
  fire time in /practices list, add inline Поставить на паузу button in reminder messages.
File-Scope:
  - src/schema.sql
  - src/db.py
  - src/handlers/practice_cmd.py
  - scripts/send_reminders.py
  - src/bot.py
Deterministic-Owned:
  - practice_completions table: INSERT OR IGNORE by (recurring_reminder_id, completed_on)
  - streak calculation: walk backwards from today using date-set membership
  - timezone inheritance: when no timezone given in update, read existing practice's timezone
  - next fire time: convert schedule_time to local time and show "сегодня/завтра в HH:MM"
  - inline pause button in reminder messages: callback_data="pause_practice:{kind}"
LLM-Owned:
  - none
Acceptance-Criteria:
  - id: AC-1
    description: "practice_completions table created with UNIQUE(recurring_reminder_id, completed_on)."
    test: "smoke test"
  - id: AC-2
    description: "/practices shows streak and weekly count per practice."
    test: "manual test"
  - id: AC-3
    description: "When user updates practice time without specifying timezone, existing timezone is preserved."
    test: "code review"
  - id: AC-4
    description: "Reminder messages include inline Поставить на паузу button."
    test: "code review"
Review-Mode: light

---

[x] P6-05 — NL UX improvements
Owner: codex
Phase: 6
Type: implementation
Depends-On: none
Objective: |
  Expand NL capture to work on natural phrasings users actually use ("хочу записать",
  "не забыть", "мысль"). When multiple entities found, announce count upfront. After
  handling a practice intent, also run NL if NL markers present. Enrich extraction prompt
  with entity-type descriptions and examples for better automatic classification.
File-Scope:
  - src/handlers/nl_handler.py
  - src/handlers/confirm.py
  - src/handlers/help_cmd.py
  - src/bot.py
Deterministic-Owned:
  - NL_CAPTURE_MARKERS expansion: add "хочу записать", "нужно зафиксировать", "не забыть", "мысль", etc.
  - multi-entity count announcement: "Нашёл N записей — разберём по одной."
  - queue progress indicator: "Ещё N в очереди:" prefix in subsequent previews
  - mixed intent: after practice intent handled, run maybe_handle_nl_capture if NL markers present
LLM-Owned:
  - enriched extraction prompt: entity-type descriptions and examples guide classification
Acceptance-Criteria:
  - id: AC-1
    description: "should_try_nl_capture returns True for 'хочу записать что-то', 'не забыть', 'мысль про монтаж'."
    test: "unit check"
  - id: AC-2
    description: "Multi-entity message shows count announcement before first preview."
    test: "code review"
  - id: AC-3
    description: "EXTRACTION_SYSTEM_PROMPT contains descriptions for all four entity types."
    test: "code review"
  - id: AC-4
    description: "Ruff passes."
    test: "CI: ruff check src/"
Review-Mode: light

---

## Phase 7 — Memory Architecture Alignment

Goal:
- align architecture, spec, and task planning around a layered memory model that matches the actual repo state

Entry condition:
- Phase 6 complete (✅ done)

Exit criteria:
- current-state memory assessment documented
- MemPalace extraction documented
- target memory architecture documented
- implementation sequence updated across source-of-truth docs

---

[x] P7-01 — Memory architecture assessment and contract update
Owner: codex
Phase: 7
Type: documentation
Depends-On: none
Objective: |
  Inspect the actual repository, inspect MemPalace critically, and update the source-of-truth
  documents so the next implementation phase is driven by the correct architecture.
File-Scope:
  - docs/MEMORY_ARCHITECTURE.md
  - docs/ARCHITECTURE.md
  - docs/PHASE_PLAN.md
  - docs/tasks.md
  - docs/spec.md
  - docs/IMPLEMENTATION_CONTRACT.md
  - docs/CODEX_PROMPT.md
Review-Mode: deep

---

## Phase 8 — MVP Evidence Memory Foundation

Goal:
- add a small, provenance-preserving evidence memory layer for project-first recall

Entry condition:
- Phase 7 complete (✅ done)
- human approval before first implementation task dispatch

Exit criteria:
- evidence memory exists as a distinct retrieval layer
- retrieval is project-first by default
- summary refresh rules are better than count-only cache reuse
- migration and observability are documented and tested

---

[ ] P8-01 — Evidence memory schema and migration
Owner: codex
Phase: 8
Type: implementation
Depends-On: none
Objective: |
  Add a dedicated `memory_items` schema for recallable evidence rows and the minimum
  indexes needed for project-first retrieval. Keep canonical project tables unchanged.
Why-Now: |
  The current system stores project records and summaries, but it has no unified recall
  layer with source provenance. This is the minimum structural addition that unlocks
  evidence-based continuity without rewriting the app into a memory platform.
File-Scope:
  - src/schema.sql
  - src/db.py
  - docs/db-migration-guide.md
Deterministic-Owned:
  - schema shape
  - source/provenance fields
  - project-scope vs user-scope rules
Acceptance-Criteria:
  - id: AC-1
    description: "`memory_items` table exists with scope, source_kind, source_id, project_id/user scope, content text, timestamps, and provenance fields."
    test: "schema review"
  - id: AC-2
    description: "Indexes support project-first lookup and source tracing."
    test: "schema review"
  - id: AC-3
    description: "Migration guidance documents how to add the table without rewriting existing records."
    test: "doc review"
Review-Mode: light

---

[ ] P8-02 — Deterministic memory-item ingestion from existing sources
Owner: codex
Phase: 8
Type: implementation
Depends-On: P8-01
Objective: |
  Populate `memory_items` from existing canonical records that are worth recall:
  notes, ideas, homework, user context entries, and selected transcript-backed text.
Why-Now: |
  A recall layer is useless unless ingestion is deterministic and inspectable. This
  phase should prefer obvious source mappings over clever extraction.
File-Scope:
  - src/db.py
  - src/handlers/confirm.py
  - src/user_context.py
Deterministic-Owned:
  - which source types produce memory items
  - source-to-memory mapping
  - duplicate prevention rules
Acceptance-Criteria:
  - id: AC-1
    description: "Saving a note or idea can create or update a corresponding project-scoped memory item."
    test: "code review"
  - id: AC-2
    description: "Saving user context creates a user-scoped memory item separate from project memory."
    test: "code review"
  - id: AC-3
    description: "Ingestion does not create cross-project memory items implicitly."
    test: "code review"
Review-Mode: light

---

[ ] P8-03 — Summary refresh rules v2
Owner: codex
Phase: 8
Type: implementation
Depends-On: P8-01, P8-02
Objective: |
  Replace the current count-heavy staleness logic with a more realistic refresh rule
  that accounts for age and material source changes. Keep `/memory` as an explicit
  refresh trigger.
Why-Now: |
  The current cache logic in `src/handlers/memory_cmd.py` reuses summaries too easily
  because it mostly checks `item_count_snapshot`. That is not enough for edits,
  project drift, or important new evidence.
File-Scope:
  - src/handlers/memory_cmd.py
  - src/config.py
  - src/db.py
Deterministic-Owned:
  - refresh trigger rules
  - stale reason calculation
  - config values
LLM-Owned:
  - bounded summary generation only
Acceptance-Criteria:
  - id: AC-1
    description: "Summary refresh reasons are inspectable and not reduced to row count only."
    test: "code review"
  - id: AC-2
    description: "A stale summary can be explained by age or source changes."
    test: "manual test or code review"
  - id: AC-3
    description: "`/memory` remains explicit; chat does not silently regenerate summaries."
    test: "code review"
Review-Mode: light

---

[ ] P8-04 — Project-first evidence retrieval helper
Owner: codex
Phase: 8
Type: implementation
Depends-On: P8-01, P8-02
Objective: |
  Add a retrieval helper that fetches verbatim evidence rows for the active project
  and returns compact, provenance-labeled results for downstream flows.
Why-Now: |
  The repo needs a practical seam between summary context and evidence recall. This
  helper is that seam.
File-Scope:
  - src/db.py
  - src/tools.py
  - src/handlers/search_cmd.py
Deterministic-Owned:
  - project-first scope resolution
  - ranking policy (scope first, then textual match, then recency)
  - provenance formatting
Acceptance-Criteria:
  - id: AC-1
    description: "Active-project retrieval does not search other projects unless explicitly requested."
    test: "code review"
  - id: AC-2
    description: "Returned results include source kind, source id, and timestamp when available."
    test: "code review"
  - id: AC-3
    description: "A broader all-project mode is not the default path."
    test: "code review"
Review-Mode: light

---

[ ] P8-05 — Memory observability and migration validation
Owner: codex
Phase: 8
Type: implementation + verification
Depends-On: P8-01, P8-02, P8-03, P8-04
Objective: |
  Make the memory upgrade debuggable: log refresh reasons, retrieval scope, and source
  counts; add tests or smoke checks for migration and basic retrieval behavior.
File-Scope:
  - src/handlers/memory_cmd.py
  - src/db.py
  - scripts/smoke_test_db.py
  - docs/review/continuity_eval_p8.md
Acceptance-Criteria:
  - id: AC-1
    description: "Logs distinguish summary-only paths from evidence retrieval paths."
    test: "code review"
  - id: AC-2
    description: "Migration and retrieval smoke checks exist or exact blockers are documented."
    test: "manual verification"
  - id: AC-3
    description: "Eval pack references the real implemented retrieval and provenance behavior."
    test: "doc review"
Review-Mode: deep

---

## Phase 9 — Continuity Surfaces And Evidence Use

Goal:
- use the new evidence layer in re-entry and reflection flows without widening scope by default

Entry condition:
- Phase 8 complete

Exit criteria:
- returning-user continuity surface exists
- `/reflect` can use evidence snippets, not only summary text
- evidence use remains scoped, bounded, and provenance-preserving

---

[ ] P9-01 — Returning-after-gap continuity surface
Owner: codex
Phase: 9
Type: implementation
Depends-On: P8-03, P8-04
Objective: |
  Add a conservative re-entry surface that shows where the user left off in the active
  project using bounded summary plus evidence, not summary text alone.
Review-Mode: light

---

[ ] P9-02 — Evidence-grounded reflection path
Owner: codex
Phase: 9
Type: implementation
Depends-On: P8-04
Objective: |
  Update `/reflect` so it can use compact evidence snippets with provenance in addition
  to the project summary, reducing over-reliance on the summary row.
Review-Mode: light

---

[ ] P9-03 — Explicit recall command or equivalent bounded tool surface
Owner: codex
Phase: 9
Type: implementation
Depends-On: P8-04
Objective: |
  Add one explicit user-facing path for project-first evidence recall instead of forcing
  all recall through summary-based chat responses.
Review-Mode: light

---

[ ] P9-04 — Continuity eval pack
Owner: claude
Phase: 9
Type: documentation / eval
Depends-On: P9-01, P9-02, P9-03
Objective: |
  Evaluate whether the new memory stack materially improves continuity without increasing
  false recall, scope leakage, or debugging difficulty.
Review-Mode: deep
Review-Mode: deep

---

## Phase 10 — Explicit Cross-Project Recall

Goal:
- add explicit, limited cross-project recall only after project-first memory is stable

Entry condition:
- Phase 9 complete

Exit criteria:
- named-project recall exists and is provenance-labeled
- all-project search mode exists but is explicitly opt-in, not default
- cross-project results include project name in provenance
- eval pack confirms no implicit cross-project leakage

---

[ ] P10-01 — All-project memory search helper and /search all: mode
Owner: codex
Phase: 10
Type: implementation
Depends-On: P9-03
Objective: |
  Add search_memory_items_all_projects() to db.py and wire it into /search
  when the query starts with "all:" prefix. Default /search behavior unchanged.
File-Scope:
  - src/db.py
  - src/handlers/search_cmd.py
Deterministic-Owned:
  - all-project scope gating (opt-in prefix only)
  - provenance: each result includes project_id
Acceptance-Criteria:
  - id: AC-1
    description: "search_memory_items_all_projects() searches across all projects, returns project_id per item."
    test: "code review"
  - id: AC-2
    description: "/search keyword → project-first (unchanged). /search all:keyword → all-project mode."
    test: "code review"
  - id: AC-3
    description: "All-project results label each item with its project_id."
    test: "code review"
Review-Mode: light

---

[ ] P10-02 — Named-project recall in /recall
Owner: codex
Phase: 10
Type: implementation
Depends-On: P9-03
Objective: |
  Extend /recall to accept a project slug argument: /recall <slug> fetches memory_items
  for the named project (not just the active one). Results include project name in label.
File-Scope:
  - src/handlers/recall_cmd.py
  - src/db.py (add get_project_by_slug if not accessible)
Deterministic-Owned:
  - slug resolution to project_id
  - cross-project access requires explicit slug
Acceptance-Criteria:
  - id: AC-1
    description: "/recall <slug> fetches memory_items for the named project with project name in output."
    test: "code review"
  - id: AC-2
    description: "/recall without args still defaults to active project (unchanged behavior)."
    test: "code review"
  - id: AC-3
    description: "Unknown slug returns a clear error message."
    test: "code review"
Review-Mode: light

---

[ ] P10-03 — Provenance labeling with project name in cross-project results
Owner: codex
Phase: 10
Type: implementation
Depends-On: P10-01, P10-02
Objective: |
  Ensure all cross-project results (all-project /search, named /recall) include the
  project name (not just project_id) in formatted output. Add a db helper that joins
  memory_items with projects to enrich results with project_name.
File-Scope:
  - src/db.py
  - src/handlers/search_cmd.py
  - src/handlers/recall_cmd.py
Deterministic-Owned:
  - provenance join
  - formatting: [project_name / source_kind#source_id]
Acceptance-Criteria:
  - id: AC-1
    description: "Cross-project results show project name, not just project_id, in formatted output."
    test: "code review"
  - id: AC-2
    description: "Project-first (single-project) results are unchanged."
    test: "code review"
Review-Mode: light

---

[ ] P10-04 — Phase 10 cross-project eval pack
Owner: claude
Phase: 10
Type: documentation / eval
Depends-On: P10-01, P10-02, P10-03
Objective: |
  Evaluate Phase 10: confirm opt-in gating, provenance accuracy,
  and absence of implicit cross-project leakage in default paths.
File-Scope:
  - docs/review/cross_project_eval_p10.md
Acceptance-Criteria:
  - id: AC-1
    description: "Default /search and /recall remain project-first — confirmed by code review."
    test: "code review"
  - id: AC-2
    description: "Cross-project mode only activates via explicit user action."
    test: "code review"
  - id: AC-3
    description: "Eval pack references real implemented code, not aspirational behavior."
    test: "doc review"
Review-Mode: deep
