# Film School Assistant — Operations and Security

**Version:** 1.0
**Date:** 2026-03-17
**Owner:** Claude Strategist

---

## Deployment Environment

- Host: Ubuntu 22.04 VPS
- User: oc_her
- Instance root: /srv/openclaw-her
- Project root: /srv/openclaw-her/workspace/film-school-assistant
- Data directory: /srv/openclaw-her/workspace/film-school-assistant/data/
- Audio directory: /srv/openclaw-her/workspace/film-school-assistant/data/audio/
- DB path: /srv/openclaw-her/workspace/film-school-assistant/data/assistant.db

---

## Secret Management

| Secret | Location | Access |
|---|---|---|
| TELEGRAM_BOT_TOKEN | /srv/openclaw-her/secrets/telegram_token or .env | oc_her only |
| TELEGRAM_ALLOWED_CHAT_ID | .env or environment | Required at startup |
| OPENCLAW_API credentials | /srv/openclaw-her/.env | Inherited from instance config |

**Rules:**
- Secrets never hardcoded in source
- Secrets never logged
- .env file is in .gitignore
- secrets/ directory is mode 700

---

## Path Boundaries

**Allowed write paths for project code:**
- `/srv/openclaw-her/workspace/film-school-assistant/` (all subdirs)

**Forbidden write paths:**
- `/opt/openclaw/src` — OpenClaw runtime source
- `/srv/openclaw-her/state` — Instance runtime state
- `/srv/openclaw-her/openclaw.json5` — Instance config
- `/srv/openclaw-her/.env` — Instance env (read-only at most)
- `/srv/openclaw-you/` — Different instance

---

## Network Security

- Bot uses Telegram long-polling (outbound only)
- No inbound port required for the bot
- UFW enabled — no new inbound rules needed for MVP
- If webhook is ever used: must sit behind nginx with TLS, not directly exposed

---

## systemd Services

| Service | Binary | User | Restart Policy |
|---|---|---|---|
| film-school-bot.service | python src/bot.py | oc_her | on-failure, max 5 restarts |
| reminder.service | python scripts/send_reminders.py | oc_her | on-failure, no restart (timer triggers) |
| summary.service | python scripts/send_summary.py | oc_her | on-failure, no restart |
| cleanup-audio.service | python scripts/cleanup_audio.py | oc_her | on-failure, no restart |

All services run as oc_her, not root.
Update each `ExecStart` to point at the virtualenv Python, for example `/path/to/.venv/bin/python3`.

---

## Backup Policy

- DB backup: daily via scripts/backup_db.sh
- Backup location: /srv/openclaw-her/workspace/film-school-assistant/data/backups/
- Retention: 7 daily backups kept
- Audio files: not backed up (reproducible from voice inputs if needed)
- Transcripts: backed up with DB (stored in SQLite)

---

## Audio Retention

- Audio files stored: data/audio/
- Retention period: 30 days (configurable via AUDIO_RETENTION_DAYS)
- Cleanup: daily timer via systemd
- No audio transmitted to external services

---

## Logging

- Log level: INFO by default, DEBUG in dev
- All log output goes to journald via systemd capture of stdout/stderr
- View logs with: `sudo journalctl -u film-school-bot.service -f`
- No file-based logger is configured
- Never log: secrets, audio paths with personal content, raw transcripts at INFO level
- Debug may log transcripts — disable in production

---

## Chat ID Guard

Every incoming Telegram message must be checked against TELEGRAM_ALLOWED_CHAT_ID.
If the chat_id does not match, the bot silently ignores the message (no reply, no log at INFO).
This check happens before any handler logic.

---

## Incident Response

If bot token is compromised:
1. Revoke token via BotFather immediately
2. Generate new token
3. Update secrets file and restart service

If DB is corrupted:
1. Stop bot service
2. Restore from latest backup in data/backups/
3. Restart service

If audio directory fills disk:
1. Check AUDIO_RETENTION_DAYS setting
2. Manually run cleanup_audio.py
3. Review audio volume — consider lowering retention window

---

## Monitoring

**Systemd timer health:**
- Check all timers: `systemctl list-timers --no-pager`
- Check specific timer: `systemctl status reminder.timer`
- Last run result: `systemctl status reminder.service`
- Live logs: `journalctl -u reminder.service -f`
- Last 50 log lines: `journalctl -u reminder.service -n 50`
- All bot logs today: `journalctl -u film-school-bot.service --since today`

**Failure alerts:**
All oneshot services (reminder, summary, backup-db, cleanup-audio) have `OnFailure=notify-failure@%n.service`.
If a timer fails, scripts/notify_failure.py sends a Telegram message:
  "⚠️ Systemd unit failed: <unit>\nCheck: journalctl -u <unit> -n 50"

**SLA:**
- Reminders: delivered within 1 hour of midnight local time (timer fires at 08:00)
- Weekly summary: delivered by 09:00 Monday
- No uptime guarantee — single VPS, no HA

---

## Log Retention

Logs are stored in journald. Default retention applies (systemd journal size limits).
To check current journal size: `journalctl --disk-usage`
To vacuum old logs: `journalctl --vacuum-time=30d`
No application-level log files are written. All logs go to stdout/stderr captured by systemd.

---

## Secret Rotation

**Rotate Telegram bot token:**
1. Generate new token via BotFather (/revoke, then /token)
2. Update token in .env or secrets file
3. Restart bot: `systemctl restart film-school-bot.service`
4. Verify: send /start in Telegram chat

**Rotate Anthropic API key:**
1. Generate new key in Anthropic console
2. Update LLM_API_KEY in .env
3. Restart bot: `systemctl restart film-school-bot.service`
4. Verify: send a voice message to trigger LLM intent detection

**Rotation frequency:** Rotate any key immediately if exposed. Otherwise no mandatory rotation schedule.
