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

Representative task areas:
- project state framing
- better continuity summaries
- clearer confirmation and progress flows
- stronger assistant tone and next-step guidance

This phase is intentionally not yet broken into implementation tasks here. It requires a Phase Decomposition Pass against the current source-of-truth docs before coding begins.
