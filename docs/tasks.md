# Film School Assistant — Task Graph

**Version:** 1.1
**Date:** 2026-03-17
**Status:** Baseline — updated by orchestrator after each cycle

---

## Task Status Legend

| Symbol | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | Implemented, pending review (set by orchestrator after Codex completes) |
| `[x]` | Complete (implemented + reviewed, set by orchestrator after PASS) |
| `[!]` | Blocked — needs human input before loop can continue |

---

## Phase 0 — Repository Baseline (Strategist)

| ID | Task | Owner | Status | Depends On |
|---|---|---|---|---|
| P0-01 | Write `docs/architecture.md` | Strategist | `[x]` | — |
| P0-02 | Write `docs/spec.md` | Strategist | `[x]` | P0-01 |
| P0-03 | Write `docs/tasks.md` | Strategist | `[x]` | P0-01 |
| P0-04 | Write `docs/dev-cycle.md` | Strategist | `[x]` | P0-01 |
| P0-05 | Write `docs/ops-security.md` | Strategist | `[x]` | P0-01 |
| P0-06 | Write `docs/prompts/workflow_orchestrator.md` | Strategist | `[x]` | P0-01 |
| P0-07 | Write `docs/prompts/workflow_quickref.md` | Strategist | `[x]` | P0-06 |
| P0-08 | Write `docs/prompts/workflow_codex_implementer.md` | Strategist | `[x]` | P0-01 |
| P0-09 | Write `docs/prompts/workflow_claude_reviewer.md` | Strategist | `[x]` | P0-01 |
| P0-10 | Write `docs/prompts/workflow_codex_fixer.md` | Strategist | `[x]` | P0-01 |
| P0-11 | Git init, `.gitignore`, initial commit | Codex | `[ ]` | P0-01 |

---

## Phase 1 — Config, Storage, Schema

| ID | Task | Owner | Status | Depends On |
|---|---|---|---|---|
| P1-01 | Create `src/config.py` (env var loader, Config dataclass, startup validation) | Codex | `[ ]` | P0-01 |
| P1-02 | Create `src/schema.sql` (all tables from architecture.md §10) | Codex | `[ ]` | P0-01 |
| P1-03 | Create `src/db.py` (aiosqlite, init_db(), CRUD for all entity types) | Codex | `[ ]` | P1-02 |
| P1-04 | Create `scripts/init_db.sh` (creates data dirs, runs init_db) | Codex | `[ ]` | P1-03 |
| P1-05 | Create `scripts/smoke_test_db.py` (standalone PASS/FAIL script) | Codex | `[ ]` | P1-03 |
| P1-06 | Create `requirements.txt` (pinned: python-telegram-bot, aiosqlite, openai-whisper, python-dotenv) | Codex | `[ ]` | P1-01 |

**Phase 1 Review Criteria:**
- All 11 tables from architecture.md §10 present in schema.sql with correct field names and types.
- UNIQUE constraint on `reminder_log(deadline_id, days_before)` present.
- `src/config.py` raises `ValueError` at startup if `TELEGRAM_BOT_TOKEN` or `TELEGRAM_ALLOWED_CHAT_ID` missing.
- `src/db.py` functions return `dict` / `list[dict]`, not raw sqlite Row objects.
- `smoke_test_db.py` runs and prints `PASS` on a fresh DB.
- No hardcoded paths — DB_PATH and AUDIO_PATH come from config.
- No secrets hardcoded.

---

## Phase 2 — Telegram Command Flows

| ID | Task | Owner | Status | Depends On |
|---|---|---|---|---|
| P2-01 | Create `src/bot.py` (startup, long-polling, allowed chat_id guard) | Codex | `[ ]` | P1-01, P1-03 |
| P2-02 | Create `src/state.py` (user session state: active project, pending confirm) | Codex | `[ ]` | P2-01 |
| P2-03 | Create `src/handlers/notes.py` (`/note` command handler) | Codex | `[ ]` | P2-01, P1-03 |
| P2-04 | Create `src/handlers/ideas.py` (`/idea` command handler) | Codex | `[ ]` | P2-01, P1-03 |
| P2-05 | Create `src/handlers/deadlines.py` (`/deadline` command handler, date parsing) | Codex | `[ ]` | P2-01, P1-03 |
| P2-06 | Create `src/handlers/homework.py` (`/homework` command handler) | Codex | `[ ]` | P2-01, P1-03 |
| P2-07 | Create `src/handlers/projects.py` (`/projects`, `/project <name>`, fuzzy match) | Codex | `[ ]` | P2-01, P1-03 |
| P2-08 | Create `src/handlers/list_cmd.py` (`/list notes/ideas/deadlines/homework`) | Codex | `[ ]` | P2-01, P1-03 |
| P2-09 | Create `src/handlers/confirm.py` (`/confirm`, `/edit`, `/discard` flow) | Codex | `[ ]` | P2-02 |
| P2-10 | Create `src/handlers/help_cmd.py` (`/help` command) | Codex | `[ ]` | P2-01 |
| P2-11 | Create `systemd/film-school-bot.service` | Codex | `[ ]` | P2-01 |

**Phase 2 Review Criteria:**
- `TELEGRAM_ALLOWED_CHAT_ID` guard fires before any handler logic — message from unknown chat_id is silently dropped.
- All explicit command handlers bypass LLM entirely (deterministic parsing only).
- `/deadline` correctly parses ISO dates and natural date expressions ("next Friday").
- Confirmation state machine does not leak state between sessions.
- `film-school-bot.service` runs as `oc_her`, not root. Has `NoNewPrivileges=true`. Has `EnvironmentFile` pointing to project `.env` or `/srv/openclaw-her/secrets/`.
- No secrets hardcoded in any handler or service file.

