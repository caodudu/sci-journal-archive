from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from common import DEFAULT_DB


def main() -> None:
    parser = argparse.ArgumentParser(description="Print compact SCI archive database counts.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    with sqlite3.connect(args.db) as conn:
        print("journal_years")
        for row in conn.execute(
            "SELECT year, index_type, COUNT(*) FROM journal_years GROUP BY year, index_type ORDER BY year, index_type"
        ):
            print(f"{row[0]}\t{row[1]}\t{row[2]}")

        print("\nbiomedical_subset")
        for row in conn.execute(
            """
            SELECT year, index_type, COUNT(*)
            FROM v_journal_summary
            WHERE is_biomed = 1
            GROUP BY year, index_type
            ORDER BY year, index_type
            """
        ):
            print(f"{row[0]}\t{row[1]}\t{row[2]}")


if __name__ == "__main__":
    main()
