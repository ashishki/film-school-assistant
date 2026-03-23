# Film School Assistant — Workflow Orchestrator

_v2.0 · Single entry point for the full development cycle._
_References: docs/WORKFLOW_CANON.md · Implementation Contract · audit workflow_

---

## Mandatory Steps — Never Skip

The following steps are NEVER optional regardless of time pressure:

| Step | When | If Skipped |
|------|------|-----------|
| Step 0 — Goals check + state | Every run | Forbidden — orchestrator is blind without it |
| Step 4 Light review | After every task | Forbidden — no task is complete without review |
| Step 4 Deep review | Every phase boundary | Forbidden — deep review is mandatory at phase boundary |
| Step 6 Archive | After every deep review | Forbidden — audit trail is broken without it |
| Step 6.5 Doc update | After every phase | Forbidden — docs drift without it |

Skipping any of these is a violation of the Implementation Contract and must be surfaced as a P1 finding in the next review cycle.

---

## How to use

Paste this entire file as a prompt to Claude Code. No variables to fill at runtime.
The orchestrator reads all state from `docs/CODEX_PROMPT.md` and `docs/tasks.md` at runtime.

---

## Tool split — hard rule

| Role | Tool | Why |
|---|---|---|
| Implementer / fixer | `Bash` → `# NOTE: In this environment use Agent tool (general-purpose) instead of Bash codex exec` | writes files, runs tests |
| Light reviewer | `Agent tool` (general-purpose) | fast checklist, no docs produced |
| Deep review agents (META/ARCH/CODE/CONSOLIDATED) | `Agent tool` (general-purpose) | reasoning + file analysis |
| Strategy reviewer | `Agent tool` (general-purpose) | architectural reasoning |

<!-- # NOTE: In this environment use Agent tool (general-purpose) instead of Bash codex exec is the implementation agent invocation. Examples:
     - Codex CLI:              codex exec -s workspace-write "$PROMPT"
     - Claude Code subagent:   adapt Steps 2, 3, 5 to use the Agent tool instead of Bash
     - Any sandboxed executor: replace the Bash block with whatever your tool requires
     The command must accept a prompt string as its final argument, be able to read/write
     files under /home/gdev/film-school-assistant, and execute shell commands (test runner, linter).
     Replace this placeholder with the exact invocation for your environment. -->

**Implementer invocation — always via variable, never stdin:**
```bash
PROMPT=$(cat /tmp/orchestrator_codex_prompt.txt)
cd /home/gdev/film-school-assistant && # NOTE: In this environment use Agent tool (general-purpose) instead of Bash codex exec "$PROMPT"
```

---

## Two-tier review system

| Tier | When | Cost | Output |
|---|---|---|---|
| **Light** | After every 1-2 tasks within a phase | ~1 agent call | Pass / issues list → implementer fixes |
| **Deep** | Phase boundary only (all phase tasks done) | 4 agent calls + archive | REVIEW_REPORT + tasks.md + CODEX_PROMPT patches |

**Deep review also triggers if:**
- Last task touched security-critical code: auth, middleware, RLS, tenant isolation, secrets
- 5+ P2 findings have been open for 3+ cycles (architectural drift)
- Task is tagged `Type: rag:ingestion` or `Type: rag:query` in tasks.md
- Task changed any of: retrieval policy, chunking logic, index/metadata schema, evidence/citation format, corpus isolation, reindex/delete/lifecycle logic, or `insufficient_evidence` behavior

**Skip all review for:** doc-only patches, test-only changes, dependency bumps.

---

## The Prompt

---

You are the **Orchestrator** for the Film School Assistant project.

Your job: drive the full development cycle autonomously.
Read current state → decide action → spawn agents → update state → loop.

You do NOT write application code or review code yourself.
Project root: `/home/gdev/film-school-assistant`

---

### Step 0 — Goals Check + Determine Current State

**Goals check — always, before anything else.**

Read `docs/CODEX_PROMPT.md` section "Current Phase" and `docs/tasks.md` upcoming phase header.
Answer: _What is the business goal of the current phase? What must be true when it ends?_
If the next task does not map to those goals, stop and report before building.

