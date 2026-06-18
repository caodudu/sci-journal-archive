from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from common import DEFAULT_DB, clean_issn, derive_country, first_present, normalize_title, parse_float
from init_db import init_db
from migrate_db import migrate


def load_index(csv_path: Path, index_type: str) -> dict[str, dict[str, str | None]]:
    out: dict[str, dict[str, str | None]] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            title = first_present(row, ["Journal title", "title", "journal"])
            issn = clean_issn(first_present(row, ["ISSN"]))
            eissn = clean_issn(first_present(row, ["eISSN", "EISSN"]))
            categories = first_present(row, ["Web of Science Categories", "categories"])
            publisher = first_present(row, ["Publisher name", "publisher"])
            publisher_address = first_present(row, ["Publisher address", "publisher_address"])
            country = first_present(row, ["Country/Region", "Country", "country"]) or derive_country(publisher_address)
            record = {
                "index_type": index_type,
                "title": title,
                "issn": issn,
                "eissn": eissn,
                "categories": categories,
                "publisher": publisher,
                "country": country,
                "publisher_address": publisher_address,
                "languages": first_present(row, ["Languages", "Language", "languages"]),
            }
            for key in [issn, eissn]:
                if key:
                    out[f"issn:{key}"] = record
            if title:
                out[f"title:{normalize_title(title)}"] = record
    return out


def upsert_journal(
    conn: sqlite3.Connection,
    title: str,
    issn: str | None,
    eissn: str | None,
    publisher: str | None,
    country: str | None,
    publisher_address: str | None,
    languages: str | None,
) -> int:
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
            """
            UPDATE journals
            SET title = ?,
                publisher = COALESCE(?, publisher),
                country = COALESCE(?, country),
                publisher_address = COALESCE(?, publisher_address),
                languages = COALESCE(?, languages),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, publisher, country, publisher_address, languages, existing[0]),
        )
        return int(existing[0])
    cur = conn.execute(
        """
        INSERT INTO journals(title, title_norm, issn, eissn, publisher, country, publisher_address, languages)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, title_norm, issn, eissn, publisher, country, publisher_address, languages),
    )
    return int(cur.lastrowid)


def match_index(row: dict[str, str], indexes: list[dict[str, dict[str, str | None]]]) -> dict[str, str | None] | None:
    title = first_present(row, ["Journal Name", "Journal title", "title"])
    issn = clean_issn(first_present(row, ["ISSN"]))
    eissn = clean_issn(first_present(row, ["eISSN", "EISSN"]))
    keys = []
    if issn:
        keys.append(f"issn:{issn}")
    if eissn:
        keys.append(f"issn:{eissn}")
    if title:
        keys.append(f"title:{normalize_title(title)}")
    for index in indexes:
        for key in keys:
            if key in index:
                return index[key]
    return None


def import_full(jcr_csv: Path, scie_csv: Path, esci_csv: Path, db_path: Path, year: int) -> tuple[int, int, int]:
    migrate(db_path)
    scie_index = load_index(scie_csv, "SCIE")
    esci_index = load_index(esci_csv, "ESCI")
    total = 0
    imported = 0
    unmatched = 0

    with sqlite3.connect(db_path) as conn, jcr_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            matched = match_index(row, [scie_index, esci_index])
            if not matched:
                unmatched += 1
                continue

            title = first_present(row, ["Journal Name", "Journal title", "title"]) or matched["title"]
            if not title:
                unmatched += 1
                continue
            issn = clean_issn(first_present(row, ["ISSN"])) or matched["issn"]
            eissn = clean_issn(first_present(row, ["eISSN", "EISSN"])) or matched["eissn"]
            publisher = first_present(row, ["Publisher"]) or matched["publisher"]
            country = matched.get("country")
            publisher_address = matched.get("publisher_address")
            languages = matched.get("languages")
            categories = first_present(row, ["Category"]) or matched["categories"]
            impact_factor = parse_float(first_present(row, ["JIF", "Journal Impact Factor", "impact_factor"]))
            journal_id = upsert_journal(conn, title, issn, eissn, publisher, country, publisher_address, languages)
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
                (journal_id, year, matched["index_type"], impact_factor, categories, str(jcr_csv)),
            )
            imported += 1
    return total, imported, unmatched


def main() -> None:
    parser = argparse.ArgumentParser(description="Import full 2025 JCR IF table and split it by SCIE/ESCI lists.")
    parser.add_argument("--jcr-csv", type=Path, required=True)
    parser.add_argument("--scie-csv", type=Path, required=True)
    parser.add_argument("--esci-csv", type=Path, required=True)
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    total, imported, unmatched = import_full(args.jcr_csv, args.scie_csv, args.esci_csv, args.db, args.year)
    print(f"Read {total} JCR rows; imported {imported} SCIE/ESCI rows; unmatched {unmatched}.")


if __name__ == "__main__":
    main()
