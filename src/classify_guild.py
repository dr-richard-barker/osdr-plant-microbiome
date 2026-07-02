"""
classify_guild.py — inferring microbial ECOLOGICAL GUILDS in the crop system.

We distinguish FOUR guilds, and in particular keep the two very different
notions of "pathogen" separate — they are both important, they co-occur in the
same hardware, but they threaten different hosts and demand different responses:

  * BENEFICIAL          — plant-growth-promoting / protective (PGPR, N-fixers,
                          methylotrophs): improve crop yield & resilience.
  * PLANT PATHOGEN      — phytopathogens (e.g. Ralstonia wilt): threaten the
                          CROP. Ecological signal = association with living
                          plant tissue, especially root/vascular niches.
  * HUMAN PATHOGEN      — clinical/opportunistic taxa (e.g. Staphylococcus,
                          Cutibacterium): a FOOD-SAFETY / CREW-HEALTH concern.
                          Ecological signal = association with human-contacted
                          hardware surfaces (swabs), i.e. the built environment.
  * UNCERTAIN           — evidence does not favour one guild.

A single "pathogen" axis would conflate a crop-yield risk with a crew-health
risk; separating them is the scientifically and operationally correct framing.

METHOD — four evidence streams fused by MULTICLASS semi-supervised learning:
  1. Weak supervision from curated genus-level priors for each guild
     (ambiguous genera left UNLABELLED on purpose).
  2. Guild-specific ecological trait features:
       - human_assoc  (swab / built-environment)     -> human-pathogen signal
       - plant_assoc  (living plant tissue)           -> plant-pathogen signal
       - root_pref    (root/vascular vs phyllosphere) -> plant-pathogen signal
       - niche_breadth, flight_lfc, prevalence, abundance moments
  3. Guilt-by-association on a Spearman co-occurrence network, computed
     separately toward each labelled guild.
  4. Multiclass `LabelSpreading` -> P(beneficial)/P(plant_path)/P(human_path);
     a RandomForest gives interpretable feature importance.

Two risk scores are reported, NOT one: crop-risk (plant_pathogen_risk) and
food-safety risk (human_pathogen_risk). Scores here use illustrative
abundances; the method runs unchanged on primary OSDR feature tables.
"""
from __future__ import annotations
import sqlite3

import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestClassifier
from sklearn.semi_supervised import LabelSpreading
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config

# ---------------------------------------------------------------------
# Curated genus-level guild PRIORS (weak labels). Genera that are genuinely
# ambiguous (Pseudomonas, Pantoea, Burkholderia, Massilia, Flavobacterium,
# Chryseobacterium) are deliberately LEFT OUT so the ecological evidence, not
# a hard prior, decides their guild.
#
# Guild codes: 0 beneficial | 1 plant_pathogen | 2 human_pathogen | -1 unlabelled
# ---------------------------------------------------------------------
GUILD_NAMES = {0: "beneficial", 1: "plant_pathogen", 2: "human_pathogen"}

GUILD_PRIOR = {
    # --- beneficial / plant-growth-promoting -------------------------
    "Bacillus": 0, "Paenibacillus": 0, "Rhizobium": 0, "Streptomyces": 0,
    "Methylobacterium": 0, "Sphingomonas": 0, "Variovorax": 0,
    # --- plant pathogens (phytopathogens) ----------------------------
    "Ralstonia": 1,        # R. solanacearum — bacterial wilt of Solanaceae
    "Curtobacterium": 1,   # C. flaccumfaciens pv. — bean/host wilt (genus-level prior; see note)
    # --- human / clinical opportunists -------------------------------
    "Staphylococcus": 2, "Cutibacterium": 2, "Acinetobacter": 2,
    "Stenotrophomonas": 2, "Enterobacter": 2,
    # unlabelled (ambiguous): Pseudomonas, Pantoea, Burkholderia, Massilia,
    # Flavobacterium, Chryseobacterium
}

GUILD_COLORS = {"beneficial": "#117733", "plant_pathogen": "#E69F00",
                "human_pathogen": "#CC6677", "uncertain": "#999999"}
PLANT_TISSUES = ["leaf", "root", "fruit"]


def _con():
    return sqlite3.connect(config.DB_PATH)


