"""
make_figures.py — export publication-quality static figures (PNG + SVG) into
a DATE-STAMPED snapshot folder (figures/<SNAPSHOT_DATE>/).

Because the OSDR plant-microbiome corpus grows over time, every figure is an
explicitly dated snapshot; the accompanying MANIFEST.md records the corpus
state and states that the result is transient by design — the live FAIR
report always re-derives the current picture.
"""
from __future__ import annotations
import sqlite3

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm

from . import config

plt.rcParams.update({
    "figure.dpi": 300, "savefig.dpi": 300, "font.size": 9,
    "font.family": "sans-serif", "axes.spines.top": False,
    "axes.spines.right": False, "axes.titlesize": 10, "axes.titleweight": "bold",
    "figure.autolayout": True,
})

TISSUE_ORDER = ["leaf", "root", "fruit", "wick", "substrate", "water", "swab"]
SAFE = ["#88CCEE", "#CC6677", "#DDCC77", "#117733", "#332288",
        "#AA4499", "#44AA99", "#999933", "#882255", "#661100"]


def _con():
    return sqlite3.connect(config.DB_PATH)


def _save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(config.FIGURES_DIR / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  [fig] {name}.png / .svg")


# ---------------------------------------------------------------- Fig 1
def fig1_sampling(con):
    df = pd.read_sql_query(
        "SELECT osd_accession, tissue_type, COUNT(*) n FROM samples GROUP BY 1,2", con)
    piv = df.pivot_table(index="osd_accession", columns="tissue_type",
                         values="n", fill_value=0)
    piv = piv[[t for t in TISSUE_ORDER if t in piv.columns]]
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    bottom = np.zeros(len(piv))
    for i, t in enumerate(piv.columns):
        ax.bar(piv.index, piv[t], bottom=bottom, label=t, color=SAFE[i % len(SAFE)])
        bottom += piv[t].values
    ax.set_ylabel("Number of samples"); ax.set_xlabel("OSDR study")
    ax.set_title("Sampling design of the integrated corpus")
    ax.legend(title="Tissue / niche", bbox_to_anchor=(1.01, 1), loc="upper left",
              frameon=False, fontsize=8)
    ax.tick_params(axis="x", rotation=30)
    _save(fig, "Fig1_sampling_design")


# ---------------------------------------------------------------- Fig 2
def fig2_diversity(con):
    a = pd.read_sql_query("SELECT * FROM v_sample_alpha", con)
    a["env"] = np.where(a.spaceflight == 1, "Spaceflight", "Ground")
    pc = pd.read_csv(config.PROCESSED_DIR / "pcoa_coords.csv")
    pc["env"] = np.where(pc.spaceflight == 1, "Spaceflight", "Ground")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5))
    # (a) alpha diversity boxplots by tissue x env
    ax = axes[0]
    tissues = [t for t in TISSUE_ORDER if t in a.tissue_type.unique()]
    for j, env in enumerate(["Ground", "Spaceflight"]):
        data = [a[(a.tissue_type == t) & (a.env == env)].shannon.values for t in tissues]
        pos = np.arange(len(tissues)) + (j - 0.5) * 0.34
        bp = ax.boxplot(data, positions=pos, widths=0.3, patch_artist=True,
                        showfliers=False)
        col = "#0b3d64" if env == "Ground" else "#CC6677"
        for box in bp["boxes"]:
            box.set(facecolor=col, alpha=0.65, edgecolor=col)
        for med in bp["medians"]:
            med.set(color="black", linewidth=1)
    ax.set_xticks(np.arange(len(tissues))); ax.set_xticklabels(tissues, rotation=30)
    ax.set_ylabel("Shannon H'"); ax.set_title("(a) Alpha diversity")
    ax.plot([], [], color="#0b3d64", lw=6, alpha=0.65, label="Ground")
    ax.plot([], [], color="#CC6677", lw=6, alpha=0.65, label="Spaceflight")
    ax.legend(frameon=False, fontsize=7.5, loc="lower left")

    # (b) PCoA of the largest study, colour by tissue, marker by env
    ax = axes[1]
    big = pc.osd_accession.value_counts().idxmax()
    sub = pc[pc.osd_accession == big]
    tmap = {t: SAFE[i % len(SAFE)] for i, t in enumerate(TISSUE_ORDER)}
    for env, mk in [("Ground", "o"), ("Spaceflight", "D")]:
        s2 = sub[sub.env == env]
        ax.scatter(s2.pc1, s2.pc2, c=[tmap[t] for t in s2.tissue_type],
                   marker=mk, s=26, edgecolor="#333", linewidth=0.4,
                   label=env)
    pc1p, pc2p = sub.pc1_pct.iloc[0], sub.pc2_pct.iloc[0]
    ax.set_xlabel(f"PC1 ({pc1p}%)"); ax.set_ylabel(f"PC2 ({pc2p}%)")
    ax.set_title(f"(b) PCoA — {big}")
    handles = [plt.Line2D([], [], marker="o", ls="", mfc=tmap[t], mec="#333",
               label=t) for t in TISSUE_ORDER if t in sub.tissue_type.unique()]
    handles += [plt.Line2D([], [], marker="D", ls="", mfc="grey", label="Flight"),
                plt.Line2D([], [], marker="o", ls="", mfc="grey", label="Ground")]
    ax.legend(handles=handles, fontsize=6.5, frameon=False,
              bbox_to_anchor=(1.01, 1), loc="upper left")
    _save(fig, "Fig2_diversity")