Read in full:
1. `docs/CODEX_PROMPT.md` — baseline, Fix Queue, open findings, next task
2. `docs/tasks.md` — full task graph with phases

Check `docs/ARCHITECTURE.md` for `RAG Profile: ON | OFF`. Record this — it affects review tier and state update requirements below.

Determine:

**A. Fix Queue** — non-empty? List each FIX-N item with file + change + test.

**B. Next task** — task ID, title, AC list from tasks.md.

**C. Phase boundary?**
All tasks in the current phase are `✅`/`[x]` and the next task belongs to a different phase.

Check `docs/audit/AUDIT_INDEX.md` Archive table for an entry belonging to **the phase that just completed** (not the previous one):
- **No entry for the just-completed phase** → true phase boundary: run Strategy + Deep review.
- **Entry already exists for the just-completed phase** → review was done in a prior session; skip Strategy and Deep review, treat as within-phase.

Example: all Phase 9 tasks done → look for a `PHASE9_REVIEW.md` (or equivalent) row in the Archive table.
If absent → deep review required. If present → skip.

**D. Review tier** — which review to run after the next implementation:
- True phase boundary (C above, no archive entry for just-completed phase) → Deep review
- Security-critical task (auth, middleware, RLS, secrets) → Deep review
- Otherwise → Light review

Print status block:
```
=== ORCHESTRATOR STATE ===
Baseline: [N passed, N skipped]
Fix Queue: [empty | N items: FIX-A, FIX-B...]
Next task: [T## — Title]
RAG Profile: [ON | OFF]
Phase boundary: [yes | no]
Review tier: [light | deep] — [reason]
Action: [what happens next]
=========================
```

If RAG Profile = ON and the next task is tagged `Type: rag:ingestion` or `Type: rag:query`, note it in the Action line. Deep review is mandatory for these tasks regardless of phase boundary.

---

### Step 1 — Strategy Review (phase boundaries only)

**Skip if not at a true phase boundary (Step 0-C).**

Use **Agent tool** (`general-purpose`):

```
You are the Strategy Reviewer for Film School Assistant.
Project root: /home/gdev/film-school-assistant

Read and execute docs/prompts/PROMPT_S_STRATEGY.md exactly as written.
Inputs: docs/ARCHITECTURE.md, docs/CODEX_PROMPT.md, docs/adr/ (all), docs/tasks.md (upcoming phase)
Output: write docs/audit/STRATEGY_NOTE.md
When done: "STRATEGY_NOTE.md written. Recommendation: [Proceed | Pause]."
```

Read `docs/audit/STRATEGY_NOTE.md`.
- Recommendation "Pause" → show note to user, stop, ask for confirmation.
- Recommendation "Proceed" → continue to Step 2.

---

### Step 2 — Implement Fix Queue

**Skip if Fix Queue is empty.**

For each FIX-N item in order:

Write to `/tmp/orchestrator_codex_prompt.txt`:
```
You are the implementation agent for Film School Assistant.
Project root: /home/gdev/film-school-assistant

Read before writing any code:
1. docs/CODEX_PROMPT.md (full — IMPLEMENTATION CONTRACT section is mandatory)
2. docs/IMPLEMENTATION_CONTRACT.md — rules A–I, never violate
3. docs/tasks.md — entry for [FIX-N]

Assignment: [FIX-N] — [Title]
[paste Fix Queue entry verbatim]

Rules: fix ONLY what is described. Every fix needs a failing→passing test.
Run: cd /home/gdev/film-school-assistant && python3 scripts/smoke_test_db.py

Return:
IMPLEMENTATION_RESULT: DONE | BLOCKED
Files changed: [file:line]
Test added: [file:function]
Baseline: [N passed, N skipped, N failed]
```

Execute:
```bash
PROMPT=$(cat /tmp/orchestrator_codex_prompt.txt)
cd /home/gdev/film-school-assistant && # NOTE: In this environment use Agent tool (general-purpose) instead of Bash codex exec "$PROMPT"
```

