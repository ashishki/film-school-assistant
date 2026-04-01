---
# META_ANALYSIS — Cycle 1
_Date: 2026-04-01 · Type: full_

## Project State

All four planned implementation phases (1–4) are complete and closed per phase-review artifacts; the development loop is declared finished in CODEX_PROMPT.md with CI passing (ruff + smoke_test_db) as of 2026-04-01.
Baseline: CI pass (ruff + smoke_test_db). First audit cycle — no previous REVIEW_REPORT.md.

## Open Findings

| ID | Sev | Description | Files | Status |
|----|-----|-------------|-------|--------|
| G1 | Low | `/list` and `/search` commands do not include project name in response header | src/handlers/nl_handler.py (list/search paths) | Deferred from P1-05 |
| G2 | Low | `chat_handler.py` tool responses do not surface project name in opening line; LLM-dynamic path not addressed by P1-03 | src/handlers/chat_handler.py | Deferred from P1-05 |
| G3 | Low | `confirm.py` resolves project name from `state.active_project_id`; entities with `project_id != active_project_id` show `(без проекта)` even when a project exists in DB | src/handlers/confirm.py | Deferred from P1-05 |
| F1 | Low | `/memory` command shows no staleness age to the user; they cannot tell how old the cached summary is without inferring from context | src/handlers/memory_cmd.py | Deferred from P2-04 |
| F2 | Low | Memory injection in chat_handler falls back silently on DB failure with no warning log; silent fallback makes injection failures invisible in production | src/handlers/chat_handler.py | Deferred from P2-04 |
| F3 | Low | `item_count_snapshot` covers notes + ideas + active deadlines only; `review_history` entries do not increment the staleness counter, so completed reviews do not trigger a cache miss | src/db.py, src/handlers/memory_cmd.py | Deferred from P2-04 |
| D1 | Low | Project memory may be stale at review time; stale context is injected into idea review prompt without any user-visible staleness indicator | src/reviewer.py, src/handlers/review.py | Deferred from P3-03 |
| D2 | Low-Medium | `/reflect` LLM (Sonnet-class) could interpolate or paraphrase beyond source data despite system prompt constraint and structured output format; flagged for production monitoring | src/handlers/reflect_cmd.py | Deferred from P3-03 |
| D3 | Low | No hard token/character limit applied to `summary_text` injected into idea review prompt; relies solely on memory generation's 200-word soft cap | src/reviewer.py | Deferred from P3-03 |

## PROMPT_1 Scope (architecture)

- memory_cmd: staleness model — `item_count_snapshot` covers only 3 entity types; review_history is excluded; F3 and D1 both trace to this gap in the staleness signal definition
- chat_handler memory injection: silent fallback path (F2) and absence of project name in LLM-dynamic tool responses (G2) — two independent gaps in the same file with different root causes
- confirm.py project resolution: uses `active_project_id` from session state rather than per-entity `project_id` DB lookup; G3 is a deliberate trade-off (no extra DB round-trip at confirm time) whose cost should be re-evaluated now that the full phase set is complete
- reflect_cmd: input assembly pipeline assembles memory + review_history next_steps + active deadlines; D2 risk is inherent to Sonnet-class + richer context; assess whether `_format_reflection` structured output enforcement is sufficient containment
- reviewer.py injection path: no secondary token cap on `summary_text` passed to review prompt (D3); assess whether 200-word soft cap from memory generation is a reliable upstream bound in practice
- /list and /search output contract: project name absent from headers (G1); assess whether fix belongs in the handler template or requires an additional DB join

## PROMPT_2 Scope (code, priority order)

1. src/handlers/reflect_cmd.py (new file — Phase 3; highest LLM risk; D2 interpolation finding; input assembly and output formatting are the critical paths)
2. src/handlers/memory_cmd.py (new file — Phase 2; staleness logic, F1 no-age display, F3 incomplete item_count_snapshot; cache hit/miss decision path)
3. src/handlers/chat_handler.py (changed — Phase 2 injection + Phase 1 partial gap; F2 silent fallback, G2 project name absent from tool responses; two independent concerns in one file)
4. src/reviewer.py (changed — Phase 3 context injection; D1 stale context, D3 no secondary token cap; inspect review_idea signature and prompt construction)
5. src/handlers/confirm.py (changed — Phase 1 core; G3 project resolution uses active_project_id not per-entity project_id; verify the exact fallback branch)
6. src/handlers/review.py (changed — Phase 3; fetches get_project_memory before calling review_idea; verify error path and None-propagation to reviewer.py)
7. src/db.py (changed — Phase 2; upsert_project_memory, get_project_memory, item_count logic; F3 root; verify _ALLOWED_TABLES whitelist)
8. src/schema.sql (changed — Phase 2; project_memory table definition; verify UNIQUE constraint on project_id and FK integrity)
9. src/bot.py (changed — Phase 4 /start rewrite, Phase 3 /reflect registration; verify no emoji regression and correct handler registration order)
10. scripts/send_summary.py (changed — Phase 1 digest rewrite; verify _build_opening_sentence, _russian_month_range, and ISO date exposure in _build_urgent_items)

## Cycle Type

Full — this is Cycle 1 with no prior REVIEW_REPORT.md; all four implementation phases (1–4) are being audited together for the first time; scope spans the complete change surface from Phase 1 UX rewrites through Phase 4 deployment packaging.

## Notes for PROMPT_3

- D2 (/reflect interpolation risk) is the highest-priority finding for production safety; PROMPT_3 should assess whether `_format_reflection` enforcement is structurally sufficient or whether a secondary output validation step is warranted.
- G3 (confirm.py active_project_id vs per-entity project_id) is a deliberate architectural trade-off, not an oversight; PROMPT_3 should evaluate cost/benefit of adding a DB lookup at confirm time versus keeping the current zero-extra-query design.
- F3 (review_history excluded from staleness counter) and D1 (stale memory at review time) share a root cause; a single fix to the `item_count_snapshot` computation would close both; PROMPT_3 should flag whether the fix belongs in db.py or memory_cmd.py.
- F2 (silent fallback in chat_handler) is low severity but operationally invisible; PROMPT_3 should confirm whether a warning log is sufficient or whether a user-visible indicator is warranted for the no-memory path.
- D3 (no secondary token cap on summary_text in reviewer.py) depends on whether the 200-word upstream generation bound is contractually enforced; PROMPT_3 should verify whether the memory generation prompt reliably produces outputs within that bound or whether a hard character slice is needed as a defensive guard.
---
