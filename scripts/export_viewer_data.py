from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from common import DEFAULT_DB, ROOT
from init_db import init_db


DEFAULT_OUT = ROOT / "web" / "journals.json"
DEFAULT_JS_OUT = ROOT / "web" / "journals-data.js"


def export_json(db_path: Path, out_path: Path, years: list[int] | None = None, js_out_path: Path | None = DEFAULT_JS_OUT) -> int:
    init_db(db_path)
    where_sql = ""
    params: list[int] = []
    if years:
        placeholders = ",".join("?" for _ in years)
        where_sql = f"WHERE jy.year IN ({placeholders})"
        params = years

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT
                j.id,
                j.title,
                j.issn,
                j.eissn,
                j.publisher,
                j.country,
                j.publisher_address,
                j.languages,
                j.founding_year,
                j.is_new_journal,
                j.new_journal_reason,
                j.is_biomed,
                j.biomed_reason,
                jy.year,
                jy.index_type,
                jy.impact_factor,
                jy.categories,
                jw.warning_level,
                jw.warning_source,
                jw.warning_note,
                jc.cas_zone,
                jc.cas_major_category,
                jc.cas_minor_category,
                py.count AS pubmed_count,
                AVG(p.days_received_to_accepted) AS avg_received_to_accepted,
                AVG(p.days_accepted_to_published) AS avg_accepted_to_published,
                AVG(p.days_received_to_published) AS avg_received_to_published
            FROM journals j
            JOIN journal_years jy ON jy.journal_id = j.id
            LEFT JOIN journal_warnings jw ON jw.journal_id = j.id AND jw.warning_year = jy.year
            LEFT JOIN journal_cas_partitions jc ON jc.journal_id = j.id AND jc.cas_year = jy.year
            LEFT JOIN pubmed_year_counts py ON py.journal_id = j.id AND py.pub_year = jy.year
            LEFT JOIN pubmed_article_dates p ON p.journal_id = j.id AND p.pub_year = jy.year
            {where_sql}
            GROUP BY
                j.id, j.title, j.issn, j.eissn, j.publisher, j.country, j.publisher_address, j.languages,
                j.founding_year, j.is_new_journal, j.new_journal_reason, j.is_biomed, j.biomed_reason,
                jy.year, jy.index_type, jy.impact_factor, jy.categories,
                jw.warning_level, jw.warning_source, jw.warning_note,
                jc.cas_zone, jc.cas_major_category, jc.cas_minor_category, py.count
            ORDER BY j.title, jy.year, jy.index_type
            """,
            params,
        ).fetchall()

    out = []
    for row in rows:
        item = dict(row)
        item["is_biomed"] = bool(item["is_biomed"])
        item["is_new_journal"] = bool(item["is_new_journal"])
        for key in ["avg_received_to_accepted", "avg_accepted_to_published", "avg_received_to_published"]:
            if item[key] is not None:
                item[key] = round(float(item[key]), 1)
        out.append(item)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(out, ensure_ascii=False, indent=2)
    out_path.write_text(json_text, encoding="utf-8")
    if js_out_path:
        js_out_path.parent.mkdir(parents=True, exist_ok=True)
        js_out_path.write_text(f"window.JOURNAL_ROWS = {json_text};\n", encoding="utf-8")
    return len(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export compact JSON for the static HTML viewer.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--js-out", type=Path, default=DEFAULT_JS_OUT, help="Also write a JS data file usable from file:// pages.")
    parser.add_argument("--years", nargs="+", type=int, help="Only export these JCR years, for example: --years 2025")
    args = parser.parse_args()
    count = export_json(args.db, args.out, args.years, args.js_out)
    print(f"Exported {count} rows to {args.out}")


if __name__ == "__main__":
    main()
