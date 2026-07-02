"""Central configuration + paths for the OSDR Plant Microbiome FAIR tool."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR      = ROOT / "data"
REGISTRY_CSV  = DATA_DIR / "registry" / "study_registry.csv"
RAW_DIR       = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_PATH       = DATA_DIR / "db" / "osdr_plant_microbiome.db"

SCHEMA_SQL    = ROOT / "db" / "schema.sql"
DASHBOARD_DIR = ROOT / "dashboards"
REPORT_HTML   = DASHBOARD_DIR / "report.html"

# Live NASA OSDR metadata endpoint (verified reachable July 2026).
# The study-level metadata JSON is served from:
#   https://osdr.nasa.gov/osdr/data/osd/meta/<numeric_id>
OSDR_META_URL = "https://osdr.nasa.gov/osdr/data/osd/meta/{osd_id}"
OSDR_FILES_URL = "https://osdr.nasa.gov/osdr/data/osd/files/{osd_id}"

# Deterministic seed — the tool NEVER uses wall-clock randomness so that
# every build is byte-for-byte reproducible (FAIR: Reusable).
RANDOM_SEED = 767

# Corpus snapshot date. The set of plant-microbiome studies in OSDR grows
# over time, so every figure/result is an explicitly dated snapshot. This is
# the raison d'etre of the live FAIR-dashboard approach: the report re-derives
# the current state, while archived figures record a fixed point in time.
SNAPSHOT_DATE = "2026-07-02"

FIGURES_DIR   = ROOT / "figures" / SNAPSHOT_DATE
GRAPH_DIR     = DATA_DIR / "graph"

for _d in (FIGURES_DIR, GRAPH_DIR):
    _d.mkdir(parents=True, exist_ok=True)

for _d in (RAW_DIR, PROCESSED_DIR, DB_PATH.parent, DASHBOARD_DIR):
    _d.mkdir(parents=True, exist_ok=True)
