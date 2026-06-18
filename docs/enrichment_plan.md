# Metadata Enrichment Plan

Last updated: 2026-06-18

## Principle

Use Python for long-running work. PowerShell is only a thin launcher when needed.

Long jobs should be:

- resumable
- rate-limited
- cache-first
- low-concurrency
- auditable
- safe to leave running without monitoring

## Why Not High-Concurrency Web Search

Several thousand journals cannot be reliably enriched by high-concurrency generic web search. It would create:

- rate-limit and blocking risk
- inconsistent sources
- hard-to-debug failures
- hallucination risk if snippets are treated as facts
- poor reproducibility

Instead, enrichment should be staged.

## Proposed Pipeline

### Stage 1: Deterministic Sources

Use existing local fields:

- ISSN
- eISSN
- JCR title
- JCR abbreviated title
- publisher
- publisher address
- WoS categories

Do not infer journal country from publisher country except as `publisher` role.

### Stage 2: External API / Database Candidates

For each journal, query low-rate APIs by ISSN/title:

- DOAJ journal metadata
- Crossref journal metadata
- OpenAlex sources
- ISSN Portal if access is available
- Wikidata as an auxiliary source

Store raw responses in cache files. Do not overwrite manually reviewed data.

Current implementation:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\enrich_journal_countries.py seed-queue --source doaj_journals --only-biomed --limit 500
powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\enrich_journal_countries.py run --source doaj_journals --limit 200 --delay 1

powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\enrich_journal_countries.py seed-queue --source openalex_sources --only-biomed --limit 500
powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\enrich_journal_countries.py run --source openalex_sources --limit 200 --delay 1 --mailto your.name@example.com
```

DOAJ is the preferred first scan for open-access journals because it can expose both `publisher.country` and `institution.country`. For example, `Signal Transduction and Targeted Therapy` returns `publisher.country = GB` and `institution.country = CN`, allowing the frontend to find it under both United Kingdom and China with distinct roles.

OpenAlex is useful for source-level coverage (`country_code`, host organization, society metadata when present), but its `country_code` should be treated as a source/publisher geography signal rather than true owner/sponsor/editorial-office country.

### Stage 3: Official Page Fetching

For unresolved/high-value journals, fetch official pages slowly:

- publisher journal homepage
- `about`
- `aims and scope`
- `contact`
- `editorial board`
- `society`
- `partner`

Extract candidate countries and roles.

Example roles:

```text
publisher
owner
sponsor
society
editorial_office
institution
collaborator
inferred
```

### Stage 4: Confidence And Review

Every country signal should have:

```text
journal_id
country
role
    source/source_url
    source_type
    confidence
    note
    fetched_at
    review_status
```

Suggested confidence:

- `1.0`: official page explicitly states sponsor/society/editorial office country.
- `0.8`: publisher metadata strongly indicates journal owner/society.
- `0.6`: API metadata indicates country but source semantics are unclear.
- `0.3`: weak inferred signal.

Ambiguous records go into a review queue.

## Python Runner Shape

Suggested command:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\enrich_journal_countries.py run --source doaj_journals --limit 200 --delay 1
```

The runner should:

- read from an SQLite queue table
- skip completed records
- retry transient failures with backoff
- save raw HTML/API JSON under `data/raw/enrichment_cache/` (gitignored)
- write normalized candidates to SQLite
- emit compact logs

## Frontend Semantics

The UI should show:

- publisher country
- journal countries
- country roles
- source/confidence in details

Filtering should support:

- publisher country
- any journal country
- country role

`Signal Transduction and Targeted Therapy` is the guiding test case: it has a UK publisher address but China-affiliated sponsor/editorial-office signals.
