from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "processed" / "sci_archive.sqlite"
SCHEMA = ROOT / "scripts" / "schema.sql"


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the SCI archive SQLite database.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    init_db(args.db)
    print(f"Initialized {args.db}")


if __name__ == "__main__":
    main()
