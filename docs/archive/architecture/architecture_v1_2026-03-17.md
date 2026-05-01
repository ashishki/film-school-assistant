# Film School Assistant — Architecture

**Version:** 1.0
**Date:** 2026-03-17
**Owner:** Claude Strategist
**Status:** Baseline — do not modify without strategist review

---

## 1. EXECUTIVE SUMMARY

### What Is Being Built

A private, single-user Telegram bot that acts as a structured creative workflow assistant for a film school student. The system accepts text and voice input via Telegram, stores structured entities (notes, ideas, homework, deadlines), associates them with projects, sends deadline reminders, generates weekly summaries, and provides creative idea review on demand.

This runs on a private VPS under the OpenClaw HER instance. It is not a public service.

### Why This Architecture Is the Right MVP

- **Structured-first, conversational-second.** The assistant stores structured data and uses the conversational interface as a thin intake layer — not as a magic agent. This makes it debuggable, predictable, and incrementally buildable.
- **Command-primary routing.** Explicit Telegram commands (`/note`, `/idea`, `/deadline`, etc.) form the reliable baseline. NL routing is an enhancement, not a dependency.
- **SQLite storage.** One user, one file, easy backup, zero ops overhead at MVP scale.
- **Local Whisper for STT.** Audio stays on the server. No external audio transmission. Privacy by default.
- **systemd timers for scheduling.** Reminders and summaries are process-independent. The bot can crash and restart; the timers still fire.
- **OpenClaw for reasoning only.** Storage, scheduling, and routing are deterministic. OpenClaw handles disambiguation, creative review, and weekly narrative synthesis.

### What Is Intentionally Deferred

- Multi-user support
- Web dashboard
- RAG / vector search over notes
- External calendar integration
- AI-driven proactive suggestions
- PostgreSQL migration
- OAuth or Telegram login security hardening
- Advanced project ontology / tagging system

---

## 2. SYSTEM POSITIONING

### The System Is: Structured Workflow System with Conversational Interface

The core of the system is a set of structured data tables (projects, notes, ideas, homework, deadlines). The Telegram interface is a thin intake and retrieval layer. The LLM is a processing accelerator for unstructured input and a synthesis engine for review/summaries.

This is **not** an agent that interprets intent and does everything autonomously. Every action produces a stored, auditable artifact. Every entity is confirmed before being saved (especially for voice input).

### The System Is Not: A Magic Chat Agent

Avoid designing flows where:
- The LLM silently decides what to store
- Multi-step reasoning chains replace simple deterministic logic
- Tool calls chain unpredictably
- Entity creation is opaque to the user

Every entity creation has a confirmation step. Every failure has a visible error message.

---

## 3. OPENCLAW ROLE IN THE SYSTEM

### What OpenClaw Does

- **Reasoning orchestration:** When NL input is ambiguous, OpenClaw resolves intent and entity type.
- **Entity extraction from NL/voice transcripts:** Given a transcript, OpenClaw extracts structured fields (type, content, project, deadline).
- **Creative review mode:** Given an idea, OpenClaw generates structured critique (core idea, dramatic center, weak points, development questions, next step).
- **Weekly summary synthesis:** Given a structured data snapshot, OpenClaw narrates a useful summary (not just counts).
- **Tool invocation:** OpenClaw can call storage write tools, search tools, and reminder query tools as part of reasoning flows.

### What OpenClaw Does Not Do

- Run the Telegram bot
- Own the database
- Schedule reminders (systemd owns this)
- Transcribe audio (Whisper layer owns this)
- Parse explicit commands (`/note`, `/deadline`, etc.) — the bot handles these deterministically
- Manage secrets or file paths
- Own the ingestion pipeline

### OpenClaw Boundary

OpenClaw is called as a reasoning service when deterministic parsing is insufficient or when creative synthesis is needed. It is invoked by the application layer and returns structured JSON or text. It does not own process lifecycle.

---

## 4. VERIFIED INVARIANTS AND BOUNDARIES

These must not be broken by any implementation:

