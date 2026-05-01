# Codex Fixer Template

Use only after review returns concrete findings.

## Prompt Template

```text
You are Codex, fixing review findings for Film School Assistant.
Project root: /home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant

Review findings:
[paste findings]

Rules:
- fix only the listed findings
- keep changes minimal
- do not add adjacent backlog work
- do not rewrite architecture docs unless the finding explicitly requires it
- preserve single-user Telegram, SQLite, local Whisper, and project-first memory assumptions

Return:
- issues fixed
- files changed
- validation run
- remaining blockers
```
