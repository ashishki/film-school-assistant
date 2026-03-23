# Film School Assistant

A private Telegram bot built for a single film school student. It captures notes, ideas,
homework, and deadlines through text commands and voice messages, sends daily deadline
reminders, and delivers a weekly narrative digest of the week's work.

Runs entirely on a private VPS. No cloud storage. All data stays local.

---

## What It Does

### Capture

Send a voice note or type freely — the bot transcribes it locally (Whisper), extracts the
intent (Claude Haiku), and asks you to confirm before saving. Or use explicit commands for
direct, no-confirm saves.

| Input type | How it works |
|---|---|
| `/note`, `/idea`, `/deadline`, `/homework` | Saves immediately, no confirmation step |
| Voice message | Transcribed → intent extracted → shown for confirmation |
| Free text | Intent extracted → routed to confirmation flow |

### Organise

Everything is scoped to projects. Create a project, set it as active, and all new entries
attach to it automatically.

```
/new_project Documentary Short
/project Documentary Short
/note rough cut needs more b-roll in the market scene
/deadline Final cut due 2026-04-15
```

### Review

Ask the bot to critique any saved idea. It runs a structured review through Claude Sonnet:
core concept, dramatic center, weak points, open questions, recommended next step.

```
/review 42
```

### Find

Search across all notes and ideas by keyword. Filter any list by status or project.
Paginate long results.

```
/search b-roll
/list deadlines status:active project:Documentary Short
/list notes page:2
```

### Edit

Change saved entities without re-entering everything.

```
/edit_note 17 the market scene needs wider establishing shots
/edit_deadline 8 title Final cut — director's version
/edit_deadline 8 due 2026-04-20
```

### Archive

Soft-delete projects you're done with. They disappear from all active lists but the data
is preserved.

```
/archive_project Old Short Film
```

### Reminders

Every morning at 08:00 the bot checks for deadlines due in 7 days, 3 days, 1 day, and
today. It sends a Telegram message for each with a `/done_deadline_N` link.
Reminders are deduplication-safe — if the timer fires twice, you get one message.

### Weekly Summary

Every Monday at 09:00 the bot sends a digest covering what you logged during the week,
what's urgent, what's stalled, and a recommended next step. Built from your actual data —
no LLM hallucination of facts.

### Failure Alerts

If any scheduled task (reminders, summary, backup, audio cleanup) fails silently, the bot
sends a Telegram alert with a `journalctl` command to investigate.

---

## Stack

| Layer | Tool | Notes |
|---|---|---|
| Bot framework | python-telegram-bot 21.6 | Async, long-polling |
| Storage | SQLite via aiosqlite | Local file, WAL mode recommended |
| STT | OpenAI Whisper (local, `small` model) | No Whisper API — fully on-device |
| Audio conversion | FFmpeg | OGG → WAV for Whisper |
| NL intent extraction | Claude Haiku (`claude-haiku-4-5`) | Structured JSON extraction |
| Idea review | Claude Sonnet (`claude-sonnet-4-6`) | Deep creative critique |
| Scheduling | systemd timers | Reminders, summary, backup, cleanup |
| Runtime | Python 3.11+, virtualenv | |

---

## Commands

### Capture

| Command | What it does |
|---|---|
| `/note <text>` | Save a note, optionally scoped to active project |
| `/idea <text>` | Save an idea |
| `/deadline <title> due <date>` | Save a deadline (ISO date or natural language) |
| `/homework <title> due <date> [course:<name>]` | Save a homework item |

### Projects

| Command | What it does |
|---|---|
| `/new_project <name>` | Create a new project |
| `/projects` | List all active projects |
| `/project <name>` | Set active project (fuzzy match) |
| `/archive_project <name>` | Soft-delete a project |

### Edit

| Command | What it does |
|---|---|
| `/edit_note <id> <new content>` | Replace note content |
| `/edit_idea <id> <new content>` | Replace idea content |
| `/edit_deadline <id> title <new title>` | Update deadline title |
| `/edit_deadline <id> due <new date>` | Update deadline due date |

### Find & Browse

| Command | What it does |
|---|---|
| `/list notes\|ideas\|deadlines\|homework` | List items |
| `/list … status:<value>` | Filter by status (active, pending, completed…) |
| `/list … project:<name>` | Filter by project |
| `/list … page:<n>` | Paginate (20 items per page) |
| `/search <keyword>` | Full-text search across notes and ideas |