| Invariant | Constraint |
|---|---|
| OpenClaw runtime | No project code inside `/opt/openclaw/src` |
| Instance isolation | No project artifacts inside `/srv/openclaw-her/state` |
| Instance isolation | Do not touch `/srv/openclaw-you` |
| Project root | All code in `/srv/openclaw-her/workspace/film-school-assistant` |
| Secrets | Secrets only in `/srv/openclaw-her/secrets` or `.env` — never hardcoded |
| No public exposure | No internal service bound to `0.0.0.0` without explicit firewall rule |
| No runtime modification | OpenClaw source at pinned commit — do not modify |
| Path isolation | Runtime paths (`/srv/openclaw-her/state`, `openclaw.json5`, `.env`) not touched by project code |
| Audio privacy | Audio files stored locally under project root only, not transmitted externally unless explicit policy decision |

---

## 5. ASSUMPTIONS AND KEY DECISIONS

### Assumptions

- Single user (one Telegram chat_id). No auth layer needed beyond TELEGRAM_ALLOWED_CHAT_ID check.
- The user interacts primarily from mobile Telegram (text + voice notes).
- The user speaks clearly enough for Whisper small/medium to produce useful transcripts.
- The VPS has sufficient compute for local Whisper inference (4 CPU, 8 GB RAM).
- Python is the implementation language (ecosystem fit: python-telegram-bot, whisper, openai SDK, SQLite).
- OpenClaw exposes an API or CLI that can be invoked from the application layer (verify this before Phase 5).

### Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Telegram library | python-telegram-bot v20+ | Mature, well-documented, async-ready |
| Storage | SQLite via sqlite3 or aiosqlite | Zero ops, single user, sufficient |
| STT | OpenAI Whisper (local, small model) | Privacy, no audio leaves server |
| Audio conversion | ffmpeg | Standard, available on Ubuntu |
| Scheduling | systemd timers | Process-independent, reliable |
| Routing primary | Explicit commands | Deterministic, debuggable |
| Routing secondary | OpenClaw NL extraction | Enhancement only |
| Review model | Stronger model via OpenClaw | Creative synthesis needs quality |
| Entity extraction model | Cheaper/faster model via OpenClaw | High frequency, low latency needed |
| Confirmation | Required for voice input | Ambiguity mitigation |
| Confirmation | Optional for explicit commands | Command signals intent |

### Rejected Alternatives

| Alternative | Rejection Reason |
|---|---|
| PostgreSQL | Overkill for single user; adds infra complexity |
| aiogram | python-telegram-bot is more stable for this scope |
| OpenAI Whisper API | Audio transmitted externally; privacy risk |
| In-process scheduler (APScheduler) | Dies with bot process; systemd is more reliable |
| Pure NL routing | Too fragile as primary interface; command routing is safer |
| Vector DB for notes | Premature; SQLite FTS is sufficient for MVP |
| LangChain / agent framework | Adds opacity; build direct invocations instead |

---

## 6. USER EXPERIENCE FLOWS

### Text Note
```
User: /note Documentary framing exercise — wide to tight arc
Bot:  Note saved under "General". Add to a project? [/project <name>]
```

### Text Idea
```
User: /idea What if the protagonist's silence IS the film — no dialogue, only mise-en-scène
Bot:  Idea saved. Type /review <id> to get structured feedback.
```

### Text Deadline
```
User: /deadline "Final cut submission" due 2026-04-15 for Documentary class
Bot:  Deadline saved: "Final cut submission" — April 15. Reminders: 7d, 3d, 1d before. Correct? (yes/edit)
```

### Voice Note
```
User: [voice message]
Bot:  Transcribing...
Bot:  Transcript: "I had this idea for the opening shot — start in black and bring in the sound before the image"
Bot:  I think this is an idea. Should I save it as:
      [Idea] "Opening shot — black, sound before image"
      Project: none detected.
      Reply /confirm, /edit, or /discard.
User: /confirm
Bot:  Saved as Idea #7.
```

### Voice Deadline
```
User: [voice message: "I need to submit my color grading homework by next Friday"]
Bot:  Transcript: "I need to submit my color grading homework by next Friday"
Bot:  Detected: Homework deadline — "Color grading homework" — due 2026-03-27
      Correct? /confirm /edit /discard
User: /confirm
Bot:  Saved. Reminders set.
```

### Review Request
```
User: /review 7
Bot:  [Reviewing Idea #7...]
Bot:  CORE IDEA: Sound precedes image as a structural device.
      DRAMATIC CENTER: Sensory disorientation → invitation to active listening.
      WEAK POINTS: Underdeveloped beyond the opening beat. What sustains this logic across the film?
      QUESTIONS: 1) Does this recur? 2) What does "black" signify — void or transition? 3) Whose sound is it?
      NEXT STEP: Write one page exploring whether this device carries the entire film or only the opening.
```

