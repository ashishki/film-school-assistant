-- Migration: add memory_items table for project-first evidence recall
-- Date: 2026-04-08
-- Phase: 8 — MVP Evidence Memory Foundation
-- Reversible: yes (DROP TABLE memory_items)

CREATE TABLE IF NOT EXISTS memory_items (
    id INTEGER PRIMARY KEY,
    scope TEXT NOT NULL CHECK (scope IN ('project', 'user')),
    project_id INTEGER,
    source_kind TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    source_created_at TEXT,
    CHECK (
        (scope = 'project' AND project_id IS NOT NULL)
        OR (scope = 'user' AND project_id IS NULL)
    ),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_memory_items_project ON memory_items(project_id, scope, source_kind);
CREATE INDEX IF NOT EXISTS idx_memory_items_source ON memory_items(source_kind, source_id);
