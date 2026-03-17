# Film School Assistant — Feature Specification

**Version:** 1.0
**Date:** 2026-03-17
**Owner:** Claude Strategist

---

## Overview

A private Telegram-based creative workflow assistant for one film school student.
Single user. Private VPS. Not a public service.

---

## Bot Commands — MVP

| Command | Description |
|---|---|
| `/note <text>` | Save a note |
| `/idea <text>` | Save an idea |
| `/deadline <title> due <date>` | Save a deadline |
| `/homework <title> due <date> [course:<name>]` | Save a homework item |
| `/projects` | List all projects |
| `/project <name>` | Set active project context |
| `/review <idea_id>` | Get structured creative review of an idea |
| `/list notes [project:<name>]` | List recent notes |
| `/list ideas [project:<name>]` | List ideas |
| `/list deadlines` | List upcoming deadlines |
| `/list homework` | List homework items |
| `/confirm` | Confirm pending entity (voice flow) |
| `/edit` | Edit pending entity fields |
| `/discard` | Discard pending entity |
| `/done_deadline_<id>` | Mark deadline as done |
| `/dismiss_deadline_<id>` | Dismiss reminders for a deadline |
| `/help` | Show command list |

---

## Entity Types

- **Note:** General capture. Can be tagged to a project.
- **Idea:** Creative concept. Can be reviewed. Tagged to a project.
- **Homework:** Assignment with due date and course name.
- **Deadline:** Any time-bound commitment.
- **Project:** Named context container for other entities.

---

## Project Context

- User can have multiple projects (one per film, one per course, etc.)
- `/project <name>` sets an active context — subsequent commands associate to it
- Project context persists in user session state (in-memory, reset on bot restart)
- Project can also be specified inline: `/note --project documentary <text>`
- Fuzzy name matching: "doc" resolves to "Documentary" if unambiguous

---

## Confirmation Flow (Voice and NL)

All voice input and free-text NL input goes through a confirmation step:

1. System shows interpreted entity
2. User responds: `/confirm`, `/edit`, or `/discard`
3. On `/edit`: system asks for specific field correction
4. Entity is not written until confirmed

---

## Review Mode

`/review <idea_id>` triggers structured creative review.

Output format:
```
CORE IDEA: [sentence]
DRAMATIC CENTER: [mechanism]
WEAK POINTS: [concrete gaps]
QUESTIONS: 1) [...] 2) [...] 3) [...]
NEXT STEP: [one action]
```

---

## Reminder Policy

- Reminders for active deadlines at: 7d, 3d, 1d, 0d (morning of)
- One reminder per bucket per deadline (no duplicates)
- No reminders for `done` or `dismissed` deadlines
- No reminders for deadlines more than 30 days out

---

## Weekly Summary

- Sent every Monday 09:00
- Covers prior 7 days of activity
- Includes: urgent deadlines, active projects, recent ideas, stalled threads, recommendations

---

## Security

- Bot ignores all messages from chat_ids not in `TELEGRAM_ALLOWED_CHAT_ID`
- Uses long-polling (no inbound port)
- Secrets from environment variables or secrets directory

---

## Configuration

All config via environment variables or config file at project root.

Required:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_CHAT_ID`
- `DB_PATH` (default: `data/assistant.db`)
- `AUDIO_PATH` (default: `data/audio/`)

Optional:
- `WHISPER_MODEL` (default: `small`)
- `AUDIO_RETENTION_DAYS` (default: `30`)
- `OPENCLAW_API_URL` (if applicable)

---

## Out of Scope (MVP)

- Web interface
- Multi-user
- File attachments
- Image recognition
- External calendar sync
- Proactive suggestions
- RAG / semantic search
