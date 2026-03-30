# Film School Assistant — Workflow Boundaries

## 1. Purpose

This document defines what the assistant should do deterministically, where LLM use is justified, where human approval is mandatory, and how the project avoids complexity drift.

This is the operational boundary document for future development.

## 2. Deterministic Ownership

The following remain deterministic unless architecture is explicitly revised:
- authorization
- persistence and schema rules
- entity IDs, timestamps, and status transitions
- project assignment after deterministic resolution
- reminders, reminder buckets, and deduplication
- weekly digest triggering and send-state rules
- search, list, edit, archive, and filter logic
- Telegram delivery rules and retry behavior
- local voice file handling and transcription execution

Reason:
- these are formalizable behaviors
- they affect integrity, reliability, and auditability
- turning them into LLM behavior would be architecture drift, not product progress

## 3. Justified LLM Ownership

LLM usage is justified only in bounded cases:
- extracting structure from messy natural-language input
- selecting from an explicit tool set in chat
- generating reflective idea critique
- later, generating bounded continuity summaries from already-structured state

Reason:
- these tasks involve ambiguity, interpretation, or helpful language synthesis
- the system benefits from flexibility here
- failure can be contained by bounded interfaces and human review points

## 4. Human Approval Gates

Human approval is required for:
- new phases that expand product surface
- changes to solution shape, governance, or runtime tier
- any move toward multi-user or web-primary product direction
- any semantic memory design that changes storage or retrieval assumptions
- destructive actions that exceed current confirmation conventions
- any new feature whose failure would silently rewrite or misrepresent user state

## 5. What Should Not Be Delegated to Agents

Do not delegate these to agents as open-ended behavior:
- product direction changes
- roadmap authority
- runtime or infrastructure mutation
- implicit prioritization across phases
- destructive bulk edits to user data
- changes to architectural constraints without artifact updates

Agents can assist implementation inside approved file/task scope.
They do not own product direction.

## 6. Accidental Complexity Drift Patterns

The project should actively reject these patterns:
- adding a web app because Telegram feels too small
- adding vector search because "memory" sounds incomplete
- adding multi-user logic because it looks more productized
- adding open-ended planning agents because the system already has some tool use
- describing future ambition as if it were already implemented

## 7. Lowest-Justified Runtime Rule

The project stays at `T1` unless there is a concrete need for:
- mutable isolated workers
- shell or workspace mutation by the assistant
- higher privilege boundaries
- more complex rollback or runtime isolation

None of those needs are currently present.

## 8. Minimum Sufficient Solution Rule

Before any new feature is approved, the Strategist must classify it as one of:
- deterministic subsystem
- workflow feature
- bounded agent behavior
- deferred higher-autonomy behavior

If the feature cannot be classified clearly, it is not ready to enter implementation.

## 9. Review Rule

Every phase must remain reviewable.

That means new work needs:
- explicit artifacts
- explicit scope
- explicit acceptance criteria
- explicit evidence requirements

If a proposed feature cannot be tested, reviewed, or bounded, it should be deferred or reshaped.
