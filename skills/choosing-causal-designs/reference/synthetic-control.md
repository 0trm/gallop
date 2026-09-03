# Synthetic control

One treated unit, many untreated candidates. Build the counterfactual as a
weighted blend of donor units chosen so the blend tracks the treated unit's
pre-period closely; the effect is the post-period gap between the unit and
its synthetic twin.

## When it fits

- Exactly one (or very few) treated units: one country got the launch, one
  city got the policy.
- A donor pool of genuinely untreated units, plausibly driven by the same
  forces: other countries, other cities, other categories.
- A long pre-period over which a good fit can be established, and enough
  donors that the blend is not one unit wearing a hat (rule of thumb: 10+
  donors, 2+ years of pre-period for weekly data, less for high-frequency
  metrics).

Two units total is not a synthetic control; that is a comparison with one
donor, and it should be called DiD-with-one-control and given its weak
inference honestly.

## How to run it honestly

1. **Freeze the donor pool first**, excluding any unit the treatment could
   have touched (spillovers make donors dirty and the effect biased toward
   zero, or away from it if donors absorbed displaced demand).
2. **Fit weights on the pre-period only**, matching the outcome path (and
   optionally a few covariates). Report the pre-period fit; a synthetic
   twin that cannot track the past has no claim on the future. Weights are
   non-negative and sum to one, which keeps the twin an interpolation
   rather than an extrapolation, and makes it inspectable: name the donors
   and their weights in the readout.
3. **Inference by placebo**: run the same procedure on every donor as if
   it were treated. The treated unit's gap is credible only if it is
   extreme in that distribution (the permutation p-value is the honest
   one; with 20 donors, the best achievable is 1/21).
4. **Backdate placebo**: fit the twin on the first half of the pre-period,
   check it tracks the second half. A twin that fails backdating is
   overfit to noise.

## What breaks it

- **A shocked donor**: one donor gets its own event in the post-period and
  drags the twin. Inspect the twin's components over time.
- **Interpolation bias**: the treated unit sits outside the donor pool's
  range on a dimension that matters; the blend then matches the path
  without matching the mechanism.
- **Short pre-periods**: with little history, many weight vectors fit
  equally well and the choice among them is arbitrary; report the
  sensitivity across them.

## Stating the result

"Sell-out in the launch country ran 6% above its synthetic twin (0.4
Germany, 0.35 Netherlands, 0.25 Sweden) for the twelve post-launch weeks;
in placebo runs on the 14 donors, the largest gap was 2.8%, so the effect
is outside the noise distribution. Assumes no launch spillover into donor
markets." Twin, gap, placebo distribution, assumption.
