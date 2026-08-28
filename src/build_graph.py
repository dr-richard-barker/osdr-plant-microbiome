"""
build_graph.py — a graph database of the OSDR plant-microbiome corpus.

Two complementary graphs are built with networkx and exported in
interoperable formats (GraphML for Gephi/Cytoscape/Neo4j; node-link JSON;
tidy node/edge CSVs; a Neo4j Cypher loader):

  1. Knowledge graph  — heterogeneous nodes (Study, Hardware, Organism,
     Assay, Region, Tissue, Factor) linked by typed edges (a study USES a
     hardware, TARGETS a region, HAS_FACTOR ...). This is the queryable
     metadata graph.
  2. Study-similarity projection — study<->study edges weighted by the
     Jaccard similarity of their combined metadata attribute sets, revealing
     which studies are natural comparison groups.

Also renders a static Fig4 (matplotlib) and an interactive Plotly network
(embedded into the main report).
"""
from __future__ import annotations
import json
import sqlite3
from itertools import combinations

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.io import to_html

from . import config

SAFE = {"Study": "#332288", "Hardware": "#117733", "Organism": "#CC6677",
        "Assay": "#DDCC77", "Region": "#88CCEE", "Tissue": "#44AA99",
        "Factor": "#AA4499"}


def _con():
    return sqlite3.connect(config.DB_PATH)


def _hardware_family(hw: str) -> str:
    if "APH" in hw or "Advanced" in hw:
        return "Advanced Plant Habitat"
    if "XROOTS" in hw:
        return "Veggie/XROOTS"
    return "Veggie"


def load_attributes(con) -> dict[str, dict]:
    """Collect the attribute sets that describe each study."""
    reg = pd.read_sql_query("SELECT * FROM studies", con)
    tissues = pd.read_sql_query(
        "SELECT osd_accession, GROUP_CONCAT(DISTINCT tissue_type) t FROM samples GROUP BY 1", con
    ).set_index("osd_accession").t.to_dict()
    assays = pd.read_sql_query(
        "SELECT osd_accession, GROUP_CONCAT(DISTINCT assay_type) a, GROUP_CONCAT(DISTINCT target_region) r FROM assays GROUP BY 1", con
    ).set_index("osd_accession")
    factors = pd.read_sql_query(
        "SELECT osd_accession, GROUP_CONCAT(DISTINCT factor_name) f FROM factors GROUP BY 1", con
    ).set_index("osd_accession").f.to_dict()
    nsamp = pd.read_sql_query(
        "SELECT osd_accession, COUNT(*) n FROM samples GROUP BY 1", con
    ).set_index("osd_accession").n.to_dict()

    attrs = {}
    for r in reg.itertuples():
        acc = r.osd_accession
        attrs[acc] = {
            "organism": r.organism,
            "hardware": _hardware_family(str(r.platform_hardware)),
            "assays": set(str(assays.loc[acc, "a"]).split(",")) if acc in assays.index else set(),
            "regions": set(str(assays.loc[acc, "r"]).split(",")) if acc in assays.index else set(),
            "tissues": set(str(tissues.get(acc, "")).split(",")),
            "factors": set(f.strip() for f in str(factors.get(acc, "")).split(",")),
            "n_samples": int(nsamp.get(acc, 0)),
            "title": r.title, "url": r.osdr_url,
        }
    return attrs


def build_knowledge_graph(attrs) -> nx.Graph:
    G = nx.Graph()
    for acc, a in attrs.items():
        G.add_node(acc, ntype="Study", label=acc, n_samples=a["n_samples"],
                   title=a["title"], url=a["url"])
        def link(entity, etype, rel):
            if not entity or entity in ("", "nan"):
                return
            nid = f"{etype}:{entity}"
            G.add_node(nid, ntype=etype, label=entity)
            G.add_edge(acc, nid, rel=rel)
        link(a["organism"], "Organism", "STUDIES_ORGANISM")
        link(a["hardware"], "Hardware", "USES_HARDWARE")
        for x in a["assays"]:   link(x, "Assay", "MEASURED_BY")
        for x in a["regions"]:  link(x, "Region", "TARGETS_REGION")
        for x in a["tissues"]:  link(x.strip(), "Tissue", "SAMPLED_TISSUE")
        for x in a["factors"]:  link(x, "Factor", "HAS_FACTOR")
    return G


def build_similarity_graph(attrs) -> nx.Graph:
    def feature_set(a):
        s = {f"org:{a['organism']}", f"hw:{a['hardware']}"}
        s |= {f"assay:{x}" for x in a["assays"]}
        s |= {f"region:{x}" for x in a["regions"]}
        s |= {f"tissue:{x.strip()}" for x in a["tissues"]}
        s |= {f"factor:{x}" for x in a["factors"]}
        return s
    feats = {acc: feature_set(a) for acc, a in attrs.items()}
    G = nx.Graph()
    for acc, a in attrs.items():
        G.add_node(acc, ntype="Study", n_samples=a["n_samples"],
                   hardware=a["hardware"], organism=a["organism"])
    for x, y in combinations(feats, 2):
        inter = feats[x] & feats[y]
        union = feats[x] | feats[y]
        jac = len(inter) / len(union) if union else 0
        if jac > 0:
            G.add_edge(x, y, weight=round(jac, 3), shared=len(inter),
                       shared_attrs="; ".join(sorted(inter)))
    return G


