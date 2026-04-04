# Film School Assistant — Architecture

Version: 3.2
Last updated: 2026-04-04
Status: Active

## 1. System Definition

Film School Assistant is a private, single-user, Telegram-first AI assistant for directors and creative thinkers.

Architecturally, it is not a chatbot with extra commands. It is a small creative workflow system with:
- a capture layer
- a structured memory layer
- a deterministic scheduling layer
- a bounded AI interpretation and reflection layer

Telegram is the current interface surface, not the full product category.

## 2. Product Category

### Now

The product category now is:

**Single-user AI creative workflow assistant for directors, delivered through Telegram**

This definition is intentionally narrower than "creative OS" and broader than "notes bot."

### Later

The later product category, if evidence supports it, is:

**AI continuity assistant for directors and creative project development**

That later category may justify additional surfaces such as a web review layer, but only after the continuity and memory model are strong enough to deserve them.

## 3. Solution Shape

### Primary Shape

**Hybrid decomposition**

- **Deterministic subsystem**
  Owns auth, persistence, schema, scheduling, reminder windows, deduplication, search, editing, archive state, and delivery rules.
- **Bounded LLM layer**
  Owns natural-language intent extraction, tool selection inside the chat loop, and idea review output.
- **Workflow orchestration**
  Owns recurring jobs such as deadline reminders, recurring practice prompts, and weekly digest generation through `systemd`.

This is the minimum sufficient shape. It does not justify planner agents, delegated workers, open-ended memory agents, or runtime mutation.

### Why This Shape Is Correct

- Fully deterministic logic is insufficient for messy creative input and idea critique.
- A fixed workflow alone is insufficient for flexible chat capture and natural-language routing.
- A freer autonomous agent is not justified because the system has narrow scope, one user, low action variety, and clear deterministic boundaries.

## 4. Governance Level

### Current Governance

**Standard**

Why:
- the system is private and single-user, so Strict governance is not justified
- it is already an operational assistant, so Lean governance is too weak
- LLM behavior affects stored state, costs, and user-facing output
- the project benefits from artifact discipline, phase gates, and explicit boundaries

### Human Approval Boundaries

Human approval is required for:
- changing product category or target user
- changing solution shape, governance, or runtime tier
- enabling multi-user behavior
- introducing web app scope beyond the current defined phase
- adding semantic memory beyond the documented bounded design
- changing destructive data flows
- changing deployment topology or secrets handling

## 5. Runtime Tier

### Current Runtime Tier

**T1**

Why:
- the assistant runs as a bounded Python service on a private VPS
- the model does not mutate the runtime, shell, packages, or host
- the blast radius is limited to one bot, one DB, one operator, one user
- operations are recoverable via restart, logs, and DB backup

T0 is too low a description because this is an operational service with ongoing automation.
T2/T3 are unjustified because there is no privileged autonomous execution and no mutable worker runtime.

## 6. System Components

| Component | Current role |
|-----------|--------------|
| `src/bot.py` | Telegram entry point, authorization guard, routing, voice and command flow coordination |
| `src/handlers/nl_handler.py` | Structured entity extraction from free text with confirmation-first save flow |
| `src/handlers/chat_handler.py` | Bounded tool-using assistant loop for conversational queries and actions |
| `src/handlers/feature_feedback.py` | Bounded feature-request capture flow when the assistant cannot satisfy a request |
| `src/practice_intents.py` and `src/handlers/practice_cmd.py` | Deterministic parsing and configuration of recurring daily practices |
| `src/user_context.py` | Personal-context capture, bounded user-profile summary generation, and prompt injection for relevant assistant flows |
| `src/tools.py` | Approved tool catalog for the bounded chat loop |
| `src/reviewer.py` | Structured idea review generation |
| `src/transcriber.py` and `src/voice.py` | Local voice transcription pipeline |
| `src/db.py` and `src/schema.sql` | SQLite persistence and query layer |
| `scripts/send_reminders.py` | Deterministic deadline reminder and recurring-practice delivery job |
| `scripts/send_summary.py` | Deterministic weekly digest job |
| `systemd/*.service`, `systemd/*.timer` | VPS scheduling and service management |

## 7. Deterministic vs LLM Ownership

| Responsibility | Owner | Why |
|---------------|-------|-----|
| Authorization and single-user gate | Deterministic | Security boundary must be explicit |
| Schema, IDs, timestamps, persistence | Deterministic | State must be reliable and testable |
| Reminder logic and due buckets | Deterministic | Time-based logic is formalizable |
| Recurring practice timezone handling | Deterministic | Reminder delivery must follow explicit user timezone settings |
| Weekly summary triggering and dedup | Deterministic | Delivery state must not depend on model judgment |
| Recurring practice scheduling and dedup | Deterministic | Time-based delivery is explicit and testable |
| Search, list, edit, archive | Deterministic | CRUD behavior is formalizable |
| Voice transcription execution | Local ML / deterministic pipeline | Audio stays local and predictable |
| Free-text entity extraction | LLM, bounded | Natural-language inputs are variable |
| User-context profile summarization | LLM, bounded | Compresses saved personal context into a stable working profile |
| Conversational tool selection | LLM, bounded | Flexible requests benefit from tool-choice reasoning |
| Feature-request clarification and brief assembly | LLM, bounded | Used only when the product hits a real capability gap |
| Idea review / reflection output | LLM, bounded | This is interpretive, not transactional |

