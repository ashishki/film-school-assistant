# Film School Assistant — Architecture

Version: 2.0
Last updated: 2026-03-30
Status: Retrofit to current AI Workflow Playbook

---

## 1. System Overview

Film School Assistant is a private single-user Telegram assistant for planning coursework,
capturing ideas, transcribing voice notes, generating review feedback, and sending reminders
and weekly summaries. It runs on a single VPS, persists state in SQLite, keeps voice
transcription local via Whisper, and uses Anthropic models only for bounded language tasks.

The system is intentionally narrow:
- one authorized Telegram user
- one local SQLite database
- one bounded tool-using chat path
- no multi-tenant boundary
- no RAG or external knowledge base

---

## 2. Solution Shape

### Primary Shape

**Hybrid decomposition**

- **Deterministic subsystem** for auth, persistence, deduplication, scheduling, reminders,
  report state, validation, and Telegram delivery
- **Bounded ReAct / tool-using assistant** for conversational intent resolution and
  controlled tool selection inside the chat handler
- **Workflow orchestration** for cron-like reminder and weekly summary execution via systemd

This project does not require a higher-autonomy agent. It has one bounded loop for chat
tool use, explicit tool catalog limits, and no open-ended planning, delegation, or mutable
runtime behavior.

### Rejected Lower-Complexity Options

- **Why not fully deterministic?**
  Natural-language task entry, idea critique, and conversational clarification are not
  reliable as fixed rules alone.
- **Why not pure workflow only?**
  User chat requests vary enough that a fixed intent tree would be brittle and costly to
  maintain.
- **Why not a freer agent?**
  The assistant does not need long-horizon planning, autonomous retries across subsystems,
  runtime mutation, or delegated work.
- **Why not RAG?**
  The system operates on current user data already stored in SQLite and local files. There
  is no document corpus retrieval problem to solve.

### Governance Level

**Standard**

Rationale:
- single-user and private lowers compliance burden
- reminder/report automation makes it an operational system, not just a prototype
- LLM calls affect user-visible behavior and cost
- deterministic controls, audit trail, and phase review remain justified

### Minimum Viable Control Surface

The smallest justified control set for this project is:
- explicit architecture, tasks, implementation contract, and session state docs
- task-by-task implementation with light review on each task
- phase-boundary strategy + deep review
- strict single-user auth boundary
- deterministic confirmation path for destructive or ambiguous actions
- bounded tool loop and daily model-call limits

---

## 3. Runtime and Isolation Model

### Runtime Tier

**T1 — bounded service runtime**

Rationale:
- the app runs as a normal Python service on a private VPS
- no runtime mutation is performed by the assistant itself
- no shell/package/toolchain modification is delegated to the model
- blast radius is bounded to one service, one DB, one user
- rollback is standard deploy/restart plus DB backup, not snapshot restore

### Isolation Boundary

- one private VPS
- systemd-managed Python bot process
- systemd timers for reminder and weekly summary scripts
- local SQLite database file
- local filesystem for Whisper model and temporary audio files

### Persistence Model

- SQLite is the system of record
- local filesystem stores temporary voice artifacts and Whisper assets
- no persistent remote vector store, cache, or planner state

### Network Model

- inbound: Telegram webhook/polling equivalent via bot API usage
- outbound: Telegram Bot API, Anthropic API
- no general web browsing or arbitrary network egress in model-driven flows

### Secrets Model

- all credentials come from environment variables or host-managed secret files
- no secrets in source control, prompts, or test fixtures

### Rollback / Recovery Model

- service restart via systemd
- SQLite backup / restore
- failed reminder or report runs are retried by operational procedure, not autonomous agent
- no T2/T3 snapshot workflow is required

---

## 4. Human Approval Boundaries

Human approval remains required for:
- changing runtime shape, deployment topology, or privilege level
- enabling multi-user or shared-tenant behavior
- modifying destructive data-handling paths
- approving ambiguous natural-language task entries before they become persisted reminders
- operational actions outside the bounded Telegram product flow

The bot may autonomously:
- parse user intent
- draft review feedback
- call approved internal tools inside the chat loop
- send reminders and weekly summaries once the deterministic schedule exists

---

## 5. Deterministic vs LLM-Owned Subproblems

