# Codex Implementer — Manual Use Template

**Use this file when re-running a single phase manually, outside the orchestrator.**
**The orchestrator embeds its own version of this prompt inline.**

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
Project root: /srv/openclaw-her/workspace/film-school-assistant

Your assignment: Phase [N] — [Phase Name]

Read these files before writing any code:
- docs/architecture.md
- docs/spec.md
- docs/tasks.md (Phase [N] section only)
- docs/ops-security.md (Path Boundaries and Secret Management sections)

Tasks to implement (in order):
[paste task rows from tasks.md for this phase — ID, description, Depends On]

Hard constraints — violating any of these will fail review:
- NEVER write to /opt/openclaw/src
- NEVER write to /srv/openclaw-her/state
- NEVER reference /srv/openclaw-you
- NEVER hardcode secrets, tokens, or API keys — read from os.environ only
- NEVER transmit audio files to external services
- TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_CHAT_ID must come from env vars
- DB_PATH defaults to data/assistant.db — configurable via env
- AUDIO_PATH defaults to data/audio/ — configurable via env
- All systemd services run as user oc_her, never root
- All systemd services have NoNewPrivileges=true
- Use logging module, not print() for status/debug output
- chat_id guard must fire before any handler logic

If this phase includes src/openclaw_client.py (Phase 5):
  First read /opt/openclaw/src to understand the wire protocol BEFORE writing the client.

When all tasks are done:
1. Verify each file exists and is syntactically valid
2. Return a completion report listing every file created or modified with its path
```

---

## Phase Reference

See `docs/tasks.md` for the full task list per phase.
See `docs/prompts/workflow_quickref.md` for the phase → files mapping.
