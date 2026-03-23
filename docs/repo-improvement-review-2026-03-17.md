# 1. Repository Understanding
- What the bot does: a single-user Telegram assistant that captures notes, ideas, deadlines, and homework; transcribes voice notes locally with Whisper; routes free text through Anthropic for intent extraction; reviews ideas with a stronger Anthropic model; sends reminder and weekly summary messages from systemd-driven scripts.
- Main runtime flow: Telegram update enters `src/bot.py`, `chat_guard` filters by allowed chat, command handlers write directly to SQLite through `src/db.py`, free text goes through `src/handlers/nl_handler.py`, voice goes through `src/voice.py` and `src/transcriber.py`, then both use in-memory pending state from `src/state.py`.
- Main modules and responsibilities:
  - `src/bot.py`: app bootstrap, chat guard, voice flow, handler registration.
  - `src/handlers/*`: command and conversational UX.
  - `src/db.py` + `src/schema.sql`: all persistence and schema.
  - `src/openclaw_client.py`: Anthropic wrapper.
  - `src/reviewer.py`: idea-review prompting and formatting.
  - `scripts/send_reminders.py` and `scripts/send_summary.py`: scheduled delivery.
  - `systemd/*`: deployment units and timers.
- Key implementation observations inferred from the repo:
  - The code is intentionally small and readable, but a lot of product behavior is embedded in handlers instead of a thin service layer.
  - The “personal assistant” feel is limited more by UX and validation gaps than by missing infrastructure.
  - The largest risks are not scale-related; they are trust-related: malformed saved data, unfinished confirmation UX, duplicate scheduled output, and a few operational/documentation mismatches.

# 2. What Is Already Good
- The core scope discipline is strong. The repo stays local-first, SQLite-first, and systemd-first without drifting into SaaS architecture.
- The chat guard is placed early and correctly in `src/bot.py`, which matches the single-user threat model.
- Command handlers are easy to scan. Files like `src/handlers/notes.py` and `src/handlers/deadlines.py` are straightforward and pragmatic.
- The schema is auditable and boring in a good way. Tables such as `voice_inputs`, `transcripts`, `parsed_events`, `review_history`, and `weekly_reports` make the bot inspectable after failures.
- Voice input is persisted before processing in `src/bot.py`, which is the right reliability choice for a personal tool.
- The reminder system has real dedupe protection via `UNIQUE(deadline_id, days_before)` in `src/schema.sql`.
- The AI boundary is mostly sane: commands are deterministic, AI is used for extraction/review rather than everything.
- The systemd split is appropriate. Reminders and summaries do not depend on the bot process being alive.
- The repo docs are broad enough that someone returning after a few months could recover intent quickly, even though some details are out of sync.

# 3. Main Rough Edges and Risks
For each issue provide:
- Title
- Severity (High / Medium / Low)
- Where found
- Why it matters
- Recommended fix

1. Unfinished `/edit` makes the core confirmation flow feel prototype-like
- Severity: High
- Where found: `src/handlers/confirm.py`
- Why it matters: Voice and NL both instruct the user to `/edit`, but the command is a dead end. That breaks trust exactly where the bot asks for trust: after a transcription or model interpretation.
- Recommended fix: Implement minimal field-level edit for pending entities, even if it is plain text based, for example `/edit due 2026-03-28`, `/edit title ...`, `/edit content ...`. For a single-user bot, a tiny explicit edit grammar is enough.

2. Voice flow can save broken deadlines and homework with empty due dates
- Severity: High
- Where found: `src/bot.py`, `src/handlers/confirm.py`
- Why it matters: `_build_pending_entity()` sets `due_date` to `""` for voice-detected deadlines and homework, and `/confirm` will save that as if it were valid. That creates records that look real but cannot drive reminders properly.
- Recommended fix: Do not allow confirmation of deadline/homework pending items unless `due_date` parses cleanly. Reply with a corrective prompt instead of saving incomplete time-bound items.

