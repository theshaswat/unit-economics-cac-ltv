"""
Part C -- Segment-level economics.

Which customer segments (state, product category) are actually margin-negative
once real freight cost is netted against real item price? No fabricated cost
components (payment fees, COGS) are added -- see docs/margin_proxy_definition.md
for exactly what "contribution margin" means here and what it excludes.
"""
import pandas as pd
from config import OLIST, TABLES


MIN_CELL = 30  # minimum order-items per segment cell to report (avoid noise)


def build_segment_economics():
    orders = pd.read_csv(OLIST / "olist_orders_dataset.csv")
    customers = pd.read_csv(OLIST / "olist_customers_dataset.csv")
    items = pd.read_csv(OLIST / "olist_order_items_dataset.csv")
    payments = pd.read_csv(OLIST / "olist_order_payments_dataset.csv")
    products = pd.read_csv(OLIST / "olist_products_dataset.csv")
    cat_map = pd.read_csv(OLIST / "product_category_name_translation.csv")

    valid_status = {"delivered", "shipped", "invoiced", "processing", "approved"}
    orders = orders[orders.order_status.isin(valid_status)]

    df = (items.merge(orders[["order_id", "customer_id"]], on="order_id")
                .merge(customers[["customer_id", "customer_state"]], on="customer_id")
                .merge(products[["product_id", "product_category_name",
                                  "product_weight_g"]], on="product_id", how="left")
                .merge(cat_map, on="product_category_name", how="left"))

    df["category"] = df["product_category_name_english"].fillna(df["product_category_name"]).fillna("unknown")
    df["contribution_margin"] = df["price"] - df["freight_value"]
    df["margin_pct"] = df["contribution_margin"] / df["price"]
    df["freight_pct_of_price"] = df["freight_value"] / df["price"]

    # --- by category ---
    by_cat = df.groupby("category").agg(
        n_items=("order_id", "count"),
        total_price=("price", "sum"),
        total_freight=("freight_value", "sum"),
        total_margin=("contribution_margin", "sum"),
        avg_margin_pct=("margin_pct", "mean"),
        avg_freight_pct=("freight_pct_of_price", "mean"),
        avg_weight_g=("product_weight_g", "mean"),
    ).query(f"n_items >= {MIN_CELL}").sort_values("avg_margin_pct")
    by_cat.round(4).to_csv(TABLES / "segment_economics_by_category.csv")

    # --- by state ---
    by_state = df.groupby("customer_state").agg(
        n_items=("order_id", "count"),
        total_price=("price", "sum"),
        total_freight=("freight_value", "sum"),
        total_margin=("contribution_margin", "sum"),
        avg_margin_pct=("margin_pct", "mean"),
        avg_freight_pct=("freight_pct_of_price", "mean"),
    ).query(f"n_items >= {MIN_CELL}").sort_values("avg_margin_pct")
    by_state.round(4).to_csv(TABLES / "segment_economics_by_state.csv")

    return by_cat, by_state


if __name__ == "__main__":
    by_cat, by_state = build_segment_economics()
    print("=== Worst 5 categories by margin % ===")
    print(by_cat.head(5)[["n_items", "avg_margin_pct", "avg_freight_pct", "avg_weight_g"]])
    print()
    print("=== Best 5 categories by margin % ===")
    print(by_cat.tail(5)[["n_items", "avg_margin_pct", "avg_freight_pct", "avg_weight_g"]])
    print()
    print("=== Worst 5 states by margin % ===")
    print(by_state.head(5)[["n_items", "avg_margin_pct", "avg_freight_pct"]])
    print()
    print("=== Best 5 states by margin % ===")
    print(by_state.tail(5)[["n_items", "avg_margin_pct", "avg_freight_pct"]])
