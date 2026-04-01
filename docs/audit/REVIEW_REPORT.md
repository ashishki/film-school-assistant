# REVIEW_REPORT — Cycle 1

_Date: 2026-04-01 · Scope: Phase 1–4 (all tasks P1-01..P4-03) · Stop-Ship: No_

---

## Executive Summary

- Stop-Ship: No
- P0: 0 · P1: 2 · P2: 8 · P3: 5 · Total: 15
- CI baseline: green (ruff + smoke_test_db). First audit cycle — no previous report.
- All phases (1–4) complete. Core functionality (capture, memory, reflection, deployment) is operational.
- Two P1 findings: `log_llm_call` fires before the LLM call in both `nl_handler.py` and `review.py` — daily quota is silently decremented on transient failures. Fix is low-complexity (move one function call).
- Key P2 issues: `due_date` not validated before DB write (risks digest crash on malformed dates); `chat_handler` bypasses `openclaw_client` retry policy; `REVIEW_SYSTEM_PROMPT` in English while all other prompts are Russian; `send_summary.py` section headers use emoji + English labels; memory cap values inconsistent across spec/prompt/API; smoke test missing Phase 2/3 coverage.
- P3 issues are carry-forwards from phase reviews (confirm edge case, memory staleness UX gaps, get_status unbounded scan). No correctness or security impact.
- No secrets or personal paths found in any committed file. SQL parameterization correct throughout.

---

## P0 Issues

None.

---

## P1 Issues

### P1-1 — log_llm_call fires before LLM in nl_handler.py

Symptom: `log_llm_call` at `nl_handler.py:56` fires inside the first `async with` DB block before `complete_json` at line 63. On `LLMError` or `LLMSchemaError`, the daily counter is already incremented for a call that never completed.

Evidence: `src/handlers/nl_handler.py:56` vs `:63`

Root cause: Logging and rate-limit check co-located before the LLM call to prevent double-counts; log fires before work is confirmed.

Impact: Every transient NL extraction failure silently decrements the user's daily quota. `nl_handler` fires on every non-command message — highest frequency path in the bot.

Fix: Move `log_llm_call` to after `complete_json` returns successfully (inside the second `async with` block where the parsed event is persisted).

Verify: Simulate `LLMError`; assert `llm_call_log` row count unchanged.

### P1-2 — log_llm_call fires before LLM in review.py

Symptom: `log_llm_call` at `review.py:49` fires inside the `async with` DB block before `review_idea()` is called at line 56. If `review_idea()` raises, the counter is already incremented.

Evidence: `src/handlers/review.py:49` vs `:56`

Root cause: Same as P1-1. Additionally `reviewer.py` opens its own DB connection for `create_review_history`; if that write fails, the call is still logged.

Impact: Failed `/review` commands silently consume daily quota.

Fix: Move `log_llm_call` to after `review_idea()` returns a valid response.

Verify: Simulate `LLMError` in `review_idea`; assert `llm_call_log` count unchanged.

---

## P2 Issues

| ID | Description | Files | Status |
|----|-------------|-------|--------|
| CODE-3 | `due_date` not pattern-validated before DB write; malformed date crashes weekly digest | `src/tools.py:269-271`, `src/schema.sql:50` | Open |
| CODE-4 | `chat_handler` bypasses `openclaw_client` retry policy; transient errors immediately surface to user | `src/handlers/chat_handler.py:77` | Open |
| CODE-5 | `reflect_cmd` no hard cap on assembled input text; long `next_step` values fed unfiltered into reflect prompt | `src/handlers/reflect_cmd.py:77-106` | Open |
| CODE-6 | `REVIEW_SYSTEM_PROMPT` in English while all other prompts are Russian; mixed-language context in Phase 3 reviews | `src/reviewer.py:15-27` | Open |
| CODE-7 | `send_summary.py` section headers use emoji + English labels; inconsistent with bot UX policy | `scripts/send_summary.py:292-299` | Open |
| CODE-8 | Memory cap inconsistent: spec says 200 tokens, prompt says 200 words, API call uses `max_tokens=220`; Russian text at 200 words ≈ 300–340 tokens, causing mid-sentence truncation | `src/handlers/memory_cmd.py:20,:163` | Open |
| CODE-9 | `smoke_test_db.py` `EXPECTED_TABLES` missing `project_memory` and `llm_call_log`; schema gaps would not be caught by CI | `scripts/smoke_test_db.py:58-70` | Open |
| CODE-10 | `smoke_test_db.py` has no coverage for Phase 2/3 DB functions (`upsert_project_memory`, `log_llm_call`, `get_llm_calls_today`, `create_review_history`) | `scripts/smoke_test_db.py` | Open |

---

## P3 Issues

| ID | Description | Files | Status |
|----|-------------|-------|--------|
| CODE-11 | `confirm.py` project name shows `(без проекта)` when entity `project_id` differs from `active_project_id` (G3 carry-forward) | `src/handlers/confirm.py:134-141` | Open |
| CODE-12 | `/memory` cache-hit response shows `_(актуально)_` with no date; user cannot tell if cache is minutes or weeks old (F1 carry-forward) | `src/handlers/memory_cmd.py:136` | Open |
| CODE-13 | `chat_handler` memory injection silent fallback emits no user-visible indicator on DB failure (F2 carry-forward) | `src/handlers/chat_handler.py:57-62` | Open |
| CODE-14 | `review_history` excluded from `item_count_snapshot` staleness counter; completed reviews don't trigger memory refresh (F3/D1 carry-forward) | `src/db.py:588-598` | Open |
| CODE-15 | `get_status` in `tools.py` uses `limit=1_000_000` for four table scans instead of `COUNT(*)` queries | `src/tools.py:347-350` | Open |

---

## Carry-Forward Status

| ID | Prior Sev | Description | Status | Change |
|----|-----------|-------------|--------|--------|
| G1 | Low | `/list` and `/search` no project name in header | Open | Unchanged |
| G2 | Low | `chat_handler` tool responses no project name | Open | Unchanged |
| G3 | Low | `confirm.py` uses `active_project_id` not per-entity `project_id` | Open → CODE-11 | Confirmed |
| F1 | Low | `/memory` no staleness age in cache-hit | Open → CODE-12 | Confirmed |
| F2 | Low | Memory injection silent fallback no log | Open → CODE-13 | Confirmed |
| F3 | Low | `review_history` not in item count | Open → CODE-14 | Confirmed |
| D1 | Low | Stale memory at review time | Open → CODE-14 root | Confirmed |
| D2 | Low-Med | `/reflect` LLM interpolation risk | Open | Containment assessed: system prompt + structured output mitigate; monitor in production |
| D3 | Low | No token limit on injected `summary_text` | Open → CODE-5 | Confirmed |

---

## Stop-Ship Decision

No — P0: 0, P1: 2. P1 issues are quota-accounting bugs with no data integrity or security impact. P2 issues are quality/reliability concerns. System is operational. P1 fixes should be dispatched to Codex before any new phase.
