"""
Part B -- Customer-side cohort economics.

Olist customers are overwhelmingly one-time buyers (no loyalty programme,
no subscription -- it's a marketplace checkout). This module builds a real
cohort table indexed on calendar months since first purchase, using only
disclosed figures:

    contribution margin proxy = item price - freight cost

(both fields Olist discloses per order-item; no assumed take-rate or
payment-fee coefficient is injected -- see docs/margin_proxy_definition.md).

The headline finding here is expected to be a clean, honest one: cohort
value flattens almost immediately after month 0 because most customers never
return. That is reported as a finding, not hidden.
"""
import pandas as pd
from config import OLIST, FINAL, TABLES


def build_customer_cohorts():
    orders = pd.read_csv(OLIST / "olist_orders_dataset.csv",
                          parse_dates=["order_purchase_timestamp"])
    customers = pd.read_csv(OLIST / "olist_customers_dataset.csv")
    items = pd.read_csv(OLIST / "olist_order_items_dataset.csv")
    products = pd.read_csv(OLIST / "olist_products_dataset.csv")
    cat_map = pd.read_csv(OLIST / "product_category_name_translation.csv")

    valid_status = {"delivered", "shipped", "invoiced", "processing", "approved"}
    orders = orders[orders.order_status.isin(valid_status)]

    df = (items.merge(orders[["order_id", "customer_id", "order_purchase_timestamp"]], on="order_id")
                .merge(customers[["customer_id", "customer_unique_id", "customer_state"]], on="customer_id")
                .merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
                .merge(cat_map, on="product_category_name", how="left"))

    df["contribution_margin"] = df["price"] - df["freight_value"]

    # order-level revenue (one row per order) for cohort math
    order_rev = df.groupby(["customer_unique_id", "order_id", "order_purchase_timestamp"]).agg(
        order_price=("price", "sum"),
        order_freight=("freight_value", "sum"),
        order_margin=("contribution_margin", "sum"),
    ).reset_index()

    first_purchase = order_rev.groupby("customer_unique_id")["order_purchase_timestamp"].min().rename("cohort_date")
    order_rev = order_rev.merge(first_purchase, on="customer_unique_id")
    order_rev["cohort_month"] = order_rev["cohort_date"].dt.to_period("M")
    order_rev["order_month"] = order_rev["order_purchase_timestamp"].dt.to_period("M")
    order_rev["months_since_first"] = (
        (order_rev["order_month"] - order_rev["cohort_month"]).apply(lambda p: p.n)
    )

    order_rev.to_parquet(FINAL / "customer_orders_dated.parquet", index=False)

    # cohort size (customers) per cohort_month
    cohort_size = first_purchase.dt.to_period("M").value_counts().sort_index()
    cohort_size = cohort_size.rename_axis("cohort_month").rename("cohort_customers")

    # cumulative contribution margin per cohort, indexed on months_since_first
    cum = (order_rev.groupby(["cohort_month", "months_since_first"])["order_margin"]
                     .sum().groupby(level=0).cumsum().reset_index())
    cum = cum.merge(cohort_size, on="cohort_month")
    cum["cum_margin_per_customer"] = cum["order_margin"] / cum["cohort_customers"]

    cum.to_csv(TABLES / "cohort_cumulative_ltv.csv", index=False)

    # repeat-rate headline stat
    orders_per_customer = order_rev.groupby("customer_unique_id").size()
    repeat_stats = {
        "total_customers": int(orders_per_customer.shape[0]),
        "one_time_share": float((orders_per_customer == 1).mean()),
        "repeat_share": float((orders_per_customer > 1).mean()),
        "avg_orders_repeat_customers": float(orders_per_customer[orders_per_customer > 1].mean()),
        "month0_avg_margin_per_customer": float(
            cum[cum.months_since_first == 0]["cum_margin_per_customer"].mean()),
        "month6_avg_margin_per_customer": float(
            cum[cum.months_since_first == 6]["cum_margin_per_customer"].mean()
        ) if (cum.months_since_first == 6).any() else None,
        "month12_avg_margin_per_customer": float(
            cum[cum.months_since_first == 12]["cum_margin_per_customer"].mean()
        ) if (cum.months_since_first == 12).any() else None,
    }
    pd.Series(repeat_stats).to_csv(TABLES / "customer_repeat_stats.csv")

    return df, order_rev, cum, repeat_stats


if __name__ == "__main__":
    df, order_rev, cum, stats = build_customer_cohorts()
    print(stats)
    print()
    print(cum[cum.months_since_first.isin([0, 1, 3, 6, 12])].groupby("months_since_first")["cum_margin_per_customer"].mean())