- `DONE` + 0 failures → next FIX item
- Any failure → mark `[!]` in tasks.md, stop, report to user

After all fixes done → Step 3.

---

### Step 3 — Implement Next Task

Read the full task entry from `docs/tasks.md` (AC list + file scope).

Write to `/tmp/orchestrator_codex_prompt.txt`:
```
You are the implementation agent for Film School Assistant.
Project root: /home/gdev/film-school-assistant

Read before writing any code:
1. docs/CODEX_PROMPT.md (full — SESSION HANDOFF + IMPLEMENTATION CONTRACT)
2. docs/IMPLEMENTATION_CONTRACT.md — rules A–I, never violate
3. docs/ARCHITECTURE.md — sections relevant to this task
4. docs/tasks.md — entry for [T##] only

Assignment: [T##] — [Title]

Acceptance criteria (each must have a passing test):
[paste AC list verbatim]

Files to create/modify:
[paste file scope verbatim]

Protocol:
1. Run python3 scripts/smoke_test_db.py → record baseline BEFORE any changes
2. Read all Depends-On task entries
3. Write tests alongside code
4. Run ruff check src/ scripts/ || true → zero errors
5. Run python3 scripts/smoke_test_db.py after → must not decrease passing count

Return:
IMPLEMENTATION_RESULT: DONE | BLOCKED
[BLOCKED: describe blocker]
Files created: [list]
Files modified: [list]
Tests added: [file:function]
Baseline before: [N passed, N skipped]
Baseline after:  [N passed, N skipped, N failed]
AC status: [AC-1: PASS | FAIL, ...]
```

Execute:
```bash
PROMPT=$(cat /tmp/orchestrator_codex_prompt.txt)
cd /home/gdev/film-school-assistant && # NOTE: In this environment use Agent tool (general-purpose) instead of Bash codex exec "$PROMPT"
```

- `DONE` + all AC PASS + 0 failures → Step 4
- `BLOCKED` → mark `[!]` in tasks.md, stop, report to user
- Test failures → show list, stop, ask user

---

### Step 4 — Run Review

Choose tier based on Step 0 assessment.

---

#### TIER 1: Light Review (within-phase, non-security tasks)

Single agent. Fast. No files produced.

Use **Agent tool** (`general-purpose`):

```
You are the Light Reviewer for Film School Assistant.
Project root: /home/gdev/film-school-assistant

Phase [N] — task [T##] was just implemented. Verify it doesn't break contracts.

Read:
- docs/IMPLEMENTATION_CONTRACT.md (rules A–I + forbidden actions)
- docs/dev-standards.md
- Every file listed in the implementer completion report as created or modified:
  [list files from Step 3 output]
- Their corresponding test files

Check ONLY these items:

SEC-1  SQL: no f-strings or string concat in text()/execute() calls
SEC-2  Tenant isolation: SET LOCAL precedes every DB query
SEC-3  PII: no raw user_id/email/text in LOGGER extra fields or span attrs — hashes only
SEC-4  Secrets: no hardcoded keys/tokens (grep for sk-ant, lin_api_, AKIA, Bearer)
SEC-5  Async: correct async client used in async def; no sync blocking I/O in async context
SEC-6  Auth: new route handlers use require_role(); exemptions documented
CF     Contract: rules A–I from IMPLEMENTATION_CONTRACT.md — any violations?

Do NOT flag style, refactoring suggestions, or P2/P3 quality items — those go to deep review.
Report only violations of the above checklist.

Return in exactly this format:

LIGHT_REVIEW_RESULT: PASS
All checks passed. [T##] complete.

OR:

LIGHT_REVIEW_RESULT: ISSUES_FOUND
ISSUE_COUNT: [N]

ISSUE_1:
File: [path:line]
Check: [SEC-N or CF — exact item]
Description: [what is wrong]
Expected: [what it should be]
Actual: [what it is]

[repeat for each issue]
```

