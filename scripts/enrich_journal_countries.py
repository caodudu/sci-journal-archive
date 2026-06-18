from __future__ import annotations

import argparse
import json
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from common import DEFAULT_DB, ROOT, clean_issn
from init_db import init_db


OPENALEX_SOURCE = "openalex_sources"
DOAJ_SOURCE = "doaj_journals"
DEFAULT_CACHE = ROOT / "data" / "raw" / "enrichment_cache"
USER_AGENT = "sci-journal-archive/0.1"

COUNTRY_BY_CODE = {
    "AR": "Argentina",
    "AT": "Austria",
    "AU": "Australia",
    "BE": "Belgium",
    "BR": "Brazil",
    "CA": "Canada",
    "CH": "Switzerland",
    "CL": "Chile",
    "CN": "China",
    "CZ": "Czech Republic",
    "DE": "Germany",
    "DK": "Denmark",
    "EG": "Egypt",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "GB": "United Kingdom",
    "GR": "Greece",
    "HU": "Hungary",
    "IE": "Ireland",
    "IN": "India",
    "IR": "Iran",
    "IT": "Italy",
    "JP": "Japan",
    "KR": "South Korea",
    "MX": "Mexico",
    "MY": "Malaysia",
    "NL": "Netherlands",
    "NO": "Norway",
    "NZ": "New Zealand",
    "PK": "Pakistan",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "RU": "Russia",
    "SA": "Saudi Arabia",
    "SE": "Sweden",
    "SG": "Singapore",
    "TH": "Thailand",
    "TR": "Turkiye",
    "US": "United States",
    "ZA": "South Africa",
}


@dataclass(frozen=True)
class CountryCandidate:
    country: str
    country_code: str | None
    role: str
    source: str
    source_type: str
    confidence: float
    note: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def backoff_time(attempts: int) -> str:
    minutes = min(24 * 60, 2 ** max(0, attempts))
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(microsecond=0).isoformat()


def source_url_for_issn(issn: str, mailto: str | None) -> str:
    path = f"https://api.openalex.org/sources/issn:{urllib.parse.quote(issn)}"
    if mailto:
        return f"{path}?mailto={urllib.parse.quote(mailto)}"
    return path


def doaj_url_for_issn(issn: str) -> str:
    return f"https://doaj.org/api/v4/search/journals/issn:{urllib.parse.quote(issn)}?pageSize=1"


def cache_path(cache_dir: Path, source: str, key: str) -> Path:
    safe_key = "".join(char if char.isalnum() else "_" for char in key)
    return cache_dir / source / f"{safe_key}.json"


def fetch_json(url: str, cache_file: Path, refresh: bool = False) -> dict[str, Any]:
    if cache_file.exists() and not refresh:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def candidates_from_openalex(payload: dict[str, Any]) -> list[CountryCandidate]:
    candidates: list[CountryCandidate] = []
    source = payload.get("id") or payload.get("ids", {}).get("openalex") or "openalex"
    country_code = payload.get("country_code")
    country = COUNTRY_BY_CODE.get(country_code or "")
    if country:
        candidates.append(
            CountryCandidate(
                country=country,
                country_code=country_code,
                role="publisher",
                source=source,
                source_type="openalex_source",
                confidence=0.6,
                note="OpenAlex source.country_code; treat as source/publisher geography, not journal owner country.",
            )
        )
    for society in payload.get("societies") or []:
        society_country_code = society.get("country_code") if isinstance(society, dict) else None
        society_country = COUNTRY_BY_CODE.get(society_country_code or "")
        if not society_country:
            continue
        society_source = society.get("id") or source
        society_name = society.get("display_name") or "OpenAlex society"
        candidates.append(
            CountryCandidate(
                country=society_country,
                country_code=society_country_code,
                role="society",
                source=society_source,
                source_type="openalex_source_society",
                confidence=0.8,
                note=f"OpenAlex society metadata: {society_name}.",
            )
        )
    return candidates


