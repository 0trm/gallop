# Forecast baselines

A forecast is a claim that the future looks like the past in a stated
way. The baseline states the simplest such claim, and the model has to
beat it.

## The seasonal naive

Next period equals the same period one season ago. Weekly data with a
yearly cycle forecasts this week from the same week last year; daily data
with a weekly cycle forecasts Monday from last Monday. It costs nothing,
it is explainable to anyone, and on product metrics it is hard to beat by
much.

MASE scales the model's error on the test window by the seasonal naive's
error on the training window (Hyndman and Koehler's MASE):

- **MASE below 1**: the model beats the naive by that factor.
- **MASE at or above 1**: the naive did as well. The naive is the
  forecast, and the model is retired or reworked. This is a verdict, not
  a tuning note.

Report the naive's error on the test window as well: the naive forecast
made at the cutoff, scored on the same dates as the model. That is the
baseline the model is actually competing with. On a multi-step horizon
the two can disagree. MASE's scale is a one-step error on the training
window, and when the test window sits where the series is more volatile
(the last days before a sell-out, a peak season), a model can post a MASE
above 1 while beating the cutoff naive by a wide margin. Read MASE as the
verdict only when the horizon is one step; otherwise the verdict is the
model's error divided by the cutoff naive's on the test window. A worked
case: [worked-example.md](worked-example.md).

## Intervals

A point forecast is a decision input only with its interval, and the
interval has to widen with the horizon. A model whose 90% band is the same
width at week 12 as at week 1 is not reporting uncertainty; it is
reporting the residual variance of its fit. Check the band on the
out-of-time window: roughly nine in ten actuals inside a 90% band, and no
fewer. A band that holds 60% of actuals is a 60% band whatever the label
says.

## Interventions

The forecast is conditional on nothing changing. Every product change
inside the horizon breaks that condition, and the model, fit on a past
without that change, cannot see through it. Three cases:

- **The change is in the past and the model was fit across it.** The
  training data mixes two regimes. Either fit on the post-change window
  only, if it is long enough, or add the change as a level shift and say
  so.
- **The change is inside the horizon.** Hand back two objects: the
  forecast under no change, and the change's effect as a causal question
  routed to `designing-experiments` or `choosing-causal-designs`. If the
  plan is still open, ask for a holdout so the effect can be read
  properly. Adding the change to the forecast by hand is a guess with an
  interval drawn round it.
- **The forecast is the argument for the change.** A forecast that beat
  plan is not evidence that something worked. It says the past was a good
  guide to the future; it cannot say what caused the difference. Route
  the impact claim to the causal branch.

## Forecasts as inputs to allocation

An allocation policy (inventory, budget, staffing) is only as good as the
forecast under it, and its cost is asymmetric: under-forecasting a stock
out and over-forecasting a write down are different losses. State the loss
on each side before choosing the point in the interval to act on; the
median is rarely it. The allocation's own impact, once it runs, is again
an experiment or a holdout, never the forecast's accuracy.
