# Film School Assistant — Orchestrator Entry Point

_v3.0 · Active entry point for the repository development loop._

---

## Status

This is the only active orchestration entry point for this repository.

Use this file when launching the Orchestrator.

Do not use:
- `docs/prompts/workflow_orchestrator.md` as the primary entry point

That file is retained only as legacy reference and should not govern the active loop.

---

## Repository Context

Project root:
`/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant`

The repository is **past bootstrap**.

That means:
- do not run a full-project Strategist rerun
- do not run the original full-repo Phase 1 Validator flow
- do use the active phase-driven loop defined in:
  - `docs/PHASE_PLAN.md`
  - `docs/CODEX_PROMPT.md`

---

## Tool Split — Hard Rule

| Role | Tool | Why |
|------|------|-----|
| Orchestrator | general-purpose reasoning agent | reads artifacts, decides next action, updates state |
| Implementer / fixer | `codex exec -s workspace-write` | task-scoped implementation and fixes |
| Light reviewer | general-purpose reasoning agent | task-level checks |
| Deep review agents | general-purpose reasoning agent | phase-boundary review |

Codex is invoked through the existing `exec`-based mechanism.

Use the variable form, not stdin:

```bash
PROMPT=$(cat /tmp/orchestrator_codex_prompt.txt)
cd /home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant && codex exec -s workspace-write "$PROMPT"
```

---

## Active Loop

The active repository loop is:

1. Read current state from repository artifacts.
2. Select the next active phase from `docs/PHASE_PLAN.md` and `docs/CODEX_PROMPT.md`.
3. Run a **Phase Decomposition Pass** for that phase.
4. Update the phase package artifacts.
5. Run a **Phase Entry Check**.
6. If the phase package passes, dispatch one task at a time to Codex.
7. Run light review after each task.
8. Run deep review at the phase boundary.
9. Update state docs.
10. Stop for human approval at the phase gate.

Definitions:
- **Phase Decomposition Pass**: narrow strategy work for the next phase only. It converts phase intent into executable tasks and reviewable artifacts.
- **Phase Entry Check**: narrow validation of the current phase package only. It checks internal consistency, scope, reviewability, and drift against source-of-truth docs.

---

## State Inputs

Before taking action, read:
- `docs/CODEX_PROMPT.md`
- `docs/PHASE_PLAN.md`
- `docs/tasks.md`
- `docs/ARCHITECTURE.md`
- `docs/WORKFLOW_BOUNDARIES.md`
- `docs/PRODUCT_OVERVIEW.md`
- `docs/USER_EXPERIENCE.md`
- `docs/spec.md`
- `docs/IMPLEMENTATION_CONTRACT.md`

Also read any task-scoped files only when needed.

---

## Step 0 — Current State Check

1. Scan these files for unresolved `{{...}}` placeholders outside fenced code blocks:
   - `docs/ARCHITECTURE.md`
   - `docs/IMPLEMENTATION_CONTRACT.md`
   - `docs/CODEX_PROMPT.md`
   If any exist: stop and report `PLACEHOLDER_ERROR`.

2. Record:
   - current phase
   - current phase goal
   - next task or next loop action
   - fix queue state if present
   - solution shape
   - governance level
   - runtime tier
   - capability profiles
   - deterministic vs LLM boundaries
   - phase gate blockers if any

3. If `Completed Tasks > 20` or `Phase History > 5` in `docs/CODEX_PROMPT.md`, compact it before proceeding.

4. Run drift checks:
   - if proposed work exceeds declared solution shape -> stop with `COMPLEXITY_DRIFT`
   - if proposed work exceeds declared runtime tier -> stop with `RUNTIME_TIER_MISMATCH`
   - if deterministic-owned behavior is being moved into LLM logic without artifact updates -> report `DETERMINISM_WARNING`
   - if product direction drifts toward web-primary, multi-user, or speculative memory expansion before the planned phase -> stop with `PHASE_DRIFT`

5. Print a state block:

```text
=== ORCHESTRATOR STATE ===
Active phase: [Phase N — Name]
Goal: [...]
Next action: [phase decomposition | phase entry check | implement task | review | stop]
Fix Queue: [empty | items]
Solution shape: [Hybrid]
Governance: [Standard]
Runtime tier: [T1]
Profiles: [RAG OFF | Tool-Use ON | Agentic ON | Planning OFF | Compliance OFF]
Drift check: [OK | warning | stopped]
```

---

## Step 1 — Phase Decomposition Pass

If the active phase has not yet been broken into executable tasks:
- decompose only the current upcoming phase
- do not redesign the whole product
- update:
  - `docs/tasks.md`
  - `docs/CODEX_PROMPT.md`
  - `docs/spec.md` if phase-specific requirements sharpen
  - any directly affected source-of-truth doc

Requirements for decomposition:
- tasks must be concrete and reviewable
- file scope must be explicit
- deterministic vs LLM ownership must be explicit where relevant
- acceptance criteria must be explicit
- evidence or eval expectations must be explicit

If the active phase is already decomposed, skip this step.

---

## Step 2 — Phase Entry Check

Before implementation starts for a phase, verify:
- `docs/tasks.md` matches the current phase objective
- tasks do not contradict `docs/ARCHITECTURE.md`
- tasks do not contradict `docs/WORKFLOW_BOUNDARIES.md`
- tasks do not drift beyond current phase scope
- tasks are reviewable and have acceptance criteria
- the phase package is specific enough for Codex to execute one task at a time

If the phase package fails, stop and report `PHASE_ENTRY_FAIL`.

---

## Step 3 — Implement One Task

For the next task:
- read only task-scoped files plus directly required helpers/tests
- prepare a task-specific Codex prompt
- dispatch Codex through the existing exec-based mechanism

The implementer prompt must restate:
- objective
- acceptance criteria
- file scope
- architecture constraints
- deterministic vs LLM boundaries
- what verification to run
- what state docs to update truthfully

The implementer must:
- change only task-scoped files unless a necessary dependency is discovered
- report what changed
- report what verification actually ran
- not claim checks that were not run

---

## Step 4 — Light Review

After each normal implementation task, run light review.

Check:
- contract violations
- missing acceptance-criteria coverage
- deterministic ownership drift
- runtime drift
- secrets/auth regressions
- scope drift

If issues are found:
- send them back as a narrow Codex fix task
- do not advance the phase until fixed

---

## Step 5 — Deep Review

Run deep review:
- at true phase boundary
- or earlier if a task touches architecture-critical boundaries

Deep review order:
1. `docs/audit/PROMPT_0_META.md`
2. `docs/audit/PROMPT_1_ARCH.md`
3. `docs/audit/PROMPT_2_CODE.md`
4. `docs/audit/PROMPT_3_CONSOLIDATED.md`

Then:
- archive the phase review output in `docs/audit/`
- update `docs/audit/AUDIT_INDEX.md`
- update `docs/CODEX_PROMPT.md`

---

## Step 6 — Phase Gate

At a phase boundary:
- stop if any P0/P1 finding remains open
- stop if architecture or phase drift is unresolved
- stop for human approval before starting the next phase

---

## Stop Conditions

Stop and report instead of implementing when:
- placeholders remain
- current phase package is underspecified
- requested work exceeds declared runtime tier
- requested work exceeds current phase scope
- the user asks for architecture expansion without source-of-truth doc updates first
