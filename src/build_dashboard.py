"""
Interactive dashboard, built with Plotly so the charts carry hover detail
the static PNGs in outputs/charts/ can't. Same burnt-sienna palette as
build_charts.py; green/red are reserved for above/below-median polarity so
they never double as a series colour.
"""
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from config import TABLES, ROOT
from product_names import PRODUCT_NAMES

# Palette: #FFC067 / #66F4FF / #66C4FF / #7D99AA. The two blues are too light
# to read as filled marks on a light surface, so SKY and AMBER are darker steps
# of the same hues; the raw swatches survive as the light end of the ramp and
# as the muted/axis tone.
SKY = "#2f8fd0"      # primary series (deep step of #66C4FF)
AMBER = "#e09b3d"    # emphasis + warm diverging pole (deep step of #FFC067)
CYAN = "#66f4ff"     # light accent
SLATE = "#7d99aa"    # muted tone, baselines
LIGHT = "#d9f6fd"    # faint fill, e.g. leads before conversion
GOOD = "#0ca30c"     # reserved status colours, never used as a series
CRITICAL = "#d03b3b"

SEQ = ["#d9f6fd", "#a5e8f7", "#66c4ff", "#3aa3e8", "#2f8fd0", "#1f6ea6", "#154d75"]
# Thin strokes need more contrast than a filled area, so the line ramp
# starts partway down the same scale rather than at the palest tint.
SEQ_LINE = ["#7cccf5", "#4fb0e8", "#2f8fd0", "#2478b4", "#1f6ea6", "#195a87", "#154d75"]

SURFACE = "#ffffff"
PAGE = "#eef5f9"
INK = "#10222b"
INK2 = "#3d5563"
MUTED = "#7d99aa"
GRID = "#dbe7ee"
BASELINE = "#adc2ce"

FONT = dict(family="-apple-system, 'Segoe UI', system-ui, sans-serif", color=INK, size=12)

BASE_LAYOUT = dict(
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, font=FONT,
    margin=dict(l=10, r=10, t=36, b=10),
    hoverlabel=dict(bgcolor="white", font_size=12, font_family=FONT["family"], bordercolor=GRID),
    showlegend=False,
)


def style_axes(fig, xgrid=True, ygrid=False):
    fig.update_xaxes(showgrid=xgrid, gridcolor=GRID, gridwidth=1, zeroline=False,
                      linecolor=BASELINE, tickfont=dict(color=MUTED, size=11))
    fig.update_yaxes(showgrid=ygrid, gridcolor=GRID, gridwidth=1, zeroline=False,
                      linecolor=BASELINE, tickfont=dict(color=INK2, size=11.5))
    return fig


def fig_channel_score():
    df = pd.read_csv(TABLES / "seller_channel_scorecard.csv", index_col=0)
    df = df[df.index != "unknown"].sort_values("channel_value_score")
    colors = [SKY] * len(df)
    colors[-1] = AMBER  # emphasize the top actionable channel
    fig = go.Figure(go.Bar(
        x=df["channel_value_score"], y=df.index, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.2f}" for v in df["channel_value_score"]],
        textposition="outside", textfont=dict(color=INK2, size=11.5),
        width=0.55,
        customdata=df[["mql_count", "win_rate", "median_gmv_if_activated"]].values,
        hovertemplate="<b>%{y}</b><br>Value score: %{x:.2f}<br>MQLs: %{customdata[0]:,.0f}"
                      "<br>Win rate: %{customdata[1]:.1%}<br>Median activated GMV: R$%{customdata[2]:,.0f}"
                      "<extra></extra>",
    ))
    fig.update_layout(**BASE_LAYOUT, title=dict(
        text="<b>Seller-Acquisition Channel Value Score</b><br>"
             "<span style='color:#7d99aa;font-size:11px'>win rate x activation rate x GMV per lead "
             "· \"unknown\" origin excluded (not actionable)</span>", x=0.02, font=dict(size=14)))
    fig.update_xaxes(range=[0, max(df["channel_value_score"]) * 1.28])
    style_axes(fig)
    fig.update_layout(height=330)
    return fig


