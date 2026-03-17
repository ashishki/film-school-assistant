#!/usr/bin/env bash
set -e

[ -f .env ] && source .env

DB_PATH="${DB_PATH:-data/assistant.db}"
BACKUP_DIR="${BACKUP_DIR:-data/backups/}"

mkdir -p "$BACKUP_DIR"

timestamp="$(date +%F_%H%M%S)"
backup_path="${BACKUP_DIR%/}/assistant_${timestamp}.db"

cp "$DB_PATH" "$backup_path"

mapfile -t backups < <(ls -1t "${BACKUP_DIR%/}"/assistant_*.db 2>/dev/null || true)
if [ "${#backups[@]}" -gt 7 ]; then
  for old_backup in "${backups[@]:7}"; do
    rm -f "$old_backup"
  done
fi

echo "Database backup created: $backup_path"
