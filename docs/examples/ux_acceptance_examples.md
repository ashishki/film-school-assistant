# Film School Assistant — UX Acceptance Examples

Phase: 1
Task: P1-01
Status: Complete

These examples define the target output behavior for Phase 1 UX tasks.
Each entry has a **Before** (current or representative), an **After** (target), and a **Why**.

They are the eval contract for P1-02, P1-03, P1-04, and P1-05.

---

## Moment 1 — Capture Confirmation (note/idea with project)

**Before**

```
✅ Заметка сохранена.
```

**After**

```
Заметка сохранена → Короткометражка «Стекло»
```

**Why**

The current confirmation tells the user only that the action succeeded.
It does not orient them to where the item landed.
The after-state confirms success and anchors the item to its project in one line.
No emoji required. No praise. Just grounded, specific feedback.

---

## Moment 2 — Capture Confirmation (note/idea without project)

**Before**

```
✅ Заметка сохранена.
```

**After**

```
Заметка сохранена (без проекта)
```

**Why**

When no project is associated, the user should still know it was saved, with a neutral note
that no project was attached — not a prompt to set one, not a placeholder.
Parenthetical is intentionally low-key; it is not an error.

---

## Moment 3 — Deadline / Homework Confirmation (with project)

**Before**

```
✅ Дедлайн сохранён.
```

**After**

```
Дедлайн сохранён → Короткометражка «Стекло» · срок 15 апреля
```

**Why**

For time-bound entities, the due date is load-bearing context.
The after-state confirms save, names the project, and echoes the date — all in one line.
The user can verify at a glance before switching tasks.

---

## Moment 4 — Edit Confirmation (pending entity updated)

**Before**

The edit command re-shows the full pending preview (Черновик, Проект, Срок lines)
with the keyboard again — the same view the user already saw.

**After**

```
Обновлено: срок → 20 апреля
[keyboard unchanged]
```

**Why**

Re-showing the full preview on every edit creates noise.
The after-state confirms only what changed and keeps the keyboard.
If the user needs to see the full draft, the preview was already shown once.

---

## Moment 5 — Active Project Reply (no pending entity; project context in chat)

**Before**

The chat handler responds to "что у меня по проекту?" with a generic list of items
or a tool response that does not name the project in the opening line.

**After**

```
Короткометражка «Стекло» — 3 заметки, 1 идея, дедлайн через 6 дней.
[items follow]
```

**Why**

When the user asks about their project state, the first line should orient them
immediately: project name, key counts, nearest deadline.
Not a generic header. The name of the project should be the first word.

---

## Moment 6 — Weekly Digest Opening

**Before**

```
Weekly Digest — 2026-03-24 – 2026-03-30

You logged 5 items this week across 2 projects.
```

**After (active week)**

```
Дайджест 24–30 марта

Короткометражка «Стекло» — основная активность недели: 3 заметки, 1 идея.
Дедлайн «Монтаж черновика» через 4 дня.
```

**After (quiet week)**

```
Дайджест 24–30 марта

Тихая неделя — ничего не зафиксировано. Ближайший дедлайн: «Монтаж черновика» через 11 дней.
```

**Why**

The current opening is a count sentence ("You logged N items").
It is generic and does not tell the user where their attention actually went.
The after-state opens with the project that had the most activity
and surfaces the nearest deadline immediately — no hunting needed.
The quiet-week variant is honest and brief, not motivational.

---

## Moment 7 — Review Completion (idea review ends)

**Before**

```
CORE IDEA: ...
DRAMATIC CENTER: ...
WEAK POINTS: ...
QUESTIONS:
  1. ...
  2. ...
  3. ...
NEXT STEP: Write scene 3
```

The review ends at NEXT STEP with no follow-through.

**After**

```
CORE IDEA: ...
DRAMATIC CENTER: ...
WEAK POINTS: ...
QUESTIONS:
  1. ...
  2. ...
  3. ...
NEXT STEP: Write scene 3

→ У тебя есть 2 непросмотренные идеи по этому проекту. Хочешь разобрать следующую?
```

**Why**

The current review ends abruptly.
The after-state adds a single grounded next-step pointer based on stored state —
not a generic "let me know how you want to proceed" fallback.
The pointer is one sentence. It references real data. It is optional: if no
unreviewed ideas exist, the line is omitted entirely.

---

## Anti-pattern reference

These phrasings are explicitly out of scope for Phase 1:

| Pattern | Why out of scope |
|---------|-----------------|
| "Отлично! Запись сохранена 🎉" | Generic AI praise |
| "Ваш дедлайн был успешно добавлен в систему" | Bureaucratic, long |
| "Хотите добавить проект к этой заметке?" | Unsolicited prompt |
| "Quiet week — keep the momentum going." | Motivational filler, not grounded |
| "Let me know how you want to proceed!" | Generic AI fallback |
| Any reply longer than 3 lines for a save/edit confirm | Length discipline (UXR-5) |
