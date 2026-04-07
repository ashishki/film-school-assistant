# Codex Implementer — Manual Use Template

Use this file only for manual debugging or ad-hoc re-runs outside the active Orchestrator loop.

The active orchestration entry point is:
- `docs/prompts/ORCHESTRATOR.md`

---

## How to use

```bash
cat > /tmp/codex_phase_prompt.txt << 'ENDOFPROMPT'
[paste filled prompt below]
ENDOFPROMPT
PROMPT=$(cat /tmp/codex_phase_prompt.txt)
codex exec -s workspace-write "$PROMPT"
```

---

## Prompt Template

```
You are Codex, the implementation agent for the Film School Assistant project.
Project root: /home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant

Your assignment: Phase [N] — [Phase Name]

Read these files before writing any code:
- docs/CODEX_PROMPT.md
- docs/ARCHITECTURE.md
- docs/MEMORY_ARCHITECTURE.md (required for memory, retrieval, continuity, or search-related tasks)
- docs/spec.md
- docs/tasks.md (Phase [N] section only)
- docs/WORKFLOW_BOUNDARIES.md
- docs/IMPLEMENTATION_CONTRACT.md

Tasks to implement (in order):
[paste task rows from tasks.md for this phase — ID, description, Depends On]

Hard constraints — violating any of these will fail review:
- NEVER hardcode secrets, tokens, or API keys — read from os.environ only
- NEVER transmit audio files to external services
- preserve the declared solution shape, governance level, and runtime tier
- do not expand into web-primary, multi-user, or speculative memory scope unless the task explicitly says so
- keep structured state as source of truth; do not replace it with summary-only or generic memory abstractions
- keep retrieval project-first by default unless the task explicitly authorizes broader scope
- preserve provenance when implementing recall or memory retrieval behavior
- Use logging module, not print() for status/debug output

When all tasks are done:
1. Verify each file exists and is syntactically valid
2. Update `docs/tasks.md` and `docs/CODEX_PROMPT.md` only if the task or orchestrator explicitly requires it
3. Return a completion report listing every file created or modified with its path
```

---

## Note

Prefer the active Orchestrator loop over manual use of this template.
