"""
Part A -- Seller-side acquisition funnel.

Olist's Marketing Funnel dataset tracks how Olist recruits sellers onto its
marketplace: a Marketing Qualified Lead (MQL) arrives via a channel, a sales
rep works it, and it either closes into a live seller or doesn't.

Channel, lead volume and win rate are all disclosed. Marketing spend by
channel is not, anywhere in the public data, so there's no dollar CAC to
compute here. Channels are ranked instead on what the data does give us:

    lead volume  x  win rate  x  activation rate  x  realized seller value

See docs/seller_cac_methodology.md for the reasoning.
"""
import pandas as pd
from config import OLIST, OLIST_MKT, FINAL, TABLES


def build_seller_funnel():
    mql = pd.read_csv(OLIST_MKT / "olist_marketing_qualified_leads_dataset.csv",
                       parse_dates=["first_contact_date"])
    deals = pd.read_csv(OLIST_MKT / "olist_closed_deals_dataset.csv",
                         parse_dates=["won_date"])
    items = pd.read_csv(OLIST / "olist_order_items_dataset.csv")
    orders = pd.read_csv(OLIST / "olist_orders_dataset.csv",
                          parse_dates=["order_purchase_timestamp"])

    mql["origin"] = mql["origin"].fillna("unknown")
    funnel = mql.merge(deals[["mql_id", "seller_id", "won_date", "business_segment",
                               "lead_type", "business_type"]],
                        on="mql_id", how="left")
    funnel["won"] = funnel["seller_id"].notna()

    # Seller-level GMV: join items -> orders to get purchase date, keep delivered/shipped/invoiced
    valid_status = {"delivered", "shipped", "invoiced", "processing", "approved"}
    ord_slim = orders[orders.order_status.isin(valid_status)][["order_id", "order_purchase_timestamp"]]
    items_dated = items.merge(ord_slim, on="order_id", how="inner")
    seller_gmv = items_dated.groupby("seller_id").agg(
        gmv=("price", "sum"),
        n_orders=("order_id", "nunique"),
        first_sale=("order_purchase_timestamp", "min"),
        last_sale=("order_purchase_timestamp", "max"),
    ).reset_index()

    funnel = funnel.merge(seller_gmv, on="seller_id", how="left")
    funnel["activated"] = funnel["won"] & funnel["gmv"].notna()
    funnel["gmv"] = funnel["gmv"].fillna(0.0)

    funnel.to_parquet(FINAL / "seller_funnel.parquet", index=False)

    # ---- Channel scorecard (all real, no fabricated cost) ----
    grp = funnel.groupby("origin")
    scorecard = pd.DataFrame({
        "mql_count": grp.size(),
        "won_count": grp["won"].sum(),
        "activated_count": grp["activated"].sum(),
        "median_gmv_if_activated": funnel[funnel.activated].groupby("origin")["gmv"].median(),
        "mean_gmv_if_activated": funnel[funnel.activated].groupby("origin")["gmv"].mean(),
        "total_gmv": grp["gmv"].sum(),
    }).fillna(0.0)

    scorecard["win_rate"] = scorecard["won_count"] / scorecard["mql_count"]
    scorecard["activation_rate_of_won"] = (scorecard["activated_count"] /
                                            scorecard["won_count"].replace(0, pd.NA))
    scorecard["gmv_per_mql"] = scorecard["total_gmv"] / scorecard["mql_count"]

    # Composite channel-value score: real, disclosed inputs only, min-max normalised
    for col in ["win_rate", "activation_rate_of_won", "gmv_per_mql"]:
        rng = scorecard[col].max() - scorecard[col].min()
        scorecard[f"{col}_norm"] = (scorecard[col] - scorecard[col].min()) / rng if rng else 0.0
    scorecard["channel_value_score"] = scorecard[
        ["win_rate_norm", "activation_rate_of_won_norm", "gmv_per_mql_norm"]
    ].mean(axis=1)

    scorecard = scorecard.sort_values("channel_value_score", ascending=False)
    scorecard.round(4).to_csv(TABLES / "seller_channel_scorecard.csv")

    return funnel, scorecard


if __name__ == "__main__":
    funnel, scorecard = build_seller_funnel()
    print(scorecard[["mql_count", "won_count", "win_rate", "activation_rate_of_won",
                      "gmv_per_mql", "channel_value_score"]])
    print()
    print(f"Total MQLs: {len(funnel)}  |  Won: {funnel.won.sum()}  |  "
          f"Activated (won AND sold something): {funnel.activated.sum()}")
