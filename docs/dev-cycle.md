# Development Cycle

The original phase-driven build loop is complete. Current work uses a smaller
maintenance loop driven by `docs/tasks.md`.

## Current Loop

1. Pick one bounded item from `docs/tasks.md`.
2. Read the relevant source-of-truth docs.
3. Implement the smallest change that satisfies the item.
4. Run focused validation.
5. Update docs only where behavior or operations changed.
6. Commit with a clear message.

## Review Focus

Every change should be checked for:

- scope discipline
- deterministic vs LLM ownership
- auth and secret handling
- SQLite schema/state consistency
- project-first memory and recall behavior
- operator-facing failure modes
- doc/runtime alignment

## Historical Records

The old cycle log, phase evals, and audit cycles are archived under
`docs/archive/`. They are useful context, but not active execution state.
