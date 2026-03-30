# Film School Assistant

Film School Assistant is a Telegram-first AI assistant for directors and creative thinkers that helps capture ideas, reduce workflow chaos, and maintain continuity across projects, deadlines, and reflections.

It is not positioned as "a Telegram bot for notes." Telegram is the current interface layer. The product is a private creative workflow assistant: a system for turning scattered voice notes, loose ideas, deadlines, and homework into a structured working rhythm.

## What Problem It Solves

Creative work often breaks down in the gaps between thinking and execution:
- ideas arrive in fragments
- deadlines drift out of context
- notes become piles instead of momentum
- projects lose continuity between sessions

This project is designed to reduce that chaos for a solo director or film student by combining fast capture, structured storage, reminders, and bounded AI assistance.

## Who It Is For

Right now, the product is built for a single primary user:
- a director in training
- a film student
- a solo creative thinker managing multiple active projects

It is intentionally single-user, private, and operationally simple.

## Core Workflow

1. Capture thoughts quickly by text or voice in Telegram.
2. Convert messy input into structured entities: notes, ideas, deadlines, homework.
3. Attach entries to projects so work stays contextual, not flat.
4. Review, search, edit, archive, and revisit work without losing continuity.
5. Receive reminders and a weekly digest that turn stored material into forward motion.

## Why It Is Not Just Notes, ChatGPT, or Telegram

- Not just notes: it adds structure, projects, reminders, review flows, and continuity.
- Not just ChatGPT: LLM use is bounded to specific jobs, while state, scheduling, and storage stay deterministic.
- Not just Telegram: Telegram is only the current interaction surface for a broader creative workflow system.

## Current Architecture Snapshot

- Interface: Telegram-first, single authorized user
- Runtime: Python service on a private VPS with `systemd`
- Storage: local SQLite
- Voice transcription: local Whisper
- Intent extraction: Claude Haiku
- Idea review: Claude Sonnet
- Automation: deterministic reminder and weekly summary scripts

See [Product Overview](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/PRODUCT_OVERVIEW.md), [Architecture](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/ARCHITECTURE.md), and [Phase Plan](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/PHASE_PLAN.md).

## Current Status

The implemented foundation is real:
- Telegram-first capture and management flows exist
- reminders and weekly summary exist
- local voice transcription exists
- structured idea review exists

The current weakness is not "missing AI." It is product framing, documentation coherence, UX continuity, and disciplined sequencing for the next phases.

## Documentation Map

- [Product Overview](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/PRODUCT_OVERVIEW.md): product category, user, boundaries, differentiation
- [Architecture](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/ARCHITECTURE.md): system shape, governance, runtime, ownership boundaries
- [Workflow Boundaries](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/WORKFLOW_BOUNDARIES.md): deterministic vs LLM rules and approval gates
- [User Experience](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/USER_EXPERIENCE.md): UX principles for a creative assistant
- [Phase Plan](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/PHASE_PLAN.md): what is built, what comes next, what is deferred
- [Decisions](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/DECISIONS.md): key architectural and product decisions for the current phase
- [Setup Spec](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/spec.md): implementation-facing product contract
- [Task Graph](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/tasks.md): playbook-compatible execution backlog

## Setup

Start with the implementation-facing setup and runtime details already in the repo:
- [Product Spec](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/spec.md)
- [Ops / Security](/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant/docs/ops-security.md)

The repository remains intentionally private-deployment-first. A public SaaS posture is not the current target.
