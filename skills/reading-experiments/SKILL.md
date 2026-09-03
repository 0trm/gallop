---
name: reading-experiments
description: Runs the trust gate on a finished experiment before the result is believed: sample ratio mismatch, exposure counts, always-valid or sequential bounds, guardrails read before the primary metric, the pre-registered segment rather than the most flattering one, CUPED variance reduction, and empirical Bayes shrinkage against the prior store. Use when analysing or reviewing A/B test results, when a test looks like a winner, when someone reports a lift, or when deciding whether to ship on an experiment readout.
---

# Reading experiments

Whether the result is a result. Five of the six steps in an experiment can
hand back a wrong number without the readout looking any different, so the reading order is fixed and the checks come before the
number. Read against the pre-registered plan; if no plan exists, say so
first, because everything below weakens without one.

The mechanical checks are scripted. Given assignment/exposure counts and
unit-level data, run them in one pass:

```
python skills/reading-experiments/scripts/run_checks.py \
  --counts counts.csv --data units.csv --y metric --x pre_metric --arm arm \
  [--store priors.jsonl --metric activation_rate --unit pp]
```

Or individually via `python -m gallop.trust|variance|sequential|shrink`.

## 1 · The trust gate, before any effect

Two checks, and a failure at either stops the reading. Details and the
cause taxonomy: [reference/trust-gate.md](reference/trust-gate.md).

- **Sample ratio mismatch.** Chi-square on assignment counts against the
  intended split (`gallop.trust.srm`, alpha 0.001). A 0.4% imbalance at a
  million units looks like nothing on a dashboard and is a broken test.
  On SRM: stop, do not analyse, work the cause taxonomy. There is no
  correction; a biased assignment is not a smaller sample, it is a
  different population per arm.
- **Exposure.** Did the variant reach anyone, at the same rate in both
  arms? (`gallop.trust.exposure_check`). Differential exposure is a
  trigger bug and invalidates the comparison. Uniform under-exposure
  dilutes the ITT estimate toward zero by a known factor; report both the
  diluted and scaled numbers, labelled.

## 2 · Guardrails before the primary

Read the guardrail metrics first, in the plan's order. A win on the primary
with a guardrail breach is a rollback, not a trade-off discussion, because
the trade was already made when the guardrail was registered. A rollback
triggered by a guardrail is the system working and still gets a readout.

## 3 · The effect, under the licence you actually have

- **If the design was fixed-horizon and nobody looked early**: the plain
  interval stands.
- **If anyone peeked without a sequential design**: the nominal p-value is
  broken (daily peeking roughly triples the false positive rate) and the
  reported effect is selected on noise. Recompute against always-valid
  bounds (`python -m gallop.sequential bound`) and label the result as
  salvaged, not as designed.
- **If the design was sequential**: read against the pre-declared boundary
  (`bound` for always-valid, `obf` for the fixed schedule). A day-three
  crossing of an always-valid bound is a licensed stop.

Apply **CUPED** if a pre-period covariate exists
(`gallop.variance.cuped`): the se falls by sqrt(1 - rho²), often the
difference between a conclusive and an inconclusive read. Validity rule
and failure modes: [reference/variance-reduction.md](reference/variance-reduction.md).

**A null is an interval, not a zero.** "No difference" when the MDE was
1.4pp means "we could not have seen less than 1.4pp". Report the interval
and the MDE every time; an underpowered null read as a kill is as wrong as
a noise spike read as a win.

## 4 · Segments: the one you registered

Read the pre-registered segment. Do not read the other eleven the platform
offers; with eleven cuts at alpha 0.05, finding a "significant" segment is
the expected outcome under a true null. Anything interesting in an
unregistered cut is a hypothesis for the next test, filed as one.

## 5 · Shrink toward what this metric actually does

Raw winners are inflated: conditioning on crossing a threshold selects the
draws noise helped. Shrink the estimate toward the prior store's
distribution for this metric (`gallop.shrink.from_store`); the shrunk
number is the planning number and the one that gets written back. Mechanics
and when shrinkage is not available:
[reference/shrinkage.md](reference/shrinkage.md).

## 6 · Time: novelty and decay

If the daily lift trends down across the run (regress daily lift on day; a
negative slope with a positive intercept), the effect is novelty and the
horizon-end average overstates the long run. A decay slower than the
horizon is invisible to any test you can afford; the only instrument for
that is a long-term holdback, so recommend one when the decision is
expensive and the mechanism is plausibly novelty-driven.

## The verdict

One of four, stated plainly with the decision rule beside it:

- **Trustworthy and clears the rule** → ship; hand to `writing-readouts`.
- **Trustworthy and misses the rule** → kill or iterate; hand to
  `writing-readouts` (nulls are filed with the same care as wins).
- **Trust gate failed** → no result exists. Diagnose, fix, rerun. Also
  filed: a broken test is a lesson about the pipeline.
- **Salvage** (peeked without licence, diluted exposure): a labelled,
  weaker number with its caveat attached in the same sentence, and a note
  in the readout that the next design fixes the licence.

Every verdict flows to `writing-readouts`; the prior store only stays
honest if losses and broken tests are written back as faithfully as wins.
