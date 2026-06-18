# SCI Journal Intelligence Archive

This repository is a long-running archive for SCI/SCIE/ESCI journal investigation, with a separated data pipeline and a static HTML viewer.

## Important Data Note

Journal Impact Factor (JIF/IF) is part of Clarivate Journal Citation Reports (JCR). Full 2025/2026 journal lists with IF usually require institutional access and should be exported from JCR or Web of Science Master Journal List by an authorized user.

This project therefore does not scrape pirated IF lists. It provides a reproducible ingest pipeline:

1. Export authorized JCR files for 2025 and 2026 as CSV.
2. Put them in `data/raw/jcr_exports/`.
3. Import them into SQLite.
4. Split SCIE and ESCI.
5. Extract the biomedical subset.
6. Collect PubMed publication counts and lifecycle dates.
7. Export compact JSON for `web/index.html`.

## Expected JCR Input

Put files such as:

```text
data/raw/jcr_exports/jcr_2025.csv
data/raw/jcr_exports/jcr_2026.csv
```

The importer accepts common column names and aliases:

```text
title, journal_title, full_journal_title
issn, eissn
edition, index, collection
jif, impact_factor, journal_impact_factor
category, categories, jcr_category
publisher
```

For SCIE/ESCI separation, the `edition/index/collection` field should contain `SCIE`, `Science Citation Index Expanded`, `ESCI`, or `Emerging Sources Citation Index`.

## Quick Start

```powershell
python scripts\init_db.py
python scripts\import_jcr.py --year 2025 --csv data\raw\jcr_exports\jcr_2025.csv
python scripts\import_jcr.py --year 2026 --csv data\raw\jcr_exports\jcr_2026.csv
python scripts\build_biomed_subset.py
python scripts\pubmed_collect.py --sample-size 20 --email your.name@example.com
python scripts\export_viewer_data.py
```

Open `web/index.html` in a browser. The viewer reads `web/journals.json`.

See `docs/data_sources.md` for the current source audit. The active viewer dataset is now the 2025 JCR impact-factor spreadsheet matched against the 2025 Web of Science SCIE/ESCI complete list. The earlier first-JIF import is backed up but no longer used by the viewer.

See `docs/biomed_filter.md` for the current biomedical-subset rule. It is now based on JCR/Web of Science subject-category whitelist matching, not loose title keyword matching.

## PubMed Date Fields

PubMed records vary by publisher. This pipeline records any available dates under:

- received
- revised
- accepted
- published

It then computes journal-level averages only when both endpoints are present. Missing lifecycle fields are common and should be treated as missing data, not zero.

## Main Outputs

- `data/processed/sci_archive.sqlite`: canonical database.
- `data/processed/biomed_journals.csv`: biomedical subset.
- `data/processed/pubmed_article_dates.csv`: sampled article-level date observations.
- `web/journals.json`: viewer data.

## Source References

- Clarivate JCR/Master Journal List: use authorized exports from your institution.
- PubMed E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25501/
