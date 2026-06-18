from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from common import DEFAULT_DB
from init_db import init_db


JOURNAL_COLUMNS = {
    "country": "TEXT",
    "publisher_address": "TEXT",
    "languages": "TEXT",
    "founding_year": "INTEGER",
    "is_new_journal": "INTEGER NOT NULL DEFAULT 0",
    "new_journal_reason": "TEXT",
}


def existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def migrate(db_path: Path) -> None:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        columns = existing_columns(conn, "journals")
        for name, sql_type in JOURNAL_COLUMNS.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE journals ADD COLUMN {name} {sql_type}")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS journal_warnings (
                journal_id INTEGER NOT NULL REFERENCES journals(id),
                warning_year INTEGER NOT NULL,
                warning_source TEXT NOT NULL,
                warning_level TEXT,
                warning_note TEXT,
                imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (journal_id, warning_year, warning_source)
            );

            CREATE TABLE IF NOT EXISTS journal_cas_partitions (
                id INTEGER PRIMARY KEY,
                journal_id INTEGER NOT NULL REFERENCES journals(id),
                cas_year INTEGER NOT NULL,
                cas_zone TEXT,
                cas_major_category TEXT,
                cas_minor_category TEXT,
                cas_source TEXT,
                imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_cas_partition_identity
            ON journal_cas_partitions(journal_id, cas_year, COALESCE(cas_source, ''));
            """
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply lightweight SQLite migrations for the SCI archive.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    migrate(args.db)
    print(f"Migrated {args.db}")


if __name__ == "__main__":
    main()