---

## Phase 3 — Reminders and Weekly Summary

| ID | Task | Owner | Status | Depends On |
|---|---|---|---|---|
| P3-01 | Create `scripts/send_reminders.py` (query active deadlines, send reminders, log) | Codex | `[ ]` | P1-03 |
| P3-02 | Create `scripts/send_summary.py` (query week data, generate narrative, send) | Codex | `[ ]` | P1-03 |
| P3-03 | Create `systemd/reminder.service` + `systemd/reminder.timer` (daily 08:00) | Codex | `[ ]` | P3-01 |
| P3-04 | Create `systemd/summary.service` + `systemd/summary.timer` (Monday 09:00) | Codex | `[ ]` | P3-02 |

**Phase 3 Review Criteria:**
- `send_reminders.py` second run on same day does not re-send (idempotent via `reminder_log` UNIQUE constraint).
- No reminders sent for deadlines with status `done` or `dismissed`.
- No reminders sent for deadlines more than 30 days out.
- `send_summary.py` output is narrative (mentions urgent deadlines, stalled projects, unreviewed ideas) — not just counts.
- Timer files have correct `OnCalendar=` syntax for Ubuntu 22.04 systemd.
- All service files run as `oc_her`. Have `NoNewPrivileges=true`.

---

## Phase 4 — Voice Ingestion and Transcription

| ID | Task | Owner | Status | Depends On |
|---|---|---|---|---|
| P4-01 | Create `src/voice.py` (download OGG from Telegram, convert to WAV via ffmpeg) | Codex | `[ ]` | P2-01 |
| P4-02 | Create `src/transcriber.py` (local Whisper inference, returns transcript text) | Codex | `[ ]` | P4-01 |
| P4-03 | Wire voice message handler into `src/bot.py` | Codex | `[ ]` | P4-01, P4-02 |
| P4-04 | Wire voice → confirmation flow (transcript shown, confirmation required) | Codex | `[ ]` | P4-03, P2-09 |
| P4-05 | Implement audio storage under `data/audio/` with `voice_inputs` DB row | Codex | `[ ]` | P4-01, P1-03 |

**Phase 4 Review Criteria:**
- Audio files written to `data/audio/` only — never transmitted to external service.
- `voice_input` row inserted in DB before processing begins (failure traceability).
- Raw transcript shown to user before any entity creation.
- Confirmation required before entity write — no silent auto-save.
- ffmpeg called as subprocess, errors caught and reported to user.
- Whisper inference runs locally — no API call to external STT service.
- Each failure stage (download, convert, transcribe, parse) produces a user-visible error message.

---

## Phase 5 — NL Routing and Review Mode

| ID | Task | Owner | Status | Depends On |
|---|---|---|---|---|
| P5-01 | `[!]` Verify OpenClaw API contract — inspect `/opt/openclaw/src` wire protocol | Manual | `[ ]` | — |
| P5-02 | Create `src/openclaw_client.py` (wrap OpenClaw call, return structured JSON) | Codex | `[ ]` | P5-01 |
| P5-03 | Create NL intent handler in `src/handlers/nl_handler.py` | Codex | `[ ]` | P5-02 |
| P5-04 | Create `src/reviewer.py` (idea review via OpenClaw strong model) | Codex | `[ ]` | P5-02 |
| P5-05 | Create `src/handlers/review.py` (`/review <id>` command handler) | Codex | `[ ]` | P5-04, P1-03 |

**Phase 5 Review Criteria:**
- P5-01 must be resolved manually before Phase 5 begins — orchestrator will stop at `[!]`.
- OpenClaw client not used for storage, scheduling, or command routing.
- OpenClaw client has a graceful fallback when unavailable (user gets error message, suggests `/command` alternative).
- `/review` output contains all 5 sections: CORE IDEA, DRAMATIC CENTER, WEAK POINTS, QUESTIONS, NEXT STEP.
- No generic praise in review output (enforced by prompt constraints in `src/reviewer.py`).
- NL handler only fires for free-text messages — explicit commands never pass through it.

---

## Phase 6 — Hardening and Operational Polish

| ID | Task | Owner | Status | Depends On |
|---|---|---|---|---|
| P6-01 | Add structured logging throughout all `src/` modules | Codex | `[ ]` | All |
| P6-02 | Add graceful error reply messages for all failure modes | Codex | `[ ]` | All |
| P6-03 | Create `scripts/cleanup_audio.py` (delete audio older than AUDIO_RETENTION_DAYS) | Codex | `[ ]` | P4-05 |
| P6-04 | Create `scripts/backup_db.sh` (copy DB with timestamp to `data/backups/`) | Codex | `[ ]` | P1-03 |
| P6-05 | Create `systemd/cleanup-audio.service` + `systemd/cleanup-audio.timer` (daily) | Codex | `[ ]` | P6-03 |
| P6-06 | Create `systemd/backup-db.service` + `systemd/backup-db.timer` (daily) | Codex | `[ ]` | P6-04 |

**Phase 6 Review Criteria:**
- `logging` module used throughout — no `print()` for status/debug output.
- No secrets appear in log output at any level.
- Every call to external systems (Telegram API, ffmpeg, Whisper, OpenClaw) has error handling.
- `cleanup_audio.py` respects `AUDIO_RETENTION_DAYS` from config — not hardcoded.
- All new service files run as `oc_her`. Have `NoNewPrivileges=true`.
- Full security checklist pass: no hardcoded secrets, no wrong paths, chat_id guard present everywhere.
