---
name: automating-decisions
description: Decides whether a repeated, at-volume decision belongs to a model, which output it needs (a forecast, a ranking, an allocation) and whether targeting needs propensity or uplift, validates the model out of time against the base rate and the naive baseline, and hands the impact claim to an experiment. Use when someone asks for a churn, propensity, LTV, scoring, forecasting, uplift, recommendation or allocation model, when a model's offline accuracy is offered as evidence that something worked, or when deciding who gets an offer, a discount or an intervention.
---

# Automating decisions

The prediction position on the map: a decision made repeatedly, per user or
per day, by a system rather than by a person reading a readout. A forecast
that sets inventory, a ranking that picks who gets the offer, an allocation
that splits a budget. The bucket asks what will happen and who gets what,
hands back a forecast, a ranking or an allocation with its uncertainty
attached, and fails by breaking the moment you intervene, because the model
learned a world in which nobody had acted on it yet.

Two rules arrive with every question routed here and leave with it. The
model needs volume, history and a trusted measurement floor. And the model
claims nothing about impact until an experiment says so: a churn model that
predicts beautifully says nothing about whether the campaign works.

The mechanical part is scripted. Given scores on an out-of-time window:

```
python skills/automating-decisions/scripts/validate_model.py \
  --data scored.csv --y churned --score p_churn --date week --cutoff 2026-07-01 \
  --k 0.1 [--arm arm --control control] [--features tenure,logins_30d]
```

Or individually via `python -m gallop.validate`. The package scores a
fitted model; it does not fit one. Fit with whatever library is at hand.

## 0 · Is this a model's decision?

Three things have to be true. Routing checked only the first.

- **Decided continuously.** A ship-or-kill call made once needs an effect
  size, not a forecast. Send it back to the causal branch.
- **The floor holds.** The outcome the model predicts is `trusted` in the
  metric registry. A model fits noise and reports confidence; it amplifies
  an instrumentation problem rather than revealing it. If the outcome is
  provisional or disputed, the work belongs to `defining-metrics` first.
- **Volume and history.** For a classifier, a few hundred positive
  outcomes in the out-of-time window alone, and about a thousand in total;
  for a forecast, several full seasons. Below that the validation cannot
  separate the model from the base rate at the operating point, so nothing
  about the model can be believed, and the verdict is not fundable. Say so
  and stop. Rolling folds do not create outcomes that do not exist, and
  "build it thin and validate as data accrues" ships an unvalidated model
  for a year. The useful object at that size is a rule: a threshold on one
  or two fields, written down with the metric it will be judged on and the
  volume at which a model would become checkable. A regional squad rarely
  has the volume to justify anything heavier, and saying so beats shipping
  a model nobody can validate.

## 1 · What will happen, or who gets what?

Three outputs, and the request names one.

- **A forecast.** A metric's value in a future window. Hands back a point
  and an interval, conditional on nothing changing.
- **A ranking.** Units ordered by an expected outcome, acted on from the
  top. Hands back the ordered list and the operating point: how far down
  the list the decision goes.
- **An allocation.** A fixed resource split across options. Hands back the
  policy and its expected value, with the forecast or ranking it rests on.

Watch for the causal question in a model's clothing. "Build a churn model
so we can see whether the retention emails work" asks two things. The
model predicts who churns; the question is whether the emails change that.
Prediction rides on correlation and does not care why. The emails were
aimed at the people most likely to leave, so the model learns the
campaign's targeting and reports it back as risk. Refuse to read impact
from a model. Split the request: the model for targeting stays here, the
impact goes to `designing-experiments`. The same refusal covers "the
forecast says we beat plan, so the launch worked": a forecast error is not
an effect size.

## 2 · Propensity or uplift

A propensity model ranks by the chance of the outcome. An uplift model
ranks by how much the treatment changes that chance. For a decision about
who gets an intervention, the second is the question and the first is the
usual answer, which targets the wrong people: the sure things who would
have stayed anyway and the lost causes who leave regardless sit at the top
of a propensity list, and the persuadables sit in the middle. The four
kinds of unit and what each model does with them:
[reference/propensity-vs-uplift.md](reference/propensity-vs-uplift.md).

Uplift needs randomised rows: units where the treatment was assigned at
random and the outcome logged. Observational rows cannot supply it; a model
fit on them learns whoever chose the targeting. If no randomised data
exists, the experiment comes first: route to `designing-experiments`,
randomise the offer across the eligible population with exposure logged,
and train the uplift model on that experiment's rows. Propensity is still
the right model when the question is who will do something rather than
whom to treat: fraud, capacity, support routing.

## 3 · Validate out of time, against the base rate