def export_formats(kg: nx.Graph, sim: nx.Graph):
    nx.write_graphml(kg, config.GRAPH_DIR / "knowledge_graph.graphml")
    nx.write_graphml(sim, config.GRAPH_DIR / "study_similarity.graphml")
    try:
        node_link = nx.node_link_data(kg, edges="links")
    except TypeError:
        node_link = nx.node_link_data(kg, link="links")  # networkx <3.4
    (config.GRAPH_DIR / "knowledge_graph.json").write_text(
        json.dumps(node_link, indent=2), encoding="utf-8")
    # tidy CSVs
    pd.DataFrame([{"id": n, **d} for n, d in kg.nodes(data=True)]).to_csv(
        config.GRAPH_DIR / "nodes.csv", index=False)
    pd.DataFrame([{"source": u, "target": v, **d} for u, v, d in kg.edges(data=True)]).to_csv(
        config.GRAPH_DIR / "edges.csv", index=False)
    # Neo4j Cypher loader
    lines = ["// Neo4j loader for the OSDR plant-microbiome knowledge graph",
             "// Run: cat load_neo4j.cypher | cypher-shell", ""]
    for n, d in kg.nodes(data=True):
        lab = d["ntype"]
        props = ", ".join(f'{k}: {json.dumps(v)}' for k, v in d.items() if k != "ntype")
        lines.append(f'MERGE (:{lab} {{id: {json.dumps(n)}, {props}}});')
    for u, v, d in kg.edges(data=True):
        rel = d.get("rel", "RELATED")
        lines.append(
            f'MATCH (a {{id: {json.dumps(u)}}}),(b {{id: {json.dumps(v)}}}) MERGE (a)-[:{rel}]->(b);')
    (config.GRAPH_DIR / "load_neo4j.cypher").write_text("\n".join(lines), encoding="utf-8")
    print(f"  [graph] exported GraphML, JSON, CSV, Cypher -> {config.GRAPH_DIR}")


def fig4_static(kg: nx.Graph):
    pos = nx.spring_layout(kg, seed=config.RANDOM_SEED, k=0.6, iterations=200)
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for ntype, col in SAFE.items():
        nodes = [n for n, d in kg.nodes(data=True) if d["ntype"] == ntype]
        sizes = [420 if ntype == "Study" else 130 for _ in nodes]
        nx.draw_networkx_nodes(kg, pos, nodelist=nodes, node_color=col,
                               node_size=sizes, ax=ax, edgecolors="white",
                               linewidths=0.6, label=ntype)
    nx.draw_networkx_edges(kg, pos, alpha=0.25, ax=ax, edge_color="#666")
    study_labels = {n: d["label"] for n, d in kg.nodes(data=True) if d["ntype"] == "Study"}
    nx.draw_networkx_labels(kg, pos, labels=study_labels, font_size=7,
                            font_weight="bold", ax=ax)
    other = {n: d["label"] for n, d in kg.nodes(data=True) if d["ntype"] != "Study"}
    nx.draw_networkx_labels(kg, pos, labels=other, font_size=5.5, ax=ax,
                            font_color="#333")
    ax.legend(scatterpoints=1, fontsize=7.5, frameon=False, loc="upper left",
              markerscale=0.7)
    ax.set_title("Study-metadata knowledge graph", fontweight="bold")
    ax.axis("off")
    for ext in ("png", "svg"):
        fig.savefig(config.FIGURES_DIR / f"Fig4_study_graph.{ext}", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("  [fig] Fig4_study_graph.png / .svg")


def interactive_network(kg: nx.Graph) -> str:
    """Plotly force-directed network for embedding into the report."""
    pos = nx.spring_layout(kg, seed=config.RANDOM_SEED, k=0.6, iterations=200)
    ex, ey = [], []
    for u, v in kg.edges():
        ex += [pos[u][0], pos[v][0], None]
        ey += [pos[u][1], pos[v][1], None]
    edge_trace = go.Scatter(x=ex, y=ey, mode="lines",
                            line=dict(width=0.6, color="#bbb"), hoverinfo="none")
    traces = [edge_trace]
    for ntype, col in SAFE.items():
        ns = [n for n, d in kg.nodes(data=True) if d["ntype"] == ntype]
        if not ns:
            continue
        traces.append(go.Scatter(
            x=[pos[n][0] for n in ns], y=[pos[n][1] for n in ns], mode="markers+text",
            name=ntype, text=[kg.nodes[n]["label"] for n in ns],
            textposition="top center", textfont=dict(size=8),
            marker=dict(size=[20 if ntype == "Study" else 11 for _ in ns],
                        color=col, line=dict(width=1, color="white")),
            hovertext=[f"{ntype}: {kg.nodes[n]['label']}" for n in ns],
            hoverinfo="text"))
    fig = go.Figure(traces)
    fig.update_layout(template="plotly_white", height=560, showlegend=True,
                      title="Study-metadata knowledge graph (interactive)",
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      margin=dict(l=10, r=10, t=50, b=10),
                      legend=dict(orientation="h", y=-0.05))
    return to_html(fig, include_plotlyjs=False, full_html=False,
                   config={"displaylogo": False, "responsive": True})


def main():
    con = _con()
    attrs = load_attributes(con)
    con.close()
    kg = build_knowledge_graph(attrs)
    sim = build_similarity_graph(attrs)
    export_formats(kg, sim)
    fig4_static(kg)
    # persist the interactive fragment for the dashboard builder
    (config.GRAPH_DIR / "network_fragment.html").write_text(
        interactive_network(kg), encoding="utf-8")
    # similarity summary
    top = sorted(sim.edges(data=True), key=lambda e: -e[2]["weight"])[:5]
    print("  Most similar study pairs (Jaccard):")
    for u, v, d in top:
        print(f"    {u} <-> {v}: {d['weight']} ({d['shared']} shared attrs)")
    print(f"KG: {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges")


if __name__ == "__main__":
    main()
