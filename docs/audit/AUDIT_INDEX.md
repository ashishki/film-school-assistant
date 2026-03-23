# Audit Index — Film School Assistant

_Append-only. One row per review cycle._

---

## Review Schedule

| Cycle | Phase | Date | Scope | Stop-Ship | P0 | P1 | P2 |
|-------|-------|------|-------|-----------|----|----|-----|
| 1 | High-priority features (T-F1, T-F2) | 2026-03-23 | /new_project + entity editing | No | 0 | 0 | 1 |
| 2 | Phase 2 UX features (T-F3–T-F6) | 2026-03-23 | status filter, pagination, search, archival | No | 0 | 2 | 2 |

---

## Archive

| Cycle | File | Phase | Health |
|-------|------|-------|--------|
| 1 | — (light review only, no deep review file) | T-F1 + T-F2 | ✅ Green |
| 2 | docs/archive/PHASE_2_REVIEW.md | T-F3–T-F6 | ⚠️ Green (P1:2) |

---

## Notes

- Cycle 1: two light reviews (T-F1, T-F2), both PASS. No phase-boundary deep review yet.
- P2 open: FINDING-09 — pre-existing f-string in db.py:60 `_insert_and_fetch`. Internal constant, not user input. Low risk.
- Deep review triggers at next true phase boundary.