### Weekly Summary
```
[Automated Telegram message every Monday 09:00]
Bot:  WEEK IN REVIEW — Mar 10–17

      URGENT: Documentary final cut due in 14 days.
      ACTIVE PROJECTS: "Documentary" (3 new notes, 1 idea), "Color Grading Homework" (1 deadline approaching)
      RECENT IDEAS: 2 new ideas this week — Idea #7 (unreviewed), Idea #8 (unreviewed)
      STALLED: "Sound Design Project" — no activity in 3 weeks
      NEXT: Review ideas before the Documentary deadline. Idea #7 directly relevant.
```

### Reminder Flow
```
[systemd timer fires — 7 days before deadline]
Bot:  REMINDER: "Final cut submission" is due in 7 days (April 15).
      Mark done? /done_deadline_<id>
```

---

## 7. VOICE-FIRST CRITIQUE AND DESIGN

### Benefits

- Natural for a film student on mobile
- Low friction for capturing ideas mid-thought
- Supports longer, richer input than typing

### Hidden Complexity

Voice input introduces ambiguity, multi-entity utterances, STT errors, and confirmation overhead that text commands avoid entirely. A 10-second voice note can contain:
- One idea
- One deadline
- A project reference
- Ambiguous time expressions ("next week", "before the review")

Each of these must be extracted, confirmed, and stored separately.

### STT Risks

- Background noise degrades Whisper accuracy significantly
- Proper nouns (course names, project names) are frequently misheard
- Filler words and false starts appear in transcripts
- Confidence scoring in Whisper is not reliable per-word

### STT Error Mitigation

- Always show the full transcript to the user before acting
- Never silently discard a voice note
- Store raw transcript separately from parsed entities
- Allow the user to edit the transcript before confirming

### Confidence and Confirmation Strategy

1. Transcribe → show transcript
2. Extract entities → show parsed interpretation
3. Ask for confirmation before saving
4. Provide `/edit` to correct fields
5. Provide `/discard` to cancel

**No silent auto-save for voice input in MVP.**

### Multi-Entity Utterances

When a voice message contains multiple entities:
- Extract all candidate entities
- Present each separately for confirmation
- Do not merge into a single ambiguous entity
- Allow partial confirmation ("save the idea, discard the deadline")

### When to Ask Clarification

- When entity type cannot be determined with high confidence
- When project cannot be resolved
- When deadline date is ambiguous ("next week" without explicit date)
- When transcript quality appears low (unusual words, likely noise)

### Voice Primary vs Secondary in MVP

**Decision: Voice is secondary in MVP.**

Rationale:
- Command interface is more reliable and faster to build
- STT pipeline adds significant complexity
- Voice confirmation flow adds UX overhead
- Phase 4 is the right point to introduce voice

**Voice is a Phase 4 feature.** The bot must work well with text commands before voice is introduced.

---

## 8. MODEL RESPONSIBILITY STRATEGY

### Layer Definitions

| Layer | Model/Tool | Responsibility | Notes |
|---|---|---|---|
| STT | Whisper (local, small/medium) | Audio → transcript | Never send audio externally |
| Command routing | No model (deterministic) | `/note`, `/idea`, `/deadline` parsing | Pure string matching |
| NL intent routing | Cheap LLM via OpenClaw | Classify intent from free-text | Haiku-class, JSON output |
| Entity extraction | Cheap LLM via OpenClaw | Extract fields from NL/transcript | Same model, structured prompt |
| Creative review | Strong LLM via OpenClaw | Structured idea critique | Sonnet/Opus class |
| Summary synthesis | Strong LLM via OpenClaw | Weekly narrative from structured data | Sonnet class |
| Storage | No model | DB read/write | Pure SQL |
| Reminder scheduling | No model (systemd) | Timer-based dispatch | No LLM involvement |
| Project resolution | Deterministic + fuzzy match | Resolve project name from text | Levenshtein or slug match first |

### Key Principle

**Use no model where deterministic logic suffices.** The LLM is expensive, slow, and non-deterministic. Every explicit command flow must bypass the LLM entirely.

### Cost and Latency Tradeoffs

