# Limitations & Assumptions

## Seller-Funnel CAC (Part A)

- **No dollar CAC or payback period is computed.** Olist's marketing spend
  by channel is not disclosed in any public source. See
  `docs/seller_cac_methodology.md` for the full reasoning; the substitute
  metric (`channel_value_score`) is built only from disclosed
  quantities and should be read as a ranking, not a currency figure.
- The `unknown` origin channel scores highest on the composite metric but is,
  by definition, not an actionable channel to invest in — it is reported
  separately in the README/memo rather than folded into the headline
  recommendation.
- `gmv` per seller is measured only within the observed data window
  (through Oct 2018); sellers who joined late in the window have had less
  time to accumulate sales, which mechanically understates their GMV
  relative to earlier-joining sellers. This censoring is not corrected for
  here.

## Customer Cohort LTV (Part B)

- **Contribution margin = price − freight only.** No payment-processing fee
  or platform take-rate is netted in — neither is disclosed by Olist. See
  `docs/margin_proxy_definition.md`.
- Cohort curves beyond ~12 months thin out rapidly (later cohorts haven't
  had 12 months to observe) — charted curves stop at each cohort's actual
  observed horizon rather than extrapolating.

## Segment Economics (Part C)

- Segments with fewer than 30 order-items are dropped from the reported
  tables to avoid noise-driven "0% or 100% margin" cells from tiny samples
  (`MIN_CELL` in `src/segments.py`).
- COGS (seller's own product cost) is not disclosed anywhere in the dataset
  and is not part of any margin figure in this project — see
  `docs/margin_proxy_definition.md`.

## Cross-Sell Propensity (Part D)

- **120,000-customer sample**, not the full ~950,000-customer panel — a
  scope decision for laptop tractability, documented in `src/propensity.py`
  (`N_CUSTOMERS_SAMPLE`). Sampling is uniform random over customer IDs, so
  month-level transition rates are expected to be representative, but this
  was not formally re-validated against the full panel.
- **8 of 24 products were not modelled** (`ind_ahor_fin_ult1`,
  `ind_aval_fin_ult1`, `ind_cder_fin_ult1`, `ind_deco_fin_ult1`,
  `ind_deme_fin_ult1`, `ind_hip_fin_ult1`, `ind_pres_fin_ult1`,
  `ind_viv_fin_ult1`) because they had fewer than 30 training positives or 5
  test positives in the sampled panel — too rare to produce a reliable AUC.
  They are excluded from every propensity output rather than imputed.
- The model is a single logistic regression per product (not an ensemble) —
  chosen for interpretability and speed given the per-product training loop
  across 16 products; absolute AUC could likely be improved further with a
  gradient-boosted model, which was not necessary to establish the headline
  finding that out-of-time predictive signal is present and strong.
- Feature set is demographic + current product-holding only; no macro or
  seasonal (month-of-year) feature is included, so the model may not
  generalise to periods with different seasonality than Mar–May 2016.

## Cross-Cutting

- Olist's buyer-side data and seller-side (marketing funnel) data describe
  two different populations on the same platform. This project does not
  claim or model any interaction between a specific buyer and a specific
  seller's acquisition channel.
- All findings are descriptive of the historical window covered by each
  dataset (Olist: Sep 2016–Oct 2018; Santander: Jan 2015–May 2016) and are
  not forecasts of current performance.
