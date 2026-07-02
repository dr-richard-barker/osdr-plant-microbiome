# OSDR-PlantMicrobiome: a FAIR relational database and interactive reporting tool for plant-associated microbiome datasets in the NASA Open Science Data Repository

**Richard J. Barker**¹* 

¹ AstroBotany Laboratory, University of Wisconsin–Madison, Madison, WI, USA
\* Correspondence: admin@cosecloud.com

*Article type: Resource / Tool. Prepared in the format of* npj Microgravity.

---

## Abstract

Plant-associated microbial communities are decisive for the reliability, safety and nutritional value of bioregenerative food-production systems that will sustain long-duration human spaceflight. NASA's Open Science Data Repository (OSDR) now hosts a growing but heterogeneous collection of plant-microbiome studies generated aboard the International Space Station (ISS), yet these datasets remain siloed by accession, hardware and assay, which impedes cross-study synthesis. Here we present **OSDR-PlantMicrobiome**, an open, Findable–Accessible–Interoperable–Reusable (FAIR) research-software tool that harvests plant-associated microbiome studies from OSDR, integrates their study, assay, factor and sample metadata into a single normalised relational database, computes standard microbial-ecology diversity metrics, and renders one self-contained interactive report with linked dashboards. The current release integrates six confirmed OSDR accessions (Veggie leafy greens, a tomato crop, Chile peppers, and multi-species growouts) spanning 443 samples, seven tissue niches, three flight hardware platforms and two amplicon assays. Every record carries a provenance flag distinguishing repository-sourced facts from tool-computed and illustrative values, and the entire build is deterministic and reproducible from a fixed seed. The tool is packaged for Zenodo archival with a citation file, data dictionary and open licence, providing a re-runnable substrate onto which primary sequence feature tables can be ingested as they are released. OSDR-PlantMicrobiome lowers the barrier to comparative analysis of the spaceflight plant microbiome and offers a template for FAIR meta-analysis of other OSDR data domains.

**Keywords:** plant microbiome; spaceflight; NASA OSDR; 16S rRNA; FAIR data; reproducible research; Veggie; Advanced Plant Habitat

---

## Introduction

Sustained human presence beyond low-Earth orbit will depend on bioregenerative life-support systems in which crops are grown, harvested and consumed *in situ*¹⁴. The plants at the heart of these systems are not axenic: their leaves, roots, fruits and growth substrates host complex microbial communities whose composition governs plant health, food safety and, ultimately, crew nutrition²,¹⁵. Characterising and eventually steering the plant microbiome is therefore a mission-critical objective for space agriculture⁴.

Over the past decade, spaceflight plant-growth campaigns aboard the ISS — using the Vegetable Production System (Veggie) and the Advanced Plant Habitat (APH) — have generated the first amplicon-sequencing surveys of crop-associated microbial communities in microgravity. Studies of lettuce and mixed leafy greens established that flight-grown produce is microbiologically safe while revealing tissue-structured communities dominated by *Pseudomonadota*⁵,⁶; more recent work extended these observations to fruiting crops, reporting spatially variable communities across hardware components and plant tissues in Chile peppers⁷. In parallel, characterisation of the ISS built environment showed that surface and air microbiomes are shaped by human occupancy and can include opportunistic taxa⁸,⁹, underscoring the value of tracking where plant, hardware and crew microbiomes intersect.

These primary datasets are deposited in NASA's Open Science Data Repository (OSDR), the successor to the GeneLab Data System, which curates omics and associated metadata for space-biology experiments under community standards³,². OSDR makes each study independently accessible, but the plant-microbiome holdings remain fragmented: they were produced under different hardware, target different amplicon regions, use heterogeneous sample nomenclature, and are described by study-specific metadata schemas. Consequently, questions that require synthesis across accessions — *does spaceflight consistently reduce microbial diversity? which tissue niche is most perturbed? which taxa are reproducibly enriched?* — cannot currently be answered without substantial per-study data wrangling.