def fig_funnel():
    df = pd.read_csv(TABLES / "seller_channel_scorecard.csv", index_col=0)
    df = df.sort_values("mql_count", ascending=True)
    fig = go.Figure()
    for col, color, label in [("mql_count", LIGHT, "MQLs (leads)"),
                                ("won_count", SKY, "Won"),
                                ("activated_count", AMBER, "Activated (sold)")]:
        fig.add_trace(go.Bar(
            y=df.index, x=df[col], orientation="h", name=label,
            marker=dict(color=color), width=0.24,
            hovertemplate=f"<b>%{{y}}</b><br>{label}: " + "%{x:,.0f}<extra></extra>",
        ))
    fig.update_layout(**{**BASE_LAYOUT, "showlegend": True, "margin": dict(l=10, r=10, t=90, b=10)},
        barmode="group",
        legend=dict(orientation="h", y=1.2, x=0, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        title=dict(text="<b>Seller Funnel by Channel</b>", x=0.02, font=dict(size=14)))
    style_axes(fig)
    fig.update_layout(height=330)
    return fig


def fig_cohorts():
    df = pd.read_csv(TABLES / "cohort_cumulative_ltv.csv")
    df["cohort_month"] = df["cohort_month"].astype(str)
    sizes = df.groupby("cohort_month")["cohort_customers"].first()
    keep = sorted(sizes[sizes >= 200].index)
    fig = go.Figure()
    n = len(keep)
    for i, c in enumerate(keep):
        sub = df[(df.cohort_month == c) & (df.months_since_first <= 12)].sort_values("months_since_first")
        shade = SEQ_LINE[min(int(i / max(n - 1, 1) * (len(SEQ_LINE) - 1)), len(SEQ_LINE) - 1)]
        fig.add_trace(go.Scatter(
            x=sub.months_since_first, y=sub.cum_margin_per_customer, mode="lines",
            line=dict(color=shade, width=1.8), name=c, showlegend=False,
            hovertemplate=f"Cohort {c}<br>" + "Month %{x}: R$%{y:.2f}<extra></extra>",
        ))
    fig.update_layout(**BASE_LAYOUT,
        title=dict(text="<b>Customer Cohort Value Curves</b><br>"
                        "<span style='color:#7d99aa;font-size:11px'>cumulative freight-adjusted margin per customer "
                        "· lighter = earlier cohort, darker = more recent · flattens almost immediately</span>",
                   x=0.02, font=dict(size=14)))
    fig.update_xaxes(title=dict(text="Months since first purchase", font=dict(size=11, color=MUTED)))
    fig.update_yaxes(title=dict(text="Cumulative margin (R$)", font=dict(size=11, color=MUTED)))
    style_axes(fig, ygrid=True)
    fig.update_layout(height=360)
    return fig


def fig_repeat_share():
    stats = pd.read_csv(TABLES / "customer_repeat_stats.csv", index_col=0).squeeze("columns")
    one_time, repeat = float(stats["one_time_share"]), float(stats["repeat_share"])
    fig = go.Figure()
    fig.add_trace(go.Bar(y=["Customers"], x=[one_time], orientation="h", name="One-time",
                          marker=dict(color=LIGHT), width=0.5,
                          text=[f"One-time  {one_time:.1%}"], textposition="inside", insidetextanchor="middle",
                          textfont=dict(color=INK2, size=13),
                          hovertemplate=f"One-time buyers: {one_time:.1%}<extra></extra>"))
    fig.add_trace(go.Bar(y=["Customers"], x=[repeat], orientation="h", name="Repeat",
                          marker=dict(color=AMBER), width=0.5,
                          hovertemplate=f"Repeat buyers: {repeat:.1%}<extra></extra>"))
    fig.add_annotation(x=one_time + repeat, y="Customers", xanchor="left", xshift=8,
                       text=f"<b>Repeat {repeat:.1%}</b>", showarrow=False,
                       font=dict(color=AMBER, size=13))
    fig.update_layout(**BASE_LAYOUT, barmode="stack",
        title=dict(text="<b>Customer Repeat-Purchase Share</b>", x=0.02, font=dict(size=14)))
    fig.update_xaxes(visible=False, range=[0, 1.22])
    fig.update_yaxes(visible=False)
    fig.update_layout(margin=dict(l=10, r=10, t=36, b=10, pad=0), height=None)
    fig.update_layout(height=140)
    return fig


def _diverging_segment(name, title_extra, min_cell_note):
    df = pd.read_csv(TABLES / f"segment_economics_by_{name}.csv", index_col=0)
    median = df["avg_margin_pct"].median()
    df = df.sort_values("avg_margin_pct")
    show = pd.concat([df.head(6), df.tail(6)])
    delta = show["avg_margin_pct"] - median
    colors = [AMBER if d < 0 else SKY for d in delta]
    fig = go.Figure(go.Bar(
        x=delta, y=show.index.astype(str), orientation="h",
        marker=dict(color=colors), width=0.6,
        customdata=show[["avg_margin_pct", "n_items"]].values,
        hovertemplate="<b>%{y}</b><br>Margin: %{customdata[0]:.1%}<br>vs median: %{x:+.1%}"
                      "<br>Items: %{customdata[1]:,.0f}<extra></extra>",
    ))
    fig.add_vline(x=0, line=dict(color=BASELINE, width=1.5))
    fig.update_layout(**BASE_LAYOUT,
        title=dict(text=f"<b>{title_extra}</b><br>"
                        f"<span style='color:#7d99aa;font-size:11px'>margin vs {median:.1%} median · freight-adjusted, {min_cell_note}</span>",
                   x=0.02, font=dict(size=14)))
    style_axes(fig)
    fig.update_xaxes(tickformat="+.0%")
    return fig


def fig_category_margin():
    return _diverging_segment("category", "Category Margin vs Median", "n≥30 items")


def fig_state_margin():
    return _diverging_segment("state", "State Margin vs Median (freight-distance effect)", "n≥30 items")


def fig_propensity():
    df = pd.read_csv(TABLES / "propensity_model_performance.csv")
    df["label"] = df["product"].map(PRODUCT_NAMES).fillna(df["product"])
    df = df.sort_values("test_auc")
    shades = []
    for v in df["test_auc"]:
        idx = min(int((v - 0.8) / 0.2 * (len(SEQ) - 1)), len(SEQ) - 1)
        shades.append(SEQ[max(idx, 2)])
    fig = go.Figure(go.Bar(
        x=df["test_auc"], y=df["label"], orientation="h",
        marker=dict(color=shades), width=0.6,
        text=[f"{v:.2f}" for v in df["test_auc"]], textposition="outside",
        textfont=dict(color=INK2, size=10.5),
        customdata=df[["train_positives", "test_positives"]].values,
        hovertemplate="<b>%{y}</b><br>Out-of-time AUC: %{x:.3f}<br>Train positives: %{customdata[0]:,.0f}"
                      "<br>Test positives: %{customdata[1]:,.0f}<extra></extra>",
    ))
    fig.add_vline(x=0.5, line=dict(color=MUTED, width=1, dash="dash"),
                  annotation_text="random", annotation_font=dict(size=10, color=MUTED),
                  annotation_position="bottom", annotation_yshift=-4,
                  annotation_bgcolor=SURFACE)
    fig.update_layout(**BASE_LAYOUT,
        title=dict(text="<b>Cross-Sell Propensity: Out-of-Time AUC by Product</b><br>"
                        "<span style='color:#7d99aa;font-size:11px'>trained through Feb 2016, tested Mar–May 2016 "
                        "· 16 of 24 products (8 too rare to model, dropped)</span>",
                   x=0.02, font=dict(size=14)))
    fig.update_xaxes(range=[0.4, 1.08])
    style_axes(fig)
    fig.update_layout(height=460)
    fig.update_layout(height=360)
    fig.update_layout(height=360)
    return fig


CHART_BUILDERS = [
    ("channel_score", fig_channel_score),
    ("funnel", fig_funnel),
    ("cohorts", fig_cohorts),
    ("repeat_share", fig_repeat_share),
    ("category_margin", fig_category_margin),
    ("state_margin", fig_state_margin),
    ("propensity", fig_propensity),
]

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parents[1] / "outputs" / "chart_fragments"
    out_dir.mkdir(exist_ok=True)
    for name, builder in CHART_BUILDERS:
        fig = builder()
        fig.write_html(out_dir / f"{name}.html", include_plotlyjs=False, full_html=False,
                        config={"displayModeBar": False, "responsive": True})
        print("built", name)
