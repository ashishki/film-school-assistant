# ARCH_REPORT — Cycle 5 (Phase 5)

_Date: 2026-03-23_

---

## Component Verdicts

| Component | Verdict | Note |
|-----------|---------|------|
| src/handlers/chat_handler.py | PASS | New agentic handler, properly isolated in handlers layer |
| src/tools.py | PASS | New tool layer, correctly dispatches to db.py only |
| src/state.py (extended) | PASS | In-memory only, no DB calls |
| src/bot.py (modified) | PASS | Routing change preserves group ordering and INV-1 |
| src/handlers/help_cmd.py (modified) | PASS | Doc-only update to HELP_TEXT |

---

## Contract Compliance

| Rule | Verdict | Note |
|------|---------|------|
| INV-1: Single-user chat_guard | PASS | TypeHandler group=-1000 unchanged in bot.py |
| INV-2: Audio never leaves server | PASS | chat_handler handles text only; voice_handler unchanged |
| INV-3: Confirmation before entity save (voice/NL) | PASS with note | Chat path intentionally saves directly (no confirm step). Voice path (voice_handler + natural_confirm_handler group=1) is preserved. This is an intentional design asymmetry, analogous to INV-4. |
| INV-4: Explicit commands save immediately | PASS | Unchanged |
| INV-5: Reminder idempotency | PASS | Unchanged |
| INV-6: Weekly summary dedup | PASS | Unchanged |
| INV-7: DB is system of record | PASS | conversation_history is in-memory only; ephemeral per INV-7 |
| INV-8: Secrets via environment | PASS | api_key from os.environ.get("LLM_API_KEY") in chat_handler |
| G-1: Anthropic retry policy | DRIFT | chat_handler uses AsyncAnthropic directly without retry policy from openclaw_client.py. LLM errors are caught but not retried (single try/except, returns Russian error). openclaw_client has 3-retry backoff. |
| G-2: JSON response enforcement | N/A | Chat handler uses tool_use flow, not complete_json(). Claude returns structured tool calls natively. |
| G-4: Whisper model caching | PASS | Unchanged |
| G-5: Async DB access | PASS | All DB calls in chat_handler via aiosqlite.Connection |
| TU-1: Model selection | PASS with note | chat_handler uses LLM_MODEL_INTENT (Haiku) — correct for extraction/conversation |
| TU-2: Prompt versions are code | DRIFT | CHAT_SYSTEM_PROMPT in chat_handler has no version comment. Per TU-2, prompt changes should be versioned. Low severity for first introduction. |

---

## Architecture Findings

### ARCH-5-1 [P2] — Agentic profile still marked OFF in ARCHITECTURE.md

**Symptom:** ARCHITECTURE.md §6 Capability Profiles table declares `Agentic: OFF`. Phase 5 adds a multi-step tool-calling loop in chat_handler.py — this is exactly the "autonomous multi-step loop" described as OFF.

**Evidence:** docs/ARCHITECTURE.md line showing `| **Agentic** | **OFF** |`

**Root cause:** Documentation not updated after Phase 5 implementation.

**Impact:** Misleading to future developers and agents reading the architecture doc.

**Fix:** Update ARCHITECTURE.md §6: change Agentic from OFF to ON; update justification to describe the chat_handler tool-calling loop.

### ARCH-5-2 [P2] — chat_handler not in ARCHITECTURE.md Component Map

**Symptom:** src/handlers/chat_handler.py and src/tools.py are new files not listed in ARCHITECTURE.md §2 Component Map or §3 Runtime Flow.

**Evidence:** ARCHITECTURE.md §2 handler list does not include chat_handler.py; no §3.x Chat Flow section.

**Fix:** Add to ARCHITECTURE.md §2: chat_handler.py, tools.py. Add §3.5 or §3.x: Chat Flow description.

### ARCH-5-3 [P2] — G-1 retry policy not applied to chat_handler LLM calls

**Symptom:** chat_handler.py creates its own AsyncAnthropic client with a single try/except, no retry/backoff. openclaw_client.py implements 3-retry exponential backoff (G-1) for all LLM calls, but chat_handler bypasses it (async SDK required; openclaw_client is sync).

**Evidence:** src/handlers/chat_handler.py:62–73 — single try/except around client.messages.create.

**Root cause:** openclaw_client.py is synchronous; AsyncAnthropic required for async handler. Retry logic not ported to async path.

**Impact:** Transient API errors in chat mode fail immediately rather than retrying. User sees error; no retry.

**Fix (P2):** Add simple retry loop (3 attempts, exponential backoff via asyncio.sleep) around client.messages.create in chat_handler.py.

---

## ADR Compliance

No ADRs filed (docs/adr/ does not exist). N/A.

---

## Retrieval Architecture Checks

RAG Profile: OFF — section omitted.

---

## Doc Patches Needed

| File | Section | Change |
|------|---------|--------|
| docs/ARCHITECTURE.md | §6 Capability Profiles | Change Agentic from OFF to ON; update justification |
| docs/ARCHITECTURE.md | §2 Component Map | Add chat_handler.py, tools.py to handlers list |
| docs/ARCHITECTURE.md | §3 Runtime Flow | Add §3.x Chat Flow section |
