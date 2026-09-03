# The promotion checklist

A metric moves from `provisional` to `trusted` only when every item below
passes. Trusted is the status that licenses primary or guardrail duty in an
experiment; everything else in the registry is context. Run the checklist as
written, record the date it passed, and re-run it after any definition change.

## 1 · Definition closed

Someone who has never seen the codebase can reimplement the metric from the
registry text and match the number within rounding. Test this literally when
the stakes justify it: hand the definition to a second person, have them
compute yesterday's value from the source of truth, compare.

## 2 · One source of truth

Exactly one table or model is named. Every surface that shows the metric
(dashboard, report, experiment readout) reads from it or from a documented
derivative. If two surfaces currently disagree, promotion is blocked until
one of them is fixed or killed; a metric with two values is not a metric.

## 3 · Instrumentation validated end to end

The events the metric is built on have been traced from the client (or the
service) to the warehouse at least once, by someone, on purpose:

- Fire the event in staging, watch it land in the source table with the
  expected fields.
- Check volume by platform and by market against expectation. The failure
  that hides best is an event that stopped firing for one platform or one
  country; the total looks plausible while a segment is dark.
- Confirm the identity join. A metric per user is only as good as the
  mapping from event to user, across devices and sessions.

## 4 · Gaming statement written

The `gaming` field is filled in with a plausible mechanism, and the guardrail
that would catch it exists or is explicitly declined with a reason. See
[gaming.md](gaming.md).

## 5 · Owner named

One person answers for the definition. Not a team: a person. The owner is
who arbitrates the next disagreement and who signs off on version changes.

## 6 · Stability known

Enough history exists to know the metric's normal variance: week-over-week
movement under no intervention, seasonality shape, and the size of day-level
noise. Without this, no experiment on the metric can be sized honestly and
no anomaly on it can be triaged. Concretely: pull at least eight weeks of
daily values, compute the coefficient of variation, and record the typical
week-over-week swing in the registry `notes`.

## 7 · Sensitivity plausible

The metric can move at the traffic and timescale a test actually has. A
metric that is 95% determined by behaviour outside the product's control, or
that responds to change with a six-week lag, can be a guardrail but should
not be a primary. If the honest answer is "this cannot detectably move in a
two-week test", promote a nearer proxy as primary instead and keep this one
directional, and say so in `notes`.

## Demotion

Deprecate, never delete. A deprecated entry keeps its definition and dates so
old readouts stay interpretable. Deprecation triggers: the definition was
superseded, the instrumentation broke irrecoverably, or the gaming statement
came true and the guardrail did not hold.
