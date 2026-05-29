# Current Backlog

**Status:** Paused product; portfolio case maintenance only
**Last updated:** 2026-05-29

The historical Phase 0-11 roadmap is complete and archived at
`docs/archive/roadmaps/tasks-phases-0-11.md`.

## Current State

Implemented:

- Telegram-first capture by text and voice
- confirmation queue for notes, ideas, homework, deadlines, and user context
- local Whisper transcription
- project-aware storage and project memory
- evidence memory through `memory_items`
- project-first recall/search with explicit cross-project access
- `/memory`, `/recall`, `/reflect`, `/search`, `/review`, `/get`, `/list`, edit flows
- natural chat access to recall and reflection tools
- recurring daily practices and deadline reminders
- feature-feedback capture
- private VPS deployment through `systemd`

## Active Maintenance Queue

| ID | Priority | Task | Notes |
|---|---:|---|---|
| DOC-1 | P1 | Keep README and docs map aligned with runtime behavior | Update after feature or deployment changes |
| OPS-1 | P1 | Run live production smoke after docs cleanup | Confirm bot service, DB path, reminders, and summary scripts still match docs |
| CASE-1 | P1 | Reframe README as a creative-professions case study | Show the real workflow: capture, memory, reflection, reminders, evidence |
| CASE-2 | P1 | Add sanitized creative workflow examples | Use fictional or redacted examples only; no private memory dump |
| PAUSE-1 | P1 | Record pause state and resume criteria | Resume only if real users or operator usage justifies it |
| QUAL-1 | P2 | Add end-to-end smoke coverage for natural recall and reflection paths | Existing tests mostly cover DB and helpers |
| QUAL-2 | P2 | Review stale audit findings and convert still-relevant items into current backlog tasks | Use archived audit reports only as input |
| MEM-1 | P2 | Verify `memory_items` dedup behavior against real user-context and project evidence | Decide whether DB-level uniqueness is needed |
| UX-1 | P2 | Revisit weekly summary wording against current creative workflow goals | Keep it useful, not dashboard-like |

## Parking Lot

- Web or desktop surface.
- Multi-user support.
- External calendar sync.
- Vector search or broad RAG layer.
- More detailed feature-feedback dashboard.

## Resume Criteria

Do not restart feature development until one of these is true:

- a real creative user relies on the assistant weekly;
- the README/case study needs a small demo artifact for interviews;
- a production bug affects the private operator workflow.
