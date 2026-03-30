# Film School Assistant — Key Decisions

## 1. Telegram-first now

### Decision

The product remains Telegram-first in the current phase.

### Why this is valid

- capture is the highest-frequency workflow
- Telegram is already operational
- it keeps the interaction loop lightweight
- it avoids unnecessary packaging work before the product is sharper

### When this should change

Consider an added surface only if:
- continuity and memory become hard to inspect in chat alone
- project review needs a stronger browse/edit surface
- the product proves value beyond quick capture

Telegram remains the current primary interface, but not the long-term identity.

## 2. SQLite now

### Decision

SQLite remains the system of record.

### Why this is valid

- the product is single-user
- the operational scale is small
- deployment simplicity matters
- it keeps the memory model inspectable and bounded

### When this should change

Change only if:
- concurrency requirements materially grow
- storage patterns become more complex than SQLite reasonably supports
- product evidence requires a different persistence shape

No such pressure exists now.

## 3. Private VPS now

### Decision

The assistant remains private-deployment-first on a VPS.

### Why this is valid

- it matches the current user model
- it keeps privacy and operational control straightforward
- it avoids premature productization work

### When this should change

Change only if:
- packaging becomes a real adoption blocker
- there is evidence for broader use
- operational simplicity improves with a different deployment model

## 4. Single-user now

### Decision

The product remains single-user by design.

### Why this is valid

- the product’s strongest use case is individual continuity
- team and tenant complexity would distort the roadmap
- current architecture and docs are correctly optimized for one user

### When this should change

Only after clear product evidence shows value that depends on collaboration.

## 5. No web layer yet

### Decision

A web layer is a later-phase option, not a current necessity.

### Why this is valid

- the current highest-value interactions are capture and reminders
- a weakly differentiated web shell would add packaging, not product value
- the product still needs stronger continuity and memory before another surface is justified

## 6. Creative memory next, not general RAG

### Decision

The next substantial capability should be a bounded creative memory layer.

### Why this is valid

- continuity is the real product gap
- the product already has structured state to build on
- generic retrieval infrastructure would be an implementation-first move instead of a product-first move

### What this rules out for now

- vector DB by default
- semantic search platform work before memory artifacts exist
- open-ended long-context claims

## 7. Governance level is Standard

### Decision

Governance remains `Standard`.

### Why this is valid

- the project is operational and AI-assisted
- it benefits from phase gates and artifact discipline
- it does not justify Strict controls

## 8. Runtime tier is T1

### Decision

Runtime remains `T1`.

### Why this is valid

- the assistant is a bounded service on a VPS
- no model-driven runtime mutation exists
- no higher isolation tier is currently justified

## 9. Source-of-truth artifacts

The following documents are source-of-truth for implementation planning:
- `docs/PRODUCT_OVERVIEW.md`
- `docs/USER_EXPERIENCE.md`
- `docs/ARCHITECTURE.md`
- `docs/WORKFLOW_BOUNDARIES.md`
- `docs/spec.md`
- `docs/PHASE_PLAN.md`
- `docs/tasks.md`
- `docs/IMPLEMENTATION_CONTRACT.md`
- `docs/CODEX_PROMPT.md`

Implementation should not proceed against informal chat intent when these artifacts disagree.
