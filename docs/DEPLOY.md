# Deployment Guide — Film School Assistant

Step-by-step instructions for deploying the bot on a VPS with systemd.

---

## Prerequisites

- Python 3.11 or newer (`python3 --version`)
- git
- systemd (standard on Debian/Ubuntu/Fedora-based VPS images)
- ffmpeg (required for voice transcription — see note at the bottom)

Install ffmpeg if not present:

```bash
sudo apt-get install -y ffmpeg     # Debian / Ubuntu
# or
sudo dnf install -y ffmpeg         # Fedora / RHEL
```

---

## 1. Clone the repository

```bash
git clone https://github.com/your-org/film-school-assistant.git /path/to/repo
cd /path/to/repo
```

Replace `/path/to/repo` with your preferred location, e.g. `/srv/film-school-assistant`.

---

## 2. Create a virtualenv and install dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

---

## 3. Configure environment variables

Copy the example file and fill in the values:

```bash
cp .env.example .env
$EDITOR .env
```

Required values to set:

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_ALLOWED_CHAT_ID` | Your numeric Telegram chat ID (the bot accepts messages only from this ID) |

All other variables have sensible defaults; adjust as needed (see `.env.example` for documentation).

---

## 4. Initialize the database schema

Run the smoke test script — it calls `init_db` and validates all CRUD operations against a temporary database. On success it prints `PASS` and exits 0.

```bash
.venv/bin/python scripts/smoke_test_db.py
```

The bot itself also calls `init_db` on every startup (idempotent via `CREATE TABLE IF NOT EXISTS`), so the production database at `DB_PATH` is initialized automatically on first launch.

---

## 5. Install and enable systemd units

All unit files live in the `systemd/` directory. Before copying, edit each file and replace the placeholder paths with real ones:

- `User=youruser` — the Linux user that will run the bot
- `WorkingDirectory=/path/to/repo` — absolute path to the cloned repo
- `ExecStart=/path/to/repo/.venv/bin/python3 ...` — venv python for each service
- `EnvironmentFile=/path/to/repo/.env` — absolute path to your `.env` file

Then install:

```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo cp systemd/*.timer  /etc/systemd/system/

sudo systemctl daemon-reload

# Start and enable the main bot service
sudo systemctl enable --now film-school-bot.service

# Enable periodic timers (reminders, weekly summary, audio cleanup, db backup)
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

## 6. Smoke test — verify the bot is running

1. Open Telegram and send `/start` to your bot.
2. You should receive a greeting message within a few seconds.
3. Try sending a short text like "Идея для документального фильма" — the bot should parse it and offer to save it.

---

## Note on voice transcription

Voice message transcription requires `ffmpeg` to convert OGG audio to WAV before passing it to the Whisper model. If `ffmpeg` is missing the conversion step will fail with an error.

Verify it is available:

```bash
ffmpeg -version
```

Audio files are stored under `AUDIO_PATH` (default: `data/audio/`) and cleaned up automatically by the `cleanup-audio.timer` according to `AUDIO_RETENTION_DAYS`.
