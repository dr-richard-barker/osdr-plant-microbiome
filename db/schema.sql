-- =====================================================================
-- OSDR Plant Microbiome FAIR Tool — Relational Schema (SQLite)
-- =====================================================================
-- Normalised schema linking NASA OSDR plant-microbiome studies to their
-- assays, experimental factors, samples, taxonomic profiles and derived
-- diversity metrics. Every row that is NOT a verbatim copy of OSDR
-- metadata carries a `data_provenance` flag so downstream consumers can
-- distinguish repository-sourced facts from tool-derived / illustrative
-- values. This is a core FAIR (Reusable) requirement.
-- =====================================================================

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS v_study_overview;
DROP VIEW  IF EXISTS v_sample_alpha;
DROP VIEW  IF EXISTS v_genus_by_tissue;
DROP TABLE IF EXISTS beta_diversity;
DROP TABLE IF EXISTS alpha_diversity;
DROP TABLE IF EXISTS abundance;
DROP TABLE IF EXISTS taxa;
DROP TABLE IF EXISTS samples;
DROP TABLE IF EXISTS factors;
DROP TABLE IF EXISTS assays;
DROP TABLE IF EXISTS studies;
DROP TABLE IF EXISTS provenance_log;

-- ---------------------------------------------------------------------
-- 1. Studies (one row per OSDR accession)
-- ---------------------------------------------------------------------
CREATE TABLE studies (
    osd_accession     TEXT PRIMARY KEY,          -- e.g. OSD-766
    glds_accession    TEXT,                       -- legacy GeneLab id
    title             TEXT NOT NULL,
    organism          TEXT,
    cultivar          TEXT,
    platform_hardware TEXT,                        -- Veggie, APH, XROOTS ...
    mission           TEXT,
    doi               TEXT,
    osdr_url          TEXT,
    confidence        TEXT CHECK (confidence IN ('high','medium','low')),
    notes             TEXT
);

-- ---------------------------------------------------------------------
-- 2. Assays (an OSDR study may carry several assays)
-- ---------------------------------------------------------------------
CREATE TABLE assays (
    assay_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    osd_accession      TEXT NOT NULL REFERENCES studies(osd_accession),
    assay_type         TEXT,                       -- 16S rRNA amplicon, ITS ...
    target_region      TEXT,                       -- V3-V4, V4, ITS1 ...
    sequencing_platform TEXT
);

-- ---------------------------------------------------------------------
-- 3. Experimental factors (study design variables)
-- ---------------------------------------------------------------------
CREATE TABLE factors (
    factor_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    osd_accession TEXT NOT NULL REFERENCES studies(osd_accession),
    factor_name   TEXT NOT NULL
);

-- ---------------------------------------------------------------------
-- 4. Samples (biological specimens / sequencing units)
-- ---------------------------------------------------------------------
CREATE TABLE samples (
    sample_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    osd_accession   TEXT NOT NULL REFERENCES studies(osd_accession),
    sample_name     TEXT NOT NULL,
    tissue_type     TEXT,                           -- leaf, root, fruit, wick ...
    spaceflight     INTEGER CHECK (spaceflight IN (0,1)),   -- 1 = flight, 0 = ground
    light_regime    TEXT,
    plant_position  TEXT,
    data_provenance TEXT NOT NULL DEFAULT 'osdr_metadata'
);

-- ---------------------------------------------------------------------
-- 5. Taxa (shared taxonomy dimension)
-- ---------------------------------------------------------------------
CREATE TABLE taxa (
    taxon_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kingdom          TEXT,
    phylum           TEXT,
    class            TEXT,
    "order"          TEXT,
    family           TEXT,
    genus            TEXT,
    taxonomy_string  TEXT UNIQUE
);

-- ---------------------------------------------------------------------
-- 6. Abundance (fact table: sample x taxon relative abundance)
-- ---------------------------------------------------------------------
CREATE TABLE abundance (
    sample_id          INTEGER NOT NULL REFERENCES samples(sample_id),
    taxon_id           INTEGER NOT NULL REFERENCES taxa(taxon_id),
    relative_abundance REAL,                        -- 0..1
    read_count         INTEGER,
    data_provenance    TEXT NOT NULL DEFAULT 'illustrative_model',
    PRIMARY KEY (sample_id, taxon_id)
);

-- ---------------------------------------------------------------------
-- 7. Alpha diversity (per-sample summary metrics)
-- ---------------------------------------------------------------------
CREATE TABLE alpha_diversity (
    sample_id         INTEGER PRIMARY KEY REFERENCES samples(sample_id),
    observed_features INTEGER,
    shannon           REAL,
    simpson           REAL,
    pielou_evenness   REAL,
    data_provenance   TEXT NOT NULL DEFAULT 'computed'
);

-- ---------------------------------------------------------------------
-- 8. Beta diversity (pairwise sample distances)
-- ---------------------------------------------------------------------
CREATE TABLE beta_diversity (
    osd_accession TEXT NOT NULL REFERENCES studies(osd_accession),
    sample_a      INTEGER NOT NULL REFERENCES samples(sample_id),
    sample_b      INTEGER NOT NULL REFERENCES samples(sample_id),
    metric        TEXT NOT NULL,                    -- bray_curtis, jaccard ...
    distance      REAL,
    PRIMARY KEY (sample_a, sample_b, metric)
);

-- ---------------------------------------------------------------------
-- 9. Provenance / build log (auditability)
-- ---------------------------------------------------------------------
CREATE TABLE provenance_log (
    step        TEXT,
    detail      TEXT,
    row_count   INTEGER,
    build_utc   TEXT
);

-- Indexes for common joins / filters
CREATE INDEX idx_samples_study   ON samples(osd_accession);
CREATE INDEX idx_samples_tissue  ON samples(tissue_type);
CREATE INDEX idx_abund_taxon     ON abundance(taxon_id);
CREATE INDEX idx_assays_study    ON assays(osd_accession);

-- ---------------------------------------------------------------------
-- Convenience views used by the dashboards
-- ---------------------------------------------------------------------
CREATE VIEW v_study_overview AS
SELECT s.osd_accession, s.title, s.organism, s.platform_hardware, s.mission,
       COUNT(DISTINCT sm.sample_id)  AS n_samples,
       COUNT(DISTINCT sm.tissue_type) AS n_tissue_types,
       GROUP_CONCAT(DISTINCT a.assay_type) AS assays
FROM studies s
LEFT JOIN samples sm ON sm.osd_accession = s.osd_accession
LEFT JOIN assays  a  ON a.osd_accession  = s.osd_accession
GROUP BY s.osd_accession;

CREATE VIEW v_sample_alpha AS
SELECT sm.sample_id, sm.osd_accession, sm.tissue_type, sm.spaceflight,
       sm.light_regime, ad.observed_features, ad.shannon, ad.simpson,
       ad.pielou_evenness
FROM samples sm
JOIN alpha_diversity ad ON ad.sample_id = sm.sample_id;

CREATE VIEW v_genus_by_tissue AS
SELECT sm.osd_accession, sm.tissue_type, t.genus,
       AVG(ab.relative_abundance) AS mean_rel_abundance,
       COUNT(*)                   AS n_obs
FROM abundance ab
JOIN samples sm ON sm.sample_id = ab.sample_id
JOIN taxa    t  ON t.taxon_id   = ab.taxon_id
GROUP BY sm.osd_accession, sm.tissue_type, t.genus;