### Voice & NL Confirmation Flow

| Command | What it does |
|---|---|
| `/confirm` | Save the pending entity shown after voice/NL input |
| `/edit <field> <value>` | Edit a field of the pending entity before saving |
| `/discard` | Discard the pending entity |

### Review & Info

| Command | What it does |
|---|---|
| `/review <idea_id>` | Structured creative critique of an idea (Sonnet) |
| `/help` | Show command list |

---

## Setup

### 1. Clone and create virtualenv

```bash
git clone https://github.com/ashishki/film-school-assistant.git
cd film-school-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Install system dependencies

```bash
sudo apt install ffmpeg
```

### 3. Create `.env`

```ini
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_ALLOWED_CHAT_ID=your_telegram_chat_id
LLM_API_KEY=your_anthropic_api_key

# Optional overrides (shown with defaults)
DB_PATH=data/assistant.db
AUDIO_PATH=data/audio/
AUDIO_RETENTION_DAYS=30
REMINDER_BUCKETS=7,3,1,0
DAILY_LLM_CALL_LIMIT=20
LOG_LEVEL=INFO
LLM_MODEL_INTENT=claude-haiku-4-5
LLM_MODEL_REVIEW=claude-sonnet-4-6
```

### 4. Initialize database and verify

```bash
bash scripts/init_db.sh
.venv/bin/python scripts/smoke_test_db.py
# → PASS
```

### 5. Run the bot

```bash
source .venv/bin/activate
python src/bot.py
```

---

## Deploy with systemd

Update `WorkingDirectory` and `ExecStart` in `systemd/*.service` to match your paths,
then point `ExecStart` at your venv Python: `/path/to/.venv/bin/python3`.

```bash
sudo cp systemd/*.service systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload

sudo systemctl enable --now film-school-bot.service
sudo systemctl enable --now reminder.timer
sudo systemctl enable --now summary.timer
sudo systemctl enable --now cleanup-audio.timer
sudo systemctl enable --now backup-db.timer
```

Check status:

```bash
sudo systemctl status film-school-bot.service
sudo journalctl -u film-school-bot.service -f
```

---

## Project Structure

```
film-school-assistant/
├── src/
│   ├── bot.py               # Entry point, chat_id guard, voice handler, restart notification
│   ├── config.py            # Config dataclass, all env var loading
│   ├── db.py                # All aiosqlite CRUD — notes, ideas, deadlines, homework,
│   │                        #   projects, reminders, LLM call log, parsed events
│   ├── schema.sql           # 12-table SQLite schema (CREATE TABLE IF NOT EXISTS)
│   ├── state.py             # In-memory user session state
│   ├── voice.py             # OGG download + ffmpeg WAV conversion
│   ├── transcriber.py       # Local Whisper inference
│   ├── reviewer.py          # Idea review via Anthropic Sonnet
│   ├── openclaw_client.py   # Anthropic SDK wrapper with retry/backoff
│   └── handlers/
│       ├── notes.py         # /note
│       ├── ideas.py         # /idea
│       ├── deadlines.py     # /deadline
│       ├── homework.py      # /homework
│       ├── projects.py      # /projects, /project, /new_project, /archive_project
│       ├── list_cmd.py      # /list with status filter, project filter, pagination
│       ├── search_cmd.py    # /search keyword
│       ├── edit_cmd.py      # /edit_note, /edit_idea, /edit_deadline
│       ├── confirm.py       # /confirm, /edit, /discard
│       ├── review.py        # /review (LLM call with daily limit guard)
│       ├── nl_handler.py    # Free-text NL routing (LLM call with daily limit guard)
│       ├── help_cmd.py      # /help
│       └── common.py        # Date parsing, project fuzzy match, reply helpers
├── scripts/
│   ├── init_db.sh              # Create data dirs + initialize schema
│   ├── smoke_test_db.py        # Standalone PASS/FAIL DB verification
│   ├── test_voice_pipeline.py  # Voice flow integration test (mocked Telegram + Whisper)
│   ├── send_reminders.py       # Daily reminder dispatch (systemd timer)
│   ├── send_summary.py         # Weekly summary dispatch (systemd timer)
│   ├── notify_failure.py       # Telegram alert on systemd unit failure
│   ├── cleanup_audio.py        # Delete audio files older than AUDIO_RETENTION_DAYS
│   └── backup_db.sh            # Timestamped DB backup to data/backups/
├── systemd/
│   ├── film-school-bot.service
│   ├── reminder.service / .timer        (daily 08:00)
│   ├── summary.service / .timer         (Monday 09:00)
│   ├── cleanup-audio.service / .timer   (daily 03:00)
│   ├── backup-db.service / .timer       (daily 02:00)
│   └── notify-failure@.service          (OnFailure= template — wired to all timers above)
├── docs/
│   ├── ARCHITECTURE.md         # System design and component map
│   ├── spec.md                 # Feature specification and acceptance criteria
│   ├── tasks.md                # Full task backlog (27 tasks, all complete)
│   ├── ops-security.md         # Deployment, monitoring, secret rotation
│   ├── db-migration-guide.md   # How to apply SQLite schema changes safely
│   ├── llm-prompts.md          # Versioned changelog of all LLM system prompts
│   ├── dev-cycle.md            # Development cycle log
│   └── audit/                  # Review cycle reports (Cycles 1–4)
├── .github/workflows/ci.yml    # Lint (ruff) + smoke test on every push
├── pyproject.toml              # ruff config
├── requirements.txt
└── .env                        # Secrets — gitignored
```

---

## Security

- **Single-user guard**: all messages from unknown `chat_id` are silently dropped before
  any handler runs — no response, no log at INFO level.
- **No secrets in source**: everything from env vars or `.env`. `.env` is gitignored.
- **Audio stays local**: voice files are stored and processed on-device. Never sent to
  any external service. Whisper runs fully on-device.
- **LLM cost guard**: daily call counter (`DAILY_LLM_CALL_LIMIT`, default 20) prevents
  runaway Anthropic API costs. Review and NL extraction check the limit before calling.
- **Systemd hardening**: all services run as an unprivileged user with `NoNewPrivileges=true`.
- **Telegram send retry**: all outbound Telegram API calls retry up to 3 times with
  exponential backoff. 4xx errors (bad token/chat_id) fail immediately without retrying.

---

## Reliability

| Feature | How it works |
|---|---|
| Reminder deduplication | `UNIQUE(deadline_id, days_before)` in DB — timer can fire twice, you get one message |
| Restart notification | On startup, bot queries recent unconfirmed entities and notifies you if any were lost |
| Failure alerting | `OnFailure=notify-failure@%n.service` on all systemd timers |
| Daily DB backup | Timestamped copy to `data/backups/`, 7 copies retained |
| Telegram retry | 3 attempts, 0.5s / 1.0s / 1.5s backoff on transient errors |

---

## What's Next

These are the known gaps worth addressing. None of them block current functionality.

### WAL mode verification

The bot (aiosqlite) and the scheduled scripts (stdlib sqlite3) write to the same database
concurrently. SQLite WAL mode allows this safely, but WAL mode has not been explicitly
verified on the deployed database. A startup check or a one-time migration running
`PRAGMA journal_mode=WAL` would close this gap permanently.

### Shared Telegram send helper

`send_telegram_message` with retry/backoff is duplicated across three scripts
(`send_reminders.py`, `send_summary.py`, `notify_failure.py`). Extracting it to
`src/telegram_client.py` would make future changes to retry policy a one-file edit.

### Voice pipeline in CI

The voice integration test (`scripts/test_voice_pipeline.py`) runs locally but is excluded
from CI because importing `src.bot` transitively pulls in `openai-whisper`, which is too
heavy for a GitHub Actions runner. A clean fix would be to refactor the module boundary so
the voice handler is importable without loading Whisper at import time.

### Multi-user support

The auth model is a single hardcoded `TELEGRAM_ALLOWED_CHAT_ID`. Adding a second user
would require a user table, per-user project scoping, and per-user reminder dispatch.
Not needed for the current setup, but the schema is already normalized enough that
adding it would be a contained change.

---

## Operations

See `docs/ops-security.md` for the full runbook: monitoring commands, log retention,
secret rotation, and incident response.

Quick reference:

```bash
# Check bot
sudo systemctl status film-school-bot.service
sudo journalctl -u film-school-bot.service -n 50

# Check all timers
systemctl list-timers --no-pager

# Run smoke test
.venv/bin/python scripts/smoke_test_db.py
```
