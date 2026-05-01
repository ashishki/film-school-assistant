# Film School Assistant — Phase 10 Cross-Project Recall Eval Pack

**Date:** 2026-04-08
**Phase:** 10 — Explicit Cross-Project Recall
**Reviewer:** Claude Orchestrator
**Tasks covered:** P10-01, P10-02, P10-03 (P10-03 merged into P10-01/02)

---

## Evaluation Structure

Each dimension: before / after / verdict / evidence / findings

---

## Dimension 1 — All-Project Memory Search (P10-01)

**Before:**
`/search <keyword>` searched `memory_items` only for the active project (project-first).
No cross-project memory search was available. Global search existed only for canonical
`notes` and `ideas` tables (no project filter).

**After:**
`/search all:<keyword>` activates all-project mode via the explicit `all:` prefix.

- Default `/search <keyword>` behavior: **unchanged** — project-first for memory, then global notes/ideas
- `/search all:<keyword>` calls `search_memory_items_all_projects(db, keyword)` — new db function

`search_memory_items_all_projects` in `src/db.py`:
- `WHERE scope = 'project' AND content LIKE ?` — no project_id filter
- LEFT JOINs `projects` table to return `project_name` per item
- Returns `project_id` and `project_name` in each row (provenance)

Output format for cross-project results:
`[project_name / source_kind#source_id] text...`

**Opt-in gating: confirmed.** The `all:` prefix is required; there is no implicit widening.

**Verdict:** ADDED — opt-in only, default behavior unchanged

**Evidence:**
- `src/db.py:search_memory_items_all_projects` — explicit opt-in function, docstring warns "Never call as default path"
- `src/handlers/search_cmd.py:_ALL_PREFIX = "all:"` — constant gates the mode
- `all_projects_mode = raw.lower().startswith(_ALL_PREFIX)` — condition checked before any DB call
- Log: `"Search mode=%s ..."` with `"all_projects"` or `"project_first"` label

**Findings:**
- F1: `search_notes` and `search_ideas` remain global in all modes (canonical table search is always cross-project). This is known from Phase 8 F3 and Phase 9 — canonical table search was always global, only memory_items are now scoped. Acceptable; memory_items is the evidence layer.

---

## Dimension 2 — Named-Project Recall (P10-02)

**Before:**
`/recall` fetched memory from the active project only.
`/recall user` fetched user-scoped items.
No way to explicitly recall from a different (non-active) project.

**After:**
`/recall <slug>` resolves the slug to a project via `get_project_by_slug(db, slug)`.
- Unknown slug → clear error: "Проект «slug» не найден."
- Known slug → `get_memory_items_for_project(db, project["id"], limit=10)` — existing helper
- Output includes `project_name` label via `_format_items(items, project_label=project_name)`

Default `/recall` (no args, active project) behavior: **unchanged**.
`/recall user` behavior: **unchanged**.

Cross-project access requires the user to explicitly type the project slug.
There is no implicit slug resolution from conversation context.

**Verdict:** ADDED — explicit slug required, defaults unchanged

**Evidence:**
- `src/handlers/recall_cmd.py:get_project_by_slug` — slug lookup before any item fetch
- Unknown slug check: early return with error message before DB query
- `project_label=project_name` passed to `_format_items` → each item shows `[project_name / label #id]`
- Default active-project path: `project_label=None` → items show only `[label #id]` (single-project, no repetition)

**Findings:**
- None.

---

## Dimension 3 — Provenance Labeling in Cross-Project Results (P10-03)

**Before:**
Project-first results showed `[source_kind] text (source_id: N)` — no project name.
Cross-project mode did not exist.

**After:**
- All-project `/search`: `[project_name / source_kind#source_id] text`
- Named `/recall <slug>`: `[project_name / label #source_id] date\ntext`
- Default project-first paths: unchanged — `[source_kind#source_id]` (no project repetition when scope is already clear)

Provenance rule: **project name only appears when the result could come from multiple projects.**
Single-project results do not repeat the project name per item (cleaner UX).

**Verdict:** IMPLEMENTED — context-appropriate provenance

**Evidence:**
- `search_memory_items_all_projects` returns `project_name` from JOIN
- `search_cmd.py`: `if all_projects_mode and item.get("project_name"): lines.append(f"[{item['project_name']} / ...]")`
- `recall_cmd.py:_format_items(items, project_label=project_label)` — `project_label` is None for single-project, non-None for named cross-project

---

## Phase 10 Summary

| Task | Verdict |
|------|---------|
| P10-01 — All-project /search all: mode | ADDED |
| P10-02 — Named-project /recall <slug> | ADDED |
| P10-03 — Cross-project provenance labeling | IMPLEMENTED |

**Implicit cross-project leakage check:**
- Default `/search <keyword>` → project-first memory, no all-projects memory ✅
- Default `/recall` → active project only ✅
- `/reflect` → project-scoped evidence only ✅
- Gap surface → active project only ✅
- All cross-project paths require explicit user action (`all:` prefix or `<slug>` arg) ✅

**False-link risk:**
- `search_notes` and `search_ideas` are global (existing behavior, not introduced in Phase 10)
- `memory_items` cross-project is opt-in only
- No implicit blending of evidence from different projects in any default flow
- Risk: LOW

**Phase 10 verdict: CLOSED — all tasks complete, no P0/P1 findings.**
