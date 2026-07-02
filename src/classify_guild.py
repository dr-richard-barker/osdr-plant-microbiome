"""
classify_guild.py — inferring which taxa are likely PATHOGENIC vs BENEFICIAL.

This module implements (and documents) a *clever, defensible* system for the
question "which microbes may be harmful and which helpful?" — a question that
is hard because (i) guild is often strain- not genus-level, (ii) ground-truth
labels are sparse, and (iii) the same genus can be both. The design combines
four independent lines of evidence so no single weak signal dominates:

  1. WEAK SUPERVISION from a curated prior knowledge base (KB) of genus-level
     guild priors drawn from the plant-pathology / PGPR / clinical literature.
     Ambiguous genera are left UNLABELLED on purpose.
  2. ECOLOGICAL TRAIT FEATURES engineered from the harmonised OSDR data:
       - human-swab association index  (built-environment / opportunist signal)
       - rhizosphere vs phyllosphere preference
       - niche breadth (tissue Shannon)
       - spaceflight response (flight/ground log-fold change)
       - prevalence and abundance moments
  3. GUILT-BY-ASSOCIATION on a co-occurrence network (Spearman across samples):
     does a taxon keep company with known beneficials or known pathogens?
  4. SEMI-SUPERVISED LEARNING (label spreading over the trait+network feature
     space) that propagates the sparse KB labels to the unlabelled genera and
     returns calibrated P(beneficial) / P(pathogen), with a RandomForest for
     interpretable feature importance.

Outputs a ranked guild table, a method card, and Fig5. NOTE: because the
per-sample abundances in this demo are from the illustrative model, the SCORES
are illustrative; the METHOD is the deliverable and runs unchanged on real
OSDR feature tables.
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
# Curated genus-level guild PRIORS (weak labels). +1 beneficial, -1 pathogen,
# 0/absent = unlabelled (let the model decide). Sources: plant-pathology &
# PGPR reviews and ISS built-environment surveys. Deliberately conservative;
# genuinely ambiguous genera (e.g. Pseudomonas, Pantoea, Burkholderia) are
# left UNLABELLED so the ecological evidence drives their call.
# ---------------------------------------------------------------------
GUILD_PRIOR = {
    # beneficial / plant-growth-promoting
    "Bacillus": +1, "Paenibacillus": +1, "Rhizobium": +1, "Streptomyces": +1,
    "Methylobacterium": +1, "Sphingomonas": +1, "Variovorax": +1,
    # pathogen / opportunist (phytopathogen or human-associated)
    "Ralstonia": -1, "Staphylococcus": -1, "Cutibacterium": -1,
    "Acinetobacter": -1, "Stenotrophomonas": -1,
    # intentionally UNLABELLED (ambiguous): Pseudomonas, Pantoea, Enterobacter,
    # Burkholderia, Curtobacterium, Massilia, Flavobacterium, Chryseobacterium
}


def _con():
    return sqlite3.connect(config.DB_PATH)


def build_features() -> pd.DataFrame:
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
    # sample x genus wide matrix for co-occurrence
    wide = df.pivot_table(index="sample_id", columns="genus",
                          values="ra", fill_value=0.0)

    def tissue_mean(g, tis):
        sub = df[(df.genus == g) & (df.tissue_type == tis)]
        return sub.ra.mean() if len(sub) else 0.0

    plant_tissues = ["leaf", "root", "fruit"]
    rows = []
    for g in genera:
        gd = df[df.genus == g]
        swab = tissue_mean(g, "swab")
        plant = np.mean([tissue_mean(g, t) for t in plant_tissues])
        root = tissue_mean(g, "root")
        leaf = tissue_mean(g, "leaf")
        # tissue-distribution Shannon (niche breadth)
        tvec = gd.groupby("tissue_type").ra.mean()
        tvec = tvec / tvec.sum() if tvec.sum() else tvec
        breadth = float(-(tvec * np.log(tvec + 1e-12)).sum())
        fl = gd[gd.spaceflight == 1].ra.mean()
        gr = gd[gd.spaceflight == 0].ra.mean()
        rows.append({
            "genus": g,
            "swab_assoc": swab / (plant + swab + 1e-9),      # opportunist signal
            "rhizo_pref": root / (root + leaf + 1e-9),        # root vs leaf
            "niche_breadth": breadth,
            "flight_lfc": np.log2((fl + 1e-6) / (gr + 1e-6)),
            "prevalence": float((wide[g] > 0).mean()),
            "mean_ra": float(wide[g].mean()),
            "cv_ra": float(wide[g].std() / (wide[g].mean() + 1e-9)),
        })
    feat = pd.DataFrame(rows).set_index("genus")
    return feat, wide


def cooccurrence_scores(wide: pd.DataFrame) -> pd.DataFrame:
    """Spearman co-occurrence network + guilt-by-association with the KB."""
    genera = list(wide.columns)
    rho, _ = spearmanr(wide.values)
    rho = np.atleast_2d(rho)
    G = nx.Graph()
    G.add_nodes_from(genera)
    for i in range(len(genera)):
        for j in range(i + 1, len(genera)):
            r = rho[i, j]
            if abs(r) >= 0.3:                 # keep meaningful associations
                G.add_edge(genera[i], genera[j], weight=float(r))
    ben = {g for g, v in GUILD_PRIOR.items() if v > 0}
    pat = {g for g, v in GUILD_PRIOR.items() if v < 0}
    out = []
    cent = nx.degree_centrality(G)
    for g in genera:
        pos = sum(d["weight"] for n, d in G[g].items() if n in ben) if g in G else 0
        neg = sum(d["weight"] for n, d in G[g].items() if n in pat) if g in G else 0
        out.append({"genus": g, "assoc_beneficial": pos, "assoc_pathogen": neg,
                    "cooccur_centrality": cent.get(g, 0.0)})
    return pd.DataFrame(out).set_index("genus"), G


def infer_guild() -> pd.DataFrame:
    feat, wide = build_features()
    coassoc, conet = cooccurrence_scores(wide)
    X = feat.join(coassoc)
    y = np.array([GUILD_PRIOR.get(g, 0) for g in X.index])   # +1/-1 labelled, 0 unlabelled
    # LabelSpreading needs -1 for unlabelled; map beneficial=1, pathogen=0
    y_ls = np.full(len(y), -1)
    y_ls[y > 0] = 1
    y_ls[y < 0] = 0
    Xs = StandardScaler().fit_transform(X.values)

    ls = LabelSpreading(kernel="rbf", gamma=1.2, alpha=0.2)
    ls.fit(Xs, y_ls)
    p_ben = ls.label_distributions_[:, list(ls.classes_).index(1)]

    # interpretable model on the labelled subset (feature importance)
    lab = y != 0
    rf = RandomForestClassifier(n_estimators=400, random_state=config.RANDOM_SEED,
                                class_weight="balanced")
    rf.fit(Xs[lab], (y[lab] > 0).astype(int))
    importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)

    res = X.copy()
    res["prior"] = [{1: "beneficial", -1: "pathogen", 0: "unlabelled"}[v] for v in y]
    res["P_beneficial"] = p_ben.round(3)
    res["P_pathogen"] = (1 - p_ben).round(3)
    # pathogen RISK score = pathogen prob boosted by human-swab association
    res["pathogen_risk"] = ((1 - p_ben) * (0.5 + 0.5 * res["swab_assoc"])).round(3)
    res["confidence"] = (np.abs(p_ben - 0.5) * 2).round(3)   # 0 = uncertain, 1 = certain
    def call(r):
        if r.P_beneficial >= 0.6:  return "likely beneficial"
        if r.P_beneficial <= 0.4:  return "likely pathogen/opportunist"
        return "uncertain"
    res["guild_call"] = res.apply(call, axis=1)
    res = res.sort_values("pathogen_risk", ascending=False)

    res.to_csv(config.PROCESSED_DIR / "guild_scores.csv")
    _method_card(importances, res)
    _fig5(res)
    return res, importances


def _method_card(importances, res):
    imp = "\n".join(f"| {k} | {v:.3f} |" for k, v in importances.items())
    top_p = res[res.guild_call.str.contains("pathogen")].index.tolist()
    top_b = res[res.guild_call.str.contains("beneficial")].index.tolist()
    (config.PROCESSED_DIR / "GUILD_METHOD.md").write_text(f"""# Guild inference method card

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
{imp}

