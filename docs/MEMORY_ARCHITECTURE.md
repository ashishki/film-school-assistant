# Film School Assistant — Memory Architecture

Version: 1.0
Last updated: 2026-04-07
Status: Active

## 1. Purpose

This document defines:
- what memory already exists in `film-school-assistant`
- where the current design is too lossy for creative continuity
- what is practical to adopt from `mempalace`
- the target memory architecture for the next implementation phases

This is the source-of-truth memory document for future implementation tasks.

---

## 2. Current State Assessment

### What Exists Today

The repository already has three real memory shapes:

1. **Structured operational state**
   - `projects`
   - `notes`
   - `ideas`
   - `deadlines`
   - `homework`
   - `review_history`
   - `recurring_reminders` and `practice_completions`
   - `user_context_entries`
   - `transcripts` and `parsed_events`

2. **Bounded summaries**
   - `project_memory.summary_text`
   - `user_context_summary.summary_text`

3. **Prompt injection paths**
   - chat injects project memory and user context summary
   - idea review injects project memory and user context summary
   - `/reflect` requires project memory and also injects user context summary

### What The Current Memory Model Actually Is

Current project continuity is built around one cached project summary per project.
That summary is generated on demand from recent notes, ideas, and active deadlines.

This is useful, but it is not a real recall layer.

The current design is:
- **project-scoped by default** for summary injection
- **bounded and inspectable**
- **cheap and simple**
- **too lossy** for nuance-heavy creative work

### Verified Current Limitations

From the current codebase:

- `src/handlers/memory_cmd.py` generates a single paragraph summary, not structured fields.
- The summary input excludes homework and transcript fragments.
- Cache reuse is driven mainly by `item_count_snapshot`, so edits and some qualitative changes are weakly represented.
- `src/handlers/chat_handler.py`, `src/handlers/review.py`, and `src/handlers/reflect_cmd.py` inject only summary text, not evidence rows.
- `/search` and the chat `search` tool are global across notes and ideas, not project-first by default.
- `review_history` is stored, but `/reflect` extracts only a thin `next_step` list from recent review JSON.
- Raw transcript storage exists, but transcript recall is not part of the memory model.

### What Is Stale In The Docs

