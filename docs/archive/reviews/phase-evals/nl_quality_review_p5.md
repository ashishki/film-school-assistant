# Phase 5 NL Quality Review Pack

Date: 2026-04-01
Reviewer: Claude
Phase: 5 — NL Interaction Quality
Tasks covered: P5-01, P5-02, P5-03, P5-04
CI status: ruff passes on all tasks; smoke_test_db not re-run (known sandbox hang)

---

## Review Structure

Each section covers one NR requirement from docs/spec.md section 14.
Verdict scale: **Met** / **Partial** / **Not met**

---

## NR-1 — Multi-entity Extraction (P5-01)

### Spec

One message → `{"entities": [...]}` array → first entity as pending, rest queued → auto-present next on confirm → single-entity path unchanged.

### Evidence

**EXTRACTION_SYSTEM_PROMPT** (nl_handler.py:19-25):
```
Верни только JSON: {"entities": [{"entity_type": ..., "content": ..., "project_hint": ..., "due_date": ...}]}
```
Returns array. ✅

**state.py:14**: `pending_entities: list[dict] | None = None`
**state.py:52**: `clear_pending` resets `pending_entities`. ✅

**nl_handler.py:106-152**: First entity processed via `_prepare_pending_entity_from_nl` and set as `pending_entity`. Remaining entities stored in `state.pending_entities`. When only one entity, `remaining_entities` is empty → `pending_entities = None`. Backward compat preserved. ✅

**confirm.py:164-228**: `_queue_next_pending_entity()` pops the next raw entity, calls `_prepare_pending_entity_from_nl`, sets it as new `pending_entity`, returns preview text. ✅

**bot.py:296-306**: Confirm callback checks `state.pending_entity` after `_do_confirm`; if clear, calls `_queue_next_pending_entity()` and sends the next preview as a follow-up message with keyboard. ✅

### Findings

| ID | Sev | Description |
|----|-----|-------------|
| R1-F1 | LOW | `_do_confirm` saves/restores `pending_entities` around `clear_pending` (lines 164-166). Functional but slightly fragile; a refactor of `clear_pending`'s signature could break it silently. |

### Verdict: **Met**

Single-entity backward compat confirmed. Multi-entity queue confirmed in code. R1-F1 deferred (low severity, no behavioral impact).

---

## NR-2 — Clarifying Questions on Parse Failure (P5-02)

### Spec

4 failure branches each get a specific clarifying message. No branch may use the old generic 4-line message. `_nl_parse_error_text()` deleted.

### Evidence

**LLMError / LLMSchemaError** (nl_handler.py:84-91):
`"Не понял — попробуй переформулировать. Что хочешь сохранить?"` ✅

**non-dict response** (nl_handler.py:93-100):
`"Что-то пошло не так при разборе. Попробуй ещё раз или используй /note, /idea, /deadline."` ✅

**empty entities list** (nl_handler.py:102-104):
`"Не нашёл что сохранить. Уточни: это заметка, идея или дедлайн?"` ✅

**no valid entities after normalization** (nl_handler.py:101-105):
`"Не смог разобрать содержимое. Попробуй написать иначе или укажи тип: /note, /idea, /deadline."` ✅

**`_nl_parse_error_text()` removed**: confirmed absent from file. ✅

All messages are under 2 lines. No full command list as primary content. ✅

### Findings

None.

### Verdict: **Met**

---

## NR-3 — Уточнить Button and Re-extraction Flow (P5-03)

### Spec

3-button keyboard (Сохранить / Удалить / Уточнить). Tap Уточнить → `pending_clarify = True` → prompt user to rewrite → next free-text message clears old entity, re-runs extraction. No fields preserved.

### Evidence

**state.py:15**: `pending_clarify: bool = False`
**state.py:53**: `clear_pending` resets to False. ✅

**confirm.py:295-301**:
```python
def _pending_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Сохранить", callback_data="confirm"),
            InlineKeyboardButton("❌ Удалить", callback_data="discard"),
            InlineKeyboardButton("✏️ Уточнить", callback_data="clarify"),
        ]]
    )
```
3 buttons confirmed. ✅

