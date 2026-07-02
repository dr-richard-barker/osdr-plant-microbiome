"""
build_dashboard.py — render a single self-contained interactive HTML report.

Consumes the SQLite DB + processed CSVs and emits dashboards/report.html:
an integrated, navigable report combining the study registry, sampling
design, alpha/beta diversity dashboards and taxonomic composition, with an
explicit data-provenance banner. Plotly is loaded from CDN; the figures are
fully interactive (hover, zoom, legend toggle, study selector).
"""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_html

from . import config, __version__

PALETTE = px.colors.qualitative.Safe
TEMPLATE = "plotly_white"


def _con():
    return sqlite3.connect(config.DB_PATH)


def _fig(fig, **kw) -> str:
    fig.update_layout(template=TEMPLATE, margin=dict(l=50, r=20, t=50, b=50),
                      font=dict(family="Inter, Segoe UI, sans-serif", size=13))
    return to_html(fig, include_plotlyjs=False, full_html=False,
                   config={"displaylogo": False, "responsive": True}, **kw)


# ---------------------------------------------------------------- panels
def panel_registry(con) -> str:
    df = pd.read_sql_query("""
        SELECT osd_accession AS 'OSD', organism AS 'Organism',
               platform_hardware AS 'Hardware', mission AS 'Mission',
               (SELECT COUNT(*) FROM samples s WHERE s.osd_accession=st.osd_accession) AS 'Samples',
               confidence AS 'Confidence'
        FROM studies st ORDER BY osd_accession""", con)
    fig = go.Figure(go.Table(
        header=dict(values=[f"<b>{c}</b>" for c in df.columns],
                    fill_color="#0b3d64", font=dict(color="white"), align="left"),
        cells=dict(values=[df[c] for c in df.columns], align="left",
                   fill_color=[["#f2f7fb", "#ffffff"] * len(df)])))
    fig.update_layout(height=60 + 30 * len(df), margin=dict(l=5, r=5, t=10, b=5))
    return _fig(fig)


def panel_sampling(con) -> str:
    df = pd.read_sql_query("""
        SELECT osd_accession, tissue_type, COUNT(*) n
        FROM samples GROUP BY osd_accession, tissue_type""", con)
    fig = px.bar(df, x="osd_accession", y="n", color="tissue_type",
                 color_discrete_sequence=PALETTE,
                 labels={"osd_accession": "Study", "n": "Samples", "tissue_type": "Tissue"},
                 title="Sampling design: specimens per study by tissue niche")
    fig.update_layout(barmode="stack", height=420)
    return _fig(fig)


def panel_alpha(con) -> str:
    df = pd.read_sql_query("SELECT * FROM v_sample_alpha", con)
    df["Environment"] = np.where(df.spaceflight == 1, "Spaceflight", "Ground")
    fig = px.box(df, x="tissue_type", y="shannon", color="Environment",
                 color_discrete_map={"Spaceflight": "#d1495b", "Ground": "#0b3d64"},
                 points="all", labels={"tissue_type": "Tissue", "shannon": "Shannon H'"},
                 title="Alpha diversity (Shannon) by tissue and environment")
    fig.update_traces(marker=dict(size=4, opacity=0.5))
    fig.update_layout(height=440, boxmode="group")
    return _fig(fig)


def panel_pcoa(con) -> str:
    df = pd.read_csv(config.PROCESSED_DIR / "pcoa_coords.csv")
    df["Environment"] = np.where(df.spaceflight == 1, "Spaceflight", "Ground")
    studies = sorted(df.osd_accession.unique())
    fig = go.Figure()
    tissues = sorted(df.tissue_type.unique())
    cmap = {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(tissues)}
    trace_study = []
    for osd in studies:
        sub = df[df.osd_accession == osd]
        for env, sym in [("Ground", "circle"), ("Spaceflight", "diamond")]:
            s2 = sub[sub.Environment == env]
            if s2.empty:
                continue
            fig.add_trace(go.Scatter(
                x=s2.pc1, y=s2.pc2, mode="markers", name=f"{env}",
                legendgroup=env, showlegend=(osd == studies[0]),
                marker=dict(size=9, symbol=sym,
                            color=[cmap[t] for t in s2.tissue_type],
                            line=dict(width=0.6, color="#333")),
                text=[f"{t} · {env}" for t in s2.tissue_type],
                hovertemplate="%{text}<br>PC1 %{x:.2f}<br>PC2 %{y:.2f}<extra></extra>",
                visible=(osd == studies[0])))
            trace_study.append(osd)
    buttons = []
    for osd in studies:
        vis = [ts == osd for ts in trace_study]
        pc = df[df.osd_accession == osd].iloc[0]
        buttons.append(dict(label=osd, method="update",
                            args=[{"visible": vis},
                                  {"title": f"PCoA (Bray-Curtis) — {osd} "
                                            f"[PC1 {pc.pc1_pct}%, PC2 {pc.pc2_pct}%]"}]))
    pc0 = df[df.osd_accession == studies[0]].iloc[0]
    fig.update_layout(
        height=520, title=f"PCoA (Bray-Curtis) — {studies[0]} "
                          f"[PC1 {pc0.pc1_pct}%, PC2 {pc0.pc2_pct}%]",
        xaxis_title="PC1", yaxis_title="PC2",
        updatemenus=[dict(buttons=buttons, x=1.0, xanchor="right", y=1.18, direction="down")],
        annotations=[dict(text="Colour = tissue · Circle = ground, Diamond = flight",
                          showarrow=False, x=0, y=1.12, xref="paper", yref="paper",
                          font=dict(size=11, color="#666"))])
    return _fig(fig)


