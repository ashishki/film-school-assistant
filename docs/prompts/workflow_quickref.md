# Workflow Quick Reference

---

## Entry Point

There is one way to start the development cycle:

```
Send docs/prompts/workflow_orchestrator.md to Claude Code (Strategist instance).
No variables. No setup. Just paste and send.
```

The orchestrator reads `docs/tasks.md` to determine the current phase,
drives Implement → Review → Fix automatically, updates `docs/tasks.md` after each phase,
and loops until all phases are complete or a blocker is found.

---

## What the Orchestrator Does

```
Read tasks.md
  │
  └─▶ Find current phase (lowest phase with [ ] tasks)
        │
        ├─▶ Write prompt to /tmp/codex_phase_prompt.txt
        │   codex exec -s workspace-write "$PROMPT"   ← Codex Implementer
        │     └─▶ Implements all tasks in phase
        │
        ├─▶ Update tasks.md: [ ] → [~]
        │
        ├─▶ Agent tool (subagent_type: Explore)  ← Claude Reviewer
        │     ├─▶ PHASE_REVIEW_RESULT: PASS → continue
        │     └─▶ PHASE_REVIEW_RESULT: ISSUES_FOUND:
        │               ├─▶ codex exec -s workspace-write  ← Codex Fixer
        │               └─▶ Agent tool (Explore) again — targeted re-check
        │                     ├─▶ PASS → continue
        │                     └─▶ SAME ISSUES → mark [!], stop, report to user
        │
        ├─▶ Update tasks.md: [~] → [x]
        │
        └─▶ Loop to next phase
```

**Tool split — hard rule:**

| Role | Tool | Reason |
|---|---|---|
| Implementer | `codex exec -s workspace-write` (via variable) | writes files |
| Reviewer | `Agent tool` (Explore, Claude) | reasoning + checklist |
| Fixer | `codex exec -s workspace-write` (via variable) | writes fixes |

**Critical:** Always invoke codex via variable, never via stdin:
```bash
# CORRECT
PROMPT=$(cat /tmp/codex_phase_prompt.txt)
codex exec -s workspace-write "$PROMPT"

# WRONG — forces wrong model, returns 401
codex exec -s workspace-write - < /tmp/codex_phase_prompt.txt
```

---

## When the Loop Stops

| Condition | tasks.md state | Action needed |
|---|---|---|
| All phases `[x]` | All done | MVP complete — proceed to ops setup |
| Task marked `[!]` | Blocked | User must resolve blocker manually, then re-run orchestrator |
| Agent unrecoverable error | `[!]` set on failed task | Check logs, fix manually, re-run |

**Expected blocker:** P5-01 — OpenClaw API contract must be verified manually before Phase 5 can proceed.

---

## Resuming After a Stop

The orchestrator is stateless — it reads all state from `docs/tasks.md` on every run.

To resume:
1. Resolve the blocker (fix the `[!]` task manually or clear the `[!]` mark)
2. Re-send `workflow_orchestrator.md` to Claude Code
3. It picks up from the current state automatically

---

## Manual Overrides

To re-run a specific phase without re-running previous phases:
1. Open `docs/tasks.md`
2. Change the phase tasks back to `[ ]`
3. Re-send the orchestrator prompt

To skip a phase (not recommended):
1. Manually mark all its tasks `[x]` in `docs/tasks.md`
2. The orchestrator will skip it

---

## Phase Reference

| Phase | Name | Key files Codex creates |
|---|---|---|
| 0 | Repository Baseline | docs/, prompts/ (Strategist), git init (P0-11 Codex) |
| 1 | Config + Storage + Schema | src/config.py, src/schema.sql, src/db.py, requirements.txt |
| 2 | Telegram Command Flows | src/bot.py, src/state.py, src/handlers/*.py, systemd/film-school-bot.service |
| 3 | Reminders + Weekly Summary | scripts/send_reminders.py, scripts/send_summary.py, systemd/*.timer |
| 4 | Voice Ingestion | src/voice.py, src/transcriber.py |
| 5 | NL Routing + Review Mode | src/openclaw_client.py, src/reviewer.py, src/handlers/nl_handler.py, src/handlers/review.py |
| 6 | Hardening | logging throughout, scripts/cleanup_audio.py, scripts/backup_db.sh, systemd timers |

---

## tasks.md Status Legend

| Symbol | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | Implemented, pending review |
| `[x]` | Complete (implemented + reviewed) |
| `[!]` | Blocked — needs human input |

---

## Individual Agent Prompts (manual use only)

These exist for ad-hoc use or debugging — the orchestrator uses them as embedded templates:

| File | Use when |
|---|---|
| `workflow_codex_implementer.md` | Manually re-running a single phase implementation |
| `workflow_claude_reviewer.md` | Manually reviewing a specific phase |
| `workflow_codex_fixer.md` | Manually applying fixes from a review |
