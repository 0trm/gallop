# Difference-in-differences

Some units got the change, some did not, and both are observed before and
after. The counterfactual for the treated units is their own pre-period
level plus the *untreated units' change over time*. The effect is
(treated after − treated before) − (untreated after − untreated before).

## When it fits

- Assignment varied across units for reasons unrelated to the outcome's
  trajectory: a rollout by market, a policy that hit one country, some CRM
  waves getting the change earlier.
- The identifying assumption: **parallel trends** – absent treatment, the
  treated units would have moved like the untreated ones. Untestable
  directly; the pre-period is the evidence.

## How to run it honestly

1. **Plot both groups' pre-trends first**, before any regression. If they
   were not moving together before, the design is dead on arrival, and no
   fixed effect resurrects it. This plot goes in the readout.
2. **The event-study version by default**: estimate a per-period effect
   relative to the switch, not one pooled number. Pre-period coefficients
   near zero are the parallel-trends check made visible; the post-period
   path shows whether the effect grows, fades, or is a one-time level
   shift.
3. **Cluster standard errors at the assignment unit** (market, country,
   wave). With few clusters (under ~20, and certainly at 2) the asymptotic
   errors are fiction; the design still stands, the inference is what
   weakens. Use wild-cluster bootstrap or say plainly that
   inference is weak. Two markets is not enough units for credible DiD
   inference; treat that case as ITS with a control series.
4. **Staggered adoption needs care**: with units treated at different
   times, the classic two-way fixed-effects estimate mixes already-treated
   units into the control group and can even flip sign when effects vary
   over time. Use a modern staggered estimator (Callaway–Sant'Anna style,
   comparing each cohort to not-yet-treated units) rather than naive TWFE.
5. **Falsification**: a placebo outcome the treatment could not touch, and
   a placebo date in the pre-period.

## What breaks it

- **Selection into treatment on the trajectory.** If the markets chosen to
  get the feature first were chosen *because* they were trending up, the
  design measures the selection. Ask how the rollout order was actually
  decided; the answer is usually in a planning doc.
- **Spillovers**: untreated units affected through shared supply or
  word-of-mouth make the control dirty and bias the effect toward zero
  (or beyond).
- **Composition shifts**: if the change alters who shows up in each unit
  (new-user influx in treated markets), the units are not the same units
  after.

## Stating the result

"Redemptions rose 2.3pp more in the provinces that got the feature than in
those that did not (event study: flat pre-trends for 8 weeks, effect stable
from week 2), assuming the provinces would have moved in parallel; rollout
order was alphabetical, which supports it." Effect, check, assumption, and
why the assumption is plausible in this instance.
