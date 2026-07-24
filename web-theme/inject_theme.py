#!/usr/bin/env python3
"""Inject the CoSE overlay (toggleable left map + COSE branding) into a
generated report HTML. Idempotent. Run by the Pages deploy workflow after the
report is staged as _site/index.html, so the freshly-built report is themed on
every deploy without touching the analytics/report generator.

Usage: python web-theme/inject_theme.py _site/index.html
Assumes the CoSE kit (cose-theme.css, theme.js, sites.js, cose-logo.png) has
been copied to <site>/assets/ alongside the HTML.
"""
import re
import sys

SITE_ID = "osdr-plant-microbiome"


def inject(path):
    html = open(path, encoding="utf-8").read()
    if "cose-theme.css" in html:
        return False
    html = html.replace(
        "</head>", '<link rel="stylesheet" href="assets/cose-theme.css"></head>', 1
    )
    html = re.sub(
        r"<body([^>]*)>",
        r'<body\1 data-site-id="%s" data-brand-logo="assets/cose-logo.png">' % SITE_ID,
        html,
        count=1,
    )
    i = html.rfind("</body>")
    scripts = (
        '<script src="assets/sites.js"></script>'
        '<script src="assets/theme.js"></script>'
    )
    html = html[:i] + scripts + html[i:]
    open(path, "w", encoding="utf-8").write(html)
    return True


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "_site/index.html"
    print("CoSE theme injected" if inject(target) else "CoSE theme already present")
