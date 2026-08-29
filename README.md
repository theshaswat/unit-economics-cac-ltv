# Unit Economics: CAC, LTV & Cross-Sell Propensity

Which acquisition channel is worth more, why customer lifetime value barely
moves after the first purchase, which segments lose money once freight is
netted out, and which product a customer is likely to buy next.

## Core Question

A marketplace has a seller-acquisition funnel, a customer base, and a
catalogue spanning dozens of categories and every region of the country.
Which acquisition channel deserves more budget, which customer/product/region
segments are quietly unprofitable, and can next-purchase behaviour be
predicted well enough to run a cross-sell program?

## Glossary

| Term | Meaning |
|---|---|
| MQL | Marketing Qualified Lead — a prospective seller who entered the funnel via a tracked channel |
| Win rate | Share of MQLs that become a signed, live seller |
| Activation | A won seller who actually sold at least one item on the platform (winning is not the same as producing revenue) |
| GMV | Gross Merchandise Value — total item price sold, before any costs |
| Contribution margin (this project) | `item price - freight value` only — see [`docs/margin_proxy_definition.md`](docs/margin_proxy_definition.md) for exactly what this excludes |
| Cohort | Customers grouped by the calendar month of their first purchase |
| Out-of-time split | Model trained on earlier months, tested on strictly later months — never a random split on time-ordered data |
| Propensity score | Predicted probability a customer adds a specific product next month, given they don't already have it |

## Key Findings

| Finding | Value |
|---|---|
| Order items analysed | 112,650 (98,666 orders), Sep 2016 – Oct 2018 |
| Total GMV / freight-adjusted margin | R$13.59M / 83.4% overall |
| Best acquisition channel (excl. "unknown") | **paid_search** — channel value score 0.71, beats organic_search (0.63) |
| Overall seller-funnel win rate | 10.5% (842 of 8,000 MQLs) |
| Won sellers who never actually sold anything | **55.0%** (463 of 842) — winning ≠ activation |
| Customer repeat-purchase share | **3.0%** — 97.0% of customers buy exactly once |
| Cohort value growth, month 0 → month 12 | R$111.41 → R$123.45 per customer (**+10.8%**, almost entirely from the 3% who return) |
| Worst-margin high-volume category | **electronics** — 31.5% margin, freight consumes 68.6% of price |
| Best-margin high-volume category | **watches_gifts** — 83.0% margin on R$1.20M GMV |
| Worst-margin states | RO, RR (Amazon-region) — ~40% margin, freight >59% of price |
| Best-margin state | SP (São Paulo, where most sellers are based) — 73.5% margin |
| Cross-sell propensity model | 16 of 24 products modelled (8 too rare to score, skipped) |
| Propensity model performance | Out-of-time test AUC 0.85 – 1.00 across products (median ~0.91) |

## Deliverables

- **Interactive dashboard:** [`dashboards/p09_dashboard.html`](dashboards/p09_dashboard.html) — open directly in any browser, no server needed
- **Recommendation memo:** [`reports/01_RECOMMENDATION_MEMO.md`](reports/01_RECOMMENDATION_MEMO.md)
- **Executive summary:** [`reports/00_EXECUTIVE_SUMMARY.md`](reports/00_EXECUTIVE_SUMMARY.md)
- **Charts:** `outputs/charts/` — channel scorecard, funnel, cohort curves, repeat share, category/state margin, propensity AUC
- **Full source register + methodology notes:** [`reports/03_SOURCE_REGISTER.md`](reports/03_SOURCE_REGISTER.md), [`docs/`](docs/)
- **Engine:** `src/*.py` (each module runs standalone) + `notebooks/` (same logic, walkthrough form)

## Methodology

Two datasets, because no single public one carries both a multi-product
repeat-customer panel and an acquisition funnel with channel and outcome
data attached:

1. **Olist Brazilian E-Commerce + Marketing Funnel** (CC BY-NC-SA) — the
   seller-acquisition funnel (Part A), customer cohort economics (Part B),
   and segment margin analysis (Part C).
2. **Santander Product Recommendation panel** (1.5 years, ~950k customers,
   24 products) — the cross-sell propensity model (Part D). Olist customers
   don't repeat-purchase often enough to model product-holding transitions.

Two things this analysis does not compute, both because the input isn't
disclosed:

- **No dollar CAC.** Olist's marketing spend by channel isn't public
  anywhere, so channels are ranked on a composite of what is disclosed —
  win rate, activation rate, GMV per lead. See
  [`docs/seller_cac_methodology.md`](docs/seller_cac_methodology.md).
- **No payment fees or platform take-rate in margin.** "Contribution margin"
  here means `price − freight`, nothing else. See
  [`docs/margin_proxy_definition.md`](docs/margin_proxy_definition.md).

The propensity model trains on data through February 2016 and is evaluated
on March–May 2016 (out-of-time split). Products with fewer than 30 training
positives or 5 test positives were dropped rather than scored on too little
signal — 8 of 24 fell out on that rule.

## Data

- Olist Brazilian E-Commerce Public Dataset (olistbr/brazilian-ecommerce, CC BY-NC-SA 4.0)
- Olist Marketing Funnel (olistbr/marketing-funnel-olist, CC BY-NC-SA 4.0)
- Santander Product Recommendation dataset (public bank panel; original Kaggle
  competition data, mirrored as `padmanabhanporaiyar/santander-product-recommendation-parquet-data`)

Full provenance, license terms, and retrieval dates: [`reports/03_SOURCE_REGISTER.md`](reports/03_SOURCE_REGISTER.md).

## Limitations & Assumptions

See [`reports/LIMITATIONS.md`](reports/LIMITATIONS.md) for the complete list.
Headline items:
- Seller-side and customer-side analyses sit on the same platform but cover
  two separate populations (sellers vs. buyers). Nothing here models an
  interaction between them.
- The propensity model runs on a random 120,000-customer sample of the
  ~950,000-customer panel, for tractability. Sampling is uniform over
  customer IDs, but transition rates were not re-validated against the full
  panel.
- No payment-processing fee or platform commission is netted into any margin
  figure — see `docs/margin_proxy_definition.md`.

## Author

**Shaswat Sharma** — [GitHub: theshaswat](https://github.com/theshaswat)

## License

Code: MIT (see [`LICENSE`](LICENSE)). The datasets keep their own licenses;
terms and retrieval dates are in
[`reports/03_SOURCE_REGISTER.md`](reports/03_SOURCE_REGISTER.md).
