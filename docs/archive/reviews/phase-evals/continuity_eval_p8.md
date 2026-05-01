# Film School Assistant — Phase 8 Continuity Eval Pack

**Date:** 2026-04-08
**Phase:** 8 — MVP Evidence Memory Foundation
**Reviewer:** Codex
**Tasks covered:** P8-01, P8-02, P8-03, P8-04, P8-05

---

## Evaluation Structure

Each dimension: before / after / verdict / evidence / findings

---

## Dimension 1 — Evidence Memory Schema (P8-01)

**Before:**
Project continuity relied on canonical tables plus bounded summaries. There was no dedicated evidence-recall table with explicit scope or source provenance, so retrieval had to search primary tables directly or rely on summary text.

**After:**
`memory_items` exists as a dedicated recall index with:
- scope enforcement via `CHECK (scope IN ('project', 'user'))`
- project/user consistency check for `project_id`
- provenance fields `source_kind`, `source_id`, `source_created_at`
- indexes for project-scoped retrieval and source-based upsert lookup

The migration guidance is documented for existing databases; new databases get the table through normal schema initialization.

**Verdict:** IMPROVED

**Evidence:**
- [src/schema.sql](/home/gdev/film-school-assistant/src/schema.sql#L142) through [src/schema.sql](/home/gdev/film-school-assistant/src/schema.sql#L159) define `memory_items`, the scope check, the project/user consistency check, and both indexes.
- [docs/db-migration-guide.md](/home/gdev/film-school-assistant/docs/db-migration-guide.md#L108) through [docs/db-migration-guide.md](/home/gdev/film-school-assistant/docs/db-migration-guide.md#L114) document that existing databases need the manual Phase 8 migration and that rollback is `DROP TABLE memory_items;`.

**Findings:**
- None for the schema itself.

---

## Dimension 2 — Deterministic Ingestion (P8-02)

**Before:**
Confirmed entities were persisted only in their canonical tables. There was no deterministic mirror into a recall-oriented evidence table, so project-first evidence retrieval had nothing to query.

**After:**
`confirm.py` writes memory items as a fire-and-forget side effect after canonical saves for:
- notes
- ideas
- homework
- user context

The canonical write still succeeds even if evidence indexing fails; the memory insert/update is wrapped in `try/except` with warning logs instead of blocking confirmation.

**Verdict:** IMPROVED

**Evidence:**
- [src/handlers/confirm.py](/home/gdev/film-school-assistant/src/handlers/confirm.py#L247) through [src/handlers/confirm.py](/home/gdev/film-school-assistant/src/handlers/confirm.py#L378) implement `_save_pending_entity`.
- [src/handlers/confirm.py](/home/gdev/film-school-assistant/src/handlers/confirm.py#L258) through [src/handlers/confirm.py](/home/gdev/film-school-assistant/src/handlers/confirm.py#L272) upsert note evidence.
- [src/handlers/confirm.py](/home/gdev/film-school-assistant/src/handlers/confirm.py#L285) through [src/handlers/confirm.py](/home/gdev/film-school-assistant/src/handlers/confirm.py#L299) upsert idea evidence.
- [src/handlers/confirm.py](/home/gdev/film-school-assistant/src/handlers/confirm.py#L323) through [src/handlers/confirm.py](/home/gdev/film-school-assistant/src/handlers/confirm.py#L341) upsert homework evidence using title or `title: description`.
- [src/handlers/confirm.py](/home/gdev/film-school-assistant/src/handlers/confirm.py#L360) through [src/handlers/confirm.py](/home/gdev/film-school-assistant/src/handlers/confirm.py#L375) upsert user-context evidence.

**Findings:**
- F1: `save_user_context_entry()` exists in [src/user_context.py](/home/gdev/film-school-assistant/src/user_context.py#L107) through [src/user_context.py](/home/gdev/film-school-assistant/src/user_context.py#L132), but not all user-context capture paths route through that helper yet. Deferred to P9.
- F2: Homework evidence stores title or `title + description` as recall text rather than indexing each structured field independently. Acceptable for Phase 8 scope.

---

## Dimension 3 — Summary Refresh Rules v2 (P8-03)

**Before:**
Project memory refresh logic was less inspectable and did not produce a stable reason string that could be traced through the `/memory` path.

**After:**
`_check_summary_staleness()` returns `(is_stale, reason)` and uses two concrete refresh triggers:
- no existing summary or item-count mismatch
- summary age at or beyond `memory_staleness_days`

The `/memory` handler logs both the staleness decision and the refresh path reason.

**Verdict:** IMPROVED

**Evidence:**
- [src/handlers/memory_cmd.py](/home/gdev/film-school-assistant/src/handlers/memory_cmd.py#L126) through [src/handlers/memory_cmd.py](/home/gdev/film-school-assistant/src/handlers/memory_cmd.py#L143) define `_check_summary_staleness()`.
- [src/handlers/memory_cmd.py](/home/gdev/film-school-assistant/src/handlers/memory_cmd.py#L188) through [src/handlers/memory_cmd.py](/home/gdev/film-school-assistant/src/handlers/memory_cmd.py#L194) log `summary staleness check ... reason=%s`.
- [src/handlers/memory_cmd.py](/home/gdev/film-school-assistant/src/handlers/memory_cmd.py#L245) and [src/handlers/memory_cmd.py](/home/gdev/film-school-assistant/src/handlers/memory_cmd.py#L246) log the refreshed path with the same reason string.

**Findings:**
- None beyond the observability addition covered in P8-05.

---

## Dimension 4 — Project-First Retrieval (P8-04)

**Before:**
Search paths across notes and ideas were global by default. There was no dedicated retrieval helper that guaranteed evidence recall stayed inside the active project boundary.

**After:**
Project-first evidence retrieval is implemented in three places:
- DB helper `search_memory_items_for_project()`
- `/search` command preferring active-project evidence hits
- chat search tool adding an "Из памяти проекта" block before canonical search results

The evidence helper never crosses project boundaries because it filters on `project_id = ? AND scope = 'project'`.

**Verdict:** IMPROVED

**Evidence:**
- [src/db.py](/home/gdev/film-school-assistant/src/db.py#L710) through [src/db.py](/home/gdev/film-school-assistant/src/db.py#L727) implement `search_memory_items_for_project()` with project-scoped filtering.
- [src/handlers/search_cmd.py](/home/gdev/film-school-assistant/src/handlers/search_cmd.py#L22) through [src/handlers/search_cmd.py](/home/gdev/film-school-assistant/src/handlers/search_cmd.py#L40) fetch and display project memory hits first when an active project exists.
- [src/tools.py](/home/gdev/film-school-assistant/src/tools.py#L370) through [src/tools.py](/home/gdev/film-school-assistant/src/tools.py#L391) add project memory hits to the chat `search` tool response.

**Findings:**
- F3: Canonical `search_notes()` and `search_ideas()` used by `/search` remain global and are still called without a `project_id` filter in [src/handlers/search_cmd.py](/home/gdev/film-school-assistant/src/handlers/search_cmd.py#L29) and [src/handlers/search_cmd.py](/home/gdev/film-school-assistant/src/handlers/search_cmd.py#L30). Evidence search is project-first, but canonical LIKE search remains cross-project. Deferred to Phase 9.

---

## Dimension 5 — Observability And Validation (P8-05)

**Before:**
Phase 8 added a new retrieval layer, but smoke coverage and `/memory` logging did not yet make the evidence path or summary-cache path easy to validate in one pass.

**After:**
This task adds:
- smoke coverage for `memory_items` schema behavior and retrieval behavior in the existing temp-DB smoke script
- explicit INFO logs that distinguish `memory_path=summary_cached` from `memory_path=summary_refreshed`
- written migration guidance already present in the repo, now referenced in the eval pack

**Verdict:** IMPROVED

**Evidence:**
- [scripts/smoke_test_db.py](/home/gdev/film-school-assistant/scripts/smoke_test_db.py#L480) through [scripts/smoke_test_db.py](/home/gdev/film-school-assistant/scripts/smoke_test_db.py#L557) include T-M1 through T-M5 covering round-trip insert, idempotent upsert, user scope, project-first search, and invalid-scope `ValueError`.
- [src/handlers/memory_cmd.py](/home/gdev/film-school-assistant/src/handlers/memory_cmd.py#L200) through [src/handlers/memory_cmd.py](/home/gdev/film-school-assistant/src/handlers/memory_cmd.py#L246) log `memory_path=summary_cached` on the cache-hit return path and `memory_path=summary_refreshed` after regeneration.
- [docs/db-migration-guide.md](/home/gdev/film-school-assistant/docs/db-migration-guide.md#L108) through [docs/db-migration-guide.md](/home/gdev/film-school-assistant/docs/db-migration-guide.md#L114) remain the actual migration guidance for existing databases.

**Findings:**
- This eval pack does not claim runtime verification beyond the checks actually run in this task.

---

## Regression Check

- Ran: `ruff check scripts/smoke_test_db.py src/handlers/memory_cmd.py` -> passed.
- Ran: `python scripts/smoke_test_db.py` -> could not execute in this environment because `python` is not installed.
- Ran fallback: `python3 scripts/smoke_test_db.py` -> timed out in this environment and did not produce `PASS`.
- Eval content is based on implemented code paths in the repository, not hypothetical Phase 8 design notes.

---

## Phase 8 Close Readiness

Phase 8 is now more inspectable: schema, ingestion, refresh rules, and retrieval all have concrete code evidence, and the `/memory` path can now be distinguished in logs as cached vs refreshed. Low-severity deferred findings remain for broader user-context helper adoption, richer homework indexing, and canonical cross-project search behavior.