Rule:
- if behavior can be written as a reliable rule, it stays deterministic
- LLMs are justified only for ambiguity, interpretation, or creative reflection

## 8. Memory Model

### Current Memory Model

The current memory model is structured operational memory, not semantic memory.

What exists now:
- projects
- notes
- ideas
- deadlines
- homework
- saved personal context entries about the user
- one bounded user-profile summary distilled from saved personal context
- raw developer feedback
- structured feature-request briefs
- parsed voice and text capture history
- review history
- weekly report history

What this means:
- the system can store and retrieve structured creative work
- it can summarize recent activity and support continuity at the record level
- it can retain bounded person-level context that improves review, reflection, and assistant guidance without introducing open-ended semantic memory
- it cannot yet maintain higher-order creative continuity across themes, tensions, evolving project intent, or long-range concept development

### Planned Memory Evolution

The next justified memory step is a **creative memory layer**, not generic embeddings-first infrastructure.

That phase should focus on:
- stable project summaries
- evolving creative threads
- continuity notes
- durable "where this project stands now" artifacts

It should not start with:
- open-ended vector architecture
- external retrieval stack
- autonomous long-horizon planning

## 9. Telegram as Interface Layer

Telegram is still the correct primary surface for the current phase because:
- the product’s strongest behavior is fast capture
- voice and text entry are the highest-frequency interactions
- private single-user deployment lowers packaging complexity
- there is no proven need yet for a richer visual workspace

Telegram should be described as the interface layer, not the identity of the product.

## 10. Current Constraints

- single-user only
- Telegram-first only
- private VPS deployment
- SQLite as system of record
- local Whisper transcription
- Anthropic models for bounded language work only
- no web layer required in the current phase
- no multi-user, team, SaaS, or shared workspace scope
- no RAG or external knowledge base

These are valid constraints, not shortcomings to hide.

## 11. Capability Profiles

| Profile | Status | Notes |
|---------|--------|-------|
| RAG | OFF | No retrieval corpus problem is defined yet |
| Tool-Use | ON | The chat loop can select from an explicit internal tool catalog |
| Agentic | ON | Only in the narrow sense of a bounded loop with hard limits |
| Planning | OFF | No runtime planner output governs execution |
| Compliance | OFF | Private personal-use assistant; no regulated-data regime in scope |

## 12. Inference Strategy

| Path | Current model class | Purpose |
|------|---------------------|---------|
| Free-text capture / intent extraction | Haiku-class | Cheap, bounded interpretation |
| Conversational tool use | Haiku-class | Fast routing and tool choice |
| Feature-gap clarification | Haiku-class | Short bounded follow-up questions |
| Feature brief assembly | Sonnet-class | Cleaner short spec when enough facts are known |
| Idea review | Sonnet-class | Better reflective quality where it matters |
| Voice transcription | Local Whisper | Keep audio local |

Model escalation is not justified unless a specific workload proves it needs it.

## 13. Architecture Evolution Path

### Current phase

Stabilize the product definition and experience around the existing foundation.

### Next justified evolution

1. Improve UX continuity and assistant behavior inside the current Telegram surface.
2. Add a bounded creative memory layer that improves continuity without changing runtime class.
3. Add higher-leverage reflection and guidance features that use the new memory artifacts.
4. Only then consider packaging expansion, including an optional web review layer.

### Explicitly Deferred

- multi-user productization
- SaaS platform framing
- collaboration features
- generalized autonomous agents
- vector-first memory architecture without product evidence
- web app as primary product before continuity and memory are strong

## 12. External Integrations

| Integration | Purpose | Credentials |
|-------------|---------|-------------|
| Telegram Bot API | send and receive assistant messages | bot token |
| Anthropic API | bounded chat and review inference | API key |

---

## 13. File Layout

```text
src/
  bot.py
  handlers/
  tools.py
  db.py
scripts/
  send_reminders.py
  send_weekly_summary.py
docs/
  ARCHITECTURE.md
  spec.md
  tasks.md
  CODEX_PROMPT.md
  IMPLEMENTATION_CONTRACT.md
  nfr.md
```

---

## 14. Runtime Contract

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot authentication |
| `TELEGRAM_CHAT_ID` or equivalent authorized user identifier | single-user access boundary |
| `ANTHROPIC_API_KEY` | bounded LLM access |
| local runtime paths / DB path vars as configured | host-specific storage locations |

---

## 15. Observability and NFR Hooks

Operational checks should track:
- reminder send success/failure
- weekly summary dedup and delivery status
- chat/tool-call failures
- AI-path latency and cost envelopes

See `docs/nfr.md` for measurable targets and baselines.

---

## 16. Non-Goals

- multi-user tenancy
- RAG, embeddings, or vector databases
- higher-autonomy planning agents
- VM or microVM isolated agent runtime
- runtime self-modification or package installation by the model
- broad compliance framework beyond basic secret handling and auditability
