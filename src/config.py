from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FINAL = ROOT / "data" / "final"
CHARTS = ROOT / "outputs" / "charts"
TABLES = ROOT / "outputs" / "tables"
REPORTS = ROOT / "reports"

for d in (FINAL, CHARTS, TABLES):
    d.mkdir(parents=True, exist_ok=True)

OLIST = RAW / "olist"
OLIST_MKT = RAW / "olist_marketing"
SANTANDER = RAW / "santander"
