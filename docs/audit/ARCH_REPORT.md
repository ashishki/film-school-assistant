---
# ARCH_REPORT — Cycle 1
_Date: 2026-04-01_

---

## Component Verdicts

| Component | Verdict | Note |
|-----------|---------|------|
| `memory_cmd.py` | DRIFT | Generates memory via Haiku-class ("intent" model path); spec MR-1 says "max 200 tokens" but prompt says "200 слов" (words) and API call uses `max_tokens=220` — three-way unit mismatch; no staleness age shown to user (F1); `item_count_snapshot` excludes `review_history` (F3) |
| `reflect_cmd.py` | PASS | Correctly gated on memory prerequisite; uses `complete_json` for structured output; `_format_reflection` enforces three-section shape; uses review-class model path; terminates on LLM error without recursive retry |
| `confirm.py` | DRIFT | Project name resolved from `state.active_project_id` only; entities whose `project_id != active_project_id` display `(без проекта)` even when a valid project exists in DB (G3); UXR-1 contract technically violated in that edge case |
| `chat_handler.py` | DRIFT | Imports and instantiates `AsyncAnthropic` directly rather than using `src.openclaw_client` abstraction used by all other LLM handlers; memory injection logs a warning on DB failure but emits no user-visible indicator (F2); project name absent from tool response strings (G2) |
| `review.py` | DRIFT | `log_llm_call` is invoked before `review_idea` is called; if `review_idea` raises, the daily counter is incremented for a call that never succeeded |
| `reviewer.py` | DRIFT | No secondary hard character/token cap on `summary_text` injected into review prompt (D3); relies solely on upstream 200-word soft cap; `REVIEW_SYSTEM_PROMPT` is in English while all other system prompts are in Russian |
| `db.py` | PASS | `_ALLOWED_TABLES` whitelist includes `project_memory`; all writes parameterized; `upsert_project_memory` uses `ON CONFLICT(project_id)` correctly; `get_project_item_count` covers notes + ideas + active deadlines only — `review_history` excluded (F3 root, known) |
| `schema.sql` | PASS | `project_memory` has `UNIQUE` constraint on `project_id`; FK to `projects(id)` present; all required columns present with `NOT NULL` constraints; index on `project_id` present |
| `bot.py` — `start_command` | PASS | No emoji; two-sentence description; concrete first-step hint (`/new_project`); under 10 lines; fully deterministic, no LLM content |
| `bot.py` — handler registration | PASS | `chat_guard` at TypeHandler group -1000; `memory_command` and `reflect_command` both registered; registration order is correct |

---

## Contract Compliance

