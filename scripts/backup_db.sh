#!/usr/bin/env bash
set -e

[ -f .env ] && source .env

DB_PATH="${DB_PATH:-data/assistant.db}"
BACKUP_DIR="${BACKUP_DIR:-data/backups/}"

mkdir -p "$BACKUP_DIR"

timestamp="$(date +%F_%H%M%S)"
backup_path="${BACKUP_DIR%/}/assistant_${timestamp}.db"

sqlite3 "$DB_PATH" ".backup '$backup_path'"

# Integrity check (non-fatal — log result only)
check_result=$(sqlite3 "$backup_path" "PRAGMA integrity_check;" 2>&1)
if [ "$check_result" = "ok" ]; then
    echo "Backup integrity: ok"
else
    echo "Backup integrity warning: $check_result"
fi

mapfile -t backups < <(ls -1t "${BACKUP_DIR%/}"/assistant_*.db 2>/dev/null || true)
if [ "${#backups[@]}" -gt 7 ]; then
  for old_backup in "${backups[@]:7}"; do
    rm -f "$old_backup"
  done
fi

echo "Database backup created: $backup_path"