- Whisper small: ~1–3s per 30s audio clip on CPU. Acceptable.
- Cheap LLM for extraction: target <2s round trip. Acceptable.
- Strong LLM for review: 5–15s. Acceptable (user expects this).
- SQLite: <10ms. Trivially fast.

---

## 9. TARGET MVP ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                     TELEGRAM CLIENT                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS (Telegram API)
┌─────────────────────────▼───────────────────────────────────┐
│              TELEGRAM INTAKE LAYER                          │
│  python-telegram-bot — handles updates, dispatches handlers │
│  Runs as: systemd service film-school-bot.service           │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
       ┌───────▼──────┐          ┌────────▼────────┐
       │ TEXT HANDLER │          │  MEDIA HANDLER  │
       │ Commands     │          │  Voice/Audio    │
       │ /note /idea  │          │  Download OGG   │
       │ /deadline    │          │  Convert → WAV  │
       │ /review      │          └────────┬────────┘
       │ /summary     │                   │
       └───────┬──────┘          ┌────────▼────────┐
               │                 │  STT LAYER      │
               │                 │  Whisper local  │
               │                 │  → transcript   │
               │                 └────────┬────────┘
               │                          │
       ┌───────▼──────────────────────────▼────────┐
       │           INTENT EXTRACTION LAYER          │
       │  Command: deterministic parse              │
       │  NL/Voice: OpenClaw cheap LLM              │
       │  Output: entity_type, fields, project_hint │
       └───────────────────────┬────────────────────┘
                               │
       ┌───────────────────────▼────────────────────┐
       │            ENTITY BUILDER                  │
       │  Resolve project (fuzzy match on slug/name)│
       │  Validate fields                           │
       │  Build confirmation message                │
       │  Wait for user confirm/edit/discard        │
       └───────────────────────┬────────────────────┘
                               │
       ┌───────────────────────▼────────────────────┐
       │            STORAGE LAYER                   │
       │  SQLite via aiosqlite                      │
       │  Tables: projects, notes, ideas, homework, │
       │          deadlines, voice_inputs,          │
       │          transcripts, parsed_events,       │
       │          reminder_log, review_history,     │
       │          weekly_reports                    │
       └───────────────────────┬────────────────────┘
                               │
       ┌───────────────────────▼────────────────────┐
       │       OPENCLAW REASONING LAYER              │
       │  review: strong LLM → structured critique  │
       │  summary: strong LLM → narrative digest    │
       │  intent: cheap LLM → JSON entity fields    │
       └────────────────────────────────────────────┘

       ┌────────────────────────────────────────────┐
       │       SYSTEMD TIMERS (independent)          │
       │  reminder.timer → reminder.service         │
       │    Queries deadlines, sends Telegram msgs  │
       │  summary.timer → summary.service           │
       │    Generates weekly summary, sends msg     │
       └────────────────────────────────────────────┘