def candidates_from_doaj(payload: dict[str, Any]) -> list[CountryCandidate]:
    results = payload.get("results") or []
    if not results:
        return []
    result = results[0]
    bibjson = result.get("bibjson") or {}
    source = f"https://doaj.org/toc/{bibjson.get('eissn') or bibjson.get('pissn') or result.get('id')}"
    candidates: list[CountryCandidate] = []

    publisher = bibjson.get("publisher") or {}
    publisher_code = publisher.get("country")
    publisher_country = COUNTRY_BY_CODE.get(publisher_code or "")
    if publisher_country:
        candidates.append(
            CountryCandidate(
                country=publisher_country,
                country_code=publisher_code,
                role="publisher",
                source=source,
                source_type="doaj_publisher",
                confidence=0.65,
                note=f"DOAJ publisher metadata: {publisher.get('name') or 'publisher'}",
            )
        )

    institution = bibjson.get("institution") or {}
    institution_code = institution.get("country")
    institution_country = COUNTRY_BY_CODE.get(institution_code or "")
    if institution_country:
        candidates.append(
            CountryCandidate(
                country=institution_country,
                country_code=institution_code,
                role="institution",
                source=source,
                source_type="doaj_institution",
                confidence=0.85,
                note=f"DOAJ institution metadata: {institution.get('name') or 'institution'}",
            )
        )

    return candidates


def seed_queue(db_path: Path, source: str, only_biomed: bool, limit: int | None) -> int:
    init_db(db_path)
    where = "WHERE j.is_biomed = 1" if only_biomed else ""
    limit_sql = "LIMIT ?" if limit else ""
    params: list[Any] = [limit] if limit else []
    with sqlite3.connect(db_path, timeout=30) as conn:
        rows = conn.execute(
            f"""
            SELECT DISTINCT j.id
            FROM journals j
            JOIN journal_years jy ON jy.journal_id = j.id
            {where}
            ORDER BY j.title
            {limit_sql}
            """,
            params,
        ).fetchall()
        for (journal_id,) in rows:
            conn.execute(
                """
                INSERT OR IGNORE INTO journal_country_enrichment_queue(journal_id, source)
                VALUES (?, ?)
                """,
                (journal_id, source),
            )
    return len(rows)


def next_jobs(conn: sqlite3.Connection, source: str, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            q.id AS queue_id,
            q.attempts,
            j.id AS journal_id,
            j.title,
            j.issn,
            j.eissn
        FROM journal_country_enrichment_queue q
        JOIN journals j ON j.id = q.journal_id
        WHERE q.source = ?
          AND q.status IN ('pending', 'retry')
          AND (q.next_run_at IS NULL OR q.next_run_at <= ?)
        ORDER BY q.updated_at, q.id
        LIMIT ?
        """,
        (source, utc_now(), limit),
    ).fetchall()


def upsert_candidates(conn: sqlite3.Connection, journal_id: int, candidates: list[CountryCandidate]) -> None:
    for candidate in candidates:
        conn.execute(
            """
            INSERT INTO journal_countries(
                journal_id, country, country_code, role, source, source_type,
                confidence, note, review_status, collected_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'candidate', CURRENT_TIMESTAMP)
            ON CONFLICT(journal_id, country, role, source) DO UPDATE SET
                country_code = excluded.country_code,
                source_type = excluded.source_type,
                confidence = excluded.confidence,
                note = excluded.note,
                collected_at = CURRENT_TIMESTAMP
            """,
            (
                journal_id,
                candidate.country,
                candidate.country_code,
                candidate.role,
                candidate.source,
                candidate.source_type,
                candidate.confidence,
                candidate.note,
            ),
        )


def mark_done(conn: sqlite3.Connection, queue_id: int) -> None:
    conn.execute(
        """
        UPDATE journal_country_enrichment_queue
        SET status = 'done', last_error = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (queue_id,),
    )


