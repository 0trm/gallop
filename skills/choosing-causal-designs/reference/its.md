# Interrupted time series

One unit (often the whole product), one switch date, no untreated twin. The
counterfactual is the pre-period's own trajectory, projected forward; the
effect is the level (and possibly slope) break at the switch.

## When it fits

- The change hit everyone at once on a known date: a migration, a policy
  change, a redesign shipped to 100%.
- The pre-period is long enough to establish trend and seasonality: as a
  rule of thumb, several full seasonal cycles of the metric, and never less
  than 3x the post-period you intend to read.
- Nothing else big happened at the same date. This is the assumption that
  usually fails: launches ship with marketing pushes, and ITS attributes
  the sum to the switch.

## How to run it honestly

1. **Model the pre-period only**: trend + seasonality (weekly at minimum;
   annual if the history supports it). Segmented regression is the
   transparent default; a forecasting model works too, but transparency is
   worth more than fit here.
2. **Project across the switch** and read the post-period gap: an
   immediate level change, a slope change, or both. Decide which of the
   two the mechanism predicts before looking.
3. **Uncertainty from the projection, not the residuals alone.**
   Autocorrelated series make naive standard errors far too small; use
   Newey-West errors or a forecast interval that widens with horizon.
4. **Falsification, non-negotiable:**
   - **Placebo dates**: run the same analysis at several pre-period dates
     where nothing happened; the effect there should be ~zero, and its
     spread is an honest floor on the real one's uncertainty.
   - **A control series** if any exists, even an imperfect one (another
     market, a metric the change could not touch): if it jumps at the same
     date, the jump is the environment, not the change.
5. **Read a fixed post-window**, declared before looking, matched to the
   mechanism's timescale. Extending the window until significance is
   peeking with extra steps.

## What breaks it

- **Simultaneous shocks** (the marketing push, a price change, a
  competitor event, a pandemic). ITS cannot separate them; say which ones
  are in the window.
- **Slow ramps.** A rollout over six weeks has no interruption; either
  model the ramp explicitly against exposure share or use the staggered
  rollout as a DiD instead. A staggered rollout is better data than a
  clean switch; check for one before settling on ITS.
- **Metric drift**: a definition change near the switch date is
  indistinguishable from an effect. Check the registry's version history
  first.

## Stating the result

"Deliveries ran 4.1% above the pre-trend projection for the eight weeks
after the migration (placebo dates: −0.5% to +0.9%), assuming the
pre-period trend would have continued and noting the June price change sits
inside the window." Effect, falsification range, assumption, known threat,
one sentence each.
