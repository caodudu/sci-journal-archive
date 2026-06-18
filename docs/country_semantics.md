# Country Semantics

Last updated: 2026-06-18

## Current Problem

The current dashboard country field is parsed from `Publisher address` in the Web of Science Core Collection list. This is only a publisher-country signal.

It is not the same as:

- journal owner country
- sponsoring society/institution country
- editorial office country
- journal registration country
- collaborating institution countries
- main author-country distribution

## Example: Signal Transduction and Targeted Therapy

The current local record says:

```text
publisher: SPRINGERNATURE
publisher_country: United Kingdom
publisher_address: CAMPUS, 4 CRINAN ST, LONDON, ENGLAND, N1 9XW
```

This is not enough. The journal is affiliated with / sponsored by West China Hospital, Sichuan University, and its editorial office is in Chengdu, Sichuan, P. R. China. Therefore it should be findable under China as well as under the publisher country.

## Implemented Model

The database has a separate `journal_countries` table:

```text
journal_id
country
country_code
role
source/source_url
source_type
confidence
note
review_status
```

Suggested roles:

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

The frontend should eventually offer:

- Publisher country filter
- Journal country filter
- Country role filter
- "match any country role" mode

Current frontend behavior:

- `publisher_country` remains visible in details.
- Country filtering matches any country role exported in `journal_country_records`.
- A country-role filter can narrow to publisher, society, institution, editorial office, and related roles.
- If no enrichment record exists yet, the viewer falls back to the parsed publisher country so old static data remains usable.

Current enrichment entry point:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\enrich_journal_countries.py seed-queue --source doaj_journals --only-biomed --limit 500
powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\enrich_journal_countries.py run --source doaj_journals --limit 200 --delay 1
```

DOAJ is the first database/API source because it can provide separate publisher and institution countries for some journals. OpenAlex is available as a broader source-level signal but should not be treated as owner/sponsor/editorial-office truth by itself.
