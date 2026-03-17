# Film School Assistant

Private Telegram bot — structured creative workflow assistant for a film school student.
Runs on a VPS, single user, no cloud dependencies except Telegram and Anthropic API.

---

## What it does

- `/note`, `/idea`, `/deadline`, `/homework` — save structured entities via commands
- `/review <id>` — get structured creative critique of an idea (CORE IDEA / DRAMATIC CENTER / WEAK POINTS / QUESTIONS / NEXT STEP)
- Voice notes — transcribed locally via Whisper, shown before saving (confirmation required)
- Free-text NL — intent extracted via Claude Haiku, routed to confirm flow
- Daily reminders — sent 7d / 3d / 1d / day-of before each deadline
- Weekly summary — every Monday 09:00, narrative digest of the week
- All data in local SQLite — no external storage

---

## Stack

| Layer | Tool |
|---|---|
| Bot | python-telegram-bot v21 (async, long-polling) |
| Storage | SQLite via aiosqlite |
| STT | OpenAI Whisper (local, `small` model) |
| Audio conversion | ffmpeg |
| NL intent + review | Anthropic API (Haiku for extraction, Sonnet for review) |
| Scheduling | systemd timers |
| Runtime | Python 3.11+, virtualenv |

---

## Project structure

```
film-school-assistant/
├── src/
│   ├── bot.py              # Entry point — Application setup, chat_id guard
│   ├── config.py           # Config dataclass, env var loading, startup validation
│   ├── db.py               # aiosqlite CRUD for all entities
│   ├── schema.sql          # 11-table SQLite schema
│   ├── state.py            # In-memory user session state
│   ├── voice.py            # Telegram OGG download + ffmpeg WAV conversion
│   ├── transcriber.py      # Local Whisper inference
│   ├── reviewer.py         # Idea review via Anthropic strong model
│   ├── openclaw_client.py  # Anthropic SDK wrapper (intent + review)
│   └── handlers/           # One file per command/flow
│       ├── notes.py        # /note
│       ├── ideas.py        # /idea
│       ├── deadlines.py    # /deadline
│       ├── homework.py     # /homework
│       ├── projects.py     # /projects, /project <name>
│       ├── list_cmd.py     # /list notes|ideas|deadlines|homework
│       ├── confirm.py      # /confirm, /edit, /discard
│       ├── review.py       # /review <id>
│       ├── nl_handler.py   # Free-text NL routing
│       ├── help_cmd.py     # /help
│       └── common.py       # Shared utilities (date parsing, project fuzzy match)
├── scripts/
│   ├── init_db.sh          # Create data dirs + init schema
│   ├── smoke_test_db.py    # Standalone PASS/FAIL DB verification
│   ├── send_reminders.py   # Daily reminder dispatch (run by systemd)
│   ├── send_summary.py     # Weekly summary dispatch (run by systemd)
│   ├── cleanup_audio.py    # Delete audio older than AUDIO_RETENTION_DAYS
│   └── backup_db.sh        # Copy DB with timestamp to data/backups/
├── systemd/
│   ├── film-school-bot.service
│   ├── reminder.service / reminder.timer        (daily 08:00)
│   ├── summary.service / summary.timer          (Monday 09:00)
│   ├── cleanup-audio.service / cleanup-audio.timer  (daily 03:00)
│   └── backup-db.service / backup-db.timer      (daily 02:00)
├── docs/
│   ├── architecture.md
│   ├── spec.md
│   ├── tasks.md
│   ├── ops-security.md
│   ├── dev-cycle.md
│   └── prompts/            # Workflow orchestrator prompts
├── data/                   # Runtime data (gitignored)
│   ├── assistant.db
│   ├── audio/
│   └── backups/
├── requirements.txt
└── .env                    # Secrets (gitignored)
```

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

# Optional overrides
DB_PATH=data/assistant.db
AUDIO_PATH=data/audio/
AUDIO_RETENTION_DAYS=30
LOG_LEVEL=INFO
LLM_MODEL_INTENT=claude-haiku-4-5
LLM_MODEL_REVIEW=claude-sonnet-4-6
```

### 4. Initialize database

```bash
bash scripts/init_db.sh
```

Verify:

```bash
python scripts/smoke_test_db.py
# → PASS
```

### 5. Run the bot

```bash
source .venv/bin/activate
python src/bot.py
```

---

## Deploy with systemd

Update `WorkingDirectory` and `ExecStart` paths in `systemd/` unit files if your project root differs.
Also update `ExecStart` to use your virtualenv Python: `/path/to/.venv/bin/python3`.

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

## Bot commands

| Command | Description |
|---|---|
| `/note <text>` | Save a note |
| `/idea <text>` | Save an idea |
| `/deadline <title> due <date>` | Save a deadline (ISO date or "next Friday") |
| `/homework <title> due <date> [course:<name>]` | Save a homework item |
| `/projects` | List all projects |
| `/project <name>` | Set active project context |
| `/review <idea_id>` | Structured creative critique of an idea |
| `/list notes\|ideas\|deadlines\|homework` | List items (optionally filter by project) |
| `/confirm` | Confirm pending entity (voice/NL flow) |
| `/edit` | Edit pending entity |
| `/discard` | Discard pending entity |
| `/help` | Show command list |

---

## Security

- Bot ignores all messages from chat IDs not in `TELEGRAM_ALLOWED_CHAT_ID` — silently dropped before any handler runs
- No secrets hardcoded — all from env vars or `.env` file
- Audio files stored locally only — never transmitted externally
- Whisper runs on-device (no OpenAI Whisper API)
- All systemd services run as unprivileged user (`oc_her`), `NoNewPrivileges=true`

---

## Development workflow

See `docs/dev-cycle.md` and `docs/prompts/workflow_orchestrator.md` for the AI-assisted Implement → Review → Fix loop used to build this project.