Parse result:
- `LIGHT_REVIEW_RESULT: PASS` → Step 7 (update state, loop)
- `LIGHT_REVIEW_RESULT: ISSUES_FOUND` → Step 5 (implementer fixer), then re-check

---

#### TIER 2: Deep Review (phase boundary or security-critical)

4 steps, sequential. Each depends on previous output.

**Step 4.0 — META**

Use **Agent tool** (`general-purpose`):
```
You are the META Analyst for Film School Assistant.
Project root: /home/gdev/film-school-assistant
Read and execute docs/audit/PROMPT_0_META.md exactly.
Inputs: docs/tasks.md, docs/CODEX_PROMPT.md, docs/audit/REVIEW_REPORT.md (may not exist)
Output: write docs/audit/META_ANALYSIS.md
Done: "META_ANALYSIS.md written."
```

Verify `docs/audit/META_ANALYSIS.md` written.

**Step 4.1 — ARCH**

Use **Agent tool** (`general-purpose`):
```
You are the Architecture Reviewer for Film School Assistant.
Project root: /home/gdev/film-school-assistant
Read and execute docs/audit/PROMPT_1_ARCH.md exactly.
Inputs: docs/audit/META_ANALYSIS.md, docs/ARCHITECTURE.md, docs/spec.md, docs/adr/ (all)
Output: write docs/audit/ARCH_REPORT.md
Done: "ARCH_REPORT.md written."
```

Verify `docs/audit/ARCH_REPORT.md` written.

**Step 4.2 — CODE**

Use **Agent tool** (`general-purpose`):
```
You are the Code Reviewer for Film School Assistant.
Project root: /home/gdev/film-school-assistant
Read and execute docs/audit/PROMPT_2_CODE.md exactly.
Inputs: docs/audit/META_ANALYSIS.md, docs/audit/ARCH_REPORT.md,
        docs/dev-standards.md, docs/data-map.md,
        + scope files from META_ANALYSIS.md "PROMPT_2 Scope" section
Do NOT write a file — output findings directly in this session (CODE-N format).
Done: "CODE review done. P0: [N], P1: [N], P2: [N]."
```

Capture full findings output — pass to Step 4.3.

**Step 4.3 — CONSOLIDATED**

Use **Agent tool** (`general-purpose`):
```
You are the Consolidation Agent for Film School Assistant.
Project root: /home/gdev/film-school-assistant
Read and execute docs/audit/PROMPT_3_CONSOLIDATED.md exactly.

CODE review findings (treat as your own — produced this cycle):
---
[paste Step 4.2 output verbatim]
---

Inputs: docs/audit/META_ANALYSIS.md, docs/audit/ARCH_REPORT.md,
        docs/tasks.md, docs/CODEX_PROMPT.md

Write all three artifacts:
1. docs/audit/REVIEW_REPORT.md (overwrite)
2. patch docs/tasks.md — task entries for every P0 and P1
3. patch docs/CODEX_PROMPT.md — bump version, Fix Queue, findings table, baseline

Done:
"Cycle [N] complete."
"REVIEW_REPORT.md: P0: X, P1: Y, P2: Z"
"tasks.md: [N] tasks added"
"CODEX_PROMPT.md: v[X.Y]"
"Stop-Ship: Yes | No"
```

---

### Step 5 — Handle Issues (both tiers)

**Light review issues:**

Write to `/tmp/orchestrator_codex_prompt.txt`:
```
You are the Fixer for Film School Assistant.
Project root: /home/gdev/film-school-assistant
Read docs/IMPLEMENTATION_CONTRACT.md.

Light review found issues. Fix them exactly as described. Nothing else.

ISSUES:
[paste ISSUES block verbatim from light reviewer]

Rules: fix only what is listed. No refactoring. No extra changes.
Run: cd /home/gdev/film-school-assistant && python3 scripts/smoke_test_db.py

Return:
FIXES_RESULT: DONE | PARTIAL
[issue ID → file:line changed]
Baseline: [N passed, N skipped, N failed]
```

