# Phase 3 Deep Review — Reliability

_Date: 2026-03-23 · Scope: T-B1/T-O4, T-O1, T-O2, T-T1, T-T2, T-A2/A3/A4_

## Executive Summary

P0:0 · P1:0 · P2:1 · P3:0

All Phase 3 tasks complete. Three open findings resolved (FINDING-03, FINDING-04, FINDING-05).
Sync/async boundary handled correctly. One soft maintenance note (P2).

---

## META Analysis

**Resolved Findings:**
- FINDING-03 ✅: `notify_restart_if_pending()` queries unconfirmed parsed_events on startup via `asyncio.to_thread()`. User notified via Telegram if pending entities found within 2 hours.
- FINDING-04 ✅: Both send_reminders.py and send_summary.py now retry Telegram sends 3x with 0.5s/1.0s/1.5s backoff. 5xx/connection errors retry; 4xx raises immediately.
- FINDING-05 ✅: `notify-failure@.service` template + `notify_failure.py` sends Telegram alert on any systemd unit failure. OnFailure= wired to all 4 oneshot services.

**Still-Open Findings:**
- FINDING-06: WAL mode unverified (pre-existing, medium)
- FINDING-07: Summary double LLM call (pre-existing, low)

**Verdict: GREEN**

---

## ARCH Report

### Contract Compliance: PASS

- INV-1 through INV-8: all satisfied
- Sync/async boundary: `get_recent_unconfirmed_events` (sync sqlite3) wrapped in `asyncio.to_thread()` — correct
- notify_failure.py: follows established script conventions (sys.path, load_config, proper exit codes)
- OnFailure loop safety: oneshot type prevents infinite retry on notification failure

### P2 Finding

**ARCH-P2-1**: Telegram retry logic (`send_telegram_message` with backoff) is duplicated in 3 files:
send_reminders.py, send_summary.py, notify_failure.py. Should eventually be extracted to
`src/telegram_client.py`. Non-blocking for MVP.

**Verdict: PASS with notes**

---

## Phase 3 Task Coverage

| Task | Status | Notes |
|------|--------|-------|
| T-B1/T-O4 | ✅ | Restart notification via post_init hook |
| T-O1 | ✅ | 3x retry with exponential backoff |
| T-O2 | ✅ | notify-failure@.service + OnFailure= on all timers |
| T-T1 | ✅ | Smoke test: status update, reminder dedup, event confirmation |
| T-T2 | ✅ | Voice pipeline test (mocked Telegram + ffmpeg + Whisper) |
| T-A2 | ✅ | dev-cycle.md: Cycles 1-4 entries |
| T-A3 | ✅ | ops-security.md: monitoring, log retention, secret rotation |
| T-A4 | ✅ | db-migration-guide.md created |

---

## Carry-Forward Open Findings

FINDING-06 (WAL mode unverified), FINDING-07 (summary LLM double-call) — pre-existing, unchanged.
ARCH-P2-1 (Telegram retry duplication) — new, non-blocking.