```

### Component Ownership

| Component | Owns | Does Not Own |
|---|---|---|
| Bot service | Telegram I/O, handler dispatch | Storage, scheduling |
| STT layer | Audio → transcript | Entity meaning |
| Entity builder | Field validation, confirmation | DB writes |
| Storage layer | All DB reads/writes | Business logic |
| OpenClaw layer | Reasoning, review, synthesis | State, scheduling |
| systemd timers | Scheduling | Bot I/O |

---

## 10. DATA MODEL DRAFT

### projects
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT NOT NULL | Display name |
| slug | TEXT UNIQUE | URL-safe, for fuzzy match |
| description | TEXT | Optional |
| status | TEXT | active/archived |
| created_at | TEXT | ISO8601 |

### notes
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK | nullable — general notes |
| content | TEXT NOT NULL | Parsed/cleaned content |
| raw_transcript | TEXT | Original voice transcript if voice |
| source | TEXT | 'text' or 'voice' |
| created_at | TEXT | ISO8601 |

### ideas
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK | nullable |
| content | TEXT NOT NULL | |
| raw_transcript | TEXT | Voice source only |
| source | TEXT | 'text' or 'voice' |
| review_status | TEXT | 'unreviewed', 'reviewed' |
| created_at | TEXT | ISO8601 |

### homework
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK | nullable |
| course | TEXT | e.g., "Documentary" |
| title | TEXT NOT NULL | |
| description | TEXT | |
| due_date | TEXT | ISO8601 date |
| status | TEXT | 'pending', 'submitted', 'done' |
| source | TEXT | 'text' or 'voice' |
| created_at | TEXT | ISO8601 |

### deadlines
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK | nullable |
| title | TEXT NOT NULL | |
| due_date | TEXT | ISO8601 date |
| status | TEXT | 'active', 'done', 'dismissed' |
| reminded_count | INTEGER | Default 0 |
| last_reminded_at | TEXT | ISO8601 nullable |
| source | TEXT | 'text' or 'voice' |
| created_at | TEXT | ISO8601 |

### voice_inputs
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| telegram_file_id | TEXT | Telegram file reference |
| local_path | TEXT | Path under project root |
| duration_seconds | INTEGER | |
| telegram_message_id | INTEGER | |
| created_at | TEXT | ISO8601 |
| processed_at | TEXT | ISO8601 nullable |

### transcripts
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| voice_input_id | INTEGER FK | |
| raw_text | TEXT NOT NULL | Verbatim Whisper output |
| model_used | TEXT | e.g., 'whisper-small' |
| created_at | TEXT | ISO8601 |

### parsed_events
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| transcript_id | INTEGER FK | nullable (NL text also parsed) |
| entity_type | TEXT | 'note', 'idea', 'homework', 'deadline' |
| extracted_json | TEXT | JSON blob of extracted fields |
| confirmed | INTEGER | 0/1 |
| entity_id | INTEGER | FK to actual entity after confirm |
| entity_table | TEXT | Which table entity was written to |
| created_at | TEXT | ISO8601 |

### reminder_log
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| deadline_id | INTEGER FK | |
| sent_at | TEXT | ISO8601 |
| message_text | TEXT | Snapshot of what was sent |
| days_before | INTEGER | 7, 3, 1, etc. |

### review_history
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| idea_id | INTEGER FK | |
| prompt_used | TEXT | Full prompt sent to model |
| response_json | TEXT | Structured response |
| model_used | TEXT | |
| created_at | TEXT | ISO8601 |

### weekly_reports
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| week_start | TEXT | ISO8601 date (Monday) |
| generated_at | TEXT | ISO8601 |
| content_json | TEXT | Structured report fields |
| sent_at | TEXT | ISO8601 nullable |
| message_text | TEXT | What was actually sent |

### Relationships

```
projects ←─── notes
         ←─── ideas ──── review_history
         ←─── homework
         ←─── deadlines ──── reminder_log

voice_inputs ──── transcripts ──── parsed_events ──── (entity tables)
```

**Raw vs Derived:** `voice_inputs` and `transcripts` are raw data. `parsed_events` is derived. The entity tables (notes, ideas, etc.) are confirmed derived data. Never delete raw rows after confirmation — preserve audit trail.

---

## 11. TEXT AND VOICE INGESTION PIPELINES

### Text Pipeline

```
Telegram text message
  → Bot handler receives update
  → Check allowed chat_id (security gate)
  → Is it a command? (/note, /idea, /deadline, /homework)
      YES → deterministic parser extracts fields
           → project resolver (slug match)
           → entity builder populates entity object
           → explicit commands: auto-confirm (no ambiguity)
           → write to storage
           → reply with confirmation + entity ID
      NO  → free text
           → check context state (are we in a pending confirm flow?)
               YES → route to confirmation handler
               NO  → NL routing: send to OpenClaw cheap model
                    → OpenClaw returns: entity_type, fields, project_hint
                    → entity builder + confirmation message
                    → wait for /confirm, /edit, /discard
```

**Idempotency:** Each command parse is idempotent. If the same message is processed twice (network retry), check for duplicate by `telegram_message_id`. Do not insert twice.

**Failure handling:**
- DB write fails → reply "Could not save. Try again. (ERR:DB)"
- OpenClaw fails → reply "Could not parse. Try a /command instead."
- Parser error → reply "Could not understand. Use /note <text>"

### Voice Pipeline

```
Telegram voice message
  → Bot handler receives voice update
  → Check allowed chat_id
  → Reply "Transcribing..." (UX signal)
  → Download OGG file to local temp path
  → Insert voice_input row (created_at, telegram_file_id, local_path)
  → Convert OGG → WAV via ffmpeg
  → Run Whisper inference
  → Store transcript row (raw_text, model_used)
  → Send transcript to user: "Transcript: [...]"
  → Run entity extraction via OpenClaw
  → Extract: entity_type, fields, project_hint
  → Send confirmation message with parsed interpretation
  → Wait for /confirm, /edit, /discard
  → On confirm: write entity row, mark voice_input as processed
  → On discard: mark voice_input as discarded, do not write entity
