"""
analysis.py — derived analytics exported for the dashboards.

  * PCoA ordination (classical MDS) of Bray-Curtis distances per study,
    implemented in numpy (no scikit-bio dependency).
  * Group-level alpha-diversity summaries (tissue x spaceflight).
  * Phylum / genus composition tables.
  * load_real_feature_table(): ingest a real OSDR taxa x samples table so
    the illustrative model can be swapped for primary data.

Outputs land in data/processed/ as tidy CSVs consumed by build_dashboard.py.
"""
from __future__ import annotations
import sqlite3

import numpy as np
import pandas as pd

from . import config


def _con() -> sqlite3.Connection:
    return sqlite3.connect(config.DB_PATH)


def pcoa_per_study() -> pd.DataFrame:
    """Classical MDS on within-study Bray-Curtis distances -> 2D coords."""
    con = _con()
    out = []
    studies = [r[0] for r in con.execute("SELECT osd_accession FROM studies").fetchall()]
    for osd in studies:
        d = pd.read_sql_query(
            "SELECT sample_a, sample_b, distance FROM beta_diversity WHERE osd_accession=? AND metric='bray_curtis'",
            con, params=(osd,))
        if d.empty:
            continue
        ids = sorted(set(d.sample_a) | set(d.sample_b))
        idx = {s: i for i, s in enumerate(ids)}
        n = len(ids)
        D = np.zeros((n, n))
        for _, r in d.iterrows():
            i, j = idx[r.sample_a], idx[r.sample_b]
            D[i, j] = D[j, i] = r.distance
        # double centering
        D2 = D ** 2
        J = np.eye(n) - np.ones((n, n)) / n
        B = -0.5 * J @ D2 @ J
        vals, vecs = np.linalg.eigh(B)
        order = np.argsort(vals)[::-1]
        vals, vecs = vals[order], vecs[:, order]
        pos = vals > 1e-9
        coords = vecs[:, :2] * np.sqrt(np.clip(vals[:2], 0, None))
        var = np.clip(vals, 0, None)
        pc1 = 100 * var[0] / var[pos].sum() if pos.any() else 0
        pc2 = 100 * var[1] / var[pos].sum() if pos.any() else 0
        meta = pd.read_sql_query(
            "SELECT sample_id, tissue_type, spaceflight, light_regime FROM samples WHERE osd_accession=?",
            con, params=(osd,)).set_index("sample_id")
        for k, s in enumerate(ids):
            out.append({
                "osd_accession": osd, "sample_id": s,
                "pc1": float(coords[k, 0]), "pc2": float(coords[k, 1]),
                "pc1_pct": round(pc1, 1), "pc2_pct": round(pc2, 1),
                "tissue_type": meta.loc[s, "tissue_type"],
                "spaceflight": int(meta.loc[s, "spaceflight"]),
                "light_regime": meta.loc[s, "light_regime"],
            })
    con.close()
    df = pd.DataFrame(out)
    df.to_csv(config.PROCESSED_DIR / "pcoa_coords.csv", index=False)
    return df


def alpha_summary() -> pd.DataFrame:
    con = _con()
    df = pd.read_sql_query("SELECT * FROM v_sample_alpha", con)
    con.close()
    df["environment"] = np.where(df.spaceflight == 1, "Spaceflight", "Ground")
    g = (df.groupby(["osd_accession", "tissue_type", "environment"])
           .agg(shannon_mean=("shannon", "mean"),
                shannon_sd=("shannon", "std"),
                observed_mean=("observed_features", "mean"),
                n=("sample_id", "count"))
           .reset_index())
    df.to_csv(config.PROCESSED_DIR / "alpha_per_sample.csv", index=False)
    g.to_csv(config.PROCESSED_DIR / "alpha_group_summary.csv", index=False)
    return g


def composition_tables() -> pd.DataFrame:
    con = _con()
    genus = pd.read_sql_query("""
        SELECT s.osd_accession, s.tissue_type,
               CASE s.spaceflight WHEN 1 THEN 'Spaceflight' ELSE 'Ground' END AS environment,
               t.phylum, t.genus, AVG(ab.relative_abundance) AS mean_rel
        FROM abundance ab
        JOIN samples s ON s.sample_id = ab.sample_id
        JOIN taxa t    ON t.taxon_id  = ab.taxon_id
        GROUP BY s.osd_accession, s.tissue_type, environment, t.phylum, t.genus
    """, con)
    con.close()
    genus.to_csv(config.PROCESSED_DIR / "genus_composition.csv", index=False)
    phylum = (genus.groupby(["osd_accession", "environment", "phylum"])["mean_rel"]
                    .sum().reset_index())
    phylum.to_csv(config.PROCESSED_DIR / "phylum_composition.csv", index=False)
    return genus


def load_real_feature_table(osd_accession: str, tsv_path: str) -> int:
    """
    Replace illustrative abundances for one study with a real OSDR feature
    table (rows = taxa/taxonomy string, columns = sample_name). Matches sample
    names already present in `samples`; unknown taxa are inserted into `taxa`.
    Returns the number of abundance rows written.
    """
    con = _con()
    con.execute("PRAGMA foreign_keys=ON")
    ft = pd.read_csv(tsv_path, sep="\t", index_col=0)
    name_to_id = dict(con.execute(
        "SELECT sample_name, sample_id FROM samples WHERE osd_accession=?",
        (osd_accession,)).fetchall())
    sids = [name_to_id[c] for c in ft.columns if c in name_to_id]
    con.executemany("DELETE FROM abundance WHERE sample_id=?", [(s,) for s in sids])
    written = 0
    for taxon_string, row in ft.iterrows():
        cur = con.execute("SELECT taxon_id FROM taxa WHERE taxonomy_string=?", (taxon_string,)).fetchone()
        if cur:
            tid = cur[0]
        else:
            genus = str(taxon_string).split(";")[-1].replace("g__", "") or None
            tid = con.execute(
                "INSERT INTO taxa(kingdom, genus, taxonomy_string) VALUES ('Bacteria',?,?)",
                (genus, taxon_string)).lastrowid
        col = row / row.sum() if row.sum() else row
        for cname, val in row.items():
            sid = name_to_id.get(cname)
            if sid is None or val == 0:
                continue
            rel = float(col[cname])
            con.execute("""INSERT OR REPLACE INTO abundance
                           (sample_id, taxon_id, relative_abundance, read_count, data_provenance)
                           VALUES (?,?,?,?, 'osdr_feature_table')""",
                        (sid, tid, rel, int(val)))
            written += 1
    con.commit()
    con.close()
    print(f"[ok] {osd_accession}: ingested {written} real abundance rows from {tsv_path}")
    return written


def main() -> None:
    pcoa_per_study()
    alpha_summary()
    composition_tables()
    print(f"Processed analytics -> {config.PROCESSED_DIR}")


if __name__ == "__main__":
    main()