3. Free-text NL accepts model due dates without validating them
- Severity: High
- Where found: `src/handlers/nl_handler.py`
- Why it matters: a malformed model output can be persisted as `due_date`, then later `date.fromisoformat()` in reminders can crash the run in `scripts/send_reminders.py`.
- Recommended fix: run all AI-provided dates through `parse_date_text()` or strict ISO validation before creating pending entities; if invalid, leave the item pending with “due date missing/unclear”.

4. Pending state is fragile and can be overwritten by another voice note
- Severity: High
- Where found: `src/bot.py`, `src/handlers/nl_handler.py`, `src/state.py`
- Why it matters: NL input blocks when a pending item exists, but voice input does not. A second voice note can replace the first pending item without warning. For a capture tool, silent loss of the reviewable draft is one of the worst UX failures.
- Recommended fix: add the same pending guard to `voice_handler`; optionally persist pending state to SQLite so bot restarts do not wipe the working draft.

5. Weekly summaries are not idempotent
- Severity: High
- Where found: `scripts/send_summary.py`, `src/schema.sql`
- Why it matters: there is no uniqueness on `weekly_reports.week_start` and no “already sent for this week” check. A manual rerun, timer replay, or operator retry can send duplicate Monday summaries.
- Recommended fix: add a unique constraint on `week_start` and fetch-or-create behavior before sending. If a report for that week exists with `sent_at`, exit cleanly.

6. Backup strategy is unsafe for live SQLite
- Severity: High
- Where found: `scripts/backup_db.sh`
- Why it matters: raw `cp` of a live SQLite DB is not the most trustworthy backup method, especially if WAL mode is ever enabled later. For a personal assistant, reliable restore matters more than backup minimalism.
- Recommended fix: use `sqlite3 "$DB_PATH" ".backup '$backup_path'"` or `VACUUM INTO` with basic integrity checking after backup.

7. Timezone handling is inconsistent between Python and SQLite
- Severity: Medium
- Where found: `scripts/send_reminders.py`, `src/db.py`, `scripts/send_summary.py`
- Why it matters: Python uses local `date.today()`, SQLite query logic uses `date('now')`, which is UTC. On a VPS, this can produce off-by-one reminder behavior around midnight and after DST changes.
- Recommended fix: choose one timezone policy explicitly. For this project, store dates as local calendar dates and compute reminder windows entirely in Python, or set SQLite queries to localtime consistently.

8. Voice transcription is more expensive and slower than necessary
- Severity: Medium
- Where found: `src/transcriber.py`
- Why it matters: `whisper.load_model()` runs on every transcription. On a small VPS that makes voice capture feel sluggish and less dependable.
- Recommended fix: cache the Whisper model in-process. For a single-user bot, one global lazy-loaded model is enough.

9. Product tone and formatting still feel like a developer tool
- Severity: Medium
- Where found: `src/handlers/list_cmd.py`, `scripts/send_reminders.py`, `scripts/send_summary.py`, `src/reviewer.py`
- Why it matters: the bot’s outputs are technically correct but often blunt, mechanical, or raw. For daily use, that is what makes it feel “MVP” more than the architecture does.
- Recommended fix: centralize a few response templates and tighten headings, spacing, previews, truncation, and phrasing.

10. Docs and operational reality are slightly out of sync
- Severity: Medium
- Where found: `README.md`, `docs/ops-security.md`, `systemd/film-school-bot.service`
- Why it matters: README says `python scripts/smoke_test_db.py` should pass, but in this environment dependencies were absent; ops docs claim a file logger and rotation, but services currently write only to journald; shipped systemd units use `/usr/bin/python3`, not the project venv.
- Recommended fix: make docs match actual deployment, or change the units and logging setup to match the docs. Right now it is ambiguous which truth to trust.

# 4. Improvement Opportunities by Category
## 4.1 Product / UX
- Implement real `/edit`; it is the single biggest polish gap.
- Add friendlier save confirmations that include project scope and due date in one calm template.
- Make `/list` outputs shorter, grouped, and truncated so long notes do not flood Telegram.
- Add `/project clear` and show the active project in `/projects` or `/help`.
- Treat reminders as supportive prompts, not just alerts with slash commands.
- Add a human fallback for ambiguous NL like “I can save this as a note or idea; which do you want?”

