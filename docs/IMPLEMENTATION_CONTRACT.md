# Film School Assistant — Implementation Contract

Version: 2.0
Last updated: 2026-03-30
Status: Active

This contract is the floor. Implementation may refine the system, but it may not violate
these rules without an explicit architecture update.

---

## 1. Core Invariants

1. The project remains a private single-user Telegram assistant unless architecture is updated first.
2. The authorized Telegram user check must guard all sensitive or state-changing flows.
3. SQLite remains the system of record; do not add a second persistence system casually.
4. Voice audio stays local to the host runtime; do not send raw audio to third-party LLM APIs.
5. Deterministic behavior owns auth, persistence, scheduling, deduplication, retry logic, and policy checks.
6. LLM behavior stays bounded to declared inference paths and approved tools.
7. No model-driven flow may execute shell commands, install packages, or mutate host runtime.
8. Reminder and report automation must remain observable and recoverable by normal operator action.

---

## 2. Solution Shape and Runtime Boundaries

- Declared solution shape: `Hybrid`
- Governance level: `Standard`
- Runtime tier: `T1`

Allowed:
- bounded conversational tool use inside the chat handler
- deterministic systemd-driven reminder and summary workflows
- local Whisper execution

Forbidden without architecture approval:
- higher-autonomy planning or delegation loops
- runtime mutation, shell execution, or package/toolchain changes from model-driven paths
- privileged host operations
- VM or microVM worker introduction
- multi-user expansion

Soft signal:
- if a task moves deterministic-owned behavior into LLM logic, treat it as architecture drift

---

## 3. Control Surface and Runtime Boundaries

This section is proportional to the current runtime tier. It is intentionally light for T1,
but still binding.

### Secrets Scope

- Anthropic, Telegram, and any future credentials come from environment-backed secrets only
- no secrets in source, prompts, docs, or fixtures

### Network Egress

- approved outbound destinations are limited to Telegram APIs and declared AI providers
- arbitrary browsing or open network tool use is out of scope

### Privileged Action Boundaries

- deployment, service configuration, systemd changes, and host-level operations remain human-only
- the bot may only perform product-scope actions already expressed in code and approved tools

### Runtime Mutation Boundaries

- no runtime self-modification
- no package installation or model-driven environment changes
- local files may be read/written only as part of the deterministic product workflow

### Rollback / Recovery Expectations

- failures must be recoverable by service restart, script rerun, or DB restore
- T2/T3 snapshot or VM rollback mechanics are not assumed

### Auditability

- state-changing behavior must be traceable through code paths, logs, or persisted records
- runtime-changing actions are not part of the app control surface

---

## 4. Deterministic-Owned Rules

- authorization must remain explicit and testable
- SQLite writes must remain parameterized and deterministic
- reminder due checks and weekly summary send guards must not depend on LLM output
- retry/backoff behavior for Telegram delivery must stay explicit in code
- calculations, thresholds, and state transitions must remain deterministic

---

## 5. Tool-Use Rules

These rules apply while `Tool-Use = ON`.

- every LLM-callable tool must be declared in the tool catalog
- tool inputs must be validated before execution
- destructive or irreversible actions require a separate confirmation path
- tool use must stay inside the current conversation scope; no background continuation
- permission checks cannot rely only on prompt text or comments

---

## 6. Agentic Rules

These rules apply while `Agentic = ON`.

- the only allowed agentic behavior is the bounded chat tool loop
- the loop must have a hard iteration limit
- errors must terminate into a deterministic fallback, not recursive retries
- the assistant may not create subagents, long-running plans, or delegated workers
- cross-iteration state must remain limited to the declared conversation/persistence structures

---

## 7. Model Strategy Rules

- use the minimum sufficient model class per workload
- routine chat/tool selection stays on the cheaper/faster path
- stronger reasoning models are allowed only on explicit review flows
- model class, cost envelope, or escalation policy changes require doc updates before implementation
- unknown metrics are acceptable; fabricated metrics are not

---

## 8. Testing and Verification Rules

- every behavior change needs a test or an explicit reason it cannot be automated
- new deterministic rules require deterministic tests
- if environment limitations block verification, record the exact blocker in `docs/CODEX_PROMPT.md`
- do not claim CI or local baseline improvements that were not actually re-run

---

## 9. Forbidden Actions

- adding RAG, embeddings, or vector storage without architecture approval
- replacing deterministic scheduling or deduplication with LLM judgment
- expanding runtime to T2/T3 behavior without approval
- storing secrets in repo files
- sending raw voice audio to external LLM APIs
- treating a doc-only retrofit as proof that runtime behavior is already verified
