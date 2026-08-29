# Recommendation Memo

**To:** Marketplace growth & finance leadership
**From:** Shaswat Sharma
**Re:** Channel investment, segment pricing, and cross-sell targeting

## Recommendation

**Reallocate seller-acquisition spend toward paid_search and referral, away
from social and email; introduce freight-aware pricing or fulfilment changes
for electronics and remote-state orders; and stand up the cross-sell
propensity model as a targeting layer for the 16 products where it clears
AUC 0.85 out-of-time.**

## Why

**1. Channel reallocation.** Ranked on the disclosed metrics (win
rate x activation rate x GMV per lead — no assumed spend figure), paid_search
(score 0.71) and organic_search (0.63) outperform social (0.38) and email
(0.28) by a wide margin, and referral, while low-volume (284 leads), converts
at the highest per-seller value (median R$1,368 activated GMV). Since spend
by channel isn't disclosed, this is a reallocation-direction call, not a
"move R$X" call — see `docs/seller_cac_methodology.md` for exactly why.

**2. Activation, not just winning, needs its own funnel stage.** 55.0% of
won sellers never sell anything. A "won → activated" nudge program (onboarding
support, first-listing incentives) targeting this specific gap has a larger
addressable upside than further top-of-funnel spend, because it converts
sellers already paid for.

**3. Freight-aware category and geography strategy.** Electronics and
remote-state orders are structurally low-margin because of freight, not
price — a fixable operational problem (regional fulfilment, category-specific
shipping subsidy caps, or minimum-order-value thresholds for the worst
combinations) rather than a demand problem.

**4. Deploy the propensity model on the 16 products it actually supports.**
Junior Account, Funds, Mas Particular Account, Particular Plus Account,
Payroll, and Pensions all clear AUC 0.90+ out-of-time — strong enough for a
live ranked cross-sell list today. The 8 excluded products (too few positive
examples to score meaningfully) should get a simple rules-based fallback, not a
forced model.

## What Would Change This Recommendation

- If Olist's actual channel spend were disclosed and paid_search turned out
  to cost materially more per lead than its value-score advantage implies,
  the reallocation case would need re-testing against actual CAC, not the
  value-score proxy used here.
- If the "unknown" origin channel (currently the single highest scorer) were
  disaggregated into named channels, some of paid_search's relative advantage
  could shift — it is reported separately and excluded from the headline
  ranking for exactly this reason.
