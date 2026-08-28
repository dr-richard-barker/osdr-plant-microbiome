# Guild inference method card

**Question:** which crop-system microbes are *beneficial*, which are *plant
pathogens* (a crop-yield risk), and which are *human/clinical pathogens* (a
food-safety / crew-health risk)? These two pathogen concepts are kept SEPARATE
throughout — they co-occur in the same hardware but threaten different hosts.

**Guild priors (weak labels; ambiguous genera deliberately unlabelled):**
- beneficial: Bacillus, Paenibacillus, Rhizobium, Streptomyces, Methylobacterium, Sphingomonas, Variovorax
- plant pathogen: Ralstonia, Curtobacterium†
- human pathogen: Staphylococcus, Cutibacterium, Acinetobacter, Stenotrophomonas, Enterobacter
- unlabelled: Pseudomonas, Pantoea, Burkholderia, Massilia, Flavobacterium, Chryseobacterium

†genus-level prior — only some *Curtobacterium* pathovars are phytopathogenic;
this illustrates why strain/ASV-level resolution is a recommended upgrade.

**Method:** four evidence streams — (1) the priors above; (2) guild-specific
ecological traits: `human_assoc` (built-environment swab signal → human
pathogen), `plant_assoc` + `root_pref` (living plant / vascular tissue → plant
pathogen), plus niche breadth, spaceflight log-fold change and prevalence;
(3) Spearman co-occurrence guilt-by-association computed separately toward each
guild; (4) **multiclass** `LabelSpreading` returning P(beneficial),
P(plant_pathogen), P(human_pathogen), with a balanced RandomForest for feature
importance. **Two separate risk scores** are reported: `plant_pathogen_risk`
(crop risk) and `human_pathogen_risk` (food-safety risk).

**Feature importance (multiclass RandomForest on labelled genera):**
| feature | importance |
|---|---|
| plant_assoc | 0.216 |
| human_assoc | 0.153 |
| flight_lfc | 0.144 |
| niche_breadth | 0.128 |
| mean_ra | 0.090 |
| cv_ra | 0.085 |
| root_pref | 0.063 |
| assoc_beneficial | 0.044 |
| assoc_human_pathogen | 0.038 |
| prevalence | 0.026 |
| assoc_plant_pathogen | 0.014 |

**This-snapshot calls (illustrative scores):**
- Likely beneficial: Bacillus, Massilia, Methylobacterium, Paenibacillus, Sphingomonas, Streptomyces, Chryseobacterium, Flavobacterium, Variovorax, Burkholderia, Rhizobium, Pantoea
- Likely PLANT pathogen (crop risk): Curtobacterium, Ralstonia
- Likely HUMAN pathogen (food-safety risk): Acinetobacter, Cutibacterium, Staphylococcus, Stenotrophomonas, Enterobacter, Pseudomonas
- Uncertain: none

**Production upgrades:** (a) resolve to ASV/strain level against curated
references — phytopathogen catalogues (e.g. PHI-base, plant-pathogen host
databases) for the plant axis and clinical/virulence databases (e.g. VFDB,
BacDive) for the human axis; (b) compositional co-occurrence (SparCC/SPIEC-EASI);
(c) genome-inferred traits (PICRUSt2, antiSMASH, virulence-factor screens);
(d) require cross-study reproducibility before any operational flag; (e) treat
the two risks with different response protocols (crop quarantine vs food-safety
handling). Scores here are illustrative until primary feature tables are ingested.
