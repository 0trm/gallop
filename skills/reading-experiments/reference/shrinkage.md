# Empirical Bayes shrinkage

The winner's-curse correction, and the moment the prior store pays for
itself.

## Why raw winners are inflated

A result is reported because it crossed a threshold. Conditioning on
crossing selects the realisations noise pushed up, so the expected reported
effect exceeds the true one, and the excess grows as power falls. An
underpowered test that "wins big" is the most inflated object in the
building: with 20% power, a just-significant result overstates the true
effect by roughly a factor of two or more. The sign is usually right; the
magnitude is not, which is worse for planning than a clean false positive.

## The model

Normal-normal. The prior is what this metric has actually done, estimated
from the store by method of moments:

    mu   = mean of past effects
    tau² = max( var(past effects) − mean(past se²), 0 )

Posterior mean = w·effect + (1−w)·mu, with w = tau²/(tau² + se²).

```
python -m gallop.shrink eb --effect 0.0031 --se 0.0012 \
    --store priors.jsonl --metric activation_rate --unit pp
```

Reading the output:

- **w near 1**: the test was precise relative to how much true effects
  vary; the data mostly stands.
- **w near 0**: the test was noisy relative to the metric's history; the
  estimate collapses toward the prior mean. This is not the method being
  timid, it is the observation carrying little information.
- **tau² = 0**: past effects are indistinguishable from noise around their
  mean; the model is saying this metric has never produced a
  distinguishable effect, and the new result shrinks all the way to mu.
  That verdict is itself worth surfacing in the readout.

The shrunk number is the planning number: what to forecast from, what to
write into the prior store, what to tell the roadmap. The raw number and
interval are still reported beside it, labelled.

## Preconditions, checked by the tooling

- **At least 3 past effects** for the metric (`gallop.shrink` refuses
  fewer; below ~8 the prior itself is noisy, so say so).
- **One unit.** Effects in `pp` do not pool with effects in `relative`;
  `from_store` refuses mixed units rather than averaging them.
- **Comparable readouts.** The store should hold effects from the same
  metric under comparable designs; a store polluted with one 10x outlier
  from a pricing change will inflate tau² and under-shrink. `supersedes`
  exists for corrections; use it.

## When there is no store

First tests at a company have no prior. Options, in honesty order: borrow
the published base rate (most experiments do nothing; the honest prior mean
is roughly zero, so at minimum discount the raw estimate mentally and say
the readout is unshrunk); or start the store with this readout and accept
that shrinkage begins from test four. What is not available is treating the
raw number as a forecast: that is the exact error the correction exists for.
