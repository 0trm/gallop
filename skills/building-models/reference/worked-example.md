# Worked example: a ticket-pricing model

The checks in this skill, run on
[dynamic-pricing](https://github.com/0trm/dynamic-pricing): a demand
forecast (one Prophet model per match and seating zone, plus an XGBoost on
its residuals) feeding a grid search for the revenue-maximising price.
The data is synthetic, so the true demand curve is known, and every number
below comes from `make evaluate` in that repo.

## Is this a model's decision?

Yes on all three counts. A price is set per zone, per day, for every
match: a decision made continuously. The outcome (tickets sold) comes from
the ticketing system, the trusted source. And there are 3,367 zone-days of
history across 10 matches, enough for an out-of-time window of 518 rows.

## Split by time, screen for leakage

The holdout is the last 14 days before each match; every model is refit on
the days before. One feature failed the leakage screen:
`web_conversion_rate` is sales divided by visits, so it is the outcome
wearing a ratio. It is dropped. Same-day web traffic passed: replacing it
with yesterday's value moves WAPE by 0.8 points.

## Beat the naive, not a straw man

The repo's first baseline was the global mean, which every model beats
(WAPE 79.7%). The baseline that matters is the forecast anyone could make
at the cutoff without a model: each series' average over its last 7 days.

| Model | WAPE | MAE vs. cutoff naive | In-sample MASE |
| :--- | :--- | :--- | :--- |
| Ensemble (Prophet + XGBoost) | 26.4% | 0.71 | 2.29 |
| XGBoost alone, on sales | 22.6% | 0.60 | 1.96 |
| Prophet alone | 41.8% | 1.12 | 3.63 |
| Naive: last 7 days | 37.4% | 1.00 | 3.25 |

Two lessons. Prophet alone loses to the naive, so the per-series stage
earns its place only through the residual model. And in-sample MASE puts
every model above 1, the cutoff naive included: the test window is the run
into the match, where daily sales swing far more than in the early days
that set MASE's scale. The verdict comes from the right-hand comparison
the forecast-baselines reference asks for, not from MASE.

## Validate the decision, not only the forecast

The model's job is a price. Scoring each recommended price against the
true demand curve found the optimiser searching up to 2.5x the base price
while no training row was priced above 1.91x. Past the data the trees
predict flat sales, revenue keeps rising with price, and 42% of
recommendations landed at the cap, earning 45% of the best achievable
revenue. Restricting the search to each zone's observed 5th to 95th
percentile of prices lifted that to 95%. Forecast accuracy did not move;
the decision did.

## The case the split hides

Splitting by date inside each series never shows the model a match it has
not seen, but that is how a new fixture is priced on the day it goes on
sale. Leaving one match out at a time: per-series Prophet has no model for
it, and the ensemble's WAPE goes to 89.8%. A pooled XGBoost fallback for
series without history brings it to 12.5%, with 94% of the best achievable
revenue.

## What stays open

The impact claim belongs to an experiment, not to these numbers: in
production the engine was judged by a holdout of seating zones on static
prices. Randomising by zone inside one stadium invites interference (fans
move between zones when prices diverge), which is the case the
randomisation-unit reference in `designing-experiments` covers.