def build_features() -> tuple[pd.DataFrame, pd.DataFrame]:
    con = _con()
    df = pd.read_sql_query("""
        SELECT t.genus, s.tissue_type, s.spaceflight, ab.relative_abundance AS ra,
               ab.sample_id
        FROM abundance ab
        JOIN taxa t     ON t.taxon_id = ab.taxon_id
        JOIN samples s  ON s.sample_id = ab.sample_id
    """, con)
    con.close()
    genera = sorted(df.genus.unique())
    wide = df.pivot_table(index="sample_id", columns="genus", values="ra", fill_value=0.0)

    def tmean(g, tis):
        sub = df[(df.genus == g) & (df.tissue_type == tis)]
        return sub.ra.mean() if len(sub) else 0.0

    rows = []
    for g in genera:
        gd = df[df.genus == g]
        swab = tmean(g, "swab")
        plant = np.mean([tmean(g, t) for t in PLANT_TISSUES])
        root, leaf, water = tmean(g, "root"), tmean(g, "leaf"), tmean(g, "water")
        tvec = gd.groupby("tissue_type").ra.mean()
        tvec = tvec / tvec.sum() if tvec.sum() else tvec
        breadth = float(-(tvec * np.log(tvec + 1e-12)).sum())
        fl = gd[gd.spaceflight == 1].ra.mean(); gr = gd[gd.spaceflight == 0].ra.mean()
        rows.append({
            "genus": g,
            "human_assoc": swab / (plant + swab + 1e-9),          # built-environment -> human
            "plant_assoc": plant / (plant + swab + water + 1e-9), # living plant tissue -> plant path
            "root_pref": root / (root + leaf + 1e-9),             # vascular/rhizosphere -> plant path
            "niche_breadth": breadth,
            "flight_lfc": np.log2((fl + 1e-6) / (gr + 1e-6)),
            "prevalence": float((wide[g] > 0).mean()),
            "mean_ra": float(wide[g].mean()),
            "cv_ra": float(wide[g].std() / (wide[g].mean() + 1e-9)),
        })
    return pd.DataFrame(rows).set_index("genus"), wide


def cooccurrence(wide: pd.DataFrame) -> pd.DataFrame:
    genera = list(wide.columns)
    rho = np.atleast_2d(spearmanr(wide.values)[0])
    G = nx.Graph(); G.add_nodes_from(genera)
    for i in range(len(genera)):
        for j in range(i + 1, len(genera)):
            if abs(rho[i, j]) >= 0.3:
                G.add_edge(genera[i], genera[j], weight=float(rho[i, j]))
    sets = {c: {g for g, v in GUILD_PRIOR.items() if v == c} for c in (0, 1, 2)}
    out = []
    for g in genera:
        d = {"genus": g}
        for c, name in GUILD_NAMES.items():
            d[f"assoc_{name}"] = (sum(w["weight"] for n, w in G[g].items() if n in sets[c])
                                  if g in G else 0.0)
        out.append(d)
    return pd.DataFrame(out).set_index("genus")


def infer_guild():
    feat, wide = build_features()
    X = feat.join(cooccurrence(wide))
    y = np.array([GUILD_PRIOR.get(g, -1) for g in X.index])
    Xs = StandardScaler().fit_transform(X.values)

    ls = LabelSpreading(kernel="rbf", gamma=1.1, alpha=0.2)
    ls.fit(Xs, y)
    classes = list(ls.classes_)
    dist = ls.label_distributions_
    P = {GUILD_NAMES[c]: dist[:, classes.index(c)] for c in (0, 1, 2)}

    # interpretable multiclass RF on the labelled subset
    lab = y != -1
    rf = RandomForestClassifier(n_estimators=500, random_state=config.RANDOM_SEED,
                                class_weight="balanced")
    rf.fit(Xs[lab], y[lab])
    importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)

    res = X.copy()
    res["prior"] = [GUILD_NAMES.get(v, "unlabelled") for v in y]
    res["P_beneficial"] = P["beneficial"].round(3)
    res["P_plant_pathogen"] = P["plant_pathogen"].round(3)
    res["P_human_pathogen"] = P["human_pathogen"].round(3)
    # two SEPARATE risk scores, each up-weighted by its own ecological signal
    res["plant_pathogen_risk"] = (P["plant_pathogen"] * (0.5 + 0.5 * res["plant_assoc"])).round(3)
    res["human_pathogen_risk"] = (P["human_pathogen"] * (0.5 + 0.5 * res["human_assoc"])).round(3)

    probs = res[["P_beneficial", "P_plant_pathogen", "P_human_pathogen"]].values
    argmax = probs.argmax(axis=1)
    top = probs.max(axis=1)
    names = np.array(["beneficial", "plant_pathogen", "human_pathogen"])
    call = np.where(top >= 0.45, names[argmax], "uncertain")
    res["guild_call"] = call
    res["confidence"] = top.round(3)
    res = res.sort_values(["guild_call", "confidence"], ascending=[True, False])

    res.to_csv(config.PROCESSED_DIR / "guild_scores.csv")
    _method_card(importances, res)
    _fig5(res)
    return res, importances