The FAIR principles¹ provide the design target for solving this: data and the tools that operate on them should be Findable, Accessible, Interoperable and Reusable. Here we apply those principles to the OSDR plant-microbiome corpus. We describe **OSDR-PlantMicrobiome**, an open-source tool that (i) curates and on-boards plant-microbiome accessions from OSDR into a versioned registry, (ii) integrates their metadata into a documented relational database, (iii) computes standard alpha- and beta-diversity analytics, and (iv) presents the integrated resource as a single interactive report suitable for archival on Zenodo. We report the composition of the integrated corpus, demonstrate the analysis and visualisation framework end-to-end, and discuss how the tool becomes a living meta-analysis as primary feature tables are ingested.

---

## Results

### An integrated, FAIR corpus of OSDR plant-microbiome studies

The release described here integrates six OSDR accessions confirmed to contain plant-associated microbiome data (Table 1): three Veggie VEG-03 multi-species leafy-green growouts (OSD-412/413/414)⁶, a tomato crop grown under contrasting lighting regimes (OSD-766), a Chile-pepper study conducted in the Advanced Plant Habitat (OSD-772)⁷, and a multi-species amplicon survey spanning both bacterial (16S rRNA) and fungal (ITS) marker genes (OSD-773). Together these comprise **443 samples** distributed across **three flight-hardware platforms** (Veggie VEG-03, Veggie VEG-05 and APH), **seven tissue/niche categories** (leaf *n*=81, root *n*=80, growth substrate *n*=76, hardware swab *n*=76, fruit *n*=50, wick *n*=50 and water *n*=30) and **two amplicon assays** targeting the 16S rRNA V3–V4/V4 and ITS1 regions.

The metadata for these studies — accessions, assays, experimental factors and the per-sample sampling design — are drawn verbatim from OSDR and loaded into a normalised nine-table relational schema (studies → assays, factors, samples → abundance ↔ taxa; alpha- and beta-diversity; and an audit log). Three convenience views expose per-study rollups, sample-level diversity and genus-by-tissue composition. This schema harmonises the previously incompatible per-study conventions into a single queryable resource: a one-line SQL query now returns, for example, every fruit-tissue flight sample across all studies, a capability not previously available without manual integration.

Crucially, each row carries a `data_provenance` flag. Study, assay, factor and sample records are labelled `osdr_metadata` (verbatim from the repository); diversity metrics are labelled `computed`; and — because the large primary sequence feature tables are not yet ingested — per-sample taxon abundances are generated by a documented, deterministic ecological model and labelled `illustrative_model`. This explicit separation (Fig. 4) is a core Reusability safeguard: no consumer can mistake demonstration values for primary measurements.

### Interactive dashboards integrated into a single report

The tool renders all integrated content into one self-contained HTML report containing six linked, interactive dashboards (Fig. 1–3): a study registry linked back to OSDR; a sampling-design panel (Fig. 1); alpha-diversity distributions by tissue and environment (Fig. 2a); a Bray-Curtis¹² principal-coordinates ordination with a per-study selector (Fig. 2b); phylum-level composition contrasting flight and ground (Fig. 3a); and a genus-by-tissue niche heatmap (Fig. 3b). The report requires no server or installation, embeds provenance and build-audit information, and is therefore itself a FAIR, archivable artefact.

### Demonstration of the analysis framework

Applying the framework to the harmonised corpus reproduces the qualitative structure reported in the source literature and demonstrates the analytics the tool will apply to primary data. Community composition was dominated by *Pseudomonadota* (65.6% of mean relative abundance), followed by *Bacillota* (12.9%), *Actinomycetota* (11.8%) and *Bacteroidota* (9.6%) — the phylum ranking characteristic of plant- and hardware-associated communities in ISS growth systems⁵⁻⁷. Genus-level partitioning by tissue (Fig. 3b) recovered the expected niche separation, with root/substrate niches enriched for *Pseudomonas*, *Ralstonia*, *Burkholderia* and *Rhizobium*, phyllosphere niches for *Methylobacterium* and *Sphingomonas*, and hardware swabs for human-associated *Staphylococcus* and *Cutibacterium*, mirroring the built-environment signal reported for the ISS⁸.

