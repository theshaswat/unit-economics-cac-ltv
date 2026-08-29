# Executive Summary — Unit Economics: CAC, LTV & Cross-Sell Propensity

**Author:** Shaswat Sharma ([github.com/theshaswat](https://github.com/theshaswat))

## The Headline

**Paid search is a stronger acquisition channel than organic search once you
look past lead volume to activated revenue.** Over half of "won" sellers
never sell a single item. Customer lifetime value is almost entirely a
**first-purchase** number, since 97.0% of customers never return. And freight
cost on its own explains why electronics and remote-state orders come in far
below the platform's average margin.

## Four Findings, Each With a Number

**1. Channel quality ≠ channel volume.** Organic search brings in the most
leads (2,296 MQLs) but paid search converts more efficiently once activation
and realised GMV are counted (channel value score 0.71 vs 0.63). Referral
leads are rare (284) but each is worth roughly 2-3x the median activated
seller (R$1,368 vs R$512-640).

**2. Winning a seller is not the same as activating one.** 842 of 8,000 MQLs
became sellers (10.5% win rate), but only 379 of those 842 (45.0%) ever sold
anything in the observed window. Any channel-ROI conversation that stops at
"win rate" is measuring the wrong thing.

**3. LTV growth almost stops after month 0.** Cohort cumulative margin per
customer moves from R$111.41 at first purchase to R$123.45 by month 12 — a
10.8% lift over a full year, produced entirely by the 3.0% of customers who
buy again. That is what a marketplace checkout with no loyalty program looks
like, and it points at retention as the lever, not lifetime-value expansion
among existing repeat buyers.

**4. Freight, not price, decides who is profitable.** Electronics is a
high-volume category (2,755 items, R$157k GMV) at only 31.5% margin because
freight eats 68.6% of price — vs. 83.0% margin on watches_gifts, a
comparably-sized category. The same pattern repeats geographically: São
Paulo (where most sellers are based) runs 73.5% margin; Amazon-region states
(RO, RR) run ~40%, purely from distance-driven freight cost.

## What This Doesn't Claim

There is no dollar CAC or payback period here. Olist doesn't disclose
marketing spend by channel, and no outside benchmark was substituted for it
(see `docs/seller_cac_methodology.md`). No payment-processing fee or platform
take-rate is netted into any margin figure (see
`docs/margin_proxy_definition.md`).

## Cross-Sell Propensity

A logistic model on an out-of-time split (train through Feb 2016, test
Mar–May 2016) predicts next-product adoption with AUC 0.85–1.00 across 16 of
24 Santander products. The other 8 had too few positive cases to score
meaningfully and were dropped. The output is a ranked top-3 next-best-product list
per customer — see `outputs/tables/cross_sell_ranked_list_sample.csv`.
