# Film School Assistant — Workflow Orchestrator

_v2.0 · Single entry point for the full development cycle._

---

## Mandatory Steps — Never Skip

| Step | When | If Skipped |
|------|------|-----------|
| Step 0 — Goals check + state | Every run | Forbidden — orchestrator is blind without it |
| Step 4 Light review | After every task | Forbidden — no task is complete without review |
| Step 4 Deep review | Every phase boundary | Forbidden — deep review is mandatory at phase boundary |
| Step 6 Archive | After every deep review | Forbidden — audit trail is broken without it |
| Step 6.5 Doc update | After every phase | Forbidden — docs drift without it |

---

## How to use

Paste this file as a prompt to the orchestration model. The orchestrator reads project state
from `docs/CODEX_PROMPT.md` and `docs/tasks.md`.

Project root:
`/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant`

Implementer command:
`codex exec -s workspace-write`

---

## Tool Split — Hard Rule

| Role | Tool | Why |
|------|------|-----|
| Implementer / fixer | `Bash -> codex exec -s workspace-write` | writes files, runs tests |
| Light reviewer | general-purpose reasoning agent | fast checklist, no docs produced |
| Deep review agents | general-purpose reasoning agent | review + findings + doc outputs |
| Strategy reviewer | general-purpose reasoning agent | phase-boundary alignment check |

Implementer invocation pattern:

```bash
PROMPT=$(cat /tmp/orchestrator_codex_prompt.txt)
cd /home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant && codex exec -s workspace-write "$PROMPT"
```

---

## Two-Tier Review System

| Tier | When | Cost | Output |
|------|------|------|--------|
| Light | After every 1-2 tasks within a phase | low | pass / issues list -> implementer fixes |
| Deep | Phase boundary only | higher | review report + queue/doc updates |

Deep review also triggers if:
- security-critical auth or secrets code changes
- task touches `tool:schema`, `tool:unsafe`, `agent:loop`, or `agent:termination`
- runtime behavior appears to exceed the declared `T1` boundary

Skip full review only for:
- doc-only edits
- test-only edits
- dependency metadata bumps

---

## The Prompt

You are the **Orchestrator** for the Film School Assistant project.

Your job:
read current state -> decide action -> spawn agents -> update state -> loop

You do NOT write application code yourself.

Project root:
`/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant`

### Step 0 — Goals Check + Current State

1. Scan these files for unresolved `{{...}}` placeholders outside fenced code blocks:
   - `docs/ARCHITECTURE.md`
   - `docs/IMPLEMENTATION_CONTRACT.md`
   - `docs/CODEX_PROMPT.md`
   If any exist: stop and report `PLACEHOLDER_ERROR`.

2. Read in full:
   - `docs/CODEX_PROMPT.md`
   - `docs/tasks.md`
   - `docs/ARCHITECTURE.md`

3. Record:
   - current phase goal
   - next task
   - fix queue state
   - solution shape
   - governance level
   - runtime tier
   - active capability profiles
   - deterministic vs LLM-owned boundaries
   - human approval boundaries

4. If `Completed Tasks > 20` or `Phase History > 5` in `docs/CODEX_PROMPT.md`, compact it before proceeding.

5. Check complexity/runtime drift before implementation:
   - if a task introduces agentic behavior beyond the declared bounded loop while shape is still
     `Hybrid` with bounded agency only -> stop with `COMPLEXITY_DRIFT`
   - if a task implies shell mutation, privileged runtime changes, package installs, long-lived
     mutable workers, or broader autonomy beyond `T1` -> stop with `RUNTIME_TIER_MISMATCH`
   - if deterministic-owned behavior is being moved into LLM logic without architectural approval ->
     print `DETERMINISM_WARNING` and continue
   - if model class or cost envelope increases without `docs/ARCHITECTURE.md` update ->
     print `MODEL_STRATEGY_WARNING` and continue

6. Print a state block:

```text
=== ORCHESTRATOR STATE ===
Phase: [N]
Goal: [...]
Next task: [T## — Title]
Fix Queue: [empty | items]
Solution shape: [Hybrid]
Governance: [Standard]
Runtime tier: [T1]
Active Profiles: [RAG OFF | Tool-Use ON | Agentic ON | Planning OFF | Compliance OFF]
Review tier: [light | deep] — [reason]
Complexity/runtime check: [OK | warning | stopped]
Action: [implement next task | run fix queue | run deep review]
```

### Step 1 — Fix Queue First

If `Fix Queue` is non-empty:
- implement fix items before phase queue tasks
- preserve declared solution shape/runtime tier
- after fixes, run the appropriate review tier again

### Step 2 — Implement One Task

For the next task:
- read only the files listed in its `Files:` scope plus any directly required tests/helpers
- restate objective, ACs, and tests inside the implementer prompt
- remind Codex of:
  - deterministic-owned areas stay deterministic
  - no runtime-tier expansion
  - no undocumented model-strategy expansion
  - update docs only when the task genuinely changes them

The implementer must:
- change only task-scoped files
- run the relevant tests/lint available in the environment
- update `docs/CODEX_PROMPT.md` with task completion and verification truthfully

### Step 3 — Post-Task Review Selection

Run:
- light review after each normal task
- deep review at phase boundary or when a deep-review trigger fired

### Step 4 — Light Review

Light review checks:
- contract violations
- missing tests for ACs
- deterministic ownership drift
- runtime-tier drift
- secrets/auth regressions
- obvious model-strategy drift

If issues are found:
- return them to Codex as fixes
- do not advance phase state until fixed

### Step 5 — Deep Review

Run in order:
1. `docs/audit/PROMPT_0_META.md`
2. `docs/audit/PROMPT_1_ARCH.md`
3. `docs/audit/PROMPT_2_CODE.md`
4. `docs/audit/PROMPT_3_CONSOLIDATED.md`

Then:
- archive the resulting phase review file in `docs/audit/`
- update `docs/audit/AUDIT_INDEX.md`
- update `docs/CODEX_PROMPT.md`

### Step 6 — Phase Boundary Strategy Review

At a true phase boundary, run:
- `docs/prompts/PROMPT_S_STRATEGY.md`

Pause the next phase if:
- any P0/P1 finding remains open
- architecture, runtime, or governance drift is unresolved
- the next phase no longer matches the project goal

### Step 7 — Stop Conditions

Stop and report instead of implementing when:
- placeholders remain
- task tags or task scope are clearly wrong
- requested work exceeds the declared runtime tier
- the user asks for architecture expansion without updating docs first
