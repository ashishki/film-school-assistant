# Film School Assistant — Improvement Task Graph

**Version:** 1.0
**Date:** 2026-03-17
**Source:** docs/repo-improvement-review-2026-03-17.md
**Status:** Active — updated by orchestrator after each cycle

---

## Task Status Legend

| Symbol | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | Implemented, pending review |
| `[x]` | Complete (implemented + reviewed) |
| `[!]` | Blocked |

---

## Phase I1 — Quick Wins: Correctness

| ID | Task | Owner | Status | Depends On |
|---|---|---|---|---|
| I1-01 | Block voice overwrite: add pending guard to `voice_handler` in `src/bot.py` | Codex | `[x]` | — |
| I1-02 | Validate due dates from NL/voice before building pending entity (`src/handlers/nl_handler.py`, `src/bot.py`, `src/handlers/common.py`) | Codex | `[x]` | — |
| I1-03 | Implement minimal `/edit` for pending items: field grammar `/edit due <date>`, `/edit title <text>`, `/edit content <text>` (`src/handlers/confirm.py`, `src/state.py`) | Codex | `[x]` | — |
| I1-04 | Weekly summary idempotency: add `UNIQUE(week_start)` to `weekly_reports`, fetch-or-skip before sending (`src/schema.sql`, `src/db.py`, `scripts/send_summary.py`) | Codex | `[x]` | — |
| I1-05 | Safe SQLite backup: replace `cp` with `sqlite3 .backup` + `PRAGMA integrity_check` (`scripts/backup_db.sh`) | Codex | `[x]` | — |

**Phase I1 Review Criteria:**
- `voice_handler` refuses to start a new voice flow when `state.pending_entity` is not None — replies "You have a pending item. /confirm, /edit, or /discard first."
- `nl_handler.py` and `voice_handler` both validate `due_date` via `parse_date_text()` or strict ISO — empty/invalid date leaves `due_date=None` with a note in the confirmation message
- `/confirm` refuses to save deadline/homework entities with `due_date=None` — replies with corrective prompt
- `/edit due <date>` updates `pending_entity["due_date"]`, `/edit content <text>` updates content/title, `/edit title <text>` updates title — each replies with updated preview
- `/edit` with unknown field replies "Usage: /edit due <date> | /edit title <text> | /edit content <text>"
- `weekly_reports` has `UNIQUE(week_start)` in schema — re-run on same week skips silently
- `send_summary.py` checks for existing `sent_at` report before sending — logs INFO and exits cleanly if already sent
- `backup_db.sh` uses `sqlite3 "$DB_PATH" ".backup '$backup_path'"` — NOT raw `cp`

---

## Phase I2 — Short-term: Polish and Performance

| ID | Task | Owner | Status | Depends On |
|---|---|---|---|---|
| I2-01 | Cache Whisper model globally in `src/transcriber.py` — lazy load once per process | Codex | `[x]` | — |
| I2-02 | Delete temp WAV after transcription in `src/voice.py` — keep `.ogg`, remove `.wav` | Codex | `[x]` | — |
| I2-03 | Add DB indexes: `deadlines(status, due_date)`, `notes(project_id, created_at)`, `ideas(project_id, created_at)`, `homework(status, due_date)` (`src/schema.sql`) | Codex | `[x]` | I1-04 |
| I2-04 | Active project UX: add `/project clear`, show active project in `/projects` output and save confirmations (`src/handlers/projects.py`, `src/handlers/notes.py`, `src/handlers/ideas.py`, `src/handlers/help_cmd.py`) | Codex | `[x]` | — |
| I2-05 | Rewrite reminder message template: include project context, human phrasing, no raw slash commands in body (`scripts/send_reminders.py`) | Codex | `[x]` | — |
| I2-06 | Rewrite weekly summary template: opening sentence, urgent section, creative momentum, stalled/neglected, one recommended next step — not a raw dashboard dump (`scripts/send_summary.py`) | Codex | `[x]` | — |

**Phase I2 Review Criteria:**
- `src/transcriber.py` loads Whisper model once per process via module-level lazy cache — second call does not reload
- WAV file is deleted after transcription in `src/voice.py` — OGG is retained
- `src/schema.sql` has CREATE INDEX statements for all 4 indexes using IF NOT EXISTS
- `/project clear` resets `state.active_project_id` and `state.active_project_name` to None — replies confirmation
- Save confirmations for note/idea show "(Project: X)" or "(General)" in the reply
- `/projects` marks the active project with a `*` or similar indicator
- Reminder messages include project name if available and use human phrasing (not raw "⏰ REMINDER: ... /done_deadline_N")
- Weekly summary has distinct sections: opening, urgent, creative momentum, stalled, next step — not just data counts

---

## Phase I3 — Medium: Review Quality + Ops Docs

| ID | Task | Owner | Status | Depends On |
|---|---|---|---|---|
| I3-01 | Enforce non-empty review fields: validate `core_idea`, `dramatic_center`, `weak_points`, `next_step` non-empty before formatting; improve system prompt for film-school critique (cinematic stakes, POV, scene engine) (`src/reviewer.py`) | Codex | `[x]` | — |
| I3-02 | Fix systemd units to use venv Python path or add clear templating comment; fix EnvironmentFile path if needed (`systemd/*.service`) | Codex | `[x]` | — |
| I3-03 | Update `README.md` and `docs/ops-security.md` to reflect: journald-only logging (no file logger), venv deployment, and add a "return after 3 months" runbook section | Codex | `[x]` | I3-02 |

**Phase I3 Review Criteria:**
- `src/reviewer.py` raises LLMSchemaError or substitutes a clean placeholder when any required section is empty — never formats a review with blank headings
- Review system prompt includes: cinematic stakes, point of view, scene engine, production-feasible next step
- All systemd `*.service` files have a comment `# ExecStart: update to your venv path: /path/to/.venv/bin/python3` or similar
- README deployment section matches actual behavior (journald, venv, no file logger)
- README has a "Return after 3 months" runbook section

---