## 4.2 Architecture
- Pull shared “save pending entity” and “format reply” behavior out of handlers into a tiny application layer.
- Keep `bot.py` as wiring only; its current voice parsing helpers are product logic, not bootstrap logic.
- Split `db.py` by concern when you next touch it: `projects`, `capture`, `reviews`, `reports`, `ops`.
- Reuse the same Telegram send helper in bot and scripts to avoid message-format drift.

## 4.3 Code Quality
- Add stricter validation at boundaries, especially dates and pending entity shapes.
- Replace open-ended `dict` pending payloads with small typed dataclasses or TypedDicts.
- Reduce generic `except Exception` usage around logic errors where validation can be explicit.
- Add a few focused integration tests for reminder idempotency, pending flows, and NL malformed output handling.

## 4.4 AI / Prompting
- Validate review JSON fields more strictly; blank `core_idea` or `next_step` should not pass through as empty headings.
- Make prompts more film-school specific: ask for cinematic stakes, point of view, scene engine, and production-feasible next step.
- Add a fallback path when review JSON is malformed: return a clean textual failure, not partial emptiness.
- Align runtime prompts with the documented intent that weekly summaries should be more narrative; the current summary is deterministic copy, not synthesis.

## 4.5 Voice / Transcription
- Cache the Whisper model.
- Guard against pending overwrite before starting another voice flow.
- Clean up `.wav` files sooner; keep original `.ogg` if you want retryability, but temporary WAVs need not live for 30 days.
- Parse likely due dates from transcripts before presenting a deadline/homework preview.

## 4.6 Storage / SQLite
- Add indexes for `deadlines(status, due_date)`, `notes(project_id, created_at)`, `ideas(project_id, created_at)`, `homework(status, due_date)`.
- Add a uniqueness rule or sent-guard for weekly summaries.
- Consider lightweight CHECK constraints for statuses (`active`, `done`, `dismissed`, `pending`, `reviewed`, `unreviewed`).
- Store active project context in DB if you want restart-safe UX.

## 4.7 Scheduling / Ops
- Make summary runs idempotent.
- Use safer SQLite backups.
- Ship systemd units that already point to the venv binary or clearly template that variable.
- Add `systemctl` verification instructions and a restore drill to the docs.

## 4.8 Security / Privacy
- Do not log transcript text at INFO in future changes.
- Consider shortening audio retention or distinguishing original `.ogg` retention from transient `.wav` retention.
- Keep review prompts and stored outputs local, but be explicit in docs that idea text is sent to Anthropic for NL/review.
- Add a simple integrity check before backup rotation deletes older backups.

## 4.9 Docs / Workflow
- Update README and ops docs to reflect actual logging and service behavior.
- Add one “return after 3 months” runbook: install deps, verify DB, check timers, inspect last reminders/summary, restore backup.
- Remove or update strategy-doc claims that are no longer true, especially around weekly “narrative synthesis” and logging files.
- Add a minimal data migration note; schema changes will happen.

# 5. How to Make This Feel Truly Polished
What currently makes it feel rough is not the architecture. It is the micro-UX. The bot often sounds like a correct script rather than a thoughtful assistant. The biggest offenders are the unfinished `/edit`, raw list formatting, rigid reminder phrasing, and review output that is structurally neat but not yet clearly tuned for a film student’s creative process.

The fastest path to polish is a small response-style layer. Standardize save confirmations, clarification prompts, reminder phrasing, summary headings, and review formatting. Right now each handler speaks its own dialect. That makes the bot feel assembled rather than authored.

For capture flows, the assistant should be calm and decisive. A voice flow should read like: transcript, interpreted item type, project, due date if present, then one short action prompt. The current two-message output in `src/bot.py` is serviceable, but it needs better structure and should never advertise `/edit` until `/edit` actually works.

