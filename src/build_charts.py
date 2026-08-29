"""Static chart exports, built from the tables in outputs/tables/.
Run after seller_cac.py, customer_ltv.py and segments.py."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import TABLES, CHARTS

PAGE = "#eef5f9"
INK = "#10222b"
INK2 = "#3d5563"

plt.rcParams.update({
    "figure.facecolor": PAGE, "axes.facecolor": "#ffffff",
    "font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.edgecolor": "#adc2ce", "grid.color": "#dbe7ee",
})

# Same palette as build_dashboard.py -- see the note there on why SKY/AMBER are
# darker steps of the #66C4FF / #FFC067 swatches.
SKY = "#2f8fd0"      # primary series
AMBER = "#e09b3d"    # emphasis + warm diverging pole
LIGHT = "#d9f6fd"    # faint/base series (e.g. leads, before conversion)
MUTED = "#7d99aa"    # baselines, reference lines


def chart_channel_scorecard():
    df = pd.read_csv(TABLES / "seller_channel_scorecard.csv", index_col=0)
    # "unknown" scores highest but isn't a channel anyone can buy more of, so
    # it's excluded here exactly as it is in the README and the dashboard.
    df = df[df.index != "unknown"].sort_values("channel_value_score", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = [AMBER if i == len(df) - 1 else SKY for i in range(len(df))]
    ax.barh(df.index, df["channel_value_score"], color=colors)
    ax.set_xlabel("Channel value score (0-1)")
    ax.set_title('Seller-Acquisition Channel Value Score\n'
                 '(win rate x activation rate x GMV per lead; "unknown" origin excluded)')
    fig.tight_layout()
    fig.savefig(CHARTS / "01_channel_value_score.png", dpi=150)
    plt.close(fig)


def chart_funnel_by_channel():
    df = pd.read_csv(TABLES / "seller_channel_scorecard.csv", index_col=0)
    df = df.sort_values("mql_count", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(df))
    ax.bar(x, df["mql_count"], color=LIGHT, label="MQLs (leads)")
    ax.bar(x, df["won_count"], color=SKY, label="Won (became sellers)")
    ax.bar(x, df["activated_count"], color=AMBER, label="Activated (actually sold)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df.index, rotation=35, ha="right")
    ax.set_ylabel("Count")
    ax.set_title("Seller Funnel by Channel: Leads -> Won -> Activated")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "02_funnel_by_channel.png", dpi=150)
    plt.close(fig)


def chart_cohort_curves():
    df = pd.read_csv(TABLES / "cohort_cumulative_ltv.csv")
    df["cohort_month"] = df["cohort_month"].astype(str)
    cohorts = sorted(df.cohort_month.unique())
    # keep cohorts with enough customers and horizon
    keep = df.groupby("cohort_month")["cohort_customers"].first()
    keep = keep[keep >= 200].index.tolist()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    from matplotlib.colors import LinearSegmentedColormap
    seq = ["#d9f6fd", "#a5e8f7", "#66c4ff", "#3aa3e8", "#2f8fd0", "#1f6ea6", "#154d75"]
    cmap = LinearSegmentedColormap.from_list("seq_sky", seq)
    for i, c in enumerate(sorted(keep)):
        sub = df[df.cohort_month == c].sort_values("months_since_first")
        sub = sub[sub.months_since_first <= 12]
        ax.plot(sub.months_since_first, sub.cum_margin_per_customer,
                color=cmap(i / max(len(keep) - 1, 1)), alpha=0.85, linewidth=1.6)
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Cumulative freight-adjusted margin per customer (R$)")
    ax.set_title("Customer Cohort Value Curves\n(flattens almost immediately -- 97% of customers never return)")
    fig.tight_layout()
    fig.savefig(CHARTS / "03_cohort_curves.png", dpi=150)
    plt.close(fig)


def chart_repeat_share():
    stats = pd.read_csv(TABLES / "customer_repeat_stats.csv", index_col=0).squeeze("columns")
    fig, ax = plt.subplots(figsize=(5, 5))
    vals = [float(stats["one_time_share"]), float(stats["repeat_share"])]
    ax.pie(vals, labels=[f"One-time\n{vals[0]:.1%}", f"Repeat\n{vals[1]:.1%}"],
           colors=[LIGHT, AMBER], autopct=None, startangle=90,
           wedgeprops=dict(edgecolor="white", linewidth=2))
    ax.set_title("Customer Repeat-Purchase Share")
    fig.tight_layout()
    fig.savefig(CHARTS / "04_repeat_share.png", dpi=150)
    plt.close(fig)


def chart_segment_margin(name, title, fname):
    df = pd.read_csv(TABLES / name, index_col=0)
    df = df.sort_values("avg_margin_pct")
    worst = df.head(6)
    best = df.tail(6)
    combo = pd.concat([worst, best])
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = [AMBER] * len(worst) + [SKY] * len(best)
    ax.barh(combo.index.astype(str), combo["avg_margin_pct"], color=colors)
    ax.axvline(df["avg_margin_pct"].median(), color=MUTED, linestyle="--", linewidth=1,
               label=f"Median = {df['avg_margin_pct'].median():.1%}")
    ax.set_xlabel("Avg freight-adjusted margin %")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / fname, dpi=150)
    plt.close(fig)


def chart_propensity_performance():
    from product_names import PRODUCT_NAMES
    df = pd.read_csv(TABLES / "propensity_model_performance.csv")
    df["label"] = df["product"].map(PRODUCT_NAMES).fillna(df["product"])
    df = df.sort_values("test_auc")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(df["label"], df["test_auc"], color=SKY)
    ax.axvline(0.5, color=MUTED, linestyle="--", linewidth=1)
    ax.annotate("random (0.5)", xy=(0.5, -0.6), xytext=(0.505, -0.6),
                color=MUTED, fontsize=9, va="center")
    ax.set_xlim(0.4, 1.02)
    ax.set_xlabel("Out-of-time test AUC")
    ax.set_title("Cross-Sell Propensity Model: Held-Out Performance by Product\n(trained Jan 2015-Feb 2016, tested Mar-May 2016)")
    fig.tight_layout()
    fig.savefig(CHARTS / "07_propensity_auc.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    chart_channel_scorecard()
    chart_funnel_by_channel()
    chart_cohort_curves()
    chart_repeat_share()
    chart_segment_margin("segment_economics_by_category.csv",
                          "Worst & Best Product Categories by Margin %",
                          "05_category_margin.png")
    chart_segment_margin("segment_economics_by_state.csv",
                          "Worst & Best States by Margin % (freight distance effect)",
                          "06_state_margin.png")
    chart_propensity_performance()
    print("Charts written to", CHARTS)