```

**Confirmation is mandatory for all voice input.**

**Audio retention:**
- Audio files stored under `/srv/openclaw-her/workspace/film-school-assistant/data/audio/`
- Retained for 30 days (configurable)
- Transcripts retained indefinitely
- No audio transmitted externally

**Failure handling:**
- Download fails → reply "Could not download audio. Try again."
- ffmpeg conversion fails → reply "Audio conversion failed. Send as text if urgent."
- Whisper fails → reply "Transcription failed. Transcript saved for retry."
- OpenClaw extraction fails → show raw transcript, ask user to confirm type manually: "/note_from <id>"
- Partial failures: always store what was received (voice_input row), even if processing fails

---

## 12. IDEA REVIEW LAYER

### Design

Review is triggered by `/review <idea_id>`.

The system:
1. Fetches idea content from DB
2. Constructs structured review prompt
3. Sends to strong model via OpenClaw
4. Parses structured JSON response
5. Formats as Telegram message
6. Saves to review_history

### Review Output Format (JSON → Message)

```
CORE IDEA: [one sentence]
DRAMATIC CENTER: [what emotion/tension is at stake]
WEAK POINTS: [what is underdeveloped or unclear]
DEVELOPMENT QUESTIONS:
  1. [...]
  2. [...]
  3. [...]
NEXT STEP: [one concrete action]
```

### Anti-patterns to Avoid

- Generic praise ("This is a great idea!")
- Vague critique ("Needs more development")
- Open-ended questions without direction ("What do you want to say?")
- Overwhelming the user with 10 questions

### Prompt Constraints

The review prompt must explicitly instruct the model:
- No generic praise
- Identify the specific dramatic or emotional mechanism
- Weak points must be concrete failures of logic, structure, or originality
- Questions must be precise and filmmaking-relevant
- Next step must be one actionable thing, not a vague mandate

---

## 13. REMINDER ARCHITECTURE

### Schedule

For each active deadline, reminders fire at:
- 7 days before due_date
- 3 days before
- 1 day before
- Day of (morning)

### systemd Timer Design

`reminder.timer` fires daily at 08:00 local time.
`reminder.service` runs a script that:
1. Queries deadlines WHERE status = 'active' AND due_date >= today
2. For each deadline, computes days_until = due_date - today
3. Checks reminder_log: has a reminder at this `days_before` value already been sent?
4. If not: send Telegram message, insert reminder_log row
5. If yes: skip (idempotent)

### Duplicate Prevention

`reminder_log` has a UNIQUE constraint on `(deadline_id, days_before)`. Insert-or-ignore prevents double-sending even if the service runs twice in one day.

### Spam Prevention

- Never send more than one reminder per deadline per `days_before` bucket
- No reminders for deadlines marked `done` or `dismissed`
- User can silence a deadline with `/dismiss_deadline <id>`
- No reminder for deadlines more than 30 days away

### Message Format

```
⏰ REMINDER: "[title]" is due in [N] days ([date]).
Mark done: /done_deadline_<id>
Dismiss reminders: /dismiss_deadline_<id>
```

---

## 14. WEEKLY SUMMARY ARCHITECTURE

### Trigger

`summary.timer` fires every Monday at 09:00 local time.
`summary.service` runs a script that:
1. Queries the past 7 days of activity
2. Queries upcoming deadlines (next 30 days)
3. Detects stalled projects (no activity > 14 days)
4. Sends structured data to OpenClaw strong model for narrative synthesis
5. Stores result in `weekly_reports`
6. Sends Telegram message

### Data Snapshot for Summary

```json
{
  "week_range": {"start": "2026-03-11", "end": "2026-03-17"},
  "new_notes": [...],
  "new_ideas": [...],
  "new_homework": [...],
  "upcoming_deadlines": [...],
  "stalled_projects": [...],
  "unreviewed_ideas": [...]
}
```

### Summary Output Format

```
WEEK IN REVIEW — [date range]

