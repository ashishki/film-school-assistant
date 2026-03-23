PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE,
    description TEXT,
    status TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    content TEXT NOT NULL,
    raw_transcript TEXT,
    source TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    content TEXT NOT NULL,
    raw_transcript TEXT,
    source TEXT,
    review_status TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS homework (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    course TEXT,
    title TEXT NOT NULL,
    description TEXT,
    due_date TEXT,
    status TEXT,
    source TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS deadlines (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    title TEXT NOT NULL,
    due_date TEXT,
    status TEXT,
    reminded_count INTEGER,
    last_reminded_at TEXT,
    source TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS voice_inputs (
    id INTEGER PRIMARY KEY,
    telegram_file_id TEXT,
    local_path TEXT,
    duration_seconds INTEGER,
    telegram_message_id INTEGER,
    created_at TEXT,
    processed_at TEXT
);

CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY,
    voice_input_id INTEGER,
    raw_text TEXT NOT NULL,
    model_used TEXT,
    created_at TEXT,
    FOREIGN KEY (voice_input_id) REFERENCES voice_inputs(id)
);

CREATE TABLE IF NOT EXISTS parsed_events (
    id INTEGER PRIMARY KEY,
    transcript_id INTEGER,
    entity_type TEXT,
    extracted_json TEXT,
    confirmed INTEGER,
    entity_id INTEGER,
    entity_table TEXT,
    created_at TEXT,
    FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
);

CREATE TABLE IF NOT EXISTS reminder_log (
    id INTEGER PRIMARY KEY,
    deadline_id INTEGER,
    sent_at TEXT,
    message_text TEXT,
    days_before INTEGER,
    UNIQUE(deadline_id, days_before),
    FOREIGN KEY (deadline_id) REFERENCES deadlines(id)
);

CREATE TABLE IF NOT EXISTS review_history (
    id INTEGER PRIMARY KEY,
    idea_id INTEGER,
    prompt_used TEXT,
    response_json TEXT,
    model_used TEXT,
    created_at TEXT,
    FOREIGN KEY (idea_id) REFERENCES ideas(id)
);

CREATE TABLE IF NOT EXISTS weekly_reports (
    id INTEGER PRIMARY KEY,
    week_start TEXT UNIQUE,
    generated_at TEXT,
    content_json TEXT,
    sent_at TEXT,
    message_text TEXT
);

CREATE TABLE IF NOT EXISTS llm_call_log (
    id INTEGER PRIMARY KEY,
    model TEXT NOT NULL,
    call_type TEXT NOT NULL,
    called_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_deadlines_status_due ON deadlines(status, due_date);
CREATE INDEX IF NOT EXISTS idx_notes_project_created ON notes(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_ideas_project_created ON ideas(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_homework_status_due ON homework(status, due_date);
