# Data Dictionary

## Part A — Seller Funnel (`data/final/seller_funnel.parquet`)

| Column | Type | Meaning |
|---|---|---|
| mql_id | str | Marketing Qualified Lead identifier |
| first_contact_date | date | Date the lead entered the funnel |
| origin | str | Acquisition channel: organic_search, paid_search, social, direct_traffic, email, referral, display, other, other_publicities, unknown |
| seller_id | str | Populated only if the MQL closed as a seller |
| won_date | date | Date the deal closed (seller_id != null) |
| won | bool | seller_id is not null |
| gmv | float | Total item price sold by this seller across all their orders in the observed data window |
| n_orders | int | Distinct orders containing this seller's items |
| activated | bool | won AND gmv > 0 |

## Part B — Customer Cohort Orders (`data/final/customer_orders_dated.parquet`)

| Column | Type | Meaning |
|---|---|---|
| customer_unique_id | str | Deduplicated customer identifier (Olist issues a new `customer_id` per order; this is the stable person-level key) |
| order_id | str | Order identifier |
| order_purchase_timestamp | datetime | When the order was placed |
| order_price / order_freight / order_margin | float | Summed across all items in the order; margin = price − freight |
| cohort_date / cohort_month | datetime / period | This customer's first-ever purchase date/month |
| months_since_first | int | Calendar months between this order and the customer's cohort month |

## Part C — Segment Economics (`outputs/tables/segment_economics_by_*.csv`)

| Column | Type | Meaning |
|---|---|---|
| n_items | int | Order-items in this segment (cells under 30 are dropped — see `MIN_CELL` in `src/segments.py`) |
| avg_margin_pct | float | Mean of (price − freight) / price across items in the segment |
| avg_freight_pct | float | Mean of freight / price |
| avg_weight_g | float | Mean disclosed product weight (category table only) |

## Part D — Propensity Model (`outputs/tables/propensity_model_performance.csv`, `cross_sell_ranked_list_sample.csv`)

| Column | Type | Meaning |
|---|---|---|
| product | str | Santander `ind_*_ult1` product code — see `src/product_names.py` for the human-readable mapping |
| train_positives / test_positives | int | Customers who added the product in-window, train vs. out-of-time test period |
| test_auc | float | Held-out AUC on the strictly-later test period |
| ncodpers | int | Customer identifier |
| propensity | float | Predicted probability of adding this product next month |

## Raw Source Files

See `reports/03_SOURCE_REGISTER.md` for every raw file, its origin, license,
and retrieval date.
