# Film School Assistant — Product Spec

Version: 2.0
Last updated: 2026-03-30
Status: Retrofit baseline

---

## 1. Product Goal

Provide a private Telegram assistant that helps one film-school student capture ideas,
manage deadlines and reminders, process voice notes locally, and receive concise AI-aided
review feedback without introducing unnecessary architecture or autonomy.

Success means:
- reminders and deadlines stay reliable
- idea capture stays fast from chat or voice
- review output is useful but bounded
- operational cost and runtime complexity stay proportionate

---

## 2. Primary User

One authorized owner uses the bot for personal productivity. There are no secondary user
roles, tenant boundaries, or public-facing admin surfaces in scope.

---

## 3. Core Workflows

### 3.1 Task and Deadline Capture

The user can create, inspect, and update tasks, deadlines, and reminders from Telegram.
Structured commands should continue to work deterministically. Natural-language inputs may
use the bounded chat/tool path to map the request into approved assistant actions.

### 3.2 Idea Capture and Review

The user can save creative ideas and request critique or review. Review generation may use
a stronger model than routine intent handling, but only on explicit review flows.

### 3.3 Voice Notes

The user can send voice messages that are processed locally through Whisper and converted
into assistant-understandable text without uploading raw audio to a third-party LLM API.

### 3.4 Reminders and Weekly Summary

Systemd timers run deterministic reminder and weekly summary flows. The assistant must avoid
duplicate sends for the same intended interval.

---

## 4. Solution Constraints

- single-user private assistant only
- SQLite remains the system of record
- local Whisper remains the voice-transcription path
- Anthropic usage stays bounded to approved inference paths
- no RAG, vector DB, planner, or higher-autonomy runtime
- runtime stays at T1 unless architecture is explicitly revised

---

## 5. Functional Requirements

### FR-1 Authorized Access

Only the configured Telegram user may use the assistant.

Acceptance:
- unauthorized updates are rejected before feature handlers run
- no sensitive action bypasses the auth guard

### FR-2 Deterministic Reminder and Deadline Management

Reminder creation, storage, due checks, and status changes remain deterministic.

Acceptance:
- persisted reminders have stable IDs and due timestamps
- due reminders can be queried and sent without model involvement
- duplicate reminder sends are prevented by deterministic state transitions

### FR-3 Bounded Conversational Tool Use

Conversational handling may use an LLM to select from approved internal tools, but the loop
must stay bounded and non-autonomous.

Acceptance:
- the tool catalog is finite and explicit
- tool rounds have a hard maximum
- failure exits cleanly without open-ended retries

### FR-4 Local Voice Processing

Voice notes are transcribed locally and routed into the same assistant workflows as text.

Acceptance:
- raw audio is not sent to third-party LLM APIs
- the voice pipeline remains testable without production secrets

### FR-5 AI Review Output

Idea critique or review flows may call a stronger model when explicitly requested by the user.

Acceptance:
- stronger-model usage is limited to review-specific flows
- review output never bypasses deterministic persistence and auth boundaries

### FR-6 Weekly Summary Integrity

Weekly summary generation must avoid duplicate sends and must remain observable.

Acceptance:
- one summary per intended period unless manually rerun
- send status is recorded or inferable from deterministic state

---

## 6. Deterministic vs LLM Requirements

### Deterministic-Owned

- authorization
- command parsing where commands are already explicit
- persistence, IDs, timestamps, and status transitions
- reminder due checks and weekly summary deduplication
- Telegram send retries/backoff behavior
- voice transcription execution

### LLM-Owned, Bounded

- conversational interpretation for non-command chat requests
- selecting among approved tools during the chat loop
- critique/review wording for idea feedback

The implementation must default to deterministic logic whenever the behavior is already
formalizable.

---

## 7. Runtime and Governance Requirements

- governance level: `Standard`
- runtime tier: `T1`
- no runtime mutation, shell execution, package installation, or privileged host changes
  from model-driven flows
- any expansion into multi-user, privileged automation, or broader autonomy requires an
  architecture update before implementation

---

## 8. Model Strategy Requirements

- use the minimum sufficient model per workload
- low-cost fast model class for routine conversational tool selection
- stronger reasoning model only for explicit review/critique paths
- track AI-path latency and cost in `docs/nfr.md`
- any increase in model class or budget envelope requires an architecture update

---

## 9. Current Hardening Scope

The next project phase should focus on operational hardening, not feature expansion:

1. verify SQLite WAL mode and startup assertions
2. prevent unnecessary summary LLM calls when the weekly report is already sent
3. consolidate Telegram send helper behavior used by scripts
4. keep the voice pipeline testable in CI without heavy runtime side effects
5. record AI-path and operational NFR baselines

---

## 10. Explicit Non-Goals

- multi-user support
- RAG or document retrieval
- higher-autonomy planning agent
- VM/microVM runtime isolation
- compliance-heavy data governance beyond current private-assistant needs