def _method_card(importances, res):
    imp = "\n".join(f"| {k} | {v:.3f} |" for k, v in importances.items())
    def lst(call):
        return ", ".join(res[res.guild_call == call].index.tolist()) or "none"
    (config.PROCESSED_DIR / "GUILD_METHOD.md").write_text(f"""# Guild inference method card

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
{imp}

**This-snapshot calls (illustrative scores):**
- Likely beneficial: {lst('beneficial')}
- Likely PLANT pathogen (crop risk): {lst('plant_pathogen')}
- Likely HUMAN pathogen (food-safety risk): {lst('human_pathogen')}
- Uncertain: {lst('uncertain')}

**Production upgrades:** (a) resolve to ASV/strain level against curated
references — phytopathogen catalogues (e.g. PHI-base, plant-pathogen host
databases) for the plant axis and clinical/virulence databases (e.g. VFDB,
BacDive) for the human axis; (b) compositional co-occurrence (SparCC/SPIEC-EASI);
(c) genome-inferred traits (PICRUSt2, antiSMASH, virulence-factor screens);
(d) require cross-study reproducibility before any operational flag; (e) treat
the two risks with different response protocols (crop quarantine vs food-safety
handling). Scores here are illustrative until primary feature tables are ingested.
""", encoding="utf-8")
    print("  [guild] method card + guild_scores.csv written")


def _fig5(res):
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 4.0),
                             gridspec_kw={"width_ratios": [1.15, 1.15]})
    # (a) the two pathogen concepts as ORTHOGONAL axes.
    # Deterministic jitter separates the many low-risk beneficials near origin.
    ax = axes[0]
    rng = np.random.default_rng(config.RANDOM_SEED)
    jit = {g: rng.normal(0, 0.012, 2) for g in res.index}
    for call, col in GUILD_COLORS.items():
        s = res[res.guild_call == call]
        if s.empty:
            continue
        xs = s.human_pathogen_risk + [jit[g][0] for g in s.index]
        ys = s.plant_pathogen_risk + [jit[g][1] for g in s.index]
        ax.scatter(xs, ys, s=30 + 220 * s.prevalence, c=col, alpha=0.8,
                   edgecolor="#333", linewidth=0.5)
    for g, r in res.iterrows():
        ax.annotate(g, (r.human_pathogen_risk + jit[g][0], r.plant_pathogen_risk + jit[g][1]),
                    fontsize=5.2, xytext=(3, 2), textcoords="offset points")
    ax.set_xlabel("Human-pathogen risk  (food-safety / crew health)")
    ax.set_ylabel("Plant-pathogen risk  (crop yield)")
    ax.set_title("(a) Two distinct pathogen concepts")
    ax.set_xlim(-0.08, 1.02); ax.set_ylim(-0.08, 0.92)
    ax.axhline(0.25, color="#ccc", lw=0.6, ls=":"); ax.axvline(0.25, color="#ccc", lw=0.6, ls=":")
    # compact custom legend (small markers), placed in the empty mid-field
    handles = [plt.Line2D([], [], marker="o", ls="", ms=7, mfc=GUILD_COLORS[k], mec="#333",
               label=k.replace("_", " ")) for k in
               ["beneficial", "plant_pathogen", "human_pathogen", "uncertain"]]
    ax.legend(handles=handles, fontsize=6.6, frameon=True, framealpha=0.9,
              loc="center", title="guild call", title_fontsize=6.8)
    ax.text(0.02, 0.86, "phytopathogens\n(crop risk)", transform=ax.transAxes,
            fontsize=6, color="#8a6d00", style="italic")
    ax.text(0.62, 0.02, "clinical opportunists\n(food-safety risk)", transform=ax.transAxes,
            fontsize=6, color="#8a2f3d", style="italic")

    # (b) stacked guild-probability bars per genus
    ax = axes[1]
    order = res.sort_values(["P_human_pathogen", "P_plant_pathogen"]).index
    r = res.loc[order]
    ax.barh(r.index, r.P_beneficial, color=GUILD_COLORS["beneficial"], label="beneficial")
    ax.barh(r.index, r.P_plant_pathogen, left=r.P_beneficial,
            color=GUILD_COLORS["plant_pathogen"], label="plant pathogen")
    ax.barh(r.index, r.P_human_pathogen, left=r.P_beneficial + r.P_plant_pathogen,
            color=GUILD_COLORS["human_pathogen"], label="human pathogen")
    ax.set_xlabel("Guild probability"); ax.set_title("(b) Per-genus guild mixture")
    ax.tick_params(axis="y", labelsize=6); ax.set_xlim(0, 1)
    ax.legend(fontsize=6.3, frameon=False, loc="lower right")
    for ext in ("png", "svg"):
        fig.savefig(config.FIGURES_DIR / f"Fig5_guild_scores.{ext}", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("  [fig] Fig5_guild_scores.png / .svg")


def main():
    res, _ = infer_guild()
    print("\n  Guild calls:")
    print(res[["prior", "P_beneficial", "P_plant_pathogen", "P_human_pathogen",
               "guild_call"]].to_string())


if __name__ == "__main__":
    main()