# ---------------------------------------------------------------- Fig 3
def fig3_composition(con):
    ph = pd.read_csv(config.PROCESSED_DIR / "phylum_composition.csv")
    gen = pd.read_csv(config.PROCESSED_DIR / "genus_composition.csv")

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.9),
                             gridspec_kw={"width_ratios": [1.05, 1.3]})
    # (a) phylum stacked, normalised per study x env
    ax = axes[0]
    ph["grp"] = ph.osd_accession.str.replace("OSD-", "") + "\n" + ph.environment.str[0]
    piv = ph.pivot_table(index="grp", columns="phylum", values="mean_rel", fill_value=0)
    piv = piv.div(piv.sum(axis=1), axis=0)
    bottom = np.zeros(len(piv))
    for i, p in enumerate(piv.columns):
        ax.bar(piv.index, piv[p], bottom=bottom, label=p, color=SAFE[i % len(SAFE)])
        bottom += piv[p].values
    ax.set_ylabel("Relative abundance"); ax.set_title("(a) Phylum composition")
    ax.tick_params(axis="x", labelsize=6, rotation=0)
    ax.legend(fontsize=6.5, frameon=False, ncol=1, bbox_to_anchor=(0, -0.18),
              loc="upper left")

    # (b) genus x tissue heatmap
    ax = axes[1]
    hm = (gen.groupby(["genus", "tissue_type"]).mean_rel.mean().reset_index()
             .pivot(index="genus", columns="tissue_type", values="mean_rel").fillna(0))
    hm = hm[[t for t in TISSUE_ORDER if t in hm.columns]]
    im = ax.imshow(hm.values, aspect="auto", cmap="YlGnBu")
    ax.set_xticks(range(len(hm.columns))); ax.set_xticklabels(hm.columns, rotation=40, fontsize=7)
    ax.set_yticks(range(len(hm.index))); ax.set_yticklabels(hm.index, fontsize=6)
    ax.set_title("(b) Genus x tissue niche")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Mean rel. abund.")
    _save(fig, "Fig3_composition")


def fig6_transience(con):
    """Cumulative-corpus timeline from REAL OSDR public release dates."""
    from datetime import datetime
    import matplotlib.dates as mdates
    rd = pd.read_csv(config.REGISTRY_CSV.parent / "release_dates.csv")
    rd["date"] = pd.to_datetime(rd["public_release_date"], format="%d-%b-%Y")
    rd = rd.sort_values("date").reset_index(drop=True)
    rd["cum"] = np.arange(1, len(rd) + 1)
    snap = datetime.strptime(config.SNAPSHOT_DATE, "%Y-%m-%d")

    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    # step function of cumulative real releases
    xs = [rd.date.iloc[0]] + list(rd.date) + [snap]
    ys = [0] + list(rd.cum) + [rd.cum.iloc[-1]]
    ax.step(xs, ys, where="post", color="#0b3d64", lw=2, zorder=2)
    ax.scatter(rd.date, rd.cum, color="#0b3d64", s=32, zorder=3)
    for r in rd.itertuples():
        ax.annotate(r.osd_accession, (r.date, r.cum), fontsize=6.2,
                    xytext=(4, -9), textcoords="offset points", color="#0b3d64")
    ax.scatter([snap], [rd.cum.iloc[-1]], s=300, marker="*", color="#CC6677",
               edgecolor="#661100", zorder=5,
               label=f"this snapshot: {rd.cum.iloc[-1]} studies")
    ax.annotate(config.SNAPSHOT_DATE, (snap, rd.cum.iloc[-1]),
                xytext=(6, -14), textcoords="offset points", fontsize=8, color="#661100")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.set_ylabel("Cumulative studies in OSDR")
    ax.set_ylim(0, rd.cum.iloc[-1] + 1.5)
    ax.set_title("A moving target: the corpus grows,\nso every result is a dated snapshot",
                 fontsize=10)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.text(0.5, -0.32, "Cumulative count from REAL OSDR public-release dates "
            "(data/registry/release_dates.csv). The live FAIR dashboard re-derives "
            "the corpus on each build.", transform=ax.transAxes, ha="center",
            fontsize=7, color="#666")
    _save(fig, "Fig6_corpus_growth")


def write_manifest(con):
    ov = pd.read_sql_query("SELECT COUNT(*) n FROM studies", con).n.iloc[0]
    ns = pd.read_sql_query("SELECT COUNT(*) n FROM samples", con).n.iloc[0]
    studies = pd.read_sql_query(
        "SELECT osd_accession, organism, platform_hardware FROM studies ORDER BY 1", con)
    rows = "\n".join(f"| {r.osd_accession} | {r.organism} | {r.platform_hardware} |"
                     for r in studies.itertuples())
    (config.FIGURES_DIR / "MANIFEST.md").write_text(f"""# Figure snapshot — {config.SNAPSHOT_DATE}

**Corpus state at this snapshot:** {ov} OSDR plant-microbiome studies, {ns} samples.

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
{rows}

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
""", encoding="utf-8")
    print(f"  [manifest] MANIFEST.md ({ov} studies, {ns} samples)")


def main():
    con = _con()
    print(f"Exporting figures -> {config.FIGURES_DIR}")
    fig1_sampling(con)
    fig2_diversity(con)
    fig3_composition(con)
    fig6_transience(con)
    write_manifest(con)
    con.close()


if __name__ == "__main__":
    main()
