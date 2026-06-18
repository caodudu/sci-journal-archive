from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from common import BIOMED_CATEGORIES, BIOMED_KEYWORDS, DEFAULT_DB, category_names
from init_db import init_db


DEFAULT_OUT = DEFAULT_DB.parents[0] / "biomed_journals.csv"


def classify(categories: str | None, title: str, fallback_keywords: bool = False) -> tuple[int, str | None]:
    matched_categories = sorted(set(category_names(categories)) & BIOMED_CATEGORIES)
    if matched_categories:
        return 1, "category: " + "; ".join(matched_categories)
    if fallback_keywords:
        text = f"{categories or ''} {title}".lower()
        matched = sorted(keyword for keyword in BIOMED_KEYWORDS if keyword in text)
        if matched:
            return 1, "keyword: " + "; ".join(matched[:8])
    return 0, None


def build_subset(db_path: Path, out_path: Path, fallback_keywords: bool) -> int:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT j.id, j.title, GROUP_CONCAT(DISTINCT jy.categories), GROUP_CONCAT(DISTINCT jy.index_type)
            FROM journals j
            LEFT JOIN journal_years jy ON jy.journal_id = j.id
            GROUP BY j.id, j.title
            """
        ).fetchall()
        for journal_id, title, categories, _index_types in rows:
            is_biomed, reason = classify(categories, title, fallback_keywords=fallback_keywords)
            conn.execute(
                "UPDATE journals SET is_biomed = ?, biomed_reason = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (is_biomed, reason, journal_id),
            )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        selected = conn.execute(
            """
            SELECT
                j.title, j.issn, j.eissn, j.publisher, j.biomed_reason,
                jy.year, jy.index_type, jy.impact_factor, jy.categories
            FROM journals j
            JOIN journal_years jy ON jy.journal_id = j.id
            WHERE j.is_biomed = 1
            ORDER BY j.title, jy.year, jy.index_type
            """
        ).fetchall()
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["title", "issn", "eissn", "publisher", "biomed_reason", "year", "index_type", "impact_factor", "categories"])
            writer.writerows(selected)
    return len(selected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mark and export biomedical journals from imported JCR data.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--fallback-keywords", action="store_true", help="Also use loose title/category keyword matching when no category whitelist hit exists.")
    args = parser.parse_args()
    count = build_subset(args.db, args.out, args.fallback_keywords)
    print(f"Exported {count} biomedical journal-year rows to {args.out}")


if __name__ == "__main__":
    main()
