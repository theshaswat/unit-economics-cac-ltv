# Why This Project Reports Channel Value, Not a Dollar CAC

The obvious thing to compute from an acquisition funnel is CAC by channel
with a payback period. Olist's public Marketing Funnel dataset gives lead
volume, channel labels and win outcomes — but not marketing spend by channel,
and no other public source discloses it either.

So there is no denominator, and a CAC figure here would have to come from
somewhere other than this business. Importing a generic cost-per-lead
benchmark (a US SaaS marketing report, say) and presenting it as Olist's
economics would produce a confident-looking number that means nothing.
Channels are ranked on the disclosed quantities instead:

| Metric | Source |
|---|---|
| MQL volume by channel | `olist_marketing_qualified_leads_dataset.csv` |
| Win rate (MQL -> closed deal) | joined MQL + closed deals |
| Activation rate (won seller sold something) | joined to `order_items` |
| GMV per activated seller | `order_items` price |
| `channel_value_score` | min-max normalised blend of the three rates above |

**Read `channel_value_score` as a ranking, not a currency figure.** It
answers "which channel should get more budget" without pretending to know
what a lead costs.
