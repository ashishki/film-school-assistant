# STRATEGY_NOTE.md — Phase 5 Strategy Review

_Date: 2026-03-23 · Reviewer: Strategy Agent · Phase: 5 (Conversational Chat Interface)_

---

## Phase Summary

Phase 5 introduces a Claude tool-calling loop as the primary free-text entry path, replacing the single-shot `nl_handler` extraction → confirm flow. The 4 tasks are:

- **T-CH1:** `src/tools.py` — 10 tool schemas + async `execute_tool()` dispatcher
- **T-CH2:** `src/state.py` — `conversation_history` field + `add_message()` / `reset_history()`
- **T-CH3:** `src/handlers/chat_handler.py` — multi-round tool-use loop with loop guard and daily LLM limit check
- **T-CH4:** `src/bot.py` wiring — route free text to `chat_handler`, add `/chat_reset`, update `/help`

---

## Feasibility Assessment

**Architecture fit:** The existing system is well-suited for this extension. `src/db.py` already exposes all the CRUD functions needed as tool targets. `src/config.py` already has `llm_daily_limit` (or equivalent) for the LLM cost guardrail from T-O3. `src/openclaw_client.py` already handles Anthropic retries. The tool executor can wrap existing db functions without any schema changes.

**Dependency chain:** T-CH1 and T-CH2 are independent. T-CH3 depends on both. T-CH4 depends on T-CH3. The linear sequence is correct.

**Scope is appropriate:** 4 tasks, each focused and completable in one Codex session.

---

## Invariant Compatibility Check

| Invariant | Compatibility | Notes |
|---|---|---|
| INV-1: Single-user chat_id guard | COMPATIBLE | `chat_guard` in group=-1000 is unaffected by handler changes in T-CH4 |
| INV-2: Audio never leaves server | COMPATIBLE | Chat handler handles text only; voice flow is explicitly preserved |
| INV-3: Confirmation required before entity save (voice/NL) | **REQUIRES ATTENTION** | Chat handler path bypasses the confirm flow — saves directly. This is intentional (tool_use result is immediate) but must be clearly documented. The voice path MUST remain on confirm flow. T-CH4 AC-2 preserves this. |
| INV-4: Explicit commands save immediately | COMPATIBLE | Slash commands unchanged (T-CH4 AC-4) |
| INV-5: Reminder idempotency | COMPATIBLE | Not touched |
| INV-6: Weekly summary dedup | COMPATIBLE | Not touched |
| INV-7: DB is system of record | COMPATIBLE | No new in-memory persistence beyond rolling history window |
| INV-8: Secrets via env vars | COMPATIBLE | No new secrets; Anthropic key already in config |

**INV-3 note:** The chat handler saves entities immediately via tool execution — this is a deliberate UX change (conversational = no confirm step) and not a violation of INV-3 as long as the voice flow remains gated. Task T-CH4 AC-2 explicitly preserves the voice confirmation flow. This is architecturally sound.

---

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Loop guard not hit but slow (4 rounds × LLM latency) | Low | Max 5 rounds is reasonable; chat is async so no blocking |
| Daily LLM limit: counter reset logic must match existing T-O3 implementation | Medium | T-CH3 must read the same counter used by T-O3; implementer must check `src/config.py` and existing LLM call paths |
| `execute_tool` saves immediately — no undo path | Low | Single-user system; acceptable for MVP |
| `conversation_history` lost on restart | Low | INV-7 already accepts this; user can `/chat_reset` |
| nl_handler fully replaced — regression risk | Medium | T-CH4 must keep `natural_confirm_handler` (group=1) active for pending voice/NL entities. AC-2 covers this but implementer must not remove group=1 handler. |

---

## Gaps and Clarifications

1. **T-CH3 system prompt language:** Tasks spec says "responds in Russian" — the EXTRACTION_SYSTEM_PROMPT and REVIEW_SYSTEM_PROMPT are versioned (TU-2). The new chat system prompt should be treated the same way (version comment in code, commit as code change).
2. **Tool result format in messages:** Anthropic tool-use API requires `ToolResultBlock` with `tool_use_id`. Implementer must use the SDK's `ToolResultBlockParam` correctly.
3. **LLM model for chat:** Not specified in tasks.md. Should use `LLM_MODEL_INTENT` (Haiku) for tool extraction rounds and final response — the spec says "conversational" not "review quality". Implementer should default to `LLM_MODEL_INTENT` unless overridden.

---

## Recommendation

**Recommendation: Proceed**

The Phase 5 plan is coherent, well-sequenced, and compatible with all system invariants. The key risk (INV-3 / voice flow preservation) is explicitly covered by T-CH4 AC-2. No blocking architectural concerns identified. Proceed with T-CH1 → T-CH2 → T-CH3 → T-CH4 in order.