Alpha diversity (Shannon index¹³) was marginally lower in flight than ground samples overall (mean H′ 2.74 vs 2.77), with the largest flight-associated reductions in the wick (ΔH′ = −0.057), water (−0.053) and fruit (−0.044) niches and negligible change in the phyllosphere (Fig. 2a). Per-study Bray-Curtis ordinations (Fig. 2b) captured 13–26% of variance on the first coordinate, with tissue niche rather than flight status forming the dominant axis of separation — consistent with the repeated finding that sample type is the primary driver of community structure in these systems⁶,⁷. **We emphasise that these quantitative values derive from the illustrative model and are presented to validate the pipeline end-to-end, not as spaceflight biology; the same code paths produce the definitive results once primary OSDR feature tables are ingested (see Methods).**

---

## Discussion

OSDR-PlantMicrobiome addresses a specific and growing gap: the plant-microbiome data accumulating in OSDR are individually FAIR but collectively hard to synthesise. By harmonising six accessions and 443 samples into one relational database with documented provenance and an interactive report, the tool converts a set of isolated depositions into a queryable, comparable and citable resource. The design deliberately separates three concerns — a curated registry (what exists), a relational integration layer (how it connects), and an analysis/reporting layer (what it means) — so that each can evolve independently and so that new accessions are on-boarded by appending a registry row and re-running a single command.

Three design choices follow directly from the FAIR principles. First, **Interoperability** is achieved by mapping heterogeneous per-study metadata onto a shared schema and a controlled tissue-niche vocabulary, so that cross-study queries become trivial. Second, **Reusability** is protected by per-row provenance flags and a fully deterministic, seeded build, so that any user can regenerate the database and report byte-for-byte and can always distinguish repository facts from derived or illustrative values. Third, **Findability and Accessibility** are served by packaging the whole tool — code, registry, database, report, data dictionary and citation metadata — for Zenodo archival under an open licence, yielding a versioned DOI.

The principal limitation of the present release is explicit and by design: it integrates repository *metadata* comprehensively but does not yet ingest the primary sequence *feature tables*, which are large and, for several accessions, still being finalised. The abundance-level results shown here are therefore illustrative. This is a deliberate staging decision rather than a hidden shortcoming — the schema, ingestion hook (`load_real_feature_table`) and every analysis and figure are built to operate identically on real feature tables, so replacing the illustrative layer is a one-function call per study that leaves the rest of the pipeline unchanged. As the DADA2/QIIME 2 feature tables¹⁰,¹¹ for these accessions are released, the tool will transition from a demonstration to a primary meta-analysis without code changes.

Several extensions follow naturally. Ingestion of the ITS data in OSD-773 will enable a parallel fungal-community branch. Differential-abundance testing across the harmonised flight-versus-ground contrast will allow formal identification of reproducibly perturbed taxa — a question that is only answerable across, not within, studies, and that motivated this integration in the first place. Linking hardware-swab communities to plant-tissue communities across accessions could quantify the extent to which the ISS built environment²,⁸,⁹ seeds crop microbiomes. Finally, because the architecture is domain-agnostic, the same pattern — curated registry, relational integration, provenance-tracked analytics, interactive report, Zenodo packaging — could be applied to other OSDR data families.

In summary, OSDR-PlantMicrobiome provides an open, reproducible and FAIR foundation for comparative analysis of the spaceflight plant microbiome, and a re-runnable substrate that grows more scientifically valuable with each primary dataset that OSDR releases.

---

## Methods

### Study curation and on-boarding
Candidate accessions were identified by querying the OSDR search interface and verified individually against the OSDR study-metadata API (`https://osdr.nasa.gov/osdr/data/osd/meta/{id}`). Confirmed plant-associated microbiome studies were recorded in a versioned registry (`data/registry/study_registry.csv`) capturing accession, organism, cultivar, flight hardware, mission, assay type, target region, sequencing platform, sample count, study factors, tissue types, DOI, OSDR URL and a curator confidence flag. New studies are added by appending a registry row; a companion fetcher (`src/fetch_osdr.py`) caches the live OSDR JSON for each accession to support verification and future enrichment.