For reminders, stop sounding like a raw scheduler. The current format in `scripts/send_reminders.py` is functional, but a more humane version would combine urgency, project context, and one suggested next action. Example shape: title, date, project, then “Today’s move:” with something small and concrete. That is much more appropriate for a film student than `⏰ REMINDER:` plus slash commands.

For weekly summaries, the current message in `scripts/send_summary.py` is still a dashboard dump. It has the right categories, but not the right feel. A polished version would keep the same deterministic data while changing the writing structure:
- one opening sentence about the week’s center of gravity
- one urgent section
- one “creative momentum” section
- one “stalled / neglected” section
- one recommended next step tied to either deadline pressure or idea development

For reviews, the structure is good, but the tone should become more workshop-like and less JSON-shaped. `src/reviewer.py` should enforce non-empty sections and better questions. The strongest improvement would be to make `WEAK POINTS` and `QUESTIONS` more scene- and form-oriented: point of view, cinematic engine, conflict behavior, production constraints, and what image/sound logic carries the idea.

For project context, the assistant should make the active project more visible. Right now `/project` sets state silently except for one confirmation. That means the user can forget what context they are in. Show active project in `/help`, in save confirmations, and in `/projects` with a marker.

For error language, remove generic vagueness wherever you can. “Could not save” is fine for DB failure, but parsing failures should explain what is missing: unclear date, missing title, unknown project, or pending item blocking a new save.

If I were aiming for the biggest user-perceived uplift without adding complexity, I would do five things: implement `/edit`, add pending overwrite protection, rewrite the reminder/summary/review templates, validate dates strictly, and make the active project visible everywhere. That would change the feel far more than any larger refactor.

# 6. Prioritized Action Plan
Make a table with columns:
- Priority
- Improvement
- Impact
- Effort
- Why now
- Files / Areas affected

Group into:
- Quick wins
- Short-term improvements
- Medium refactors
- Optional later improvements

| Priority | Improvement | Impact | Effort | Why now | Files / Areas affected |
|---|---|---|---|---|---|
| Quick wins | Implement minimal `/edit` for pending items | High | Medium | It removes the most obvious trust break in the core flow | `src/handlers/confirm.py`, `src/state.py` |
| Quick wins | Validate all due dates before confirm/save | High | Low | Prevents malformed records and reminder crashes | `src/handlers/nl_handler.py`, `src/bot.py`, `src/handlers/common.py` |
| Quick wins | Block new voice/NL input when a pending item exists | High | Low | Prevents silent overwrite of unsaved work | `src/bot.py`, `src/handlers/nl_handler.py` |
| Quick wins | Make weekly summary idempotent by week | High | Low | Stops duplicate Monday messages | `src/schema.sql`, `src/db.py`, `scripts/send_summary.py` |
| Quick wins | Replace raw `cp` backup with SQLite-native backup | High | Low | Directly improves recoverability | `scripts/backup_db.sh` |
| Short-term improvements | Cache Whisper model in process | Medium | Low | Makes voice capture feel much less rough | `src/transcriber.py` |
| Short-term improvements | Improve reminder wording and include project context | Medium | Low | High perceived polish for daily use | `scripts/send_reminders.py` |
| Short-term improvements | Improve weekly summary structure and tone | Medium | Medium | Turns it from useful raw output into a real weekly assistant message | `scripts/send_summary.py` |
| Short-term improvements | Make active project visible and clearable | Medium | Low | Reduces user confusion in daily capture | `src/handlers/projects.py`, `src/handlers/help_cmd.py`, `src/handlers/notes.py`, `src/handlers/ideas.py` |
| Short-term improvements | Add indexes on due dates and project-scoped reads | Medium | Low | Cheap performance and future-proofing for longer use | `src/schema.sql` |
| Medium refactors | Move save/confirm formatting into a small service layer | Medium | Medium | Reduces handler drift without adding framework complexity | `src/bot.py`, `src/handlers/*` |
| Medium refactors | Split `db.py` by domain | Medium | Medium | Helps maintainability before it becomes a dumping ground | `src/db.py` |
| Medium refactors | Persist active project and pending draft state | Medium | Medium | Improves restart resilience and trust | `src/state.py`, `src/schema.sql`, `src/db.py`, handlers |
| Optional later improvements | Add lightweight tests for reminder, summary, and confirm flows | Medium | Medium | Good once core UX is stabilized | `scripts/`, `src/handlers/`, test files |
| Optional later improvements | Tighten review prompt and validation for film-school critique | Medium | Medium | Raises assistant quality without architectural change | `src/reviewer.py`, prompt docs |
| Optional later improvements | Unify docs with actual journald/venv deployment | Medium | Low | Prevents operator confusion later | `README.md`, `docs/ops-security.md`, `systemd/*` |