| Rule | Verdict | Note |
|------|---------|------|
| IC-1.1 Single-user private assistant | PASS | `chat_guard` enforces `allowed_chat_id` at TypeHandler group -1000 before any feature handler |
| IC-1.2 Auth guard on all state-changing flows | PASS | `chat_guard` is a global pre-handler; every update passes through it |
| IC-1.3 SQLite as sole persistence system | PASS | No second persistence system introduced; all writes go through `db.py` |
| IC-1.4 Voice audio stays local | PASS | `transcriber.transcribe` uses local Whisper; no raw audio sent to Anthropic API |
| IC-1.5 Deterministic owns auth, persistence, scheduling, dedup, retry | PASS | All reminder/summary logic remains deterministic; no LLM in scheduling paths |
| IC-1.6 LLM bounded to declared inference paths and approved tools | DRIFT | `chat_handler.py` instantiates `AsyncAnthropic` directly, bypassing `openclaw_client`; the approved `TOOLS` catalog is used correctly, but the client layer diverges from the abstraction used by all other LLM-touching handlers |
| IC-1.7 No model-driven shell execution or host mutation | PASS | No subprocess, shell calls, or package installation in any scoped file |
| IC-1.8 Reminder/report automation observable and recoverable | PASS | systemd-driven; no LLM in delivery path |
| IC-2 Solution shape: Hybrid / T1 / Standard | PASS | No planner agents, delegated workers, or VM isolation introduced |
| IC-3 Secrets from environment only | PASS | `os.environ.get("LLM_API_KEY")`, `os.environ.get("LLM_MODEL_INTENT")` — no hardcoded credentials in scoped files |
| IC-3 Network egress: Telegram + Anthropic only | PASS | No arbitrary outbound calls introduced |
| IC-4 Auth remains explicit and testable | PASS | `chat_guard` is synchronous and deterministic |
| IC-4 SQLite writes parameterized | PASS | All `db.execute` calls use `?` placeholders; no string interpolation in write paths |
| IC-4 Reminder/summary checks not LLM-dependent | PASS | Confirmed; not touched in Phase 2–4 scope |
| IC-5 Every tool declared in catalog | PASS | All 10 tools in `TOOLS` list have `name`, `description`, `input_schema`, and `additionalProperties: false` |
| IC-5 Tool inputs validated before execution | DRIFT | `execute_tool` casts inputs (`str()`, `int()`) but performs no range checks or date-format validation; a malformed LLM-supplied value (e.g., `due_date` not in YYYY-MM-DD format) passes through to the DB write without validation |
| IC-5 Destructive/irreversible actions require confirmation path | N/A | No destructive tool (delete, archive, bulk-edit) is exposed in the chat tool catalog |
| IC-5 Tool use stays in current conversation scope | PASS | No background continuation; loop terminates via `stop_reason != "tool_use"` or `MAX_TOOL_ROUNDS` guard |
| IC-5 Permission checks not prompt-only | PASS | `chat_guard` is code-enforced, not a prompt instruction |
| IC-6 Only bounded chat tool loop as agentic behavior | PASS | No subagents, long-running plans, or delegated workers |
| IC-6 Hard iteration limit | PASS | `MAX_TOOL_ROUNDS = 5` declared and enforced in `chat_handler.py` |
| IC-6 Errors terminate to deterministic fallback | PASS | `except Exception` inside the while loop returns an error string; no recursive retry |
| IC-7 Minimum sufficient model class | DRIFT | `memory_cmd.py` uses Haiku-class for memory generation; `MEMORY_SYSTEM_PROMPT` specifies "200 слов", the API call passes `max_tokens=220`, and spec MR-1 says "max 200 tokens" — three inconsistent values for the same constraint |
| IC-9 No RAG/embeddings | PASS | No vector operations or embedding calls in any scoped file |
| IC-9 No LLM-driven scheduling | PASS | Confirmed |
| IC-9 No secrets in repo files | PASS | Not observed in scoped files |

---

## Right-Sizing / Runtime Checks

| Check | Verdict | Note |
|-------|---------|------|
| Implementation fits Hybrid / T1 / Standard shape | PASS | No planner agents, no VM workers, no privileged operations |
| Deterministic-owned subproblems remain deterministic | PASS | Auth, persistence, scheduling, dedup, retry all in deterministic code |
| Runtime behavior expanded beyond T1 | PASS | No shell exec, no mutable worker runtime, no privileged host ops |
| Human approval boundaries respected | PASS | No product category change, no shape/governance/tier change, no multi-user expansion, no RAG introduction |
| Memory model stays bounded (no semantic/vector memory) | PASS | `project_memory` is structured operational memory; no embeddings, no external retrieval |
| Memory injection is read-only | PASS | No tool in `TOOLS` can update or delete `project_memory`; confirmed in `tools.py` |
| `/reflect` correctly gated on memory prerequisite | PASS | Returns early with user message if `memory_row is None` |
| Weekly digest and reminder delivery deterministic | PASS | Not modified in Phase 2–4 scope; no LLM in delivery paths |

---

## Tool-Use Architecture Checks

