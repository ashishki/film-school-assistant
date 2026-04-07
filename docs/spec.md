# Film School Assistant — Product Spec

Version: 3.2
Last updated: 2026-04-07
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
- deterministic deadline reminders and recurring daily-practice reminders
- weekly summary
- structured feature-feedback capture when the assistant cannot satisfy a user request
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
- NL capture triggers on a broad set of natural phrasings (not only explicit command words) including «хочу записать», «не забыть», «мысль», «нужно зафиксировать»
- entity type is inferred from context using an extraction prompt that includes type descriptions and examples — the user is not required to name the type
- when a single message contains multiple entities, the total is announced upfront and each entity is confirmed individually in sequence with a remaining-count indicator
- when a message contains both a practice intent and NL save content, both are handled without dropping either

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
- recurring daily-practice scheduling and deduplication remain deterministic

### FR-5 Bounded AI assistance

LLM behavior is allowed only where interpretation or reflection is needed.

Acceptance:
- free-text capture can use bounded extraction
- bounded conversational tool use stays inside explicit tool limits
- feature-feedback clarification may use a bounded multi-step LLM flow with explicit question limits
- idea review uses a stronger model only on explicit review request

### FR-7 Feature feedback capture

When the assistant cannot satisfy a request with current capabilities, it may offer to convert that gap into developer feedback.

Acceptance:
- the user must explicitly accept the capture flow after the assistant says it cannot do the requested action
- the clarification flow must be bounded to a small number of questions
- the final result may be saved both as raw feedback and as a structured feature brief
- the flow must not promise that the requested feature will be implemented

### FR-8 Recurring daily practices

The assistant must support recurring daily creative practices such as morning pages and end-of-day reflection prompts.

Acceptance:
- recurring practices may be configured by command or by natural language in text and voice
- if the user requests a recurring practice without explicit times, the assistant asks for times instead of silently assuming them
- delivery must deduplicate by reminder kind and calendar day
- users can list, pause, and resume recurring practices
- when no timezone is given during setup or correction, the timezone is inherited from the existing practice for that kind instead of falling back to a system default
- `/practices` must show the next scheduled fire time per practice in the user's local timezone
- practice completions are tracked in `practice_completions`; streak and weekly count are shown in `/practices` and the weekly summary
- reminder messages must include an inline pause button so the user can pause without typing a command

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
- recurring daily-practice prompts
- structured developer-feedback capture

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
- recurring-practice scheduling and deduplication
- weekly report state
- project archive state
- delivery rules

### LLM-owned, bounded

- NL extraction for messy input
- bounded chat tool selection
- feature-gap clarification and brief assembly
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

The next implementation phase must add a small evidence-memory layer for project-first recall before expanding continuity UX further.

That means:
- preserve structured state as source of truth
- keep bounded summaries for fast working context
- add recallable evidence with provenance
- keep retrieval project-first by default

It does not mean:
- jump straight to a web app
- add speculative team features
- turn the repo into a generic memory platform
- add embeddings or external retrieval infrastructure without a documented need

## 10. Phase 1 UX Behavioral Requirements

These requirements are implementation-explicit for Phase 1. They supplement the functional requirements above by defining expected output behavior at specific interaction moments. They are the behavioral contract that acceptance tests in Phase 1 tasks refer to.

### UXR-1 — Confirmation Flow Language

When a capture action produces a confirmation reply, the reply must:
- name the entity type saved (note, idea, deadline, homework)
- include the project name when a project is associated
- avoid generic AI praise phrases (great, got it, awesome, perfect, etc.)
- stay under three lines
- not append a help command list

When no project is associated, the reply must:
- confirm the save without a placeholder or error about missing project context
- not prompt the user to set a project unless they explicitly asked how

### UXR-2 — Active Project Orientation

When the assistant performs a save or edit action for an entity with project association:
- the project name must appear in the reply
- the project name must come before or alongside the entity description, not as an afterthought at the end

When the assistant has no project context for an entity:
- the reply must not prompt the user to set a project unless they raised the question

### UXR-3 — Weekly Digest Framing

The weekly digest must:
- open with a brief project-state framing sentence derived from actual stored state (not a generic "here is your weekly summary" header)
- group items by project or type where volume justifies grouping
- include a directional next-step pointer per active project when records for that project exist
- not increase in total length relative to the current implementation

The framing sentence is a bounded LLM output anchored to stored state. The rest of the digest is deterministic.

The digest must not:
- open with motivational or generic AI language
- summarize the same items more than once
- invent activity not supported by stored records

### UXR-4 — Review Completion Framing

When an idea review completes:
- the reply must end with a one-sentence next-step pointer if stored project data supports one
- the next-step pointer is a bounded LLM output constrained to one sentence
- the reply must not end with a generic "let me know how you want to proceed" fallback

### UXR-5 — Reply Length Discipline

Across all Phase 1 changes:
- no reply should be longer after changes than before, except where the added content is the project name that was previously absent
- confirmations, digests, and review completions must not accumulate decorative language
- longer is not better; grounded and brief is better

## 11. Memory Behavioral Requirements

These requirements define the intended layered memory model.

### MR-1 — Memory Tier Contract

The product has three memory tiers:
- **structured state**: canonical operational records such as projects, notes, ideas, deadlines, homework, user context entries, and review history metadata
- **bounded summaries**: short project and user summaries used for orientation and prompt efficiency
- **evidence memory**: recallable verbatim or excerpted items with source provenance

Structured state is the source of truth.
Summaries and evidence memory must never replace canonical records.

### MR-2 — Project Summary Contract

Project summary storage must remain one row per project and must contain:
- `summary_text`
- `generated_at`
- a deterministic freshness signal
- `model_used`

