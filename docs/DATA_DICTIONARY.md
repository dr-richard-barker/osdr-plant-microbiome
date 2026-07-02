# Data Dictionary

Relational schema of `data/db/osdr_plant_microbiome.db` (SQLite). Full DDL in
[`db/schema.sql`](../db/schema.sql). Every non-verbatim row carries a
`data_provenance` flag.

## Entity–relationship overview

```
studies (1)───(N) assays
   │  │
   │  └────────(N) factors
   │
   └────────────(N) samples ──(1:1) alpha_diversity
                     │
                     ├──(N) abundance (N)── taxa
                     └──(N) beta_diversity  (sample_a, sample_b)
```

## Tables

### `studies` — one row per OSDR accession
| column | type | source | description |
|---|---|---|---|
| osd_accession | TEXT PK | OSDR | e.g. `OSD-766` |
| glds_accession | TEXT | OSDR | legacy GeneLab id |
| title | TEXT | OSDR | study title |
| organism | TEXT | OSDR | host plant / community |
| cultivar | TEXT | OSDR | cultivar / species mix |
| platform_hardware | TEXT | OSDR | Veggie, APH, XROOTS |
| mission | TEXT | OSDR | flight programme |
| doi | TEXT | OSDR | dataset DOI (where minted) |
| osdr_url | TEXT | OSDR | landing page |
| confidence | TEXT | curator | high/medium/low registry confidence |
| notes | TEXT | curator | provenance notes |

### `assays` — measurement assays per study
`assay_id` PK · `osd_accession` FK · `assay_type` (16S rRNA amplicon / ITS amplicon) · `target_region` (V3-V4, V4, ITS1) · `sequencing_platform`.

### `factors` — study design variables
`factor_id` PK · `osd_accession` FK · `factor_name` (e.g. Spaceflight, Light regime, Tissue type).

### `samples` — biological specimens / sequencing units
`sample_id` PK · `osd_accession` FK · `sample_name` · `tissue_type` (leaf/root/fruit/wick/substrate/water/swab) · `spaceflight` (1=flight, 0=ground) · `light_regime` · `plant_position` · `data_provenance` (`osdr_metadata`).

### `taxa` — shared taxonomy dimension
`taxon_id` PK · `kingdom` `phylum` `class` `order` `family` `genus` · `taxonomy_string` (UNIQUE).

### `abundance` — fact table (sample × taxon)
`sample_id`+`taxon_id` PK · `relative_abundance` (0–1) · `read_count` · `data_provenance` (`illustrative_model` by default; `osdr_feature_table` once real tables are ingested).

### `alpha_diversity` — per-sample metrics (`data_provenance = computed`)
`observed_features` · `shannon` · `simpson` · `pielou_evenness`.

### `beta_diversity` — pairwise sample distances
`osd_accession` · `sample_a` · `sample_b` · `metric` (bray_curtis) · `distance`.

### `provenance_log` — build audit trail
`step` · `detail` · `row_count` · `build_utc`.

## Views
- `v_study_overview` — per-study sample / tissue / assay rollup.
- `v_sample_alpha` — samples joined to alpha diversity.
- `v_genus_by_tissue` — mean genus relative abundance by study × tissue.

## Provenance flags
| flag | meaning |
|---|---|
| `osdr_metadata` | verbatim from NASA OSDR |
| `computed` | derived by the pipeline from abundance data |
| `illustrative_model` | deterministic ecological model (demo; replace with real data) |
| `osdr_feature_table` | ingested from a real OSDR feature table |
