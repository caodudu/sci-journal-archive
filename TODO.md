# SCI Journal Archive TODO

Last updated: 2026-06-18

## Current Focus

Build the 2025 backend database and frontend dashboard into an extensible journal-intelligence workspace. Keep 2026 as a later data-ingest path, but do not block 2025 work on it.

## Data Model / Backend

- [x] Add publisher-country field parsed from publisher address.
- [ ] Rename current `country` semantics in UI/docs to `publisher_country` unless a better source is imported.
- [x] Add journal-country / affiliation-country model separate from publisher country:
  - `journal_countries`
  - country name
  - role: publisher, owner, sponsor, society, editorial office, institution, collaborator, inferred
  - source URL/file
  - confidence
- [x] Add frontend/export support for multi-country journals. A journal can be found by any associated country once enrichment records exist.
- [ ] Run broad multi-country enrichment scan and review coverage. Start with DOAJ institution/publisher metadata, then OpenAlex source/society metadata, then Wikidata/official pages for unresolved records.
- [ ] Add country-source audit note for cases like `Signal Transduction and Targeted Therapy`, where publisher country can differ from journal/institutional origin.
- [x] Add Python runner shape for journal-country enrichment:
  - queue table
  - checkpoint/resume
  - rate limit
  - structured logs
  - no continuous monitoring
- [ ] Build full journal metadata enrichment pipeline for country/owner/sponsor/editorial-office:
  - start from DOAJ and OpenAlex database/API scans
  - then use known publisher/journal pages
  - cache every fetched page/API response
  - low concurrency only
  - confidence scoring
  - human review queue for ambiguous records
  - never overwrite publisher country with inferred journal country
- [ ] Store JCR abbreviated journal title from the full JCR spreadsheet:
  - `abbreviated_title`
  - normalized abbreviation
  - abbreviation source
- [ ] Add search index fields or generated frontend fields:
  - normalized title
  - normalized abbreviated title
  - title initials/acronym
  - abbreviation initials/acronym
- [x] Add publisher address and language fields from WoS collection list.
- [x] Add publisher statistics support in frontend and database exports.
- [x] Add warning-journal fields:
  - `is_warning`
  - `warning_source`
  - `warning_level`
  - `warning_year`
  - `warning_note`
- [x] Add CAS / Chinese Academy of Sciences partition fields:
  - `cas_zone`
  - `cas_major_category`
  - `cas_minor_category`
  - `cas_year`
  - `cas_source`
- [x] Add journal founding year / start year:
  - `founding_year`
  - `is_new_journal`
  - `new_journal_reason`
- [x] Add recent five-year publication counts runner:
  - `pubmed_year_counts` already exists for yearly PubMed counts.
  - `scripts/start_pubmed_background.ps1` collects 2021-2025 for biomedical/cross-biology journals, 20 sampled articles per year, skip-existing enabled.
- [ ] Add import scripts for external annotation files:
  - warning journals CSV
  - CAS partition CSV
  - founding year CSV

## Biomedical Filter

- [x] Replace loose title keyword matching with JCR/WoS category whitelist.
- [ ] Review adjacent life-science categories:
  - Plant Sciences
  - Zoology
  - Ecology
  - Entomology
  - Marine & Freshwater Biology
  - Agronomy
  - Food Science & Technology
  - Mathematical & Computational Biology
  - Biochemical Research Methods
  - Biology
  - Multidisciplinary Sciences
- [x] Explicitly include biology, bioinformatics, systems biology, biomaterials, and computational biology related categories when available.
- [x] Add a frontend toggle to inspect why a journal is included in biomedical subset.

## Frontend

- [x] Replace raw Excel-like table with journal intelligence dashboard.
- [x] Make local `file://` viewing work via `journals-data.js`.
- [x] Add country/region distribution and filter.
- [x] Add publisher distribution and filter.
- [x] Rename/reshape country filter semantics so it matches multi-role country signals and still distinguishes publisher country in details.
- [x] Add multi-country filter after `journal_countries` exists.
- [x] Replace the cramped right-side journal detail panel with a click-to-open floating detail page/modal.
- [x] Support journal filtering by publication-time interval once five-year PubMed counts are populated:
  - user chooses start year and end year
  - dashboard filters journals with publications in that interval
  - show total publications in selected interval
- [ ] Support journal abbreviation search:
  - exact abbreviation
  - normalized abbreviation without punctuation
  - JCR abbreviated journal field
- [x] Support initials/acronym search from journal title words:
  - `ng` should match `Nature Genetics`
  - ignore stopwords such as `of`, `and`, `the`, `for`, `in`
  - support partial initials and mixed title tokens
- [ ] Support initials/acronym search from JCR abbreviated journal title after backend stores abbreviations.
- [x] Improve fuzzy search for title fragments such as `nature genetic` matching `Nature Genetics`.
- [x] Add warning-journal badge placeholder.
- [x] Add CAS partition badge placeholder.
- [x] Add new-journal badge placeholder.
- [x] Add recent five-year publication count column/card metric.
- [x] Add journal detail sections:
  - JCR/WoS category
  - PubMed publication trend
  - manuscript timeline averages
  - warning/CAS/founding annotations
- [x] Add export button for filtered subset CSV.
- [x] Add GitHub Pages workflow to publish `web/`.
- [x] Add dark mode for the web viewer.
- [x] Add local web maintenance/publishing documentation.

## Data Sources Needed

- [x] 2025 JCR impact-factor spreadsheet.
- [x] 2025 WoS Core Collection complete list for SCIE/ESCI matching.
- [ ] Warning journal list source.
- [ ] CAS partition source.
- [ ] Founding year source.
- [ ] PubMed five-year counts collection.
- [ ] Journal-country enrichment sources:
  - official journal homepage
  - publisher journal page
  - society/sponsor page
  - Crossref / ISSN / OpenAlex / Wikidata only as auxiliary signals
  - manual CSV override for high-value journals

## Completion Checks

- [x] Dashboard shows non-zero country statistics.
- [x] Dashboard can filter by publisher country and publisher.
- [ ] Dashboard can filter by true multi-country journal affiliation/owner/sponsor/editorial-office country.
- [x] Biomedical subset count is generated from category rules and documented.
- [ ] Warning/CAS/founding annotations are present when source files exist and remain empty otherwise.
- [ ] PubMed counts are collected for at least the biomedical subset.
- [x] PubMed 2021-2025 biomedical background scan started; see `docs/pubmed_scan.md`.
