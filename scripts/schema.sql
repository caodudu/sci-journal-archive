CREATE TABLE IF NOT EXISTS journals (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    title_norm TEXT NOT NULL,
    issn TEXT,
    eissn TEXT,
    publisher TEXT,
    country TEXT,
    publisher_address TEXT,
    languages TEXT,
    founding_year INTEGER,
    is_new_journal INTEGER NOT NULL DEFAULT 0,
    new_journal_reason TEXT,
    is_biomed INTEGER NOT NULL DEFAULT 0,
    biomed_reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_journals_identity
ON journals(title_norm, COALESCE(issn, ''), COALESCE(eissn, ''));

CREATE TABLE IF NOT EXISTS journal_years (
    journal_id INTEGER NOT NULL REFERENCES journals(id),
    year INTEGER NOT NULL,
    index_type TEXT NOT NULL CHECK(index_type IN ('SCIE', 'ESCI', 'UNKNOWN')),
    impact_factor REAL,
    categories TEXT,
    raw_source TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (journal_id, year, index_type)
);

CREATE TABLE IF NOT EXISTS pubmed_year_counts (
    journal_id INTEGER NOT NULL REFERENCES journals(id),
    pub_year INTEGER NOT NULL,
    query TEXT NOT NULL,
    count INTEGER NOT NULL,
    collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (journal_id, pub_year)
);

CREATE TABLE IF NOT EXISTS pubmed_article_dates (
    pmid TEXT PRIMARY KEY,
    journal_id INTEGER NOT NULL REFERENCES journals(id),
    pub_year INTEGER,
    title TEXT,
    received_date TEXT,
    revised_date TEXT,
    accepted_date TEXT,
    published_date TEXT,
    days_received_to_accepted INTEGER,
    days_accepted_to_published INTEGER,
    days_received_to_published INTEGER,
    raw_pubmed_xml TEXT,
    collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS journal_warnings (
    journal_id INTEGER NOT NULL REFERENCES journals(id),
    warning_year INTEGER NOT NULL,
    warning_source TEXT NOT NULL,
    warning_level TEXT,
    warning_note TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (journal_id, warning_year, warning_source)
);

CREATE TABLE IF NOT EXISTS journal_cas_partitions (
    id INTEGER PRIMARY KEY,
    journal_id INTEGER NOT NULL REFERENCES journals(id),
    cas_year INTEGER NOT NULL,
    cas_zone TEXT,
    cas_major_category TEXT,
    cas_minor_category TEXT,
    cas_source TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cas_partition_identity
ON journal_cas_partitions(journal_id, cas_year, COALESCE(cas_source, ''));

CREATE VIEW IF NOT EXISTS v_journal_summary AS
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
    jy.categories
FROM journals j
JOIN journal_years jy ON jy.journal_id = j.id;