def panel_phylum(con) -> str:
    df = pd.read_csv(config.PROCESSED_DIR / "phylum_composition.csv")
    df["grp"] = df.osd_accession + " · " + df.environment
    fig = px.bar(df.sort_values("osd_accession"), x="grp", y="mean_rel", color="phylum",
                 color_discrete_sequence=PALETTE,
                 labels={"grp": "Study · Environment", "mean_rel": "Mean relative abundance",
                         "phylum": "Phylum"},
                 title="Phylum-level composition: ground vs spaceflight")
    fig.update_layout(barmode="stack", height=460, xaxis_tickangle=-40)
    return _fig(fig)


def panel_genus_heatmap(con) -> str:
    df = pd.read_csv(config.PROCESSED_DIR / "genus_composition.csv")
    piv = (df.groupby(["genus", "tissue_type"])["mean_rel"].mean()
             .reset_index()
             .pivot(index="genus", columns="tissue_type", values="mean_rel")
             .fillna(0))
    fig = px.imshow(piv, color_continuous_scale="YlGnBu", aspect="auto",
                    labels=dict(color="Mean rel. abund."),
                    title="Genus × tissue niche partitioning (all studies)")
    fig.update_layout(height=560)
    return _fig(fig)


def panel_graph() -> str:
    """Load the pre-rendered interactive knowledge-graph network fragment."""
    frag = config.GRAPH_DIR / "network_fragment.html"
    if frag.exists():
        return frag.read_text(encoding="utf-8")
    return "<p><em>Graph not built — run <code>python -m src.build_graph</code>.</em></p>"


def panel_guild() -> str:
    df = pd.read_csv(config.PROCESSED_DIR / "guild_scores.csv")
    cmap = {"beneficial": "#117733", "plant_pathogen": "#E69F00",
            "human_pathogen": "#CC6677", "uncertain": "#999999"}
    df["guild"] = df["guild_call"].str.replace("_", " ")
    fig = px.scatter(
        df, x="human_pathogen_risk", y="plant_pathogen_risk",
        color="guild_call", size="prevalence", text="genus",
        color_discrete_map=cmap,
        hover_data={"prior": True, "P_beneficial": ":.2f",
                    "P_plant_pathogen": ":.2f", "P_human_pathogen": ":.2f",
                    "confidence": ":.2f", "genus": False, "prevalence": False,
                    "guild_call": False},
        labels={"human_pathogen_risk": "Human-pathogen risk (food-safety / crew health)",
                "plant_pathogen_risk": "Plant-pathogen risk (crop yield)",
                "guild_call": "Guild call"},
        title="Guild inference — plant pathogens vs human pathogens are distinct axes")
    fig.update_traces(textposition="top center", textfont_size=9,
                      marker=dict(line=dict(width=0.6, color="#333")))
    fig.add_annotation(x=0.02, y=0.9, text="phytopathogens<br>(crop risk)", showarrow=False,
                       font=dict(size=10, color="#8a6d00"), xanchor="left")
    fig.add_annotation(x=0.9, y=0.05, text="clinical opportunists<br>(food-safety risk)",
                       showarrow=False, font=dict(size=10, color="#8a2f3d"), xanchor="right")
    fig.update_layout(height=560)
    return _fig(fig)


