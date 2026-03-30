# Film School Assistant — Task Graph

Status legend:
- `[ ]` not started
- `[-]` in progress
- `[x]` done
- `[!]` blocked

Current phase goal:
- harden the existing single-user assistant without increasing solution-shape, runtime, or
  governance complexity

---

## Phase 6 — Hardening and Measurement

Goal:
- close the highest-value operational gaps in the current bounded assistant
- improve reliability and measurement without adding new architecture classes

Exit criteria:
- SQLite runtime expectations are verified at startup
- weekly summary path avoids unnecessary duplicate work
- Telegram delivery helper logic is consistent across scripts
- voice pipeline boundary is testable in CI
- operational and AI-path baselines are recorded

[ ] T61 — Verify SQLite WAL mode and startup contract
Owner: codex
Phase: 6
Type: none
Depends-On: none
Objective: |
  Assert the expected SQLite runtime mode on startup and document the operational contract so
  the database behavior does not silently drift across environments.
Acceptance-Criteria:
  - id: AC-1
    description: "Application startup verifies the intended SQLite journal mode."
    test: "pytest tests/test_db_startup.py::test_sqlite_journal_mode_verified"
  - id: AC-2
    description: "Architecture, spec, and contract docs reflect the SQLite runtime expectation."
    test: "manual-doc-check"
Files:
  - src/db.py
  - tests/test_db_startup.py
  - docs/ARCHITECTURE.md
  - docs/IMPLEMENTATION_CONTRACT.md
Notes: |
  This is a deterministic hardening task. It must not introduce new persistence layers or
  runtime tiers.

[ ] T62 — Skip weekly-summary inference when the report is already sent
Owner: codex
Phase: 6
Type: tool:call
Depends-On: none
Objective: |
  Ensure the weekly summary flow exits before performing an unnecessary AI call when the
  current reporting period is already completed.
Acceptance-Criteria:
  - id: AC-1
    description: "A previously completed weekly report does not trigger another summary model call."
    test: "pytest tests/test_weekly_summary.py::test_skips_generation_when_report_already_sent"
  - id: AC-2
    description: "The summary path still produces one report for a fresh reporting period."
    test: "pytest tests/test_weekly_summary.py::test_generates_summary_for_unsent_period"
Files:
  - scripts/send_weekly_summary.py
  - tests/test_weekly_summary.py
  - docs/nfr.md
Notes: |
  This task changes cost behavior, not architecture shape. Keep the workflow deterministic.

[ ] T63 — Consolidate Telegram send helper behavior
Owner: codex
Phase: 6
Type: tool:call
Depends-On: none
Objective: |
  Remove duplicated Telegram send/backoff behavior across scripts so operational delivery
  rules remain consistent.
Acceptance-Criteria:
  - id: AC-1
    description: "Reminder and summary scripts share one Telegram send helper path."
    test: "pytest tests/test_telegram_delivery.py::test_scripts_use_shared_send_helper"
  - id: AC-2
    description: "Transient Telegram API errors still follow the declared retry/backoff behavior."
    test: "pytest tests/test_telegram_delivery.py::test_shared_send_helper_retries_transient_failures"
Files:
  - scripts/send_reminders.py
  - scripts/send_weekly_summary.py
  - src/telegram.py
  - tests/test_telegram_delivery.py
Notes: |
  This is codebase cleanup inside the existing T1 runtime. It must not create a new worker or queue.

[ ] T64 — Isolate voice pipeline imports for CI-safe testing
Owner: codex
Phase: 6
Type: none
Depends-On: none
Objective: |
  Keep the voice pipeline testable in CI by separating import-time runtime weight from the
  code path the tests need to validate.
Acceptance-Criteria:
  - id: AC-1
    description: "Voice pipeline tests run without loading production-only Whisper dependencies at module import time."
    test: "pytest tests/test_voice_pipeline.py::test_voice_pipeline_imports_without_runtime_side_effects"
  - id: AC-2
    description: "Production voice transcription behavior remains unchanged once the runtime dependency is available."
    test: "pytest tests/test_voice_pipeline.py::test_voice_pipeline_uses_whisper_when_available"
Files:
  - src/handlers/voice_handler.py
  - scripts/test_voice_pipeline.py
  - tests/test_voice_pipeline.py
Notes: |
  Keep voice processing local. Do not replace Whisper with a hosted transcription service.

[ ] T65 — Record AI and operational NFR baseline
Owner: codex
Phase: 6
Type: none
Depends-On: T62, T63, T64
Objective: |
  Record the first explicit baseline for latency, cost, delivery reliability, and AI-path
  usage so later changes can be measured instead of guessed.
Acceptance-Criteria:
  - id: AC-1
    description: "docs/nfr.md contains baseline values or explicit measurement procedures for each declared metric."
    test: "manual-doc-check"
  - id: AC-2
    description: "CODEX_PROMPT.md baseline and open findings reflect the measured or pending metrics honestly."
    test: "manual-doc-check"
Files:
  - docs/nfr.md
  - docs/CODEX_PROMPT.md
  - README.md
Notes: |
  This task must not fabricate metrics. Unknown values are acceptable if the measurement path is explicit.
