"""
fetch_osdr.py — pull live study-level metadata from the NASA OSDR API.

Given the curated study registry, this module queries the public OSDR
metadata endpoint for each accession and caches the raw JSON under
data/raw/. The pipeline is fully functional offline from the curated
registry alone; this step *enriches / verifies* the registry against the
live repository and is the mechanism by which new OSDR plant-microbiome
studies are on-boarded (Findable + Accessible).

Usage:
    python -m src.fetch_osdr            # fetch all registry accessions
    python -m src.fetch_osdr OSD-766    # fetch a single accession
"""
from __future__ import annotations
import json
import sys
import time
import urllib.request
import urllib.error

import pandas as pd

from . import config


def _osd_id(accession: str) -> str:
    """OSD-766 -> 766"""
    return "".join(ch for ch in accession if ch.isdigit())


def fetch_one(accession: str, pause: float = 0.5) -> dict | None:
    """Fetch and cache raw OSDR metadata JSON for one accession."""
    osd_id = _osd_id(accession)
    url = config.OSDR_META_URL.format(osd_id=osd_id)
    out = config.RAW_DIR / f"{accession}.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "osdr-fair-tool/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"[ok]   {accession}: cached -> {out.name}")
        time.sleep(pause)
        return payload
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(f"[warn] {accession}: could not fetch live metadata ({exc}). "
              f"Falling back to curated registry.")
        return None


def fetch_all() -> None:
    reg = pd.read_csv(config.REGISTRY_CSV)
    for acc in reg["osd_accession"]:
        fetch_one(acc)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fetch_one(sys.argv[1])
    else:
        fetch_all()