| Check | Verdict | Note |
|-------|---------|------|
| Every LLM-callable tool declared in `TOOLS` catalog | PASS | 10 tools: `save_note`, `save_idea`, `save_deadline`, `save_homework`, `list_items`, `search`, `create_project`, `set_active_project`, `list_projects`, `get_status` |
| Each tool has description, input_schema, required fields | PASS | All 10 tools have all three fields; `additionalProperties: false` present on all |
| ARCHITECTURE.md lists tools with side-effect class, idempotency, permission | VIOLATION | ARCHITECTURE.md Section 6 names `tools.py` as the tool catalog but does not enumerate individual tools with side-effect class, idempotency classification, or per-tool permission level; IC-5 requires declaration |
| Unsafe-action gate: destructive tools have confirmation code path | N/A | No destructive tools exposed in the chat tool catalog |
| Permission checked at each tool boundary | DRIFT | `execute_tool` dispatches directly to DB operations after resolving `project_slug`; no re-verification of caller authorization at the tool boundary; relies entirely on upstream `chat_guard`; acceptable at T1 but single defense layer |
| Tool inputs validated before execution | DRIFT | Input fields cast but not range-checked or pattern-validated; malformed LLM-supplied `due_date` passes through to DB write without date-format validation |

---

## Agentic Architecture Checks

| Check | Verdict | Note |
|-------|---------|------|
| Chat loop has hard iteration limit | PASS | `MAX_TOOL_ROUNDS = 5` declared and enforced at `chat_handler.py` line 127 |
| Loop terminates on error (not recursive retry) | PASS | `except Exception` block inside while loop returns an error string immediately; no retry |
| No subagents, delegated workers, or long-running plans | PASS | Confirmed across all scoped files |
| Cross-iteration state limited to declared structures | PASS | `messages` list grows per round within function scope only; persisted state written via `user_state.add_message` after loop exit |

---

## Architecture Findings

### ARCH-1 [P2] — Tool Catalog Not Documented in ARCHITECTURE.md with Side-Effect and Idempotency Classification

**Symptom:** ARCHITECTURE.md Section 6 mentions `src/tools.py` as the "Approved tool catalog for the bounded chat loop" but does not enumerate individual tools, their side-effect class, idempotency, or per-tool permission level.

**Evidence:** 10 tools are implemented in `tools.py`. Of these, 4 are write-side-effect (`save_note`, `save_idea`, `save_deadline`, `save_homework`), 1 is session-state-mutating (`set_active_project`), and 5 are read-only. None of this is captured in the architecture document.

**Root cause:** Architecture doc was not updated when the tool catalog was finalized.

**Impact:** Audit and future contributor review cannot verify tool-use architecture compliance from the architecture doc alone. The approved tool surface is only discoverable by reading source code.

**Fix:** Add a Tool Catalog section to ARCHITECTURE.md listing each tool name, side-effect class (read / write / state), idempotency, and whether it requires a confirmation code path.

---

### ARCH-2 [P2] — chat_handler.py Bypasses openclaw_client Abstraction

**Symptom:** `chat_handler.py` imports and instantiates `AsyncAnthropic` directly, while all other LLM-calling handlers use `src.openclaw_client.complete` / `complete_json`.

**Evidence:** `chat_handler.py` lines 8 and 77: `from anthropic import AsyncAnthropic` and `client = AsyncAnthropic(api_key=api_key)`. All other handlers call `from src.openclaw_client import LLMError, complete` or `complete_json`. Model name is resolved independently via `os.environ.get("LLM_MODEL_INTENT", "claude-haiku-4-5")` rather than via `get_model_name`.

**Root cause:** The chat handler requires `AsyncAnthropic` for async streaming; `openclaw_client` is synchronous. The refactor to unify the client layer was not completed.

**Impact:** Two LLM client patterns coexist. Changes to model routing, error wrapping, or instrumentation in `openclaw_client` will not propagate to the chat path. The `G-1` retry policy from the earlier cycle audit (3-attempt exponential backoff in `openclaw_client`) is not applied to chat handler LLM calls.