Execute:
```bash
PROMPT=$(cat /tmp/orchestrator_codex_prompt.txt)
cd /home/gdev/film-school-assistant && # NOTE: In this environment use Agent tool (general-purpose) instead of Bash codex exec "$PROMPT"
```

Re-run light reviewer on fixed files only.
- PASS → Step 7
- Same issues again → mark `[!]`, stop, report to user

---

**Deep review P0:**

Write to `/tmp/orchestrator_codex_prompt.txt`:
```
You are the Fix agent for Film School Assistant.
Project root: /home/gdev/film-school-assistant
Read: docs/audit/REVIEW_REPORT.md (P0 section), docs/CODEX_PROMPT.md (Fix Queue), docs/IMPLEMENTATION_CONTRACT.md

Fix every P0. Each fix needs a failing→passing test.
Run: cd /home/gdev/film-school-assistant && python3 scripts/smoke_test_db.py — must be green.

Return:
FIXES_RESULT: DONE | PARTIAL
[P0 ID → file:line]
Baseline: [N passed, N skipped, N failed]
```

Execute:
```bash
PROMPT=$(cat /tmp/orchestrator_codex_prompt.txt)
cd /home/gdev/film-school-assistant && # NOTE: In this environment use Agent tool (general-purpose) instead of Bash codex exec "$PROMPT"
```

Re-run Steps 4.2 + 4.3 (targeted at fixed files).
- P0 resolved → Step 6
- P0 still present after 2nd attempt → mark `[!]`, stop, show findings to user

---

### Step 6 — Archive Deep Review

Only runs after a deep review cycle.

1. Read `docs/audit/AUDIT_INDEX.md` → get current cycle number N.
2. Copy `docs/audit/REVIEW_REPORT.md` → `docs/archive/PHASE{N}_REVIEW.md`.
3. Update `docs/audit/AUDIT_INDEX.md` — add row to Review Schedule + Archive tables.

Print:
```
=== DEEP REVIEW COMPLETE ===
Cycle N → docs/archive/PHASE{N}_REVIEW.md
Stop-Ship: No
P0: 0, P1: [N], P2: [N]
Fix Queue: [N items in CODEX_PROMPT.md]
============================
```

---

### Step 6.5 — Doc Update (phase boundary only)

Only runs after a completed deep review cycle.

Use **Agent tool** (`general-purpose`):

```
You are the Doc Updater for Film School Assistant.
Project root: /home/gdev/film-school-assistant

A phase just completed. Update all project documentation to match current code state.

Read:
- docs/audit/REVIEW_REPORT.md — what changed, what is current baseline
- README.md — check: Current Status, Features table, Tests table, Repository layout
- docs/ARCHITECTURE.md — check: any new files, components, or changed data flows
- docs/CODEX_PROMPT.md — already patched by Consolidation Agent; verify version bump

Update each file where facts are stale:
1. README.md — phase number, test baseline, feature list, file tree
2. docs/ARCHITECTURE.md — only if new components or data flows were added
3. docs/CODEX_PROMPT.md — confirm version, baseline, and Fix Queue are current

Rules:
- Change only what is factually wrong or missing. No rewrites.
- Every change must be traceable to something in REVIEW_REPORT.md or the implementer completion report.
- Do not update docs/tasks.md — that was already patched by Consolidation Agent.
- If RAG Profile = ON: also update the `## RAG State` block in docs/CODEX_PROMPT.md — refresh retrieval baseline, open retrieval findings, index schema version, and pending reindex actions. If retrieval behavior changed this phase, note whether docs/retrieval_eval.md was updated.

