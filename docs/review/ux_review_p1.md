# Film School Assistant — UX Review Pack: Phase 1

Phase: 1
Task: P1-05
Reviewer: Claude (Orchestrator)
Date: 2026-03-31
Status: Complete — pending human phase-gate approval

This review covers the four key interaction moments defined in P1-01 against the
implementation delivered in P1-02, P1-03, P1-04.

Evidence basis: code review of changed files against P1-01 examples and USER_EXPERIENCE.md.
Synthetic transcript walkthroughs are used where live transcripts are unavailable.

---

## Moment 1 — Capture Confirmation (with project)

**Before**
```
✅ Заметка сохранена.
```

**After**
```
Заметка сохранена → Короткометражка «Стекло»
```

**Verdict: IMPROVED**

`_confirm_success_text` in `confirm.py` now takes `project_name` and produces the `→ {project_name}` format.
Project name is resolved deterministically from `state.active_project_name` where `project_id == active_project_id`.
No LLM, no DB lookup. Emoji removed. Gender agreement correct (сохранена/сохранён/сохранено by type).

**Residual gap:** If the pending entity's `project_id` was resolved from NL extraction but does not match
`state.active_project_id` (i.e. the user mentioned a different project in the message), project name falls back to
`(без проекта)`. This is the correct safe behavior given no additional DB lookup is done. Acceptable for Phase 1.

---

## Moment 2 — Capture Confirmation (without project)

**Before**
```
✅ Заметка сохранена.
```

**After**
```
Заметка сохранена (без проекта)
```

**Verdict: IMPROVED**

The parenthetical is neutral and low-key. No error. No unsolicited prompt to set a project.
Matches UXR-1 and P1-01 Moment 2 target exactly.

---

## Moment 3 — Edit Confirmation

**Before**
Full pending preview re-shown without change acknowledgement on every `/edit` call.

**After**
```
Обновлено: срок → 20 апреля
Черновик (дедлайн): ...
Проект: ...
Срок: 20 апреля
[keyboard]
```

**Verdict: IMPROVED**

`_build_edit_ack` in `confirm.py` produces a one-line change summary before the preview.
For `field == "due"`, the ack shows the new date directly.
For `field in {"title", "content"}`, the ack shows a truncated preview of the new text.
The keyboard is unchanged. Length is slightly longer (one line added) but the added line is
the actionable information the user needed. Matches P1-01 Moment 4 target.

---

## Moment 4 — Active Project Context Reply (chat)

**Before**
Chat handler response does not name the project in the opening line.

**After (P1-03 scope in chat_handler.py)**
P1-03 scoped only to `confirm.py` — `chat_handler.py` was read but not changed in this phase
(no confirmation template exists there; tool responses are handled dynamically by the LLM-bounded loop).

**Verdict: PARTIAL — acceptable for Phase 1 scope**

The chat handler's project-context replies depend on the bounded LLM loop selecting the correct tool and
formatting the response. P1-03 correctly limited scope to deterministic confirmation templates.
Chat handler project orientation is a Phase 2 candidate (where active project injection into the
system prompt or tool context would be the right architectural move).

No regression introduced.

---

## Moment 5 — Weekly Digest Opening

**Before**
```
Weekly Digest — 2026-03-24 – 2026-03-30

You logged 5 items this week across 2 projects.
```

**After (active week, one dominant project)**
```
Дайджест 24–30 марта

Короткометражка «Стекло» — основная активность недели: 3 заметки, 1 идея.

🔴 Urgent (due this week):
...
```

**After (quiet week, nearest deadline exists)**
```
Дайджест 24–30 марта

Тихая неделя. Ближайший дедлайн: «Монтаж черновика» через 4 дн.
```

**Verdict: IMPROVED**

`_build_opening_sentence` in `send_summary.py` now identifies the dominant project by item count,
uses Russian genitive month range, and falls back to `Тихая неделя.` on ties or empty weeks.
`_russian_month_range` is pure Python with hardcoded Russian month names — no locale dependency.
Russian plurals are handled correctly by `_russian_plural`.

Section headers and empty-state strings are now Russian throughout.
Old `Weekly Digest — YYYY-MM-DD` header removed.

**Residual gap:** `_build_urgent_items` shows `срок {ISO date}` which is functional but ISO date format
is less readable than `20 апреля`. This is a UX polish item, not a regression. Deferred to Phase 2.

---

## Moment 6 — Review Completion

**Before**
```
CORE IDEA: ...
...
NEXT STEP: Write scene 3
```

**After**
```
CORE IDEA: ...
...
NEXT STEP: Write scene 3

→ Ещё 2 идеи без разбора в этом проекте.
```

**Verdict: IMPROVED**

`_fetch_unreviewed_count` makes one parameterized DB query, returns 0 for `project_id is None`.
Pointer is appended only when `count > 0`. If the DB call fails, a warning is logged and the
pointer is silently omitted — review output is not degraded.
Russian plural is handled correctly by `_russian_plural_ideas`.
Matches P1-01 Moment 7 target.

---

## Anti-pattern check

| Pattern | Status |
|---------|--------|
| Generic AI praise in templates | Eliminated — no "отлично", "замечательно" in changed templates |
| Replies longer than 3 lines for save/confirm | Confirm: 1 line ✅. Edit: 2–4 lines (ack + preview) — justified |
| Motivational filler in digest | Eliminated — "keep the momentum going." removed ✅ |
| Generic AI fallback at review end | Eliminated — replaced with grounded count or nothing ✅ |
| Unsolicited prompts to set project | Not introduced ✅ |

---

## Gaps and rework items

| ID | Gap | Severity | Recommended action |
|----|-----|----------|-------------------|
| G1 | Chat handler project-context reply (Moment 4) not addressed | Low — by design, out of P1 scope | Phase 2: inject active project into chat context deterministically |
| G2 | Urgent items show ISO date format (`срок 2026-04-20`) instead of Russian readable date | Low | Phase 2 or standalone fix |
| G3 | Confirm reply for entity with `project_id != active_project_id` shows `(без проекта)` even when project exists | Low — safe fallback | Phase 2: resolve project name from DB at confirm time |

No gaps are blocking. All three are Phase 2 candidates.

---

## Phase 1 close decision

**Phase 1 is complete and can be closed.**

All four P1-01 moments have improvements delivered:
- Capture confirmation: project-aware, emoji removed, gender correct
- Edit confirmation: one-line change ack before preview
- Weekly digest: Russian locale, project-framing opening, grounded quiet-week fallback
- Review completion: grounded next-step pointer from real stored count

UX continuity inside the Telegram surface is materially better than at Phase 0 exit.
The three residual gaps are low-severity and correctly deferred to Phase 2.

No architecture drift was introduced. All changes are either deterministic template rewrites
or bounded DB queries inside already-approved code paths.

**Human approval required before Phase 2 starts.**