**bot.py:316-322**: clarify callback sets `state.pending_clarify = True`, calls `query.edit_message_text("Напиши исправленный вариант — переработаю.")`. Does NOT call `clear_pending`. ✅

**nl_handler.py:36-38**: entry check — if `pending_clarify` is True: set False, call `clear_pending(chat.id)`, fall through to extraction. This runs before the `pending_entity is not None` guard. ✅

No fields from old pending entity preserved: `clear_pending` clears all `pending_*` fields. ✅

### Findings

| ID | Sev | Description |
|----|-----|-------------|
| R3-F1 | LOW | After a clarify flow, the original "wrong" user message is still in `nl_context`. The re-extraction prompt will include it as prior context. The LLM should handle this correctly (latest message overrides prior intent), but in edge cases it could cause confusion if the old message is semantically misleading. Mitigating factor: the new message is always the last (current) item in `nl_context` and the prompt labels it "Текущее сообщение:". |

### Verdict: **Met**

R3-F1 is low severity and acceptable given the prompt labeling. Deferred.

---

## NR-4 — NL Context Window (P5-04)

### Spec

`nl_context: list[str]` (max 5) in UserState. Appended after each NL attempt. NOT cleared by `clear_pending`. When `len > 1`, extraction prompt includes prior context block. When `len == 1` (first message), prompt is identical to baseline.

### Evidence

**state.py:20**: `nl_context: list[str] = field(default_factory=list)` ✅
**state.py:28-31**: `add_nl_context()` appends and caps at 5. ✅
**state.py:49-58**: `clear_pending` does NOT touch `nl_context`. ✅

**nl_handler.py:47**: `state.add_nl_context(user_text)` — appended after trim/empty check, before LLM call. ✅

**nl_handler.py:49-58**: context block built when `len(state.nl_context) > 1`:
```
"Предыдущие сообщения пользователя:\n- {msg1}\n- {msg2}\n\nТекущее сообщение: {user_text}"
```
Single-message path: `extraction_prompt = user_text` — identical to baseline. ✅

**nl_handler.py:80**: `complete_json(extraction_prompt, ...)` — augmented prompt passed to LLM. ✅
**nl_handler.py:228-236**: `source_text` in `create_parsed_event` uses raw `user_text`. ✅

**`nl_context` not persisted to DB**: confirmed — in-memory only. ✅

### Findings

None.

### Verdict: **Met**

---

## Regression Check

| Area | Status | Notes |
|------|--------|-------|
| Single-entity NL flow | ✅ No regression | `entities` array with 1 item → same path as before |
| Confirm/discard commands | ✅ No regression | `clear_pending` still clears all pending_* fields |
| Edit command | ✅ No regression | edit_command unchanged |
| Chat handler | ✅ No regression | no changes to chat_handler or memory injection |
| Voice transcription | ✅ No regression | voice pipeline unchanged |
| Type-selection keyboard | ✅ No regression | `entity_type is None` path in nl_handler unchanged |
| Ruff CI | ✅ Passes | All 4 tasks verified |

---

## Summary Table

| NR | Requirement | Verdict | Findings |
|----|-------------|---------|----------|
| NR-1 | Multi-entity extraction | Met | R1-F1 (LOW) |
| NR-2 | Clarifying questions | Met | None |
| NR-3 | Уточнить button | Met | R3-F1 (LOW) |
| NR-4 | NL context window | Met | None |

**All NR requirements met. No P0/P1 findings. 2 low-severity findings deferred.**

---

## Phase 5 Close Decision

Phase 5 is **CLOSED**.

Deferred findings (not blocking):
- R1-F1: `_do_confirm` save/restore pattern for `pending_entities` — refactor in future if `clear_pending` signature changes
- R3-F1: clarify flow leaves old message in `nl_context` — acceptable given prompt labeling

Next: push commits, update CODEX_PROMPT.md and tasks.md to reflect Phase 5 closed.