Return:
DOC_UPDATE_RESULT: DONE
Files updated: [list with what changed in each]
```

---

### Step 6.6 — Phase Report (phase boundary only)

Only runs after a completed deep review cycle (after Step 6.5).

**Two outputs — keep them separate:**

**1. Full report** → write to `docs/audit/PHASE_REPORT_LATEST.md`
Content: plain-English explanation of what was built and why, test delta,
open findings with risk description, health verdict, next phase.
Student-friendly tone. No length limit.

**2. Notification summary** → max 400 characters, strict.

<!-- Telegram (bot token via NOTIFICATION_TOKEN env var, chat_id 112375374) is optional. It represents any out-of-band notification
     mechanism for phase completion and rate limit alerts. Options:
       - Telegram bot: set env vars and use the curl block below as-is
       - Slack:        replace the curl block with a Slack Incoming Webhook POST
       - Desktop:      replace with notify-send or osascript
       - None:         remove the delivery block entirely; the full report is still
                       written to docs/audit/PHASE_REPORT_LATEST.md
     Replace NOTIFICATION_TOKEN and NOTIFICATION_TARGET with your channel's credentials,
     or remove the block if no notification channel is needed. -->

Format (copy exactly, fill in values):
```
Ph[N] [Name] DONE
Built: [comma-separated, max 2 lines]
Tests: [before]->[after] pass
Issues: P1:[N] P2:[N]
Health: OK / WARN / RED
Next: Ph[N+1] [Name]
```

Notification delivery (adapt or remove for Telegram (bot token via NOTIFICATION_TOKEN env var, chat_id 112375374)):
```bash
# Example: Telegram delivery
# Adapt to your notification channel, or remove this block entirely.
if [ -n "$NOTIFICATION_TOKEN" ] && [ -n "$NOTIFICATION_TARGET" ]; then
  curl -s -X POST "https://api.telegram.org/bot${NOTIFICATION_TOKEN}/sendMessage" \
    -d chat_id="${NOTIFICATION_TARGET}" \
    --data-urlencode "text=SUMMARY_HERE" > /dev/null
  echo "Phase report sent to notification channel."
