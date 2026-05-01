# Workflow Quick Reference

## Entry Point

Use `docs/prompts/ORCHESTRATOR.md`.

## Active Loop

1. Read `docs/CODEX_PROMPT.md` and `docs/tasks.md`.
2. Pick one bounded maintenance item.
3. Read the relevant source-of-truth docs.
4. Implement or dispatch one small packet.
5. Run focused validation.
6. Update docs if behavior changed.
7. Commit with a clear message.

## Review Focus

- auth and single-user guard
- deterministic vs LLM ownership
- SQLite state and migration safety
- project-first memory behavior
- Telegram UX and failure modes
- doc/runtime alignment
