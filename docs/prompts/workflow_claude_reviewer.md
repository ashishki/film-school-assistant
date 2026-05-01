# Reviewer Template

Use for focused review of one bounded change.

## Read First

- `docs/CODEX_PROMPT.md`
- `docs/tasks.md`
- `docs/ARCHITECTURE.md`
- `docs/WORKFLOW_BOUNDARIES.md`
- `docs/IMPLEMENTATION_CONTRACT.md`
- `docs/MEMORY_ARCHITECTURE.md` when memory, recall, search, reflection, or continuity is touched

## Checklist

- Scope matches the work item.
- No secrets or auth regressions.
- Telegram single-user guard remains intact.
- SQLite remains canonical state.
- LLMs do not own deterministic routing, persistence, scheduling, or auth.
- Memory/retrieval remains project-first by default.
- Cross-project access is explicit.
- Docs match behavior.
- Validation is evidenced, not assumed.

## Output Format

```text
REVIEW_RESULT: PASS | ISSUES_FOUND

Findings:
- [severity] [file:line] [issue]

Residual risk:
- [note or none]
```
