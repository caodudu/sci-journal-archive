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

### Stage 2: External API Candidates

For each journal, query low-rate APIs by ISSN/title:

- Crossref journal metadata
- OpenAlex sources
- ISSN Portal if access is available
- Wikidata as an auxiliary source

Store raw responses in cache files. Do not overwrite manually reviewed data.

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
source_url
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
powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\enrich_journal_metadata.py run --limit 200 --delay 2 --max-workers 1
```

The runner should:

- read from an SQLite queue table
- skip completed records
- retry transient failures with backoff
- save raw HTML/API JSON under `data/raw/enrichment_cache/`
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
