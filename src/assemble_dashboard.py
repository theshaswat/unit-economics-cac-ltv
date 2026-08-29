"""Assembles the standalone dashboard HTML from the chart fragments built by
build_dashboard.py, embedding plotly.js inline so the file works fully
offline in any browser with no server."""
import plotly.offline as pyo
from pathlib import Path
from config import ROOT

FRAG_DIR = ROOT / "outputs" / "chart_fragments"
OUT = ROOT / "dashboards" / "dashboard.html"

CHART_NAMES = ["channel_score", "funnel", "cohorts", "repeat_share",
               "category_margin", "state_margin", "propensity"]

TEMPLATE = (Path(__file__).parent / "dashboard_template.html").read_text()


def build():
    frags = {name: (FRAG_DIR / f"{name}.html").read_text() for name in CHART_NAMES}
    html = TEMPLATE
    html = html.replace("__PLOTLYJS__", pyo.get_plotlyjs())
    html = html.replace("__CHANNEL__", frags["channel_score"])
    html = html.replace("__FUNNEL__", frags["funnel"])
    html = html.replace("__REPEAT__", frags["repeat_share"])
    html = html.replace("__COHORTS__", frags["cohorts"])
    html = html.replace("__PROPENSITY__", frags["propensity"])
    html = html.replace("__CATEGORY__", frags["category_margin"])
    html = html.replace("__STATE__", frags["state_margin"])
    OUT.write_text(html)
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
