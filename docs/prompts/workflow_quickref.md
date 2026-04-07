# Workflow Quick Reference

## Active Entry Point

Start the repository loop with:

`docs/prompts/ORCHESTRATOR.md`

## Active Loop

The repository loop is:

1. Read current state from `docs/CODEX_PROMPT.md`, `docs/PHASE_PLAN.md`, and `docs/tasks.md`.
2. Select the next active phase.
3. Run a Phase Decomposition Pass if that phase is not yet broken into executable tasks.
4. Run a Phase Entry Check.
5. Dispatch one task at a time to Codex through the existing exec-based mechanism.
6. Run light review after each task.
7. Run deep review at the phase boundary.
8. Update state docs.
9. Stop for human approval at the phase gate.

## Tool Split

| Role | Tool |
|---|---|
| Orchestrator | Claude / reasoning agent |
| Implementer | `codex exec -s workspace-write` |
| Fixer | `codex exec -s workspace-write` |
| Reviewer | Claude / reasoning agent |

## Current Reality

The repository is past bootstrap.

That means:
- no full-project Strategist rerun
- no original full-repo Phase 1 Validator flow
- phase-level planning and validation only

## Current Phase Intent

Phases 0–7 are complete for planning purposes.

Next active work:
- Phase 8 — MVP Evidence Memory Foundation

Before coding Phase 8:
- confirm the phase entry package in `docs/tasks.md`
- confirm the active state in `docs/CODEX_PROMPT.md`
- use `docs/MEMORY_ARCHITECTURE.md` as the memory source-of-truth
- run a Phase Entry Check

## Resume Rule

The loop is artifact-driven. To resume, re-run the active Orchestrator entry point and let it read the current repo state.