Several repository docs still describe creative memory as future work, even though partial memory primitives already exist:
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/spec.md`

The planning docs also over-focus on improving the paragraph summary instead of defining a durable evidence memory layer.

### Current Pain Points

1. **Project memory is too lossy**
   - One paragraph cannot preserve reasoning texture, exact phrasing, or useful transcript fragments.

2. **The source of truth is mixed**
   - Structured records are canonical, but the summary is doing too much continuity work.

3. **There is no explicit verbatim recall tier**
   - Notes and transcripts exist, but there is no unified project-first recall layer with provenance.

4. **Retrieval boundaries are underdefined**
   - Chat memory injection is project-first, but search behavior is broader and not clearly separated by scope.

5. **Debuggability is weaker than it should be**
   - It is easy to inspect the summary row, but not easy to inspect why a specific memory would or would not be recalled.

---

## 3. Critical MemPalace Extraction

This section separates verified implementation facts from intended architecture and from claims that should not drive this repository.

### Verified Implementation Facts In `mempalace`

From the checked repository state on 2026-04-07:

- It stores verbatim chunks in local `ChromaDB` collections.
- Each chunk has metadata such as `wing`, `room`, `source_file`, and `chunk_index`.
- `searcher.py` performs semantic search over stored verbatim chunks and can filter by `wing` and `room`.
- `miner.py` ingests project files and chunks them by text boundaries.
- `convo_miner.py` ingests conversations and chunks them by exchange pair or paragraph.
- `knowledge_graph.py` stores temporal triples in local SQLite.
- `mcp_server.py` exposes read/write tools for search, taxonomy inspection, graph traversal, duplicate checks, and direct drawer writes.
- `layers.py` defines a layered loading model: identity, essential story, on-demand retrieval, and deep search.
- Room detection and memory classification are mostly heuristic, not magical.

### Likely Intended Architecture

The practical underlying architecture appears to be:
- verbatim storage first
- vector retrieval over verbatim chunks
- optional structured overlays
- explicit scope metadata (`wing`, `room`)
- AI integration through MCP rather than direct app-specific orchestration

### Unclear Or Unproven Claims

These claims should be treated carefully:
- AAAK as "lossless" compression
- benchmark claims as direct proof of real product usefulness in this repo
- structure-only retrieval improvements being portable to a very different product
- contradiction detection as a mature production capability

Some benchmark runners exist, but the product value for `film-school-assistant` cannot be inferred from benchmark numbers alone.

### What Is Actually Useful For This Repo

Useful ideas:
- keep verbatim evidence, not only summaries
- keep scope explicit and narrow before widening
- separate always-loaded summary context from on-demand recall
- preserve source metadata and timestamps
- keep storage local and debuggable

Useful only in lighter custom form:
- layered memory model
- topic grouping
- explicit retrieval API surface

Not useful here:
- palace / wing / hall / tunnel naming
- generic knowledge-graph ambitions
- ChromaDB-first architecture
- broad MCP memory platform scope
- benchmark-driven architecture inflation

---

## 4. What Should Live In Each Memory Tier

### Structured State

Structured state should remain the canonical source of truth for:
- projects
- notes
- ideas
- deadlines
- homework
- recurring practices and completions
- feature feedback
- user context entries
- review history metadata

Rule:
- if the system needs CRUD, status transitions, reminders, or stable IDs, it belongs in structured state

### Bounded Summary

Bounded summaries should exist only for fast working context:
- `project_state_summary`
- `user_profile_summary`

Rule:
- summaries are for orientation and prompt efficiency
- summaries are not source of truth
- summaries must be regenerable from canonical state plus selected evidence memory

### Verbatim Searchable Memory

Verbatim searchable memory should hold recallable evidence such as:
- important note text
- idea text
- transcript fragments tied to saved notes or ideas
- selected reflection or review excerpts when they carry durable project value
- user-context entries worth recall at user scope

Rule:
- verbatim memory exists so the assistant can recover nuance and exact language when needed
- every recalled memory must retain provenance

### What Should Not Be Stored

Do not store:
- generic chat that produced no project state or durable user context
- every assistant reply by default
- duplicate copies of the same note without a retrieval purpose
- speculative inferred personality facts
- cross-project aggregates created automatically without an explicit reason

---

## 5. Target Memory Architecture

### Design Goals

- project continuity first
- narrow retrieval before broad retrieval
- local-first and inspectable
- deterministic boundaries around storage and retrieval
- enough recall to preserve nuance without building a generic memory platform

### Tier Model

#### Tier A — Structured State

Canonical rows already in SQLite:
- projects
- notes
- ideas
- deadlines
- homework
- user context entries
- review history
- transcripts

This tier remains authoritative.

#### Tier B — Summary Layer

Two summary artifacts:
- `project_state_summary`
- `user_profile_summary`

Recommended evolution:
- keep one row per scope
- move from count-only staleness toward revision-aware or source-aware refresh
- keep summaries short and operationally useful

#### Tier C — Evidence Memory

Add a dedicated evidence-memory layer for recall.

Recommended core shape:
- `memory_items`
- optional SQLite FTS table over `memory_items.content_text`

Recommended fields:
- `id`
- `scope_type` (`project`, `user`)
- `scope_id`
- `source_kind` (`note`, `idea`, `homework`, `transcript_fragment`, `review_excerpt`, `user_context`)
- `source_id`
- `project_id` nullable for user-scope items
- `content_text`
- `source_created_at`
- `created_at`
- `importance`
- `status`
- `provenance_json` or equivalent explicit source metadata

Rule:
- `memory_items` are a recall index, not the primary source of truth
- provenance must point back to the canonical source row

### Retrieval Flow

Default retrieval policy:

1. Determine active scope.
   - If there is an active project, retrieval starts in that project only.
   - User-profile memory remains separate.

2. Load bounded summary first.
   - Inject short project summary and user summary when relevant.

3. Retrieve evidence only when the task needs it.
   - reflection
   - project re-entry
   - note recall
   - transcript recall
   - "what did I say/decide earlier?" queries

4. Evidence retrieval is project-first.
   - query only `memory_items` for the active project unless the user explicitly asks wider.

5. Cross-project retrieval is explicit.
   - allowed only when the user asks to compare or search broadly
   - responses must label the project/source clearly

6. Returned memory must preserve provenance.
   - source kind
   - source id
   - project name when relevant
   - timestamp when known

### Summary Refresh Rules

Summary refresh should be deterministic.

Recommended rules:
- refresh on explicit `/memory`
- refresh when underlying source revision changed materially
- refresh when summary is older than a configured age threshold
- do not silently regenerate inside every chat request

The summary input should come from:
- current structured project state
- a bounded set of recent/high-value `memory_items`
- not from arbitrary global search

### Scope Boundaries

#### Project Scope

Project scope should contain:
- project notes
- project ideas
- project homework
- project deadlines
- project transcript fragments
- project review excerpts when useful

This is the default memory scope for continuity work.

#### User Scope

User scope should contain:
- stable personal context
- working preferences
- creative habits
- recurring constraints or blockers

This scope should never silently absorb project-specific material.

#### Cross-Project Scope

Cross-project recall is allowed only as an explicit action.

Examples:
- compare themes across two named projects
- search all projects for a recurring topic
- find where a specific idea appeared before

Default chat and reflection flows should not do this automatically.

### Provenance Rules

Every recallable memory should expose:
- source type
- source record ID
- originating project or user scope
- source timestamp when available
- whether the text is verbatim or excerpted

This is mandatory for debugging and trust.

### Privacy And Local-First Assumptions

- SQLite remains the system of record.
- No cloud vector store is justified.
- Retrieval must work from local storage only.
- Audio remains local; transcript fragments may be indexed, but raw audio must not leave the host.

### Observability Requirements

The memory system should log:
- summary refresh reason
- retrieval scope used
- number of memory items considered and returned
- whether a result came from summary only or evidence retrieval

The system should also make it easy to inspect:
- why a summary is stale
- which source rows produced a recalled memory
- when cross-project retrieval was invoked

---

## 6. What To Adopt, Redesign, Reject, Or Defer From MemPalace

| Candidate idea | Decision | Why |
|---|---|---|
| Verbatim-first recall | Adopt | High leverage for creative nuance; fixes summary lossiness directly. |
| Layered memory | Adopt in lighter custom form | Useful, but only three practical tiers are needed here. |
| Project-first retrieval | Adopt | Matches this product's continuity model and privacy expectations. |
| Source provenance on recall | Adopt | Essential for trust and debugging. |
| Local-first storage | Adopt | Already aligned with this repo's deployment model. |
| Topic grouping | Adopt in lighter custom form | Useful as labels or retrieval hints, but not as a full palace taxonomy. |
| MCP memory surface | Defer | Helpful only if this repo later exposes memory to external agent clients. |
| AAAK compression | Reject | No evidence it is needed here; adds a custom dialect with poor ROI. |
| Palace / wing / hall / tunnel metaphor | Reject | Branding abstraction, not an engineering need for this repo. |
| ChromaDB-first retrieval stack | Reject | Too much operational complexity for a single-user SQLite app. |
| Generic temporal knowledge graph | Reject | Overbuilt for the current product and data model. |
| Broad auto-ingest of all chats | Reject | Violates scope discipline and would store too much low-value material. |
| Explicit cross-project comparison | Defer | Valuable later, but only after project-first recall works cleanly. |
| Contradiction detection layer | Defer | Potentially useful later, but not necessary for MVP continuity. |

---

## 7. Recommended Implementation Sequence

### Phase 7 — Architecture Alignment

Done in documentation first:
- align source-of-truth docs
- define memory tiers
- define scope boundaries
- define migration strategy

### Phase 8 — MVP Evidence Memory Foundation

Build next:
- `memory_items` schema and migration
- ingestion from existing project/user records
- project-first retrieval helper
- provenance-first recall formatting
- `project_state_summary` refresh rules updated to use better staleness signals

### Phase 9 — Continuity Surfaces

Then build:
- re-entry snippet after a gap
- explicit evidence retrieval in `/reflect`
- optional `/recall` or equivalent bounded evidence command
- better prompt injection rules that distinguish summary from evidence

### Phase 10 — Explicit Cross-Project Recall

Only after the above works:
- explicit compare/search across named projects
- strict labeling of project provenance
- evaluation for false-linking risk

---

## 8. Migration Principles

- Reuse current tables wherever they are already canonical.
- Do not replace notes/ideas with a generic memory object.
- Add a dedicated evidence-memory layer only where it simplifies recall and provenance.
- Keep migration incremental and inspectable.
- Prefer deterministic ingestion over magical memory extraction.

---

## 9. Architectural Verdict

`film-school-assistant` should not become a generic memory engine.

It should become:
- a project-first creative assistant
- with explicit structured state
- short bounded summaries
- and a small verbatim evidence layer for recall when nuance matters

That is the minimum architecture that closes the real continuity gap without importing MemPalace's extra metaphors or platform ambition.
