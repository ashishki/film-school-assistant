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

    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        raw_query = "SELECT id, source, created_at, content FROM user_feedback"
        raw_params: list = []
        if args.since:
            raw_query += " WHERE created_at >= ?"
            raw_params.append(args.since)
        raw_query += " ORDER BY created_at ASC LIMIT ?"
        raw_params.append(args.limit)
        raw_rows = db.execute(raw_query, raw_params).fetchall()

        feature_query = """
            SELECT id, source, created_at, summary_title, problem, desired_behavior, trigger_condition, success_result
            FROM feature_feedback
        """
        feature_params: list = []
        if args.since:
            feature_query += " WHERE created_at >= ?"
            feature_params.append(args.since)
        feature_query += " ORDER BY created_at ASC LIMIT ?"
        feature_params.append(args.limit)
        try:
            feature_rows = db.execute(feature_query, feature_params).fetchall()
        except sqlite3.OperationalError:
            feature_rows = []

    if not raw_rows and not feature_rows:
        print("Фидбека пока нет.")
        return

    if raw_rows:
        print(f"Сырой фидбек пользователя — {len(raw_rows)} записей\n" + "=" * 60)
        for row in raw_rows:
            source_label = "голос" if row["source"] == "voice" else "текст"
            print(f"\n[{row['id']}] {row['created_at']}  ({source_label})")
            print(row["content"])
            print("-" * 40)

    if feature_rows:
        print(f"\nСтруктурированные пожелания к функциям — {len(feature_rows)} записей\n" + "=" * 60)
        for row in feature_rows:
            source_label = "голос" if row["source"] == "voice" else "текст"
            print(f"\n[feature:{row['id']}] {row['created_at']}  ({source_label})")
            print(f"Коротко: {row['summary_title']}")
            print(f"Проблема: {row['problem']}")
            print(f"Нужно: {row['desired_behavior']}")
            print(f"Когда: {row['trigger_condition']}")
            print(f"Результат: {row['success_result']}")
            print("-" * 40)


if __name__ == "__main__":
    main()
