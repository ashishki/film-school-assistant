#!/usr/bin/env python3
"""Developer tool: print all collected user feedback.

Usage:
    python scripts/show_feedback.py
    python scripts/show_feedback.py --since 2026-03-01
    python scripts/show_feedback.py --limit 50
"""
import argparse
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Show collected user feedback")
    parser.add_argument("--since", metavar="YYYY-MM-DD", help="Show only feedback after this date")
    parser.add_argument("--limit", type=int, default=200, help="Max rows to show (default: 200)")
    args = parser.parse_args()

    config = load_config()
    db_path = config.db_path

    query = "SELECT id, source, created_at, content FROM user_feedback"
    params: list = []

    if args.since:
        query += " WHERE created_at >= ?"
        params.append(args.since)

    query += " ORDER BY created_at ASC LIMIT ?"
    params.append(args.limit)

    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(query, params).fetchall()

    if not rows:
        print("Фидбека пока нет.")
        return

    print(f"Фидбек пользователя — {len(rows)} записей\n" + "=" * 60)
    for row in rows:
        source_label = "голос" if row["source"] == "voice" else "текст"
        print(f"\n[{row['id']}] {row['created_at']}  ({source_label})")
        print(row["content"])
        print("-" * 40)


if __name__ == "__main__":
    main()