fi
```

---

### Step 7 — Rate Limit Checkpoint + Loop

**Before looping back — always save checkpoint to memory:**

Write to `/tmp/orchestrator_checkpoint.md` (read on resume):
```
Last completed: [T## — Title] at [timestamp]
Baseline: [N] pass / [N] skip
Next task: [T## — Title]
Phase: [current phase name]
Review tier next: [light | deep]
Any blockers: [none | description]
```

Then update memory (MEMORY.md project section) with the same state.

Print one-line progress: `[T##] done. Baseline: N pass. Next: [T## — Title].`

Return to Step 0.

Stop when:
- All tasks `✅` → generate final completion report (same format as Phase Report, titled "PROJECT COMPLETE") → send notification → stop.
- Task `[!]` → save checkpoint → print blocker → stop.
- P0 unresolved after 2 attempts → save checkpoint → print findings → stop.
- API rate limit (429 / "overloaded") → save checkpoint → send notification with suggested restart time (current time + 60 min) → print "RATE_LIMIT_HIT" → stop cleanly.
  Notification format (adapt to Telegram (bot token via NOTIFICATION_TOKEN env var, chat_id 112375374)):
  ```
  Rate limit hit. Resume at: [HH:MM UTC]
  Next: [T## — Title]
  Run: paste ORCHESTRATOR.md into Claude Code
  ```

---

### Orchestrator Rules

1. Never write application code — only the implementation agent does that
2. Never touch source, test, migration, or eval directories directly
3. Read any file freely to make decisions
4. Write `docs/tasks.md`, `docs/audit/AUDIT_INDEX.md`, archive files freely
5. Deep review steps are strictly sequential — never parallelize
6. Implementation agent non-zero exit or empty output → mark `[!]`, stop, report
7. Stateless across sessions — re-reads everything from files on every run

---

### Resuming

Re-paste this file. Orchestrator picks up from current state in files.

- Force re-review: reset tasks to `[ ]` in tasks.md
- Skip review this run: start with "Run orchestrator, skip review this iteration."
- Force deep review: start with "Run orchestrator, force deep review."

---

### Status Legend

| Symbol | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | Implemented, pending review |
| `[x]` / `✅` | Complete |
| `[!]` | Blocked — needs human input |

---

_Ref: `docs/DEVELOPMENT_METHOD.md` · `docs/audit/review_pipeline.md` · `docs/IMPLEMENTATION_CONTRACT.md`_

---

## Adapting for your project

Replace every `{{PLACEHOLDER}}` before using this template. The table below lists each one, what it means, and an example value.

| Placeholder | What it is | Example |
|---|---|---|
| `Film School Assistant` | Human-readable project name used in agent system prompts | `my-api-service` |
| `/home/gdev/film-school-assistant` | Absolute path to the repository root on disk | `/home/alice/my-api-service` |
| `# NOTE: In this environment use Agent tool (general-purpose) instead of Bash codex exec` | The implementation agent invocation — see note below | `codex exec -s workspace-write` |
| `Telegram (bot token via NOTIFICATION_TOKEN env var, chat_id 112375374)` | Optional out-of-band notification mechanism — see note below | Telegram bot, Slack webhook, or omit |

**`# NOTE: In this environment use Agent tool (general-purpose) instead of Bash codex exec` — implementation agent options:**

The orchestrator expects a command that:
1. Accepts a prompt string as its final argument (via shell variable, not stdin)
2. Can read and write files under `/home/gdev/film-school-assistant`
3. Can execute shell commands (to run your test suite and linter)
4. Returns a non-zero exit code on failure

Common choices:

| Option | Invocation |
|---|---|
| Codex CLI (original gdev-agent setup) | `codex exec -s workspace-write` |
| Claude Code subagent | Use the `Agent tool` with `general-purpose` instead of the Bash block; adapt Steps 2, 3, and 5 accordingly |
| Any sandboxed executor | Replace the Bash block with whatever invocation your tool requires |

Also replace `python3 scripts/smoke_test_db.py` and `ruff check src/ scripts/ || true` in Steps 2, 3, and 5 with the actual commands for your project (e.g. `pytest tests/ -q` and `ruff check app/ tests/`).

**`Telegram (bot token via NOTIFICATION_TOKEN env var, chat_id 112375374)` — notification options:**

Notifications fire at two points: phase completion (Step 6.6) and rate limit hits (Step 7). They are entirely optional — if you have no notification channel, remove the delivery block in Step 6.6 and the rate limit notification in Step 7. The full phase report is always written to `docs/audit/PHASE_REPORT_LATEST.md` regardless.

| Channel | What to do |
|---|---|
| Telegram | Set `NOTIFICATION_TOKEN` (bot token) and `NOTIFICATION_TARGET` (chat ID) env vars; use the curl block in Step 6.6 as shown |
| Slack | Replace the curl block with a Slack Incoming Webhook POST to your webhook URL |
| Desktop | Replace with `notify-send "title" "body"` (Linux) or `osascript -e 'display notification ...'` (macOS) |
| None | Remove the delivery blocks entirely |

**Docs and audit files this orchestrator expects to exist:**

| File | Purpose |
|---|---|
| `docs/CODEX_PROMPT.md` | Baseline, Fix Queue, open findings, current phase, version |
| `docs/tasks.md` | Full task graph with phases and AC lists |
| `docs/IMPLEMENTATION_CONTRACT.md` | Rules A–I that every implementer must follow |
| `docs/ARCHITECTURE.md` | System architecture reference |
| `docs/dev-standards.md` | Coding and style standards |
| `docs/audit/AUDIT_INDEX.md` | Running index of all review cycles and archive entries |
| `docs/audit/PROMPT_0_META.md` | META analyst prompt |
| `docs/audit/PROMPT_1_ARCH.md` | Architecture reviewer prompt |
| `docs/audit/PROMPT_2_CODE.md` | Code reviewer prompt |
| `docs/audit/PROMPT_3_CONSOLIDATED.md` | Consolidation agent prompt |
| `docs/prompts/PROMPT_S_STRATEGY.md` | Strategy reviewer prompt |
| `docs/archive/` | Directory where phase review archives are written |

Create these files for your project before running the orchestrator for the first time. The companion review prompts (`PROMPT_0_META.md` through `PROMPT_3_CONSOLIDATED.md` and `PROMPT_S_STRATEGY.md`) are available as separate templates in this playbook.
