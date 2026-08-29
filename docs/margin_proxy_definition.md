# Contribution Margin Proxy — Exact Definition

Everywhere this project reports "contribution margin" or "margin %" on a customer,
cohort, category, or state, it means exactly:

```
contribution_margin = item_price - freight_value
margin_pct          = contribution_margin / item_price
```

Both `price` and `freight_value` are fields Olist discloses directly in
`olist_order_items_dataset.csv` for every line item. No other number is
combined into this margin.

## What this explicitly does NOT include

- **Payment processing fees** — not disclosed by Olist anywhere in the public
  dataset. Brazilian card-acquiring rates vary by installment count and are
  not attributable per-order here, so no rate is assumed or netted in.
- **Olist's marketplace commission / take-rate** — not publicly disclosed.
  All GMV and margin figures in this project are at **item/seller level**,
  not "revenue to Olist."
- **Seller's own product cost (COGS)** — Olist is a marketplace; it does not
  disclose what a seller paid for the goods it lists.

## Why freight-only, and not a fuller P&L

Freight is the largest disclosed non-price cost, and it varies systematically
by geography and product weight — which turns out to be the dominant driver
of the profitability differences reported here (see
`outputs/tables/segment_economics_by_category.csv` and `..._by_state.csv`).

A payment-fee or take-rate assumption layered on top would move every margin
number by roughly the same amount without changing any of the comparisons,
so it would add decimal places rather than information.

**Read every margin number in this project as "freight-adjusted contribution
margin," not "net profit."**
