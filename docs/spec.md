# Film School Assistant — Product Spec

Version: 3.0
Last updated: 2026-03-30
Status: Active

## 1. Product Goal

Provide a private AI assistant that helps a director or film student think more clearly, keep continuity across projects, and reduce chaos in everyday creative work.

The current implementation surface is Telegram-first. The product goal is continuity and structure, not chat novelty.

## 2. Primary User

One authorized user:
- a film student
- an early-career director
- a solo creative thinker managing multiple active threads of work

No team roles, admin roles, or shared workspace roles exist in scope.

## 3. Current Product Scope

The current product must support:
- quick capture of notes, ideas, deadlines, and homework
- project-based organization
- text and voice entry
- confirmation-first handling for ambiguous NL capture
- editing, search, listing, and archive flows
- reminders
- weekly summary
- idea review / critique

## 4. Core User Outcomes

The product should help the user:
- capture quickly without losing context
- recover what matters later
- maintain project continuity
- feel less scattered between thinking sessions
- move from stored material toward next action

## 5. Functional Requirements

### FR-1 Single-user private operation

Only the authorized Telegram user may use the assistant.

Acceptance:
- unauthorized updates are rejected before feature handling
- state-changing actions remain behind the same auth guard

### FR-2 Structured capture

The assistant must persist notes, ideas, deadlines, and homework as structured records.

Acceptance:
- records have stable IDs and timestamps
- project association is supported where relevant
- capture works from commands and free text

### FR-3 Local voice handling

Voice notes must be transcribed locally and routed into the same structured workflows.

Acceptance:
- raw audio is not uploaded to external LLM services
- the transcribed result can enter confirmation-first save flow

### FR-4 Deterministic workflow integrity

Persistence, editing, scheduling, reminder windows, archive state, and search remain deterministic.

Acceptance:
- reminder and summary delivery do not depend on model judgment
- CRUD behavior is explicit and testable

### FR-5 Bounded AI assistance

LLM behavior is allowed only where interpretation or reflection is needed.

Acceptance:
- free-text capture can use bounded extraction
- bounded conversational tool use stays inside explicit tool limits
- idea review uses a stronger model only on explicit review request

### FR-6 Continuity support

The product must maintain enough structure that the user can re-enter work without starting from zero.

Acceptance:
- projects act as continuity anchors
- summaries reflect real stored activity
- future phases may deepen continuity, but the current system must not pretend it already has semantic memory

## 6. Product Boundaries

### In scope now

- single-user private assistant
- Telegram-first interaction
- SQLite storage
- bounded LLM use
- local voice transcription
- deterministic reminders and weekly digest

### Out of scope now

- multi-user support
- SaaS packaging
- web app as a required primary surface
- generalized semantic retrieval
- autonomous project planning agents
- collaborative filmmaking workspace

## 7. Deterministic vs LLM Requirements

### Deterministic-owned

- auth
- persistence
- search
- edit flows
- reminder logic
- weekly report state
- project archive state
- delivery rules

### LLM-owned, bounded

- NL extraction for messy input
- bounded chat tool selection
- idea reflection / critique

The default is deterministic unless ambiguity or interpretive output makes LLM use necessary.

## 8. Product Positioning Rules

The documentation and future implementation must not position the system as:
- a generic productivity bot
- a note-taking chatbot
- a thin Telegram wrapper around Claude

It should be positioned as:
- a creative workflow assistant
- a continuity aid for directors and serious creative thinkers
- a small but coherent system, not a feature bundle

## 9. Immediate Product Requirement for the Next Phase

The next build phase after documentation must improve user-visible continuity and assistant feel inside the current Telegram surface before introducing larger architectural expansion.

That means:
- better status framing
- clearer progress feeling
- stronger weekly and project continuity signals
- less mechanical interaction

It does not mean:
- jump straight to a web app
- add speculative team features
- add embeddings only because "memory" sounds modern