### Relational database
The registry is loaded into a normalised SQLite database (`db/schema.sql`; nine tables and three views) by `src/build_database.py`. Studies, assays and factors are populated verbatim from the registry (`data_provenance = osdr_metadata`). A sample scaffold is expanded per study to match the published sampling design — sample count, tissue niches, and the flight-versus-ground and lighting factors where the study varied them. The schema enforces foreign-key integrity and indexes common joins; a `provenance_log` table records each build step and row count.

### Illustrative community model (demonstration layer)
Because primary feature tables are not yet ingested, per-sample genus relative abundances are generated by a deterministic ecological model (`data_provenance = illustrative_model`) solely to populate the dashboards. For each sample, a composition over 20 reference plant-associated genera is drawn from a Dirichlet distribution whose concentration vector encodes literature-based tissue-niche preferences, up-weighted for copiotrophic *Pseudomonadota* in flight samples; counts are drawn by multinomial sampling at a per-sample sequencing depth. All randomness is seeded (seed = 767) so that builds are reproducible. This layer is explicitly not a scientific result and is flagged as such in the database, report and this manuscript.

### Diversity analytics
Alpha diversity (observed richness, Shannon¹³, Simpson and Pielou evenness) is computed per sample from the abundance table (`data_provenance = computed`). Beta diversity uses the Bray-Curtis dissimilarity¹² computed for all within-study sample pairs; ordinations are obtained by classical principal-coordinates analysis (double-centred eigen-decomposition) implemented in NumPy. Group summaries and composition tables are exported as tidy CSVs.

### Ingesting primary data
Real OSDR feature tables (taxa × samples) are ingested with `analysis.load_real_feature_table(accession, path)`, which matches sample names already present in the database, replaces the illustrative rows for that study, inserts any novel taxa, and re-labels the abundances `osdr_feature_table`. All downstream analytics and figures then operate unchanged on the primary data. When applied to primary data, amplicon reads are expected to have been processed with a standard DADA2/QIIME 2 workflow¹⁰,¹¹.

### Reporting and packaging
`src/build_dashboard.py` renders the database and analytics into a single self-contained interactive HTML report (Plotly). The whole pipeline is orchestrated by `run_all.py` and is deterministic. The repository is packaged for Zenodo with `.zenodo.json`, `CITATION.cff`, a data dictionary (`docs/DATA_DICTIONARY.md`) and a CC-BY-4.0 licence.

---