The order is fixed and the checks come before the number. Mechanics and
the leakage taxonomy: [reference/validation.md](reference/validation.md).

- **Split by time.** Fit on rows before a cutoff, score rows after it
  (`gallop.validate.time_split`). Random folds on time-ordered data leak
  the future into the training set and report an accuracy the model will
  never see in production. Leave a gap the length of the label horizon.
- **Screen for leakage.** A feature that separates the outcome
  near-perfectly on its own is usually the outcome, or something logged
  after it (`leakage_screen`). Every flagged feature is explained before
  any number below counts.
- **Beat the base rate at the operating point.** The decision acts on the
  top k. Report precision at k against the base rate, as a lift
  (`baseline_lift`). A lift of 1.0 is the base rate wearing a model. AUC
  on its own is not a validation, because no decision acts on the whole
  ranking.
- **Calibration, if the scores are used as probabilities.** Thresholds and
  expected values need calibrated scores; a ranking does not. Reliability
  table, Brier score against the base-rate forecast, expected calibration
  error (`calibration`).
- **Uplift: Qini on the randomised rows** (`qini`), against random
  targeting. Precision at k means nothing for an uplift model.

The number reported reads "at the top 10% the precision is 31% against a
base rate of 8%, a lift of 3.9, out of time on July", never "AUC 0.91".

## 4 · Forecasts and interventions

A forecast is conditional on nothing changing. It has to beat the seasonal
naive (`mase`): at a MASE of 1 or above, last season's value did as well
and is the forecast. Baselines and intervals:
[reference/forecast-baselines.md](reference/forecast-baselines.md).

A launch inside the horizon is the failure mode in its purest form. The
model has never seen one and cannot see through it. Hand back two objects:
the forecast under no change, and the launch's effect routed to the causal
branch as its own question, with a holdout if the plan is still open. A
forecast that "includes the launch" is a guess with an interval drawn round
it.

## 5 · The holdout that measures impact

Offline validation says the ranking beats the base rate. It does not say
that acting on the ranking moves the metric. That claim belongs to an
experiment: hand to `designing-experiments` with the model as the
treatment and the current rule as the control, never no rule at all,
randomised at the unit the decision acts on, exposure logged, the metric
the model exists to move as the primary. `reading-experiments` reads it.
That readout enters the prior store with `design` set to `experiment`. The
model's lift and AUC never do; an offline metric is not a readout.

When the decision runs continuously, keep a permanent holdout: a small
slice never scored, so the model's contribution can be read at any time
and drift shows up as the gap closing.

## 6 · Drift and expiry

What ships changes the data. A model in production is scored on the
population it changed, and its calibration decays from the day it goes
live. Compare production scores with realised outcomes at the label's
horizon, on a schedule. The knowledge entry names the expiry event as a
retrain trigger: calibration drift past a stated bound, the holdout gap
closing, or a product change to a feature's source. A model without a
stated expiry is a stale belief automated at volume.

## The verdict

One of four, stated with the evidence beside it:

- **Not a model's decision** → route back: a once-only call needs an
  effect size; an untrusted outcome needs `defining-metrics` first.
- **Not fundable at this volume** → a rule, written down, with the metric
  it is judged on and the volume at which a model becomes checkable. Not a
  thinner model with a warning attached: that is the failure this verdict
  exists to prevent, and the rule's effect is read by a holdout like any
  other policy.
- **Validated, impact unmeasured** → ship behind a holdout; the impact
  question goes to `designing-experiments`.
- **Impact measured** → `writing-readouts` files the readout, the belief
  and the prior-store record, from the experiment's numbers.

## Worked requests

| The request as it arrives | Verdict | Why |
|---|---|---|
| "Build a churn model so we can see if the retention emails work." | split | The model targets; the emails' effect is an experiment |
| "Score users by churn risk and send the riskiest 20% the discount." | uplift, not propensity | Sure things and lost causes top a propensity list; randomise the offer first |
| "Which users get the win-back discount this week?" | ranking | Continuous, at volume; validate out of time, ship behind a holdout |
| "Forecast Q4 signups. New pricing lands in November." | two objects | A forecast under no change, and the pricing effect as a causal question |
| "Our churn model has 0.94 AUC on cross-validation. Ship it?" | not validated | Random folds on time-ordered data; rerun out of time, report lift at k |
| "We have 300 conversions a month. Build a propensity model." | not fundable | Too few outcomes to separate a model from the base rate; hand back a rule |
| "Build a demand forecast for the regional warehouse." | forecast | Beat the seasonal naive or ship the naive; intervals widen with horizon |
| "The forecast beat plan by 8%, so the campaign worked." | refuse | A forecast error is not an effect size; route to the causal branch |