**Fix:** Either (a) refactor `chat_handler.py` to use `openclaw_client` if an async wrapper is added, or (b) formally document in ARCHITECTURE.md that the chat path uses the async SDK directly and enumerate what guarantees it provides vs. `openclaw_client`.

---

### ARCH-3 [P2] — review.py Logs LLM Call Before LLM Is Invoked

**Symptom:** In `review.py`, `await log_llm_call(db, "review", "review")` is called inside the `async with` DB block at line 49, before the DB connection closes and `review_idea()` is awaited at line 56. If `review_idea()` fails, the daily counter is already incremented.

**Evidence:** `review.py` line 49 (`log_llm_call` inside DB block) vs. line 56 (`review_idea` after DB block closes).

**Root cause:** Log and limit check were placed together before the actual call to prevent exceeding the daily limit; the log fires before the work is confirmed.

**Impact:** On LLM or DB failure inside `reviewer.py`, the daily call counter is incremented for a call that never succeeded. Over repeated failures this could exhaust the daily limit prematurely. Low severity at T1 with one user but operationally misleading.

**Fix:** Move `log_llm_call` to after a successful return from `review_idea`, or have `reviewer.py` own the log write (it already opens its own DB connection).

---

### ARCH-4 [P2] — item_count_snapshot Excludes review_history (Staleness Signal Gap)

**Symptom:** `get_project_item_count` in `db.py` counts only notes + ideas + active deadlines. Completed reviews are not included. Reviewing an idea does not trigger a memory cache miss, so the memory summary may not reflect the review state.

**Evidence:** `db.py` lines 587–599: the COUNT query covers `notes`, `ideas`, and `deadlines` only. `review_history` is excluded.

**Root cause:** Deliberate scope decision during Phase 2 (F3 in META_ANALYSIS.md), deferred.

**Impact:** A project with completed reviews will serve a cached memory summary that does not account for those reviews. The `/reflect` command consumes this stale summary as its primary input (D1). The user has no visibility into this staleness gap.

**Fix:** Include a count of `review_history` rows for the project in the staleness computation. The fix belongs in `db.py` (add `review_history` to the COUNT query) with a corresponding update to any documentation of the staleness model.

---

### ARCH-5 [P2] — Memory Soft Cap Has Three Inconsistent Values Across Spec, Prompt, and API Call

**Symptom:** The memory output length constraint is specified as "max 200 tokens" in `spec.md` MR-1, as "Максимум 200 слов" (200 words) in `MEMORY_SYSTEM_PROMPT`, and as `max_tokens=220` in the `complete()` call. Words and tokens are not the same unit (Russian text averages ~1.3–1.7 tokens per word).

**Evidence:** `spec.md` MR-1 ("max 200 tokens"), `memory_cmd.py` line 21 ("Максимум 200 слов"), `memory_cmd.py` line 163 (`complete(... 220 ...)`).

**Root cause:** Three independent references to the same constraint were not kept in sync during implementation.

**Impact:** The effective output length cap is unpredictable. When this summary is injected into the review prompt without a secondary hard cap (D3), a longer-than-intended memory block can silently expand the prompt. Low severity in practice but is a spec compliance gap.

**Fix:** Align the three references: choose one authoritative value (e.g., `max_tokens=200` in the API call), express the same constraint consistently in the system prompt ("Максимум 200 токенов" or the word equivalent), and update MR-1 in `spec.md` to match.

---

### ARCH-6 [P3] — reviewer.py System Prompt in English; All Other Prompts in Russian

**Symptom:** `REVIEW_SYSTEM_PROMPT` in `reviewer.py` is entirely in English. All other LLM-facing system prompts in scoped files are in Russian.

