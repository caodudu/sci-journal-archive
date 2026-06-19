from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError

from common import DEFAULT_DB, parse_partial_date
from init_db import init_db


EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ARTICLE_DATES_CSV = DEFAULT_DB.parents[0] / "pubmed_article_dates.csv"
DEFAULT_LOG = DEFAULT_DB.parents[2] / "logs" / "pubmed_collect_progress.log"
DEFAULT_STATUS = DEFAULT_DB.parents[2] / "logs" / "pubmed_collect_status.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def request_text(endpoint: str, params: dict[str, str | int], retries: int, retry_delay: float) -> str:
    url = f"{EUTILS}/{endpoint}?{urllib.parse.urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "sci-journal-archive/0.1"})
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read().decode("utf-8")
        except (HTTPError, TimeoutError, URLError, ssl.SSLError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(retry_delay * attempt)
    assert last_error is not None
    raise last_error


def journal_query(title: str, year: int) -> str:
    escaped = title.replace('"', "")
    return f'"{escaped}"[Journal] AND {year}[dp]'


def esearch(query: str, retmax: int, email: str | None, api_key: str | None, retries: int, retry_delay: float) -> tuple[int, list[str]]:
    params: dict[str, str | int] = {
        "db": "pubmed",
        "term": query,
        "retmode": "xml",
        "retmax": retmax,
        "sort": "pub date",
    }
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key
    root = ET.fromstring(request_text("esearch.fcgi", params, retries, retry_delay))
    count = int(root.findtext("Count") or "0")
    ids = [node.text for node in root.findall(".//Id") if node.text]
    return count, ids


def efetch(pmids: list[str], email: str | None, api_key: str | None, retries: int, retry_delay: float) -> ET.Element:
    params: dict[str, str | int] = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key
    return ET.fromstring(request_text("efetch.fcgi", params, retries, retry_delay))


def article_title(article: ET.Element) -> str | None:
    title_node = article.find(".//ArticleTitle")
    return "".join(title_node.itertext()).strip() if title_node is not None else None


def parse_date_node(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    return parse_partial_date(node.findtext("Year"), node.findtext("Month"), node.findtext("Day"))


def publication_date(article: ET.Element) -> str | None:
    for path in [
        ".//ArticleDate",
        ".//PubDate",
        ".//PubMedPubDate[@PubStatus='pubmed']",
        ".//PubMedPubDate[@PubStatus='epublish']",
        ".//PubMedPubDate[@PubStatus='ppublish']",
    ]:
        parsed = parse_date_node(article.find(path))
        if parsed:
            return parsed
    return None


def history_dates(article: ET.Element) -> dict[str, str | None]:
    out: dict[str, str | None] = {"received": None, "revised": None, "accepted": None}
    for node in article.findall(".//PubMedPubDate"):
        status = (node.attrib.get("PubStatus") or "").lower()
        if status in out:
            out[status] = parse_date_node(node)
    return out


def days_between(start: str | None, end: str | None) -> int | None:
    if not start or not end:
        return None
    try:
        return (date.fromisoformat(end) - date.fromisoformat(start)).days
    except ValueError:
        return None


class ProgressReporter:
    def __init__(self, log_path: Path | None, status_path: Path | None, total: int) -> None:
        self.log_path = log_path
        self.status_path = status_path
        self.total = total
        self.started = time.time()
        self.started_at = now_iso()
        self.completed = 0
        self.ok = 0
        self.skipped = 0
        self.failed = 0
        self.article_rows = 0
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if self.status_path:
            self.status_path.parent.mkdir(parents=True, exist_ok=True)

    def elapsed(self) -> float:
        return time.time() - self.started

    def eta(self) -> float | None:
        if self.completed <= 0 or self.total <= 0:
            return None
        return self.elapsed() / self.completed * max(0, self.total - self.completed)

    def percent(self) -> float:
        return round(self.completed / self.total * 100, 2) if self.total else 100.0

    def write(self, status: str, journal: str | None = None, year: int | None = None, count: int | None = None, error: str | None = None) -> None:
        state = {
            "status": status,
            "started_at": self.started_at,
            "updated_at": now_iso(),
            "current_journal": journal,
            "current_year": year,
            "completed": self.completed,
            "total": self.total,
            "percent": self.percent(),
            "elapsed_seconds": round(self.elapsed(), 1),
            "elapsed": format_duration(self.elapsed()),
            "eta_seconds": None if self.eta() is None else round(self.eta(), 1),
            "eta": format_duration(self.eta()),
            "ok": self.ok,
            "skipped": self.skipped,
            "failed": self.failed,
            "article_rows": self.article_rows,
            "last_count": count,
            "last_error": error,
        }
        line = (
            f"{state['updated_at']} status={status} progress={self.completed}/{self.total} "
            f"percent={state['percent']:.2f}% elapsed={state['elapsed']} eta={state['eta']} "
            f"ok={self.ok} skipped={self.skipped} failed={self.failed} articles={self.article_rows}"
        )
        if journal:
            line += f" journal={journal!r}"
        if year is not None:
            line += f" year={year}"
        if count is not None:
            line += f" count={count}"
        if error:
            line += f" error={error!r}"
        if self.log_path:
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        if self.status_path:
            temp_path = self.status_path.with_suffix(self.status_path.suffix + ".tmp")
            temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            temp_path.replace(self.status_path)


def collect(
    db_path: Path,
    years: list[int],
    sample_size: int,
    email: str | None,
    api_key: str | None,
    delay: float,
    limit: int | None,
    only_biomed: bool,
    skip_existing: bool,
    retries: int,
    retry_delay: float,
    progress_log: Path | None,
    status_json: Path | None,
) -> tuple[int, int]:
    init_db(db_path)
    count_rows = 0
    article_rows = 0
    reporter: ProgressReporter | None = None
    with sqlite3.connect(db_path) as conn:
        where_sql = "WHERE is_biomed = 1" if only_biomed else ""
        journals = conn.execute(
            f"""
            SELECT id, title
            FROM journals
            {where_sql}
            ORDER BY title
            """
        ).fetchall()
        if limit:
            journals = journals[:limit]

        reporter = ProgressReporter(progress_log, status_json, len(journals) * len(years))
        reporter.write("running")

        for journal_id, title in journals:
            for year in years:
                if skip_existing:
                    existing = conn.execute(
                        "SELECT 1 FROM pubmed_year_counts WHERE journal_id = ? AND pub_year = ?",
                        (journal_id, year),
                    ).fetchone()
                    if existing:
                        reporter.completed += 1
                        reporter.skipped += 1
                        reporter.write("skipped", title, year)
                        continue
                query = journal_query(title, year)
                try:
                    total, ids = esearch(query, sample_size, email, api_key, retries, retry_delay)
                    conn.execute(
                        """
                        INSERT INTO pubmed_year_counts(journal_id, pub_year, query, count)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(journal_id, pub_year) DO UPDATE SET
                            query = excluded.query,
                            count = excluded.count,
                            collected_at = CURRENT_TIMESTAMP
                        """,
                        (journal_id, year, query, total),
                    )
                    count_rows += 1
                    time.sleep(delay)
                    if ids:
                        root = efetch(ids, email, api_key, retries, retry_delay)
                        for article in root.findall(".//PubmedArticle"):
                            pmid = article.findtext(".//PMID")
                            if not pmid:
                                continue
                            dates = history_dates(article)
                            published = publication_date(article)
                            received = dates["received"]
                            revised = dates["revised"]
                            accepted = dates["accepted"]
                            xml_text = ET.tostring(article, encoding="unicode")
                            conn.execute(
                                """
                                INSERT INTO pubmed_article_dates(
                                    pmid, journal_id, pub_year, title,
                                    received_date, revised_date, accepted_date, published_date,
                                    days_received_to_accepted, days_accepted_to_published, days_received_to_published,
                                    raw_pubmed_xml
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(pmid) DO UPDATE SET
                                    journal_id = excluded.journal_id,
                                    pub_year = excluded.pub_year,
                                    title = excluded.title,
                                    received_date = excluded.received_date,
                                    revised_date = excluded.revised_date,
                                    accepted_date = excluded.accepted_date,
                                    published_date = excluded.published_date,
                                    days_received_to_accepted = excluded.days_received_to_accepted,
                                    days_accepted_to_published = excluded.days_accepted_to_published,
                                    days_received_to_published = excluded.days_received_to_published,
                                    raw_pubmed_xml = excluded.raw_pubmed_xml,
                                    collected_at = CURRENT_TIMESTAMP
                                """,
                                (
                                    pmid,
                                    journal_id,
                                    year,
                                    article_title(article),
                                    received,
                                    revised,
                                    accepted,
                                    published,
                                    days_between(received, accepted),
                                    days_between(accepted, published),
                                    days_between(received, published),
                                    xml_text,
                                ),
                            )
                            article_rows += 1
                            reporter.article_rows += 1
                    conn.commit()
                    reporter.completed += 1
                    reporter.ok += 1
                    reporter.write("ok", title, year, total)
                    time.sleep(delay)
                except Exception as exc:
                    conn.rollback()
                    reporter.completed += 1
                    reporter.failed += 1
                    reporter.write("failed", title, year, error=f"{type(exc).__name__}: {exc}")
                    continue

    export_article_dates(db_path, ARTICLE_DATES_CSV)
    if reporter:
        reporter.write("complete")
    return count_rows, article_rows


def export_article_dates(db_path: Path, out_path: Path) -> None:
    with sqlite3.connect(db_path) as conn, out_path.open("w", encoding="utf-8", newline="") as handle:
        rows = conn.execute(
            """
            SELECT
                j.title AS journal,
                p.pmid,
                p.pub_year,
                p.title,
                p.received_date,
                p.revised_date,
                p.accepted_date,
                p.published_date,
                p.days_received_to_accepted,
                p.days_accepted_to_published,
                p.days_received_to_published
            FROM pubmed_article_dates p
            JOIN journals j ON j.id = p.journal_id
            ORDER BY j.title, p.pub_year, p.pmid
            """
        ).fetchall()
        writer = csv.writer(handle)
        writer.writerow([
            "journal",
            "pmid",
            "pub_year",
            "title",
            "received_date",
            "revised_date",
            "accepted_date",
            "published_date",
            "days_received_to_accepted",
            "days_accepted_to_published",
            "days_received_to_published",
        ])
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect PubMed counts and sampled article lifecycle dates for biomedical journals.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    default_years = [date.today().year - 2, date.today().year - 1, date.today().year]
    parser.add_argument("--years", nargs="+", type=int, default=default_years, help="Publication years. Defaults to the most recent three calendar years.")
    parser.add_argument("--sample-size", type=int, default=20)
    parser.add_argument("--email", help="NCBI recommends identifying requests with an email address.")
    parser.add_argument("--api-key", help="Optional NCBI API key.")
    parser.add_argument("--delay", type=float, default=0.34, help="Delay between requests. Keep at least 0.34 without an API key.")
    parser.add_argument("--limit", type=int, help="Limit journals for testing.")
    parser.add_argument("--only-biomed", action="store_true", help="Collect only journals marked as biomedical/cross-biology.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip journal-year counts already present in the database.")
    parser.add_argument("--retries", type=int, default=5, help="Retry transient PubMed network failures up to this many attempts.")
    parser.add_argument("--retry-delay", type=float, default=3.0, help="Base seconds for retry backoff.")
    parser.add_argument("--progress-log", type=Path, default=DEFAULT_LOG, help="Append progress lines to this log file.")
    parser.add_argument("--status-json", type=Path, default=DEFAULT_STATUS, help="Overwrite this JSON status file with latest progress.")
    args = parser.parse_args()
    count_rows, article_rows = collect(
        args.db,
        args.years,
        args.sample_size,
        args.email,
        args.api_key,
        args.delay,
        args.limit,
        args.only_biomed,
        args.skip_existing,
        args.retries,
        args.retry_delay,
        args.progress_log,
        args.status_json,
    )
    print(f"Updated {count_rows} journal-year PubMed counts and {article_rows} sampled article date rows.")


if __name__ == "__main__":
    main()