def provenance_rows(con) -> str:
    log = pd.read_sql_query("SELECT step, detail, row_count FROM provenance_log", con)
    prov = pd.read_sql_query(
        "SELECT data_provenance, COUNT(*) n FROM abundance GROUP BY data_provenance", con)
    rows = "".join(f"<tr><td>{r.step}</td><td>{r.detail}</td><td>{r.row_count:,}</td></tr>"
                   for r in log.itertuples())
    prv = "".join(f"<li><code>{r.data_provenance}</code>: {r.n:,} abundance rows</li>"
                  for r in prov.itertuples())
    return rows, prv


HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OSDR Plant Microbiome — Integrated Report</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
:root{{--nav:#0b3d64;--accent:#d1495b;--bg:#f7f9fb;}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:Inter,Segoe UI,sans-serif;color:#1a2733;background:var(--bg)}}
header{{background:linear-gradient(120deg,#0b3d64,#12658f);color:#fff;padding:28px 40px}}
header h1{{margin:0 0 6px;font-size:26px}}
header p{{margin:2px 0;opacity:.9;font-size:14px}}
nav{{position:sticky;top:0;background:#fff;border-bottom:1px solid #dce4ea;padding:10px 40px;
     display:flex;gap:18px;flex-wrap:wrap;z-index:10}}
nav a{{color:var(--nav);text-decoration:none;font-size:14px;font-weight:600}}
nav a:hover{{color:var(--accent)}}
main{{max-width:1180px;margin:0 auto;padding:24px 40px 80px}}
section{{background:#fff;border:1px solid #e5ebf0;border-radius:10px;padding:22px 26px;margin:22px 0;
         box-shadow:0 1px 3px rgba(10,40,70,.05)}}
section h2{{margin-top:0;color:var(--nav);font-size:20px;border-bottom:2px solid #eef3f7;padding-bottom:8px}}
.banner{{background:#fff4e5;border:1px solid #ffd9a0;border-radius:8px;padding:14px 18px;font-size:13.5px}}
.banner b{{color:#a15c00}}
.kpi{{display:flex;gap:18px;flex-wrap:wrap;margin:6px 0}}
.kpi div{{background:var(--nav);color:#fff;border-radius:10px;padding:14px 20px;min-width:120px}}
.kpi span{{display:block;font-size:28px;font-weight:700}}
.kpi small{{opacity:.85}}
table.log{{border-collapse:collapse;width:100%;font-size:13px}}
table.log td,table.log th{{border:1px solid #e2e8ee;padding:6px 10px;text-align:left}}
table.log th{{background:#eef3f7}}
code{{background:#eef3f7;padding:1px 5px;border-radius:4px;font-size:12.5px}}
footer{{text-align:center;color:#7d8b98;font-size:12.5px;padding:30px}}
a.ext{{color:var(--accent)}}
</style></head><body>
<header>
  <h1>NASA OSDR Plant Microbiome — Integrated Interactive Report</h1>
  <p>A FAIR analysis tool for plant-associated microbiome datasets in the NASA Open Science Data Repository</p>
  <p>Build v{version} · generated {built} · {n_studies} studies · {n_samples} samples</p>
</header>
<nav>
  <a href="#about">Overview</a><a href="#registry">Study Registry</a>
  <a href="#design">Sampling Design</a><a href="#alpha">Alpha Diversity</a>
  <a href="#beta">Ordination</a><a href="#phylum">Composition</a>
  <a href="#niche">Niche Heatmap</a><a href="#graph">Graph DB</a>
  <a href="#guild">Guild ML</a><a href="#provenance">Provenance</a>
</nav>
<main>
  <section id="about">
    <h2>Overview</h2>
    <div class="kpi">
      <div><span>{n_studies}</span><small>OSDR studies</small></div>
      <div><span>{n_samples}</span><small>samples</small></div>
      <div><span>{n_tissue}</span><small>tissue niches</small></div>
      <div><span>{n_taxa}</span><small>reference genera</small></div>
      <div><span>{n_abund}</span><small>abundance records</small></div>
    </div>
    <p>This report integrates every plant-associated microbiome study currently
    curated from the NASA Open Science Data Repository (OSDR) into a single
    relational database and a set of linked, interactive dashboards. Study,
    assay, factor and sample metadata are sourced from OSDR; diversity metrics
    are computed by the pipeline.</p>
    <div class="banner"><b>Data provenance.</b> Study / assay / factor / sample
    records are drawn verbatim from OSDR metadata. Per-sample <b>taxon abundances
    shown below are produced by a documented, deterministic illustrative model</b>
    (flagged <code>illustrative_model</code>) that reproduces published qualitative
    patterns so the dashboards are populated before the large primary feature
    tables are ingested. Drop real OSDR feature tables into
    <code>data/processed/</code> and re-run to replace them
    (<code>data_provenance = osdr_feature_table</code>).</div>
  </section>
  <section id="registry"><h2>Study Registry</h2>
    <p>Curated, versioned registry of OSDR plant-microbiome accessions. Each links
    to its OSDR landing page.</p>{registry}
    <p style="font-size:13px">Sources:
    {links}</p></section>
  <section id="design"><h2>Sampling Design</h2>{sampling}</section>
  <section id="alpha"><h2>Alpha Diversity</h2>{alpha}</section>
  <section id="beta"><h2>Community Ordination (PCoA)</h2>{pcoa}</section>
  <section id="phylum"><h2>Taxonomic Composition</h2>{phylum}</section>
  <section id="niche"><h2>Genus × Tissue Niche Heatmap</h2>{heatmap}</section>
  <section id="graph"><h2>Study-Metadata Graph Database</h2>
    <p>Heterogeneous knowledge graph linking studies to their shared metadata
    entities (hardware, organism, assay, region, tissue, factor). Studies that
    cluster together share comparison-relevant attributes; the same graph is
    exported as GraphML / Cypher for Gephi, Cytoscape or Neo4j.</p>{graph}</section>
  <section id="guild"><h2>Guild Inference (ML): Beneficial · Plant Pathogen · Human Pathogen</h2>
    <p>Multiclass semi-supervised inference of microbial ecological guilds,
    fusing a curated prior knowledge base, guild-specific trait features,
    co-occurrence guilt-by-association and label spreading. Crucially, the two
    very different meanings of <em>pathogen</em> are kept on <b>separate axes</b>:
    a <b>plant-pathogen</b> (phytopathogen, e.g. <i>Ralstonia</i>) is a
    <b>crop-yield</b> risk, whereas a <b>human/clinical pathogen</b>
    (e.g. <i>Staphylococcus</i>) is a <b>food-safety / crew-health</b> risk. They
    co-occur in the same hardware but threaten different hosts and demand
    different responses. See <code>data/processed/GUILD_METHOD.md</code>.</p>{guild}
    <div class="banner"><b>Interpretation caveat.</b> Guild is often strain- not
    genus-level; scores here use illustrative abundances and are a
    decision-support prior — not a phytosanitary or clinical determination.</div></section>
  <section id="provenance"><h2>Build Provenance &amp; Audit Log</h2>
    <ul>{prv}</ul>
    <table class="log"><tr><th>Pipeline step</th><th>Detail</th><th>Rows</th></tr>
    {log}</table></section>
</main>
<footer>Generated by the OSDR Plant Microbiome FAIR tool · CC-BY-4.0 ·
Reproducible build (seed {seed}) · Data © NASA OSDR contributors</footer>
</body></html>"""


def build() -> None:
    con = _con()
    n = lambda q: con.execute(q).fetchone()[0]
    log_rows, prv_rows = provenance_rows(con)
    reg = pd.read_sql_query("SELECT osd_accession, osdr_url FROM studies ORDER BY osd_accession", con)
    links = " · ".join(f'<a class="ext" href="{r.osdr_url}">{r.osd_accession}</a>'
                       for r in reg.itertuples())
    html = HTML.format(
        version=__version__,
        built=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        n_studies=n("SELECT COUNT(*) FROM studies"),
        n_samples=n("SELECT COUNT(*) FROM samples"),
        n_tissue=n("SELECT COUNT(DISTINCT tissue_type) FROM samples"),
        n_taxa=n("SELECT COUNT(*) FROM taxa"),
        n_abund=f'{n("SELECT COUNT(*) FROM abundance"):,}',
        registry=panel_registry(con), sampling=panel_sampling(con),
        alpha=panel_alpha(con), pcoa=panel_pcoa(con), phylum=panel_phylum(con),
        heatmap=panel_genus_heatmap(con), graph=panel_graph(),
        guild=panel_guild(), log=log_rows, prv=prv_rows,
        links=links, seed=config.RANDOM_SEED)
    con.close()
    config.REPORT_HTML.write_text(html, encoding="utf-8")
    print(f"Report written -> {config.REPORT_HTML}")


if __name__ == "__main__":
    build()