**Evidence:** `reviewer.py` lines 16–27 vs. `memory_cmd.py` lines 17–22, `reflect_cmd.py` lines 17–26, `chat_handler.py` lines 18–23.

**Root cause:** Review feature was implemented independently; language consistency standard was not enforced.

**Impact:** Minor. The model receives a Russian-language memory context block injected into an English prompt. Not an architectural violation, but a language-layer inconsistency that may affect output language consistency on the review path.

**Fix (Low priority):** Translate `REVIEW_SYSTEM_PROMPT` to Russian for consistency, or document the deliberate choice to use English for the review path.

---

### ARCH-7 [P3] — No User-Visible Staleness Age in /memory Cache-Hit Response (F1)

**Symptom:** When `/memory` returns a cached result, the reply shows `_(актуально)_` but does not include when the memory was last generated. The user cannot determine whether the cache is minutes or weeks old.

**Evidence:** `memory_cmd.py` line 136: cache-hit reply appends `_(актуально)_`. The `generated_at` field is available in `existing_memory` but is not displayed.

**Root cause:** F1 deferred from Phase 2 review.

**Impact:** Low. The binary "актуально" flag gives no temporal context. Could cause confusion when memory was generated before a large batch of new content.

**Fix:** Include `generated_at` in the cache-hit reply, e.g., `_(актуально, обновлено: {generated_at[:10]})_`.

---

### ARCH-8 [P3] — confirm.py Active Project Resolution Violates UXR-1 in Edge Case (G3)

**Symptom:** `_do_confirm` resolves the project name from `state.active_project_id`. If `pending["project_id"]` differs from `state.active_project_id`, the reply shows `(без проекта)` even if the entity has a valid `project_id` in the DB. UXR-1 requires the confirmation reply to include the project name when a project is associated.

**Evidence:** `confirm.py` lines 133–141: project name is set only when `project_id == state.active_project_id and state.active_project_name`.

**Root cause:** Deliberate zero-extra-query design to avoid a DB round-trip at confirm time (documented as G3).

**Impact:** Low frequency. The entity is saved correctly; only the confirmation message is incomplete. UXR-1 is technically violated in this edge case.

**Fix:** Either accept one additional DB lookup to fetch the project name by `project_id` when `project_id != active_project_id`, or document the trade-off explicitly in ARCHITECTURE.md as an accepted UXR-1 exception.

---

## Doc Patches Needed

| File | Section | Change |
|------|---------|--------|
| `ARCHITECTURE.md` | Section 6 (System Components) | Add `src/handlers/memory_cmd.py` and `src/handlers/reflect_cmd.py` to the component table; both are new files from Phase 2/3 not currently listed |
| `ARCHITECTURE.md` | Section 8 (Memory Model) | "Planned Memory Evolution" describes the creative memory layer as future work; it is now implemented as `project_memory` table + `/memory` command + `/reflect` command; update to reflect current state and move the "planned" language to a "Next evolution" note |
| `ARCHITECTURE.md` | Section 13 (File Layout) | Script name is `scripts/send_summary.py` not `scripts/send_weekly_summary.py`; layout omits `src/handlers/memory_cmd.py`, `src/handlers/reflect_cmd.py`, `docs/DEPLOY.md`, `.env.example`, and `systemd/` directory |
| `ARCHITECTURE.md` | Missing section | Add a Tool Catalog section listing all 10 LLM-callable tools with side-effect class (read / write / state), idempotency, and confirmation requirement — required to satisfy IC-5 declaration rule (see ARCH-1) |
| `ARCHITECTURE.md` | Duplicate Section 12 | Section 12 appears twice: "Inference Strategy" (~line 200) and "External Integrations" (~line 232); renumber External Integrations to Section 17 or correct the numbering throughout |
| `spec.md` | Section 11 MR-1 | Align "max 200 tokens" statement with the actual system prompt and API call values; all three references should specify the same unit and value (see ARCH-5) |

---
