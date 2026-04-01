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

## 11. Phase 2 Memory Behavioral Requirements

These requirements are implementation-explicit for Phase 2. They define expected system behavior for the creative memory layer.

### MR-1 — project_memory Storage Contract

One memory row per project. A memory row contains:
- `summary_text`: bounded LLM output, one paragraph, max 200 tokens
- `generated_at`: UTC ISO timestamp of last generation
- `item_count_snapshot`: count of notes+ideas+deadlines at generation time (used for staleness check)
- `model_used`: model identifier used for generation

The memory row must not:
- contain invented facts not traceable to stored records
- exceed one paragraph in summary_text
- be generated without an LLM call being logged in llm_call_log

### MR-2 — Memory Generation Rules

Memory generation is triggered by `/memory` command only. It is not automatic.

Staleness check: if `item_count_snapshot` equals current count of notes+ideas+deadlines for the project, return cached memory without an LLM call.

If the project has no notes, ideas, or deadlines yet, the command must return a clear message that there is not enough stored material to generate memory, rather than generating a placeholder.

### MR-3 — Memory Injection Rules

When the chat handler is invoked:
- if `user_state.active_project_id` is set and a memory row exists for that project, prepend it to the system prompt as a labeled block: `Контекст проекта: {summary_text}`
- if no active project or no memory row, system prompt is unchanged
- injection must not prevent the chat from working if the DB read fails — fall back to base prompt silently

The injected context is read-only. The LLM may not update or delete the memory row through tool calls.

### MR-4 — Memory Anti-Goals

The memory layer must not:
- use embeddings or vector similarity at any point
- retrieve records from multiple projects simultaneously
- autonomously update memory without an explicit trigger
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
