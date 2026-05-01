# Film School Assistant — Phase 11 NL Access Eval Pack

**Date:** 2026-04-08
**Phase:** 11 — Natural Language Access to Memory and Reflection
**Reviewer:** Claude Orchestrator
**Tasks covered:** P11-01, P11-02, P11-03

---

## Evaluation Structure

Each dimension: before / after / verdict / evidence / findings

---

## Dimension 1 — Shared Reflect Logic (P11-01)

**Before:**
Reflection logic was inlined inside `reflect_command` only. No other caller could trigger it.

**After:**
`run_project_reflect(db, project_id, project_name, config) -> str | None` extracted as a
standalone async function in `src/handlers/reflect_cmd.py`.

Responsibilities of `run_project_reflect`:
- fetch project memory (returns None if missing)
- fetch evidence snippets with degraded fallback
- extract next_steps from review history
- fetch active deadlines
- fetch user context with degraded fallback
- call `complete_json` via `asyncio.to_thread`
- return `_format_reflection(response)` string on success, None on LLMError or bad response

Does NOT call `log_llm_call` or `get_llm_calls_today` — these remain caller responsibility.

`reflect_command` updated to call `run_project_reflect`, then log on success, then reply.

**Verdict:** EXTRACTED — behavior of /reflect unchanged; logic now reusable

**Evidence:**
- `src/handlers/reflect_cmd.py:134` — `run_project_reflect` defined
- `src/handlers/reflect_cmd.py:~209` — quota check remains in `reflect_command`
- `src/handlers/reflect_cmd.py:~226` — `log_llm_call` called after successful result

**Findings:**
- None.

---

## Dimension 2 — recall_memory Tool (P11-02)

**Before:**
No tool existed for evidence recall. User had to use `/recall` command explicitly.

**After:**
`recall_memory` added to `TOOLS` catalog in `src/tools.py`.

Description triggers: "что последнее", "напомни записи", "что я делала", "what's in my notes"

Behavior:
- no active project → clear message
- keyword provided → `search_memory_items_for_project(db, project_id, keyword, limit)`
- no keyword → `get_memory_items_for_project(db, project_id, limit)`
- default limit = 5
- each item formatted: `[source_kind#source_id] date\ntext[:200]`
- no items → "Нет записей в памяти проекта."

**Verdict:** ADDED — no LLM cost, pure DB read

**Evidence:**
- `src/tools.py:166` — `recall_memory` in TOOLS list
- `src/tools.py:461` — execute_tool branch with keyword/no-keyword routing
- Imports: `get_memory_items_for_project`, `search_memory_items_for_project` from `src.db`

**Findings:**
- None.

---

## Dimension 3 — reflect_project Tool (P11-03)

**Before:**
Reflection required explicit `/reflect` command.

**After:**
`reflect_project` added to `TOOLS` catalog.

Description triggers: "разобраться где я", "что делать дальше", "помочь с фокусом", "порефлексируем"

Behavior:
- no active project → clear message
- quota check via `get_llm_calls_today` before LLM call
- calls `run_project_reflect(db, project_id, project_name, config)`
- None result → error message
- success → `log_llm_call(db, "review", "reflect_tool")`, return formatted reflection

**Verdict:** ADDED — quota/log pattern correct

**Evidence:**
- `src/tools.py:182` — `reflect_project` in TOOLS list
- `src/tools.py:488` — execute_tool branch with quota check and run_project_reflect call
- `log_llm_call` called only after successful result (not before)

**Findings:**
- None.

---

## NL Routing Check

Interrogative/recall phrases already excluded from nl_handler by `should_try_nl_capture`:
- `should_try_nl_capture` at `src/handlers/nl_handler.py:67` excludes phrases starting with
  "что ", "покажи ", "найди ", "где ", "когда ", "какие ", "какая ", "какой "
- Reflective phrases ("порефлексируем", "помоги разобраться", "как дела по проекту") do not
  match any `NL_CAPTURE_MARKERS` → routed to chat_handler automatically

No changes to NL routing were needed. Tools are invoked by the LLM inside the chat loop
when it judges the tool fits the user intent.

**Implicit command leakage check:**
- `/recall` command: unchanged ✅
- `/reflect` command: calls `run_project_reflect` then logs — behavior identical to before ✅
- chat tool loop: `recall_memory` and `reflect_project` available as tools ✅

---

## Phase 11 Summary

| Task | Verdict |
|------|---------|
| P11-01 — Shared reflect logic extracted | EXTRACTED |
| P11-02 — recall_memory tool | ADDED |
| P11-03 — reflect_project tool | ADDED |

**Phase 11 verdict: CLOSED — all tasks complete, smoke test PASS, no P0/P1 findings.**
