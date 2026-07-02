# Figure snapshot — 2026-07-02

**Corpus state at this snapshot:** 6 OSDR plant-microbiome studies, 443 samples.

> ⏳ **This is a transient result — by design.** The set of plant-associated
> microbiome studies in the NASA OSDR changes over time: a snapshot taken one
> year earlier would contain fewer studies, and one taken a year later will
> contain more. These figures therefore record a *fixed point in time*. The
> living, always-current picture is produced by the interactive FAIR report
> (`dashboards/report.html`), which re-derives every figure from the database
> on each build. This temporal caveat is the core motivation for the FAIR
> dashboard approach: archived figures for the record, a live report for truth.

## Studies included in this snapshot
| OSD accession | Organism | Hardware |
|---|---|---|
| OSD-412 | mixed community | Veggie (VEG-03D) |
| OSD-413 | mixed community | Veggie (VEG-03E) |
| OSD-414 | mixed community | Veggie (VEG-03F) |
| OSD-766 | Solanum lycopersicum | Veggie (VEG-05) |
| OSD-772 | Capsicum annuum | Advanced Plant Habitat (APH) |
| OSD-773 | mixed community | Veggie / XROOTS |

## Files
| File | Figure |
|---|---|
| Fig1_sampling_design | Sampling design (samples per study x tissue) |
| Fig2_diversity | (a) alpha diversity, (b) PCoA ordination |
| Fig3_composition | (a) phylum composition, (b) genus x tissue heatmap |
| Fig4_study_graph | Study-metadata graph (see build_graph.py) |
| Fig5_guild_scores | Pathogen/beneficial guild scores (see classify_guild.py) |

Each figure is provided as 300-dpi PNG and vector SVG. Values at genus level
derive from the illustrative model (see manuscript Methods); study/sample
metadata are verbatim from OSDR.
