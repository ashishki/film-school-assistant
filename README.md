# Film School Assistant

Telegram-first private assistant for film-school and director workflow: capture scattered ideas, voice notes, homework, deadlines, project context, and reflections, then turn them into a steadier creative working rhythm.

Status: paused creative portfolio case. The product is not in active feature development; roadmap and pause rules are in `docs/PROJECT_PLAN.md`.

It is not a public SaaS product or a generic notes bot. Telegram is the current interface; the product is a single-user continuity assistant for creative projects.

## What It Does

1. Captures text and voice input in Telegram.
2. Extracts structured entities: notes, ideas, homework, deadlines, and user context.
3. Confirms each entity before saving.
4. Keeps entries attached to active projects.
5. Supports review, search, edit, recall, archive, and project reflection.
6. Sends deadline reminders, recurring practice prompts, and weekly summaries.
7. Maintains bounded memory:
   - structured SQLite state as source of truth
   - project summaries for fast context
   - verbatim `memory_items` evidence for recall and reflection
   - user context summary for personal grounding

## Current Capabilities

- Telegram bot with single authorized user guard.
- Text and voice capture with local Whisper transcription.
- Multi-entity natural-language extraction.
- Confirmation queue with save/discard/rewrite.
- Project-aware notes, ideas, homework, and deadlines.
- `/memory`, `/recall`, `/reflect`, `/search`, `/review`, `/get`, `/list`, and edit flows.
- Natural chat access to recall and reflection tools.
- Recurring daily practices with timezone-aware reminders.
- Feature-feedback capture for unsupported requests.
- SQLite persistence and private VPS deployment through `systemd`.

## Architecture Snapshot

| Area | Current choice |
|---|---|
| Interface | Telegram-first |
| Runtime | Python service on private VPS |
| Storage | SQLite |
| Voice | local Whisper |
| LLM usage | bounded extraction, review, reflection, summaries |
| Memory | structured state + bounded summaries + provenance evidence |
| Deployment | private single-user `systemd` service |

Deterministic code owns auth, persistence, reminders, scheduling, search scope, and confirmation. LLMs are used only for bounded interpretation and generation tasks.

## Main Docs

- [docs/README.md](docs/README.md) — documentation map
- [docs/PRODUCT_OVERVIEW.md](docs/PRODUCT_OVERVIEW.md) — product definition and boundaries
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system architecture
- [docs/MEMORY_ARCHITECTURE.md](docs/MEMORY_ARCHITECTURE.md) — memory model
- [docs/WORKFLOW_BOUNDARIES.md](docs/WORKFLOW_BOUNDARIES.md) — deterministic vs LLM ownership
- [docs/DEPLOY.md](docs/DEPLOY.md) — VPS deployment
- [docs/tasks.md](docs/tasks.md) — current maintenance backlog

Historical phase plans, audit cycles, eval packs, and old review reports live under [docs/archive/](docs/archive/README.md).

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Initialize the database:

```bash
./scripts/init_db.sh
```

Copy and fill environment variables:

```bash
cp .env.example .env
```

Useful checks:

```bash
python3 scripts/smoke_test_db.py
python3 scripts/test_voice_pipeline.py
```

See [docs/DEPLOY.md](docs/DEPLOY.md) for production service setup.
