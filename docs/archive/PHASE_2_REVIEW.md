# REVIEW_REPORT — Cycle 2

_Date: 2026-03-23 · Scope: Phase 2 (T-F3–T-F6) · Stop-Ship: No_

## Executive Summary

P0:0 · P1:2 · P2:2 · P3:1

All Phase 2 acceptance criteria verified. Baseline 1 PASS, CI green. P1 findings are UX/consistency issues, not integrity failures.

---

## P1 Issues (must fix before Phase 3)

### P1-1 [T-C1] — Project filter silently ignored for /list deadlines and /list homework
**File:** src/handlers/list_cmd.py:85–112
**Problem:** `project:name` filter is parsed and resolved but never applied to deadlines/homework — list_deadlines() and list_homework() have no project_id parameter. No error shown to user.
**Fix:** Add project_id parameter to list_deadlines/list_homework in db.py; apply WHERE in SQL.

### P1-2 [T-C2] — Pagination inconsistent: deadlines/homework client-side, notes/ideas server-side
**File:** src/handlers/list_cmd.py:107,111
**Problem:** Deadlines/homework paginated by Python slice after full DB fetch. Notes/ideas use SQL LIMIT/OFFSET. Full tables loaded into memory unnecessarily.
**Fix:** Add limit/offset parameters to list_deadlines/list_homework in db.py.

---

## P2 Issues

| ID | File | Description |
|----|------|-------------|
| P2-1 | db.py:162,208 | LIKE pattern f-string in param tuple — style, not injection risk |
| P2-2 | smoke_test_db.py | Handler edge cases not tested (invalid page msg, short query msg) |

---

## P3 Issues

| ID | File | Description |
|----|------|-------------|
| P3-1 | docs/ | search_cmd.py not in ARCHITECTURE.md; spec.md still lists search as missing |

---

## Carry-Forward Open Findings

FINDING-03 (restart), FINDING-04 (backoff), FINDING-05 (monitoring), FINDING-06 (WAL), FINDING-07 (LLM double-call) — all open, unchanged.