def mark_retry(conn: sqlite3.Connection, queue_id: int, attempts: int, error: str) -> None:
    conn.execute(
        """
        UPDATE journal_country_enrichment_queue
        SET status = 'retry',
            attempts = ?,
            next_run_at = ?,
            last_error = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (attempts, backoff_time(attempts), error[:500], queue_id),
    )


def run_openalex(
    db_path: Path,
    cache_dir: Path,
    limit: int,
    delay: float,
    mailto: str | None,
    refresh_cache: bool,
) -> tuple[int, int]:
    init_db(db_path)
    processed = 0
    candidate_count = 0
    with sqlite3.connect(db_path, timeout=30) as conn:
        conn.row_factory = sqlite3.Row
        jobs = next_jobs(conn, OPENALEX_SOURCE, limit)
        for job in jobs:
            issns = [clean_issn(job["eissn"]), clean_issn(job["issn"])]
            issn = next((value for value in issns if value), None)
            if not issn:
                mark_retry(conn, job["queue_id"], job["attempts"] + 1, "Missing ISSN/eISSN")
                continue
            url = source_url_for_issn(issn, mailto)
            path = cache_path(cache_dir, OPENALEX_SOURCE, issn)
            try:
                payload = fetch_json(url, path, refresh_cache)
                candidates = candidates_from_openalex(payload)
                upsert_candidates(conn, job["journal_id"], candidates)
                mark_done(conn, job["queue_id"])
                processed += 1
                candidate_count += len(candidates)
                print(f"{job['title']}: {len(candidates)} candidate(s)")
            except urllib.error.HTTPError as exc:
                mark_retry(conn, job["queue_id"], job["attempts"] + 1, f"HTTP {exc.code}: {exc.reason}")
                print(f"{job['title']}: HTTP {exc.code}")
            except Exception as exc:  # noqa: BLE001 - persisted as queue error for resume.
                mark_retry(conn, job["queue_id"], job["attempts"] + 1, str(exc))
                print(f"{job['title']}: {exc}")
            conn.commit()
            if delay > 0:
                time.sleep(delay)
    return processed, candidate_count


def run_doaj(
    db_path: Path,
    cache_dir: Path,
    limit: int,
    delay: float,
    refresh_cache: bool,
) -> tuple[int, int]:
    init_db(db_path)
    processed = 0
    candidate_count = 0
    with sqlite3.connect(db_path, timeout=30) as conn:
        conn.row_factory = sqlite3.Row
        jobs = next_jobs(conn, DOAJ_SOURCE, limit)
        for job in jobs:
            issns = [clean_issn(job["eissn"]), clean_issn(job["issn"])]
            issn = next((value for value in issns if value), None)
            if not issn:
                mark_retry(conn, job["queue_id"], job["attempts"] + 1, "Missing ISSN/eISSN")
                continue
            url = doaj_url_for_issn(issn)
            path = cache_path(cache_dir, DOAJ_SOURCE, issn)
            try:
                payload = fetch_json(url, path, refresh_cache)
                candidates = candidates_from_doaj(payload)
                upsert_candidates(conn, job["journal_id"], candidates)
                mark_done(conn, job["queue_id"])
                processed += 1
                candidate_count += len(candidates)
                print(f"{job['title']}: {len(candidates)} candidate(s)")
            except urllib.error.HTTPError as exc:
                mark_retry(conn, job["queue_id"], job["attempts"] + 1, f"HTTP {exc.code}: {exc.reason}")
                print(f"{job['title']}: HTTP {exc.code}")
            except Exception as exc:  # noqa: BLE001 - persisted as queue error for resume.
                mark_retry(conn, job["queue_id"], job["attempts"] + 1, str(exc))
                print(f"{job['title']}: {exc}")
            conn.commit()
            if delay > 0:
                time.sleep(delay)
    return processed, candidate_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Low-speed journal-country enrichment runner.")
    parser.add_argument("command", choices=["seed-queue", "run"])
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--source", choices=[DOAJ_SOURCE, OPENALEX_SOURCE], default=DOAJ_SOURCE)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--mailto", help="Email for OpenAlex polite pool.")
    parser.add_argument("--only-biomed", action="store_true")
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()

    if args.command == "seed-queue":
        count = seed_queue(args.db, args.source, args.only_biomed, args.limit)
        print(f"Seeded {count} journal(s) for {args.source}")
    else:
        if args.source == OPENALEX_SOURCE:
            processed, candidates = run_openalex(
                args.db,
                args.cache_dir,
                args.limit,
                args.delay,
                args.mailto,
                args.refresh_cache,
            )
        else:
            processed, candidates = run_doaj(
                args.db,
                args.cache_dir,
                args.limit,
                args.delay,
                args.refresh_cache,
            )
        print(f"Processed {processed} journal(s); stored {candidates} country candidate(s).")


if __name__ == "__main__":
    main()
