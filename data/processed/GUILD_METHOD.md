# Guild inference method card

**Question:** which taxa are likely *pathogenic/opportunistic* and which
*beneficial* for crop health in spaceflight growth systems?

**Approach — four independent evidence streams fused by semi-supervised learning:**
1. Weak supervision from a curated genus-level prior KB (beneficial / pathogen /
   deliberately unlabelled-ambiguous).
2. Ecological trait features (human-swab association, rhizosphere preference,
   niche breadth, spaceflight log-fold change, prevalence, abundance moments).
3. Guilt-by-association on a Spearman co-occurrence network (does a taxon
   consort with known beneficials or known pathogens?).
4. `LabelSpreading` (RBF) propagates sparse labels to all genera → calibrated
   P(beneficial)/P(pathogen); a balanced RandomForest gives feature importance.

**Pathogen risk** = P(pathogen) up-weighted by human-swab association, so
built-environment opportunists that colonise crops are flagged.

**Feature importance (RandomForest on labelled genera):**
| feature | importance |
|---|---|
| swab_assoc | 0.234 |
| mean_ra | 0.146 |
| niche_breadth | 0.142 |
| flight_lfc | 0.141 |
| assoc_beneficial | 0.089 |
| cooccur_centrality | 0.078 |
| cv_ra | 0.076 |
| rhizo_pref | 0.057 |
| assoc_pathogen | 0.028 |
| prevalence | 0.010 |

**This-snapshot calls (illustrative scores):**
- Likely pathogen/opportunist: Staphylococcus, Cutibacterium, Acinetobacter, Stenotrophomonas, Enterobacter, Pseudomonas, Pantoea, Ralstonia
- Likely beneficial: Rhizobium, Burkholderia, Curtobacterium, Bacillus, Chryseobacterium, Methylobacterium, Massilia, Flavobacterium, Paenibacillus, Sphingomonas, Streptomyces, Variovorax

**Recommended production upgrades:** (a) resolve to ASV/strain level with a
reference DB (e.g. BacDive/PLaBAse virulence & PGP trait annotations); (b)
replace Spearman with SparCC/SPIEC-EASI for compositional robustness; (c) add
genome-inferred traits (antiSMASH BGCs, virulence factor DBs) via PICRUSt2;
(d) calibrate against curated phytopathogen lists; (e) report per-call
uncertainty and require multi-study reproducibility before any operational
flag. Scores here are illustrative until primary OSDR feature tables are ingested.