Project summaries must:
- be grounded only in stored project data
- remain bounded and inspectable
- be refreshable from canonical state plus selected evidence

Project summaries must not:
- act as the only record of project facts
- silently absorb data from other projects

### MR-3 — Evidence Memory Contract

Evidence memory rows must preserve:
- scope (`project` or `user`)
- source kind
- source record ID
- text content or excerpt
- timestamp when available
- provenance sufficient to inspect the original source

Evidence memory must:
- default to project scope when an active project exists
- support explicit user-scope recall separately
- preserve verbatim wording when nuance matters

Evidence memory must not:
- become a dumping ground for all chat
- store speculative inferred facts as if they were records

### MR-4 — Retrieval Rules

Default retrieval behavior:
- active project first
- user profile memory separate
- cross-project retrieval only on explicit request

When the chat handler or another assistant path needs orientation:
- inject bounded summary first
- retrieve evidence only when the task requires deeper recall
- fall back safely if the memory read fails

Any recalled evidence returned to the user or passed into prompts must retain source labeling.

### MR-5 — Summary Refresh Rules

Summary refresh remains deterministic.

The system may refresh a project summary when:
- the user explicitly runs `/memory`
- the summary is stale by age
- relevant source material changed materially

The system must not:
- regenerate summaries implicitly on every chat turn
- rely only on item count as the long-term freshness signal

### MR-6 — Memory Anti-Goals

The memory layer must not:
- retrieve across multiple projects by default
- introduce decorative memory metaphors into the app architecture
- become a giant universal memory engine
- fabricate project state not derivable from stored records

## 12. Phase 3 Reflection Behavioral Requirements

### RR-1 — Enhanced Review Context Injection

When an idea belongs to a project with stored memory:
- the review prompt must include a labeled project context block before the idea
- the block format: `Контекст проекта: {summary_text}`
- the LLM must use this context to make the critique project-specific, not generic
- when no memory exists, the review prompt is identical to the Phase 1/2 baseline

### RR-2 — /reflect Output Contract

The /reflect command must produce a structured response with three sections:
- **Состояние проекта** — one paragraph describing where the project currently stands based on stored records
- **Творческие напряжения** — identified tensions or unresolved questions from ideas and reviews (concrete, not generic)
- **Фокус** — one concrete recommended action for the next work session, grounded in stored state

The output must not:
- invent facts not present in the input data
- give generic advice ("explore your themes", "trust your instincts")
- exceed the scope of the stored records

### RR-3 — Reflection Anti-Goals

- /reflect must not run without project memory (require /memory first)
- reflection output must not be longer than a focused short message (3 sections, no padding)
- no persistent agent role or follow-up scheduling from reflection output

The memory layer must not:
- use embeddings or vector similarity at any point
- retrieve records from multiple projects simultaneously
- autonomously update memory without an explicit trigger
- fabricate project state not derivable from stored records

## 13. Phase 4 Deployment and Onboarding Requirements

### DR-1 — Deployment Package

The repository must include:
- a `.env.example` file listing all required environment variables with placeholder values and a one-line comment per key
- a `docs/DEPLOY.md` covering: prerequisites, clone, venv setup, .env configuration, schema init, systemd unit install, smoke test
- a corrected `systemd/film-school-bot.service` where `ExecStart` uses the venv Python binary, not system Python

The deployment package must not:
- contain real secrets, personal paths, or user-specific configuration
- require Docker or any container runtime

### DR-2 — Onboarding Flow

The `/start` command reply must:
- contain no emoji
- describe what the assistant does in one or two sentences without generic AI praise
- end with a concrete first-step hint pointing to `/new_project <название>`
- stay under 10 lines

The `/start` reply must not:
- use LLM-generated content
- be longer than the current reply (exception: adding the first-step hint)
- repeat the full command list (that belongs in /help)

## 14. Phase 5 NL Interaction Quality Requirements

### NR-1 — Multi-entity Extraction

When a single user message contains more than one distinct entity (e.g. a deadline and a note):
- the extraction schema returns `{"entities": [...]}` where each item has `entity_type`, `content`, `project_hint`, `due_date`
- the first entity is presented as the current pending entity
- remaining entities are stored in `state.pending_entities` (queue)
- after the user confirms the current entity, the next queued entity is auto-presented
- single-entity messages behave identically to the pre-Phase-5 baseline
- the queue is cleared when the user discards or the last entity is confirmed

### NR-2 — Clarifying Questions on Parse Failure

When NL extraction fails, the reply must be a targeted clarifying question, not a generic error:
- on LLMError or non-dict response: ask the user to rephrase as a question (under two lines)
- on empty content extraction: ask what exactly to save
- no failure branch may show the full command list as the primary response
- no branch may use the old generic 4-line "Не совсем понял" message

### NR-3 — Уточнить Button

The pending entity keyboard must have three buttons: "✅ Сохранить", "❌ Удалить", "✏️ Уточнить".

When the user taps "✏️ Уточнить":
- the bot replies asking the user to write a corrected version of their message
- `state.pending_clarify` is set to True
- the next free-text message clears the current pending entity and re-runs NL extraction on the new text
- no fields from the discarded pending entity are preserved into the re-extraction

### NR-4 — NL Context Window

The nl_handler must maintain a rolling context of the last 5 raw user messages (`state.nl_context`):
- `nl_context` is appended after each NL extraction attempt (success or failure)
- `nl_context` is not cleared by `clear_pending` (survives across confirms and discards)
- when `nl_context` is non-empty, the extraction prompt includes a labeled context block before the current message
- when `nl_context` is empty, the extraction prompt is identical to the pre-Phase-5 baseline
- the context window must not be persisted to DB
