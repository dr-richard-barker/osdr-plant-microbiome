#!/usr/bin/env python
"""
run_all.py — one-command reproducible build of the whole tool.

    python run_all.py            # build DB + analytics + report (offline)
    python run_all.py --fetch    # also refresh metadata from the live OSDR API

Steps: (0 optional fetch) -> build_database -> analysis -> build_dashboard.
Deterministic: same registry + seed => identical database and report.
"""
import argparse
from src import (build_database, analysis, build_graph, classify_guild,
                 make_figures, build_dashboard)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true",
                    help="refresh raw metadata from the live NASA OSDR API first")
    args = ap.parse_args()

    if args.fetch:
        from src import fetch_osdr
        print("== [0/6] Fetching live OSDR metadata ==")
        fetch_osdr.fetch_all()

    print("== [1/6] Building relational database ==")
    build_database.main()
    print("\n== [2/6] Running analysis / diversity metrics ==")
    analysis.main()
    print("\n== [3/6] Building study-metadata graph database ==")
    build_graph.main()
    print("\n== [4/6] Inferring pathogen/beneficial guilds ==")
    classify_guild.main()
    print("\n== [5/6] Exporting dated publication figures ==")
    make_figures.main()
    print("\n== [6/6] Rendering integrated interactive report ==")
    build_dashboard.build()
    print("\nDone. Open dashboards/report.html")


if __name__ == "__main__":
    main()