| Subproblem | Owner | Notes |
|-----------|-------|-------|
| Authorized chat guard | Deterministic | Reject unauthorized users before business logic |
| Task/reminder persistence | Deterministic | SQLite writes, IDs, timestamps, status transitions |
| Reminder scheduling and due checks | Deterministic | Cron/timer driven, no model judgment |
| Weekly summary dedup and send-window checks | Deterministic | One report per intended period |
| Voice transcription | Deterministic/local ML | Whisper runs locally; no LLM reasoning involved |
| Telegram delivery and retry/backoff | Deterministic | Network error handling must stay explicit |
| Chat intent interpretation | LLM-owned, bounded | Haiku-class model maps requests into allowed tool calls |
| Idea critique / review feedback | LLM-owned, bounded | Sonnet-class path for higher-quality textual analysis |

Deterministic default applies whenever the task is already formalizable.

---

## 6. Inference / Model Strategy

| Path / Task | Model Class | Why | Fallback | Budget / Latency Constraint |
|-------------|-------------|-----|----------|------------------------------|
| Conversational tool selection in `chat_handler` | Fast low-cost model (Haiku-class) | Frequent, bounded, low-latency intent resolution | Ask for clarification or fall back to deterministic command handling | Keep per-message cost low; optimize for responsiveness |
| Idea review / critique output | Stronger reasoning model (Sonnet-class) | Higher-quality feedback matters more than lowest cost | Return a simpler template review or defer | Use only on explicit review flows |
| Voice transcription | Local Whisper model | Keeps audio local and avoids LLM cost | Manual text entry | Higher latency acceptable; no external audio upload |

Rules:
- choose the minimum sufficient model per workload, not one model for the whole system
- do not increase model class or cost envelope without updating this section
- compare model pricing/capability data before changes, but record the accepted decision here

---

## 7. Capability Profiles

| Profile | Status | Notes |
|---------|--------|-------|
| RAG | OFF | No retrieval corpus or citation contract required |
| Tool-Use | ON | Chat path can call approved internal tools through a bounded tool catalog |
| Agentic | ON | One bounded tool loop exists; no higher-autonomy delegation |
| Planning | OFF | No plan schema or planner role |
| Compliance | OFF | Private personal assistant; no regulated-data framework in scope |

---

## 8. Component Model

| Component | Responsibility |
|-----------|----------------|
| `src/bot.py` | Telegram entry point, command routing, auth guard hookup |
| `src/handlers/chat_handler.py` | Bounded LLM chat loop and tool-call orchestration |
| `src/tools.py` | Tool catalog, schema definitions, executor bridge |
| `src/db.py` and related state modules | SQLite persistence and query helpers |
| `src/handlers/*` | Explicit feature handlers for reminders, ideas, deadlines, and reports |
| `scripts/send_reminders.py` | Deterministic reminder delivery workflow |
| `scripts/send_weekly_summary.py` | Deterministic weekly report workflow |
| `scripts/test_voice_pipeline.py` | Voice pipeline verification path |

### Agent Roles

Only one runtime agent-like role exists:

| Role | Authority Scope | Termination |
|------|------------------|-------------|
| Chat assistant loop | Select from declared tools and produce user-facing text within the current conversation | Stop on non-tool response, max tool rounds, or explicit failure path |

### Tool Catalog Contract

Every LLM-callable tool must be:
- declared in `src/tools.py`
- side-effect scoped to the single-user assistant domain
- validated before execution
- permission-checked through the existing auth boundary

Destructive or irreversible mutations require explicit confirmation as a separate code path.

### Termination Contract

The chat loop must enforce:
- explicit maximum tool rounds
- deterministic failure path on tool or model errors
- no recursive self-invocation
- no background autonomous continuation

---

## 9. Data Flow

1. Telegram update arrives from the authorized user.
2. `src/bot.py` routes the message to a command handler or `chat_handler`.
3. Deterministic guards validate authorization and message type.
4. For chat flows, the bounded LLM loop may choose from approved tools.
5. Tool execution persists or queries state through SQLite helpers.
6. The response is returned to Telegram.
7. Separately, systemd timers invoke deterministic reminder and weekly-summary scripts.

---

## 10. Security and Operational Boundaries

- single-user auth is the primary access boundary
- Anthropic and Telegram credentials must remain environment-backed only
- local voice processing keeps raw audio off third-party APIs
- no model may execute shell commands or mutate host runtime
- all runtime-changing actions remain human-only operational tasks

---

## 11. Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Bot runtime | Python | Existing project language and operational fit |
| Messaging surface | Telegram Bot API | Primary user interface |
| Persistence | SQLite | Small single-user system of record |
| Voice transcription | Local Whisper | Keeps audio local |
| LLM provider | Anthropic models | Bounded language tasks only |
| Scheduling | systemd services and timers | Simple deterministic automation on one host |

---

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
