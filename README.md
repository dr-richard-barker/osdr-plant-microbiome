# OSDR-PlantMicrobiome 🌱🛰️
### A FAIR relational database, analysis pipeline and interactive report for NASA OSDR plant-associated microbiome datasets

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-blue.svg)](LICENSE)
[![Reproducible](https://img.shields.io/badge/build-reproducible%20(seed%20767)-success)](run_all.py)
[![Data: NASA OSDR](https://img.shields.io/badge/data-NASA%20OSDR-0b3d64)](https://osdr.nasa.gov)
[![Status](https://img.shields.io/badge/status-v0.1.0%20alpha-orange)]()

> Harvests every plant-associated microbiome study in the NASA **Open Science Data
> Repository (OSDR)**, integrates their metadata into a normalised **relational
> database**, computes microbial-ecology **diversity metrics**, and renders one
> self-contained **interactive HTML report** with linked dashboards — packaged
> for **Zenodo** archival and accompanied by an **npj Microgravity-style
> manuscript**.

---

## 🎯 Project goals

The mission is a single, **FAIR** ([Findable, Accessible, Interoperable,
Reusable](https://www.go-fair.org/fair-principles/)) tool that turns the
scattered plant-microbiome holdings of NASA OSDR into an analysable,
citable, interactive resource.

| # | Goal | FAIR pillar |
|---|------|-------------|
| G1 | **Curate & on-board** every plant-associated microbiome study in OSDR into a versioned registry, with a live API fetcher for new accessions. | Findable |
| G2 | **Integrate** study/assay/factor/sample metadata + community profiles into one **relational database** (SQLite, documented schema). | Interoperable |
| G3 | **Analyse** — standard alpha (Shannon, Simpson, Pielou, observed) and beta (Bray-Curtis PCoA) diversity, taxonomic composition, tissue-niche partitioning. | Reusable |
| G4 | **Visualise** — a series of **interactive dashboards integrated into a single report** (`dashboards/report.html`). | Accessible |
| G5 | **Graph database** — a **knowledge graph** of study↔metadata relationships (GraphML / JSON / CSV / Neo4j Cypher) revealing natural comparison groups. | Interoperable |
| G6 | **Guild ML** — a semi-supervised engine inferring which taxa are likely **pathogenic vs beneficial** (weak-supervision + traits + co-occurrence + label spreading). | Reusable |
| G7 | **Dated figure snapshots** — publication figures (PNG+SVG) exported to `figures/<date>/`, acknowledging the corpus is **transient** (the FAIR-dashboard rationale). | Findable |
| G8 | **Package for Zenodo** — `.zenodo.json`, `CITATION.cff`, license, data dictionary, deterministic reproducible build. | Findable + Reusable |
| G9 | **Communicate** — a manuscript in **npj Microgravity** style (text + figures versions) with accurate references in the journal's format. | — |
| G10 | **Track provenance** — every row flags whether it is OSDR-sourced, computed, or illustrative. | Reusable |

---

## 📊 Progress tracker

**Legend:** ✅ done · 🟡 in progress · ⬜ planned

| # | Deliverable | Status | Artefact |
|---|-------------|:------:|----------|
| G1 | Curated study registry (6 accessions) | ✅ | [`data/registry/study_registry.csv`](data/registry/study_registry.csv) |
| G1 | Live OSDR API fetcher | ✅ | [`src/fetch_osdr.py`](src/fetch_osdr.py) |
| G2 | Relational schema (9 tables, 3 views) | ✅ | [`db/schema.sql`](db/schema.sql) |
| G2 | Database builder + loader | ✅ | [`src/build_database.py`](src/build_database.py) |
| G2 | Built database (6 studies · 443 samples · 8.9k abundances) | ✅ | `data/db/osdr_plant_microbiome.db` |
| G3 | Diversity / ordination analysis | ✅ | [`src/analysis.py`](src/analysis.py) |
| G3 | Real feature-table ingestion hook | ✅ | `analysis.load_real_feature_table()` |
| G4 | Interactive integrated report (8 dashboards) | ✅ | [`dashboards/report.html`](dashboards/report.html) |
| G5 | Knowledge graph + study-similarity projection | ✅ | [`src/build_graph.py`](src/build_graph.py) · `data/graph/*.graphml` · `load_neo4j.cypher` |
| G6 | Guild-inference ML engine + method card | ✅ | [`src/classify_guild.py`](src/classify_guild.py) · `data/processed/GUILD_METHOD.md` |
| G7 | Dated figure snapshot (6 figs, PNG+SVG) + transience manifest | ✅ | [`figures/2026-07-02/`](figures/2026-07-02/) |
| G8 | Zenodo metadata + citation + license + data dictionary | ✅ | [`.zenodo.json`](.zenodo.json) · [`CITATION.cff`](CITATION.cff) · [`LICENSE`](LICENSE) · [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) |
| G9 | npj manuscript — text + **figures** versions + references | ✅ | [`manuscript/manuscript.md`](manuscript/manuscript.md) · [`manuscript/manuscript_with_figures.md`](manuscript/manuscript_with_figures.md) · [`references.bib`](manuscript/references.bib) |
| G10 | Per-row provenance flags + audit log | ✅ | `provenance_log`, `data_provenance` columns |
| — | CI: reproducible build + publish report to GitHub Pages | ✅ | [`.github/workflows/build-and-deploy.yml`](.github/workflows/build-and-deploy.yml) |
| — | **Ingest real OSDR feature tables** (replace illustrative model) | ⬜ | roadmap |
| — | ITS/fungal analysis branch for OSD-773 | ⬜ | roadmap |
| — | Guild engine v2: strain-level + SparCC/SPIEC-EASI + PICRUSt2 traits | ⬜ | roadmap |
| — | Differential-abundance testing (ANCOM-BC / ALDEx2) | ⬜ | roadmap |

---

## 🗂️ Curated studies (v0.1.0)

| OSD | Organism | Hardware | Assay | Samples | Confidence |
|-----|----------|----------|-------|:-------:|:----------:|
| [OSD-766](https://osdr.nasa.gov/bio/repo/data/studies/OSD-766) | Tomato (*Solanum lycopersicum* cv. Red Robin) | Veggie | 16S V3–V4 | 144 | high |
| [OSD-412](https://osdr.nasa.gov/bio/repo/data/studies/OSD-412) | Multi-species leafy greens | Veggie VEG-03D | 16S V4 | 47 | high |
| [OSD-413](https://osdr.nasa.gov/bio/repo/data/studies/OSD-413) | Multi-species leafy greens | Veggie VEG-03E | 16S V4 | 48 | high |
| [OSD-414](https://osdr.nasa.gov/bio/repo/data/studies/OSD-414) | Multi-species leafy greens | Veggie VEG-03F | 16S V4 | 48 | high |
| [OSD-772](https://osdr.nasa.gov/bio/repo/data/studies/OSD-772) | Chile pepper (*Capsicum annuum* cv. NuMex Española Improved) | Advanced Plant Habitat | 16S V4 | 96 | high |
| [OSD-773](https://osdr.nasa.gov/bio/repo/data/studies/OSD-773) | Multi-species (radish/lettuce/mizuna/wheat) | Veggie / XROOTS | ITS + 16S | 60 | medium |

> The registry is versioned; new accessions are added by appending a row and
> re-running `python run_all.py --fetch`.

---

## 🚀 Quick start

```bash
# 1. install (Python ≥ 3.10)
pip install -r requirements.txt

# 2. reproducible offline build: DB → analytics → interactive report
python run_all.py

# 3. (optional) refresh metadata against the live NASA OSDR API first
python run_all.py --fetch

# 4. open the report
#    dashboards/report.html   (any browser)

# 5. query the database directly
python -c "import sqlite3,pandas as pd; \
print(pd.read_sql_query('SELECT * FROM v_study_overview', \
sqlite3.connect('data/db/osdr_plant_microbiome.db')))"
```

---

## 📈 What the report contains

`dashboards/report.html` is one self-contained, navigable file with eight
interactive dashboards (Plotly):

1. **Study registry** — curated accessions linked to OSDR.
2. **Sampling design** — specimens per study by tissue niche.
3. **Alpha diversity** — Shannon by tissue × environment (flight vs ground).
4. **Community ordination** — Bray-Curtis PCoA with a per-study selector.
5. **Taxonomic composition** — phylum-level, ground vs spaceflight.
6. **Niche heatmap** — genus × tissue partitioning across all studies.
7. **Graph database** — interactive study↔metadata knowledge graph.
8. **Guild ML** — pathogen-risk vs beneficial-probability for each genus.

Plus an **overview KPI strip** and a **provenance / build-audit log**.

### 🧠 Which microbes are friend or foe — and foe to *whom*?
The [guild engine](src/classify_guild.py) fuses four independent signals —
a curated prior knowledge base, guild-specific ecological traits, co-occurrence
guilt-by-association, and multiclass semi-supervised label spreading — to place
each genus into one of **four guilds**, propagating calls even to genera left
deliberately unlabelled. Critically, it keeps the **two distinct meanings of
"pathogen" separate**:

| Guild | Threatens | Signal | Example |
|---|---|---|---|
| 🟢 **Beneficial / PGPR** | — (helps the crop) | plant-tissue resident, N-fixer/methylotroph | *Rhizobium*, *Bacillus* |
| 🟠 **Plant pathogen** | **the crop** (yield) | living plant / root-vascular association | *Ralstonia* (bacterial wilt) |
| 🔴 **Human pathogen** | **crew** (food safety) | human-contacted hardware (swab) association | *Staphylococcus*, *Cutibacterium* |
| ⚪ **Uncertain** | — | ambiguous evidence | — |

A single "pathogen" axis would conflate a crop-yield risk with a crew-health
risk; the engine reports **two separate risk scores** accordingly. See
[`data/processed/GUILD_METHOD.md`](data/processed/GUILD_METHOD.md).

### 🕸️ Graph database
[`src/build_graph.py`](src/build_graph.py) builds a knowledge graph (studies ↔
hardware / organism / assay / region / tissue / factor) and a study-similarity
projection, exported as **GraphML, node-link JSON, CSVs and a Neo4j Cypher
loader** for Gephi / Cytoscape / Neo4j.

### ⏳ Transient by design
The set of OSDR plant-microbiome studies grows over time, so every figure is a
**dated snapshot** under [`figures/<date>/`](figures/2026-07-02/) with a
manifest stating this explicitly. The live report always re-derives the current
picture — this is the whole point of the FAIR-dashboard approach.

---

## ⚠️ Data provenance (please read)

This tool cleanly separates three kinds of data:

| flag | what it is |
|------|-----------|
| `osdr_metadata` | **Real** — verbatim from NASA OSDR (studies, assays, factors, samples) |
| `computed` | **Real-derived** — diversity metrics computed by the pipeline |
| `illustrative_model` | **Demo** — per-sample taxon abundances from a documented, deterministic ecological model that reproduces published qualitative patterns, so the dashboards render *before* the large primary feature tables are ingested |
| `osdr_feature_table` | **Real** — once you ingest an OSDR feature table via `analysis.load_real_feature_table()` |

The illustrative layer exists purely so the tool is demonstrable end-to-end; it
is **not** a scientific result and is flagged as such in the database, the
report banner and the manuscript. Swapping in real feature tables is a
one-function call per study.

---

## 🏗️ Repository layout

```
OSDR Plant microbiome/
├── README.md                      ← you are here (goals + progress)
├── run_all.py                     ← one-command reproducible build
├── requirements.txt · LICENSE · CITATION.cff · .zenodo.json
├── data/
│   ├── registry/study_registry.csv    ← curated accessions (versioned)
│   ├── raw/                            ← cached live OSDR JSON (fetch)
│   ├── processed/                      ← tidy analytics + guild scores + method card
│   ├── graph/                          ← knowledge graph (GraphML/JSON/CSV/Cypher)
│   └── db/osdr_plant_microbiome.db     ← the relational database
├── db/schema.sql                  ← DDL (9 tables, 3 views)
├── src/
│   ├── config.py · fetch_osdr.py · build_database.py · analysis.py
│   ├── build_graph.py · classify_guild.py · make_figures.py · build_dashboard.py
├── dashboards/report.html         ← integrated interactive report (8 dashboards)
├── figures/2026-07-02/            ← dated figure snapshot (Fig1–6, PNG+SVG) + MANIFEST
├── docs/DATA_DICTIONARY.md
└── manuscript/
    ├── manuscript.md                  ← text version
    ├── manuscript_with_figures.md     ← embedded-figures version + npj legends
    └── references.bib
```

---

## 🔁 Reproducibility

The pipeline uses **no wall-clock randomness** — a fixed seed (`767`) means every
build produces a byte-identical database and report. The `provenance_log` table
records each step and row count for audit.

---

## 📜 Citing & license

Released under [CC BY 4.0](LICENSE). Cite via [`CITATION.cff`](CITATION.cff) (a
Zenodo DOI is minted on first release). When reusing the integrated data, please
also cite the individual OSD accessions listed above and in
[`manuscript/references.bib`](manuscript/references.bib).

*Underlying study metadata © the NASA OSDR / GeneLab contributors, reused under
the NASA open-data policy.*
