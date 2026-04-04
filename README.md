# Film School Assistant

Film School Assistant is a Telegram-first AI assistant for directors and creative thinkers that helps capture ideas, reduce workflow chaos, and maintain continuity across projects, deadlines, reflections, and recurring creative practices.

It is not positioned as "a Telegram bot for notes." Telegram is the current interface layer. The product is a private creative workflow assistant: a system for turning scattered voice notes, loose ideas, deadlines, and homework into a structured working rhythm.

## What Problem It Solves

Creative work often breaks down in the gaps between thinking and execution:
- ideas arrive in fragments
- deadlines drift out of context
- notes become piles instead of momentum
- projects lose continuity between sessions

This project is designed to reduce that chaos for a solo director or film student by combining fast capture, structured storage, reminders, recurring practice prompts, and bounded AI assistance.

## Who It Is For

Right now, the product is built for a single primary user:
- a director in training
- a film student
- a solo creative thinker managing multiple active projects

It is intentionally single-user, private, and operationally simple.

## Core Workflow

1. Capture thoughts quickly by text or voice in Telegram — one message can contain multiple items at once.
2. Convert messy input into structured entities: notes, ideas, deadlines, homework — each confirmed individually.
3. Attach entries to projects so work stays contextual, not flat.
4. Review, search, edit, archive, and revisit work without losing continuity.
5. Receive deadline reminders, recurring daily practice prompts, and a weekly digest that turn stored material into forward motion.
6. Run `/memory` to generate a bounded summary of the current project state.
7. Run `/reflect` to get a grounded orientation: where the project stands, what tensions are active, and what to focus on next.
8. Turn missing-feature requests into stored developer feedback, either as raw feedback or as a short structured feature brief.

## Why It Is Not Just Notes, ChatGPT, or Telegram

- Not just notes: it adds structure, projects, reminders, review flows, and continuity.
- Not just ChatGPT: LLM use is bounded to specific jobs, while state, scheduling, and storage stay deterministic.
- Not just Telegram: Telegram is only the current interaction surface for a broader creative workflow system.

## Current Architecture Snapshot

- Interface: Telegram-first, single authorized user
- Runtime: Python service on a private VPS with `systemd`
- Storage: local SQLite
- Voice transcription: local Whisper
- Intent extraction: Claude Haiku — multi-entity, context-aware, with targeted error recovery
- Project memory: Claude Haiku (bounded summary, one paragraph per project)
- User context memory: Claude Haiku (bounded user profile summary from saved personal context)
- Idea review: Claude Sonnet
- Project reflection: Claude Sonnet (`/reflect` command)
- Feature-feedback capture: bounded multi-step LLM flow with separate quota and structured storage
- Automation: deterministic deadline reminders, timezone-aware recurring daily-practice prompts, and weekly summary scripts

See [Product Overview](docs/PRODUCT_OVERVIEW.md), [Architecture](docs/ARCHITECTURE.md), and [Phase Plan](docs/PHASE_PLAN.md).

## Current Status

The system is complete through five development phases and one audit cycle:

**Capture and confirmation**
- Telegram-first capture by text or voice; local Whisper transcription
- one free-text message can contain multiple entities — each is confirmed individually in sequence
- confirmation keyboard has three options: save, discard, or rewrite (✏️ Уточнить — re-runs extraction on next message)
- when extraction fails, the assistant asks a specific clarifying question instead of a generic error
- NL handler uses the last five messages as context so back-references ("а ещё добавь дедлайн") resolve correctly

**Project continuity**
- confirmation and edit replies are project-aware and include the project name
- the weekly digest is framed in Russian with project-level next-step pointers
- `/memory` generates a bounded project-state summary and stores one paragraph per project
- stored project memory is injected into chat context so the assistant retains project state without re-explanation
- personal context about the user can be saved separately from project notes and condensed into a short working profile
- the saved user profile is injected into relevant assistant flows so review, reflection, and chat help stay grounded in the person, not only the project

**Feedback and practices**
- when the assistant cannot do something yet, it can offer to turn that gap into a developer-facing feature request
- feature requests can be captured as short structured briefs and stored separately from raw user feedback
- the bot supports recurring daily practices such as morning pages and end-of-day reflection prompts
- these practices can be configured by command or natural language, including text and voice requests
- recurring practices now support explicit timezone capture and correction flows such as switching reminders to Tbilisi time
- correction-style replies like “нет, только утренние страницы в 10:00” are handled as updates to the existing practice setup instead of generic chat

**Reflection and review**
- idea review uses project memory when available so critique is specific to the active project
- `/reflect` produces a structured project reflection: current state, creative tensions, and next focus

**Deployment**
- deployment is documented for VPS setup with `.env.example`, `docs/DEPLOY.md`, and corrected `systemd` service files

## Documentation Map

- [Product Overview](docs/PRODUCT_OVERVIEW.md): product category, user, boundaries, differentiation
- [Architecture](docs/ARCHITECTURE.md): system shape, governance, runtime, ownership boundaries
- [Workflow Boundaries](docs/WORKFLOW_BOUNDARIES.md): deterministic vs LLM rules and approval gates
- [User Experience](docs/USER_EXPERIENCE.md): UX principles for a creative assistant
- [Phase Plan](docs/PHASE_PLAN.md): build phases, shipped scope, and deferred work
- [Decisions](docs/DECISIONS.md): key architectural and product decisions
- [Setup Spec](docs/spec.md): implementation-facing product contract
- [Deployment Guide](docs/DEPLOY.md): step-by-step VPS deployment instructions
- [Audit Review Report](docs/audit/REVIEW_REPORT.md): audit cycle findings and follow-up priorities
- [Task Graph](docs/tasks.md): playbook-compatible execution backlog

## Setup

Start with the implementation-facing setup and runtime details already in the repo:
- [Product Spec](docs/spec.md)
- [Ops / Security](docs/ops-security.md)

See [docs/DEPLOY.md](docs/DEPLOY.md) for step-by-step VPS deployment instructions.

The repository remains intentionally private-deployment-first. A public SaaS posture is not the current target.