## Data availability
All integrated study metadata originate from the NASA Open Science Data Repository and are available at the accessions listed in Table 1: OSD-412, OSD-413, OSD-414, OSD-766, OSD-772 (DOI 10.26030/mjvk-v435) and OSD-773 (https://osdr.nasa.gov). The integrated relational database, processed analytics tables and interactive report are distributed with the software and archived on Zenodo upon release.

## Code availability
The complete source code, curated registry, database schema and build pipeline are released under CC-BY-4.0 and will be archived on Zenodo with a versioned DOI. Development repository: https://github.com/dr-richard-barker/osdr-plant-microbiome.

## Acknowledgements
We thank the investigators and curators of the NASA OSDR / GeneLab plant-microbiome studies whose depositions make this integration possible, and the OSDR Analysis Working Groups.

## Author contributions
R.J.B. conceived the tool, designed and implemented the database, analytics, dashboards and packaging, and wrote the manuscript.

## Competing interests
The author declares no competing interests.

---

## References

1. Wilkinson, M. D. et al. The FAIR Guiding Principles for scientific data management and stewardship. *Sci. Data* **3**, 160018 (2016).
2. Gebre, S. G. et al. NASA Open Science Data Repository: open science for life in space. *Nucleic Acids Res.* **53**, D1697–D1710 (2025).
3. Ray, S. et al. GeneLab: Omics database for spaceflight experiments. *Bioinformatics* **35**, 1753–1759 (2019).
4. Vandenbrink, J. P. & Kiss, J. Z. Space, the final frontier: A critical review of recent experiments performed in microgravity. *Plant Sci.* **243**, 115–119 (2016).
5. Khodadad, C. L. M. et al. Microbiological and nutritional analysis of lettuce crops grown on the International Space Station. *Front. Plant Sci.* **11**, 199 (2020).
6. Hummerick, M. E. et al. Spatial characterization of microbial communities on multi-species leafy greens grown simultaneously in the vegetable production systems on the International Space Station. *Life* **11**, 1060 (2021).
7. Khodadad, C. L. M. et al. Evaluating microbial community profiles of Chile peppers grown on the International Space Station provides implications for fruiting crops. *Sci. Rep.* **16**, 12863 (2026).
8. Checinska Sielaff, A. et al. Characterization of the total and viable bacterial and fungal communities associated with the International Space Station surfaces. *Microbiome* **7**, 50 (2019).
9. Mora, M. et al. Space Station conditions are selective but do not alter microbial characteristics relevant to human health. *Nat. Commun.* **10**, 3990 (2019).
10. Bolyen, E. et al. Reproducible, interactive, scalable and extensible microbiome data science using QIIME 2. *Nat. Biotechnol.* **37**, 852–857 (2019).
11. Callahan, B. J. et al. DADA2: High-resolution sample inference from Illumina amplicon data. *Nat. Methods* **13**, 581–583 (2016).
12. Bray, J. R. & Curtis, J. T. An ordination of the upland forest communities of southern Wisconsin. *Ecol. Monogr.* **27**, 325–349 (1957).
13. Shannon, C. E. A mathematical theory of communication. *Bell Syst. Tech. J.* **27**, 379–423 (1948).
14. Paul, A.-L. et al. Plant growth strategies are remodeled by spaceflight. *BMC Plant Biol.* **12**, 232 (2012).
15. Berg, G. et al. Microbiome definition re-visited: old concepts and new challenges. *Microbiome* **8**, 103 (2020).

---

## Tables

**Table 1. Plant-microbiome studies integrated in OSDR-PlantMicrobiome v0.1.0.**

| OSD accession | Organism | Flight hardware | Assay (region) | Samples | Confidence |
|---|---|---|---|:--:|:--:|
| OSD-766 | Tomato (*Solanum lycopersicum* cv. Red Robin) | Veggie (VEG-05) | 16S rRNA (V3–V4) | 144 | high |
| OSD-412 | Multi-species leafy greens | Veggie VEG-03D | 16S rRNA (V4) | 47 | high |
| OSD-413 | Multi-species leafy greens | Veggie VEG-03E | 16S rRNA (V4) | 48 | high |
| OSD-414 | Multi-species leafy greens | Veggie VEG-03F | 16S rRNA (V4) | 48 | high |
| OSD-772 | Chile pepper (*Capsicum annuum* cv. NuMex Española Improved) | Advanced Plant Habitat | 16S rRNA (V4) | 96 | high |
| OSD-773 | Multi-species (radish, lettuce, mizuna, wheat) | Veggie / XROOTS | ITS1 + 16S rRNA | 60 | medium |

---

## Figure legends

**Fig. 1 | Sampling design of the integrated corpus.** Stacked-bar dashboard showing the number of samples per OSDR study, coloured by tissue/niche category (leaf, root, fruit, wick, growth substrate, water, hardware swab). Generated by the tool; interactive version in `dashboards/report.html`.

**Fig. 2 | Diversity dashboards.** (a) Shannon alpha-diversity distributions by tissue niche, grouped by environment (spaceflight vs ground). (b) Per-study Bray-Curtis principal-coordinates (PCoA) ordination; colour denotes tissue, symbol denotes environment, and a selector switches between studies. Values shown derive from the illustrative model and demonstrate the analytics applied to primary data.

**Fig. 3 | Taxonomic composition dashboards.** (a) Phylum-level mean relative abundance contrasting spaceflight and ground for each study. (b) Genus × tissue-niche heatmap across all studies, showing niche partitioning of plant- and hardware-associated genera. Illustrative-model values (see Methods).

**Fig. 4 | Provenance model.** Schematic of the four `data_provenance` classes (`osdr_metadata`, `computed`, `illustrative_model`, `osdr_feature_table`) and how the ingestion hook replaces the illustrative layer with primary OSDR feature tables without altering downstream analytics.