URGENT: [deadline titles within 7 days]
ACTIVE PROJECTS: [projects with activity + summary]
RECENT IDEAS: [N ideas — reviewed/unreviewed]
STALLED: [projects with no activity > 2 weeks]
RECOMMENDED NEXT: [2-3 concrete suggestions]
```

### Anti-patterns to Avoid

- Pure counts ("You created 3 notes this week")
- Listing everything without prioritization
- Ignoring urgency (deadline context)
- Generic filler ("Keep up the great work!")

---

## 15. PRIVACY, RETENTION, AND SECURITY

### Audio Retention

- Audio files: deleted after 30 days (cleanup script or timer)
- Transcripts: retained indefinitely (text only, low storage cost)
- Parsed events: retained indefinitely (audit trail)
- Audio never transmitted to external service

### Secret Handling

- Telegram bot token: `/srv/openclaw-her/secrets/telegram_token` or `TELEGRAM_BOT_TOKEN` env var
- OpenClaw credentials: from `/srv/openclaw-her/.env` or secrets directory
- DB path: config-driven, not hardcoded
- `TELEGRAM_ALLOWED_CHAT_ID`: required env var — bot ignores all other chat IDs

### Local vs External STT

**Decision: Local Whisper only in MVP.**

Rationale:
- Audio content can be personally sensitive (creative work, personal deadlines)
- External API (OpenAI Whisper API) transmits audio off-server
- Local inference is sufficient given 4 CPU, 8 GB RAM
- Whisper small model: ~150 MB, reasonable accuracy

Future option: If local inference is too slow, OpenAI Whisper API can be enabled as an opt-in config flag.

### Security Posture

- Bot ignores messages from any chat_id not in ALLOWED list
- No ports opened beyond existing SSH
- Bot communicates outbound only (Telegram long-polling or webhook)
- If webhook used: must be behind a reverse proxy with TLS, not directly exposed
- Prefer long-polling for MVP (no inbound port required)

---

## 16. MVP VS FUTURE EVOLUTION

### MVP (Build Now)

- `/note`, `/idea`, `/deadline`, `/homework` commands
- Project listing and association (`/projects`, `/project <name>`)
- `/review <id>` — idea review mode
- Voice ingestion pipeline (Phase 4)
- Daily reminder timer
- Weekly summary timer
- SQLite storage
- Local Whisper STT
- OpenClaw integration for NL routing and review

### Future (Do Not Build Now)

| Feature | Reason to Defer |
|---|---|
| Web dashboard | Adds infra complexity, not needed for one user |
| Multi-user | Requires auth, schema changes, complexity |
| Vector search over notes | No evidence this is needed yet |
| External calendar sync | Complex integration, unclear value |
| Proactive AI suggestions | Requires behavioral modeling, high noise risk |
| PostgreSQL | No justification for one user |
| File attachments (PDF, images) | Scope creep |
| Advanced project ontology | Premature categorization |
| RAG over past ideas | Post-MVP when corpus is large enough |
| Telegram webhook | Long-polling is sufficient and simpler |

**Discipline rule:** Any feature not listed under MVP must be explicitly approved before being added to the codebase.

---

## 17. AI DEVELOPMENT WORKFLOW

### Roles

#### Claude Strategist (this document)
- Owns architecture, spec, phases, task graph
- Produces implementation prompts for Codex
- Reviews architecture compliance of Codex output (via Claude Reviewer)
- Updates living docs after each cycle
- **Forbidden:** Writing application code, overriding Codex implementation details

#### Codex Implementer
- Receives a single-phase prompt with explicit file targets
- Writes code for one phase only
- Outputs working code + brief implementation notes
- **Forbidden:** Changing architecture, adding features outside scope, modifying docs/prompts unilaterally

#### Claude Reviewer
- Receives Codex output + review checklist
- Checks code against architecture, security, path correctness
- Produces a structured review: PASS / ISSUES list
- **Forbidden:** Rewriting code, approving code that violates invariants

#### Codex Fixer
- Receives review findings
- Applies fixes to code
- Updates living docs (tasks.md status, dev-cycle.md log)
- **Forbidden:** Expanding scope, modifying architecture, skipping issues

### Handoff Artifacts

| From → To | Artifact |
|---|---|
| Strategist → Codex | Phase prompt (docs/prompts/), architecture.md, spec.md |
| Codex → Reviewer | Code diff + implementation notes |
| Reviewer → Fixer | Review report (structured PASS/ISSUES) |
| Fixer → Strategist | Updated code + updated tasks.md + dev-cycle.md log entry |

### Go/No-Go Criteria

A phase is complete when:
- All tasks in the phase have status: done
- Reviewer has issued PASS (or PASS-WITH-MINOR)
- Living docs are updated
- No open CRITICAL or HIGH issues

---

## 18. LIVING DOCS AND CONTEXT PRESERVATION

### Document Set

| File | Purpose | Updated By |
|---|---|---|
| `docs/architecture.md` | System design, boundaries, decisions | Strategist only |
| `docs/spec.md` | Feature spec, UX flows, commands | Strategist only |
| `docs/tasks.md` | Task graph, phase status, done definitions | Fixer after each cycle |
| `docs/dev-cycle.md` | Cycle log — what ran, what was reviewed, what changed | Fixer after each cycle |
| `docs/ops-security.md` | Deployment, secrets, backup, security posture | Strategist + Fixer |

### Update Rules

- `architecture.md`: only modified for architectural changes. Not updated for implementation details.
- `spec.md`: updated when UX flows change.
- `tasks.md`: status column updated after each phase completes.
- `dev-cycle.md`: append-only log. One entry per review cycle.
- `ops-security.md`: updated when deployment or secrets model changes.

### Anti-patterns to Avoid

- Do not create additional docs without explicit need
- Do not duplicate content across docs
- Do not put implementation notes into architecture.md
- Do not create per-phase docs (use tasks.md instead)
- Do not let dev-cycle.md grow into a changelog for every file

---

## 19. PHASED IMPLEMENTATION PLAN

### Phase 0 — Repository Baseline and Docs

**Objective:** Create repo structure, initialize git, write living docs.
**Deliverables:** Directory structure, git init, all docs/, prompts/ files written.
**Dependencies:** None.
**Risks:** Doc sprawl. Keep docs minimal.
**Validation:** `git status` clean, all expected files present.

### Phase 1 — Config, Storage, Schema

**Objective:** Config loading, DB initialization, schema creation, storage module.
**Deliverables:** `src/config.py`, `src/db.py`, `src/schema.sql`, migration script.
**Dependencies:** Phase 0.
**Risks:** Schema changes are painful later. Get it right.
**Validation:** Schema creates cleanly, CRUD operations testable via script.

### Phase 2 — Telegram Command Flows

**Objective:** Bot setup, command handlers for all MVP commands, confirmation flow.
**Deliverables:** `src/bot.py`, `src/handlers/`, `systemd/film-school-bot.service`.
**Dependencies:** Phase 1.
**Risks:** Confirmation state management. Keep it simple (user_state dict).
**Validation:** Manual test all commands end-to-end. Bot handles unknown input gracefully.

### Phase 3 — Reminders and Weekly Summary

**Objective:** systemd timers for daily reminders and weekly summaries. Summary uses OpenClaw.
**Deliverables:** `scripts/send_reminders.py`, `scripts/send_summary.py`, `systemd/*.timer`, `systemd/*.service`.
**Dependencies:** Phase 1 (storage), Phase 2 (Telegram send function).
**Risks:** Timer misconfiguration. Test with short interval first.
**Validation:** Manual trigger of scripts, verify reminder_log insertion, verify summary format.

### Phase 4 — Voice Ingestion and Transcription

**Objective:** Voice note download, ffmpeg conversion, Whisper transcription, confirmation flow.
**Deliverables:** `src/voice.py`, `src/transcriber.py`, audio storage path setup.
**Dependencies:** Phase 2 (bot handlers), Phase 1 (storage).
**Risks:** Whisper slow on CPU. FFmpeg not installed. Audio path permissions.
**Validation:** Send voice note, verify transcript, confirm entity created.

### Phase 5 — NL Routing and Review Mode

**Objective:** OpenClaw integration for NL intent extraction and /review command.
**Deliverables:** `src/openclaw_client.py`, `src/reviewer.py`, updated NL handler.
**Dependencies:** Phase 1, Phase 2, OpenClaw API confirmed.
**Risks:** OpenClaw API contract unclear. Build against explicit interface, not assumptions.
**Validation:** Send free-text message, verify intent extraction. Run /review, verify structured output.

### Phase 6 — Hardening and Operational Polish

**Objective:** Error handling, logging, audio cleanup timer, backup script, ops polish.
**Deliverables:** Improved error replies, `scripts/cleanup_audio.py`, `scripts/backup_db.sh`, logging config.
**Dependencies:** All previous phases.
**Risks:** None major. Polish phase.
**Validation:** Intentional failure injection — verify graceful degradation.
