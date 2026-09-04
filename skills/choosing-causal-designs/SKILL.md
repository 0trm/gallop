---
name: choosing-causal-designs
description: Selects a causal design when assignment already happened and randomisation was never possible: interrupted time series for one unit and one switch date, difference-in-differences for treated and untreated units seen before and after, synthetic control for one treated unit and many donors, matching on observables, instrumental variables, and the exit that says there is no valid comparison group. Use when measuring the impact of something already rolled out, a launch, a migration, a pricing change, or a campaign that reached everyone at once.
---

# Choosing causal designs

Assignment already happened; the design's job is to reconstruct the
comparison that randomisation would have provided. Pick by **how assignment
happened**, not by which method is fashionable, and hand back an effect size
*plus the assumptions it rests on*, stated in the readout, because here the
assumptions are doing the work the coin flip would have done.

First, one check worth thirty seconds: is randomisation really unavailable?
If the change has not fully shipped, a holdout or staggered rollout is still
possible and strictly better. This skill is for the past tense.

## The selection table

Work down; take the first row whose conditions hold.

| Assignment looked like | Design | Needs |
|---|---|---|
| One unit (or everyone), one sharp product switch on a known date, no untreated twin | **ITS** – [reference/its.md](reference/its.md) | A long, stable pre-period; no simultaneous shock; a discrete switch, not a diffuse push |
| Some units got it, some did not, both observed before and after | **DiD** – [reference/did.md](reference/did.md) | Parallel pre-trends |
| One treated unit, many untreated candidates to blend | **Synthetic control** – [reference/synthetic-control.md](reference/synthetic-control.md) | A donor pool the treatment did not touch |
| Individuals selected themselves in, on things you can observe | **Matching** – [reference/matching-iv.md](reference/matching-iv.md) | Selection on observables (a strong claim; say it) |
| Something nudged uptake without touching the outcome directly | **IV** – [reference/matching-iv.md](reference/matching-iv.md) | A real instrument (rare; most candidates fail) |
| None of the above | **No comparison group** – [reference/no-comparison-group.md](reference/no-comparison-group.md) | Honesty |

The last row is a first-class exit, not a failure. Saying "there is no
defensible number here" out loud beats shipping a number that dissolves
under the first follow-up question, and the reference file says what to
offer instead.

One row needs guarding against a tempting misread: a **campaign or
marketing push that ran everywhere at once is not an ITS candidate**, even
though "everyone, one date" appears to match. ITS needs a discrete switch
in the product itself; a media flight is a diffuse, ramping shock whose
effect shape is unknown, it usually arrives with seasonality and other
pushes, and the pre-trend projection cannot separate any of that. That
case takes the last row: bounds at most, a referral to whoever owns mix
modelling or panel data, and a holdout designed into the next flight.

The second row has its own misread: **two units, one treated, is still
DiD.** An Android switch with iOS untouched has a comparison group, and
the twin is the counterfactual, not a falsification check bolted onto an
ITS. With two clusters the standard errors are weak and the readout says
so in words; that is a reason to state the inference honestly, never a
reason to drop to a design that throws away the only comparison there is.

## What every design here must state

1. **The counterfactual, in one sentence.** What would have happened
   without the change, and which data stands in for it. If the sentence
   cannot be written, the design is not chosen yet.
2. **The identifying assumption, in the requester's language.** "Madrid
   would have moved like Barcelona" (DiD), "the trend would have
   continued" (ITS), "adopters and matched non-adopters differ only on
   what we matched" (matching). This is the sentence the readout hangs on.
3. **The falsification checks run and passed.** Pre-trends for DiD,
   placebo dates for ITS, placebo units for synthetic control, balance
   tables for matching. A design whose checks were not run is an
   assertion, not an estimate.
4. **What would change the answer.** The known threat the design cannot
   exclude: the simultaneous marketing push, the seasonality no control
   captures, the unobservable that matching cannot see.

## Discipline shared across all five

- **Pick the design before computing the estimate**, from the assignment
  story alone. Running three designs and reporting the one with the
  nicest number is the observational version of peeking.
- **Effects here deserve wider error bars than their standard errors
  say.** Standard errors price sampling noise, not assumption risk. Say
  which of the two dominates.
- **Modeling is the machinery, not the design.** DiD is a regression;
  synthetic control is a weighted counterfactual model. The design decides
  what comparison is valid; the model just computes it. Adding controls to
  a regression is not, by itself, a design.
- **File the result** through `writing-readouts` with `design` set
  honestly in the prior-store record (`its`, `did`, `synthetic_control`,
  `matching`, `iv`). Observational effects mixing into the experimental
  prior is exactly the kind of thing the field records to prevent.
- **The calibration habit:** when a causal-design estimate later gets
  tested properly (a holdout on the next iteration), compare. A team that
  never checks its observational calls against experimental ones never
  learns which of its designs to trust.
