"""Generates the four project notebooks as thin, real wrappers around the
src/ modules -- markdown narration + actual executed code, not a duplicate
implementation. Run this, then execute each notebook top-to-bottom."""
import nbformat as nbf
from pathlib import Path

NB_DIR = Path(__file__).resolve().parents[1] / "notebooks"
NB_DIR.mkdir(exist_ok=True)

SETUP = "import sys; sys.path.insert(0, '../src')"


def make_nb(filename, title, blurb, cells):
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell(f"# {title}\n\n{blurb}"),
        nbf.v4.new_code_cell(SETUP),
    ]
    for c in cells:
        if c["type"] == "md":
            nb["cells"].append(nbf.v4.new_markdown_cell(c["src"]))
        else:
            nb["cells"].append(nbf.v4.new_code_cell(c["src"]))
    with open(NB_DIR / filename, "w") as f:
        nbf.write(nb, f)


make_nb(
    "01_seller_acquisition_funnel.ipynb",
    "Part A — Seller Acquisition Funnel",
    "Real MQL -> won -> activated funnel from Olist's Marketing Funnel dataset. "
    "See `docs/seller_cac_methodology.md` for why this reports a channel value "
    "score rather than a fabricated dollar CAC.",
    [
        {"type": "code", "src": "from seller_cac import build_seller_funnel\nfunnel, scorecard = build_seller_funnel()"},
        {"type": "md", "src": "## Channel scorecard (real, disclosed metrics only)"},
        {"type": "code", "src": "scorecard[['mql_count','won_count','win_rate','activation_rate_of_won','gmv_per_mql','channel_value_score']]"},
        {"type": "md", "src": "## Headline numbers"},
        {"type": "code", "src": (
            "print(f'Total MQLs: {len(funnel)}')\n"
            "print(f'Won: {funnel.won.sum()}  ({funnel.won.mean():.1%} win rate)')\n"
            "print(f'Activated (won AND sold something): {funnel.activated.sum()}  '\n"
            "      f'({funnel.activated.sum()/funnel.won.sum():.1%} of won sellers)')"
        )},
    ],
)

make_nb(
    "02_customer_cohort_ltv.ipynb",
    "Part B — Customer Cohort Economics",
    "Cumulative freight-adjusted margin per customer, indexed on months since "
    "first purchase. See `docs/margin_proxy_definition.md` for exactly what "
    "'margin' means here.",
    [
        {"type": "code", "src": "from customer_ltv import build_customer_cohorts\ndf, order_rev, cum, stats = build_customer_cohorts()"},
        {"type": "md", "src": "## Repeat-purchase headline"},
        {"type": "code", "src": "import pandas as pd\npd.Series(stats)"},
        {"type": "md", "src": "## Cohort value curve (selected horizons)"},
        {"type": "code", "src": "cum[cum.months_since_first.isin([0,1,3,6,12])].groupby('months_since_first')['cum_margin_per_customer'].mean()"},
    ],
)

make_nb(
    "03_segment_economics.ipynb",
    "Part C — Segment Economics",
    "Which categories and states are margin-negative once real freight cost "
    "is netted against real item price.",
    [
        {"type": "code", "src": "from segments import build_segment_economics\nby_cat, by_state = build_segment_economics()"},
        {"type": "md", "src": "## Worst 5 categories by margin %"},
        {"type": "code", "src": "by_cat.head(5)[['n_items','avg_margin_pct','avg_freight_pct','avg_weight_g']]"},
        {"type": "md", "src": "## Best 5 categories by margin %"},
        {"type": "code", "src": "by_cat.tail(5)[['n_items','avg_margin_pct','avg_freight_pct','avg_weight_g']]"},
        {"type": "md", "src": "## Worst 5 states by margin % (freight-distance effect)"},
        {"type": "code", "src": "by_state.head(5)[['n_items','avg_margin_pct','avg_freight_pct']]"},
        {"type": "md", "src": "## Best 5 states by margin %"},
        {"type": "code", "src": "by_state.tail(5)[['n_items','avg_margin_pct','avg_freight_pct']]"},
    ],
)

make_nb(
    "04_cross_sell_propensity.ipynb",
    "Part D — Cross-Sell Propensity Model",
    "Built on the real Santander product-holding panel. Strict out-of-time "
    "split (train through Feb 2016, test Mar-May 2016). Products too rare to "
    "model honestly are dropped, not force-fit -- see `reports/LIMITATIONS.md`.",
    [
        {"type": "code", "src": (
            "from propensity import load_panel, build_transitions, train_and_score\n"
            "panel = load_panel()\n"
            "merged = build_transitions(panel)\n"
            "results_df, ranked = train_and_score(merged)"
        )},
        {"type": "md", "src": "## Held-out (out-of-time) AUC by product"},
        {"type": "code", "src": "from product_names import PRODUCT_NAMES\nresults_df['product_name'] = results_df['product'].map(PRODUCT_NAMES)\nresults_df[['product_name','train_positives','test_positives','test_auc']]"},
        {"type": "md", "src": "## Sample of the ranked cross-sell output (top-3 per customer, latest test month)"},
        {"type": "code", "src": "ranked.head(15)"},
    ],
)

print("Notebooks written:", sorted(p.name for p in NB_DIR.glob("*.ipynb")))
