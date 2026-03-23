# Film School Assistant — Database Migration Guide

**DB engine:** SQLite 3 (WAL mode)
**Schema source:** src/schema.sql
**Applied by:** src/db.py:init_db() on every bot startup (CREATE TABLE IF NOT EXISTS — safe)

---

## When to Use Migrations

Use a migration when:
- Adding a new column to an existing table
- Adding a new table that references an existing table
- Renaming a column or table (rare — prefer additive changes)

Do NOT use a migration for:
- New tables with no FK to existing data (init_db handles this safely)
- Read-only query changes

---

## Migration Process

### Step 1 — Write the migration SQL
Create a file: `migrations/YYYYMMDD_description.sql`
Example: `migrations/20260323_add_note_tags.sql`

```sql
-- Migration: add tags column to notes
-- Date: 2026-03-23
-- Reversible: yes (DROP COLUMN notes.tags)
ALTER TABLE notes ADD COLUMN tags TEXT DEFAULT NULL;
```

### Step 2 — Test on a copy of production DB
```bash
# Copy prod DB
cp /srv/openclaw-her/workspace/film-school-assistant/data/assistant.db /tmp/assistant_test.db

# Apply migration
sqlite3 /tmp/assistant_test.db < migrations/20260323_add_note_tags.sql

# Verify schema
sqlite3 /tmp/assistant_test.db ".schema notes"

# Run smoke test against the test DB (edit DB_PATH temporarily or pass as env)
DB_PATH=/tmp/assistant_test.db .venv/bin/python scripts/smoke_test_db.py
```

### Step 3 — Apply to production
```bash
# Stop bot first
systemctl stop film-school-bot.service

# Backup current DB
cp /srv/openclaw-her/workspace/film-school-assistant/data/assistant.db \
   /srv/openclaw-her/workspace/film-school-assistant/data/backups/pre-migration-$(date +%Y%m%d).db

# Apply migration
sqlite3 /srv/openclaw-her/workspace/film-school-assistant/data/assistant.db \
  < migrations/20260323_add_note_tags.sql

# Restart bot
systemctl start film-school-bot.service

# Verify
systemctl status film-school-bot.service
journalctl -u film-school-bot.service -n 20
```

### Step 4 — Update src/schema.sql
Add the ALTER TABLE statement outcome to schema.sql so `init_db()` creates new DBs with the column.
Use `CREATE TABLE IF NOT EXISTS` pattern — it is idempotent.

---

## Rollback

SQLite does not support DROP COLUMN before SQLite 3.35. For older deployments:
- Rollback: restore from backup (Step 3 backup above)
- For SQLite >= 3.35: `ALTER TABLE notes DROP COLUMN tags;`

Check version: `sqlite3 --version`

---

## WAL Mode Note

The bot uses aiosqlite (async), scripts use synchronous sqlite3. Both access the same DB.
WAL mode (Write-Ahead Logging) allows concurrent reads. Verify it is active:
```bash
sqlite3 /srv/.../data/assistant.db "PRAGMA journal_mode;"
# Expected output: wal
```
If not wal, enable: `sqlite3 /srv/.../data/assistant.db "PRAGMA journal_mode=WAL;"`

---

## Schema Invariants (from IMPLEMENTATION_CONTRACT.md)

- All tables use INTEGER PRIMARY KEY (rowid alias)
- All foreign keys reference INTEGER primary keys
- created_at uses ISO 8601 UTC strings (TEXT)
- Status fields use CHECK constraints — add new values via ALTER TABLE or migration
