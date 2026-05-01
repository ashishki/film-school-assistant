# Film School Assistant — Orchestrator Prompt

Use this prompt to run maintenance work for the repository.

## Source Of Truth

Read first:

1. `docs/CODEX_PROMPT.md`
2. `docs/tasks.md`
3. `docs/ARCHITECTURE.md`
4. `docs/MEMORY_ARCHITECTURE.md` for memory, retrieval, recall, reflection, or continuity work
5. `docs/WORKFLOW_BOUNDARIES.md`
6. `docs/IMPLEMENTATION_CONTRACT.md`

Historical phase plans and audits under `docs/archive/` are context only.

## Loop

1. Select one bounded backlog item.
2. Define allowed scope, non-goals, files likely to change, and validation steps.
3. Dispatch implementation or do the edit directly when operating in the repo.
4. Review against architecture, security, memory scope, and doc alignment.
5. Update `docs/tasks.md` or `docs/CODEX_PROMPT.md` only when state actually changes.

## Hard Rules

- Do not revive archived phase-roadmap instructions as active work.
- Do not combine unrelated backlog items.
- Keep Telegram single-user and private-deployment assumptions intact.
- Keep structured SQLite state canonical.
- Keep recall/search project-first unless explicit cross-project behavior is requested.
- Do not introduce web, multi-user, vector search, external calendar, or broad RAG scope without a new explicit backlog item.
