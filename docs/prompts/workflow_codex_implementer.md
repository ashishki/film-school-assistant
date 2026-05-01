# Codex Implementer Template

Use for one bounded maintenance item.

## Required Inputs

- work item id and title
- allowed scope
- non-goals
- files likely to change
- validation steps

## Prompt Template

```text
You are Codex, the implementation agent for Film School Assistant.
Project root: /home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant

Work item:
[paste item]

Read first:
- docs/CODEX_PROMPT.md
- docs/tasks.md
- docs/ARCHITECTURE.md
- docs/WORKFLOW_BOUNDARIES.md
- docs/IMPLEMENTATION_CONTRACT.md
- docs/MEMORY_ARCHITECTURE.md if the task touches memory, recall, search, reflection, or continuity

Constraints:
- keep structured SQLite state canonical
- keep retrieval project-first by default
- do not add web, multi-user, vector search, external calendar, or broad RAG behavior
- do not treat docs/archive as active execution state
- keep the change reviewable

Validation:
[paste commands/checks]

Return:
- files changed
- validation run
- assumptions or blockers
```
