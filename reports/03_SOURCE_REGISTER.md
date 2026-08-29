# Source Register

| File(s) | Source | License | Retrieved |
|---|---|---|---|
| `olist_customers_dataset.csv`, `olist_orders_dataset.csv`, `olist_order_items_dataset.csv`, `olist_order_payments_dataset.csv`, `olist_products_dataset.csv`, `product_category_name_translation.csv` | Kaggle: `olistbr/brazilian-ecommerce` — "Brazilian E-Commerce Public Dataset by Olist" | CC BY-NC-SA 4.0 | 2026-08-29, via Kaggle API |
| `olist_marketing_qualified_leads_dataset.csv`, `olist_closed_deals_dataset.csv` | Kaggle: `olistbr/marketing-funnel-olist` — "Marketing Funnel by Olist" | CC BY-NC-SA 4.0 | 2026-08-29, via Kaggle API |
| Santander product-holding panel (`parquet_files/part.*.parquet`) | Kaggle: `padmanabhanporaiyar/santander-product-recommendation-parquet-data` — a parquet re-upload of the original "Santander Product Recommendation" Kaggle competition dataset (Banco Santander, 2016) | Original competition data; this re-upload lists no additional restriction | 2026-08-29, via Kaggle API |

## Notes on Provenance

- Both Olist datasets come from the **same organisation** (Olist) and cover
  overlapping but not identical entities: the e-commerce dataset is
  buyer/order-side, the marketing funnel dataset is seller-acquisition-side.
  They are joined in this project only through `seller_id` (Part A), never
  by assuming a buyer-side record implies anything about the funnel.
- The Santander dataset is unrelated to Olist (different company, country,
  and business) and is used **only** for Part D (cross-sell propensity),
  where a multi-product repeat-customer panel is needed and Olist's own
  data cannot supply one (97% one-time buyers — see README).
- No web scraping was used anywhere in this project. All data was retrieved
  through Kaggle's official API from datasets/competitions the account
  authenticated against.
- The source Kaggle dataset also ships `olist_order_reviews_dataset.csv`,
  `olist_sellers_dataset.csv`, and `olist_geolocation_dataset.csv`. None of
  the four parts (A-D) reads them, so they are not retained in this repo —
  dropped to keep the repo small.