**This-snapshot calls (illustrative scores):**
- Likely pathogen/opportunist: {', '.join(top_p) or 'none'}
- Likely beneficial: {', '.join(top_b) or 'none'}

**Recommended production upgrades:** (a) resolve to ASV/strain level with a
reference DB (e.g. BacDive/PLaBAse virulence & PGP trait annotations); (b)
replace Spearman with SparCC/SPIEC-EASI for compositional robustness; (c) add
genome-inferred traits (antiSMASH BGCs, virulence factor DBs) via PICRUSt2;
(d) calibrate against curated phytopathogen lists; (e) report per-call
uncertainty and require multi-study reproducibility before any operational
flag. Scores here are illustrative until primary OSDR feature tables are ingested.
""", encoding="utf-8")
    print(f"  [guild] method card + guild_scores.csv written")


def _fig5(res):
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.8),
                             gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    cmap = {"likely beneficial": "#117733", "likely pathogen/opportunist": "#CC6677",
            "uncertain": "#999999"}
    for call, col in cmap.items():
        s = res[res.guild_call == call]
        ax.scatter(s.P_beneficial, s.pathogen_risk, s=40 + 600 * s.prevalence,
                   c=col, alpha=0.8, edgecolor="#333", linewidth=0.5, label=call)
    for g, r in res.iterrows():
        ax.annotate(g, (r.P_beneficial, r.pathogen_risk), fontsize=5.5,
                    xytext=(2, 2), textcoords="offset points")
    ax.set_xlabel("P(beneficial)"); ax.set_ylabel("Pathogen risk score")
    ax.set_title("(a) Guild inference"); ax.legend(fontsize=6.5, frameon=False, loc="upper right")

    ax = axes[1]
    top = res.sort_values("swab_assoc", ascending=True).tail(10)
    cols = [cmap[c] for c in top.guild_call]
    ax.barh(top.index, top.swab_assoc, color=cols, edgecolor="#333", linewidth=0.4)
    ax.set_xlabel("Human-swab association index")
    ax.set_title("(b) Built-environment signal")
    ax.tick_params(axis="y", labelsize=6.5)
    for ext in ("png", "svg"):
        fig.savefig(config.FIGURES_DIR / f"Fig5_guild_scores.{ext}", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("  [fig] Fig5_guild_scores.png / .svg")


def main():
    res, importances = infer_guild()
    print("\n  Guild calls (top pathogen risk):")
    print(res[["prior", "P_beneficial", "pathogen_risk", "guild_call"]].head(8).to_string())


if __name__ == "__main__":
    main()
