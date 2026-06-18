from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from common import DEFAULT_DB, clean_issn, detect_index_type, first_present, normalize_title, parse_float
from init_db import init_db


TITLE_ALIASES = ["title", "journal_title", "full_journal_title", "journal name", "journal", "full title"]
ISSN_ALIASES = ["issn", "print issn"]
EISSN_ALIASES = ["eissn", "e-issn", "online issn"]
PUBLISHER_ALIASES = ["publisher", "publisher name"]
IF_ALIASES = ["jif", "impact_factor", "journal_impact_factor", "journal impact factor", "2025 jif", "2026 jif"]
CATEGORY_ALIASES = ["category", "categories", "jcr_category", "jcr categories", "web of science categories"]
INDEX_ALIASES = ["edition", "index", "collection", "web of science index", "jcr edition"]


def row_index_types(row: dict[str, str], categories: str | None, index_value: str | None) -> list[str]:
    lowered = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
    detected: list[str] = []
    if lowered.get("scie"):
        detected.append("SCIE")
    if lowered.get("esci"):
        detected.append("ESCI")
    if not detected:
        detected.append(detect_index_type(index_value, categories))
    return detected


def upsert_journal(conn: sqlite3.Connection, title: str, issn: str | None, eissn: str | None, publisher: str | None) -> int:
    title_norm = normalize_title(title)
    existing = conn.execute(
        """
        SELECT id FROM journals
        WHERE title_norm = ?
          AND COALESCE(issn, '') = COALESCE(?, '')
          AND COALESCE(eissn, '') = COALESCE(?, '')
        """,
        (title_norm, issn, eissn),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE journals SET title = ?, publisher = COALESCE(?, publisher), updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, publisher, existing[0]),
        )
        return int(existing[0])

    cur = conn.execute(
        "INSERT INTO journals(title, title_norm, issn, eissn, publisher) VALUES (?, ?, ?, ?, ?)",
        (title, title_norm, issn, eissn, publisher),
    )
    return int(cur.lastrowid)


def import_csv(db_path: Path, csv_path: Path, year: int) -> tuple[int, int]:
    init_db(db_path)
    total = 0
    imported = 0
    with sqlite3.connect(db_path) as conn, csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{csv_path} has no header row")
        for row in reader:
            total += 1
            title = first_present(row, TITLE_ALIASES)
            if not title:
                continue
            issn = clean_issn(first_present(row, ISSN_ALIASES))
            eissn = clean_issn(first_present(row, EISSN_ALIASES))
            publisher = first_present(row, PUBLISHER_ALIASES)
            impact_factor = parse_float(first_present(row, IF_ALIASES))
            categories = first_present(row, CATEGORY_ALIASES)
            journal_id = upsert_journal(conn, title, issn, eissn, publisher)
            index_value = first_present(row, INDEX_ALIASES)
            for index_type in row_index_types(row, categories, index_value):
                conn.execute(
                    """
                    INSERT INTO journal_years(journal_id, year, index_type, impact_factor, categories, raw_source)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(journal_id, year, index_type) DO UPDATE SET
                        impact_factor = excluded.impact_factor,
                        categories = excluded.categories,
                        raw_source = excluded.raw_source,
                        imported_at = CURRENT_TIMESTAMP
                    """,
                    (journal_id, year, index_type, impact_factor, categories, str(csv_path)),
                )
                imported += 1
    return total, imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Import an authorized JCR CSV export.")
    parser.add_argument("--year", type=int, required=True, help="JCR year, for example 2025 or 2026.")
    parser.add_argument("--csv", type=Path, required=True, help="Authorized JCR CSV export.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    total, imported = import_csv(args.db, args.csv, args.year)
    print(f"Read {total} rows; imported {imported} journal-year records into {args.db}")


if __name__ == "__main__":
    main()