# 7. Concrete Repo-Specific Refactoring Suggestions
Give at least 12 suggestions.
Each must reference actual files or code locations.

1. In `src/handlers/confirm.py`, replace the stub `/edit` handler with a simple field-edit parser instead of pushing users to `/discard`.
2. In `src/bot.py`, add the same pending-item guard used by NL so a new voice note cannot overwrite an unsaved pending entity.
3. In `src/bot.py`, refuse to build confirmable `deadline` or `homework` pending entities with empty `due_date`.
4. In `src/handlers/nl_handler.py`, validate `due_date` with shared parsing instead of trusting the model’s raw string.
5. In `src/handlers/common.py`, add a stricter date parser mode for AI-derived dates so malformed ISO-like strings cannot pass.
6. In `src/transcriber.py`, cache `whisper.load_model()` globally to avoid reloading on every voice note.
7. In `src/voice.py`, separate “temporary WAV” lifecycle from retained original audio; delete WAV after transcription unless you explicitly need it.
8. In `src/reviewer.py`, enforce non-empty `core_idea`, `dramatic_center`, `weak_points`, and `next_step` before formatting output.
9. In `src/openclaw_client.py`, add optional field-level schema validation helpers so handlers do not each re-interpret loose model JSON.
10. In `src/schema.sql`, add `UNIQUE(week_start)` to `weekly_reports` and handle conflict cleanly in `scripts/send_summary.py`.
11. In `src/schema.sql`, add indexes for deadline lookups and project-scoped browsing; current scans are fine now but cheap to harden.
12. In `scripts/send_reminders.py`, move reminder window calculation fully into Python to avoid mixing local and SQLite UTC dates.
13. In `scripts/send_summary.py`, rewrite the summary template so it reads like a weekly creative digest rather than a raw status report.
14. In `scripts/backup_db.sh`, switch to SQLite `.backup` and run `PRAGMA integrity_check` periodically.
15. In `src/handlers/list_cmd.py`, either support `project:` filters for deadlines/homework too or reject them explicitly; the current UX implies support more broadly than it delivers.
16. In `src/handlers/projects.py`, add `/project clear` and show the active project marker in `/projects`.
17. In `systemd/film-school-bot.service` and sibling services, template or document the venv Python path directly instead of shipping `/usr/bin/python3`.
18. In `README.md` and `docs/ops-security.md`, reconcile deployment docs with actual journald-only logging and current runtime assumptions.

# 8. If I Were Polishing This Project Personally
Write a concise opinionated roadmap:
- what I would change first
- what I would postpone
- what I would intentionally not overengineer

I would change first: `/edit`, due-date validation, pending overwrite protection, weekly summary idempotency, and SQLite-safe backups. Those are the highest-trust fixes. Then I would rewrite the response templates for save confirmations, reminders, summaries, and reviews so the bot feels more like a calm creative assistant and less like a utility script.

I would postpone: larger module splitting, persistent state storage, and a fuller service layer. They are worthwhile, but they matter less than fixing correctness and tone in the existing flows.

I would intentionally not overengineer: multi-user auth, web UI, queue systems, PostgreSQL, agent frameworks, or anything “smart” for its own sake. This project’s best version is still a small, boring, reliable Telegram bot with better validation and much better taste.
