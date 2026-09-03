---
name: defining-metrics
description: Turns a metric name into a computation, a source of truth, a registry entry, and a written statement of how it will be gamed, then decides whether it is trustworthy enough to promote. Use when defining a north-star or guardrail metric, when two dashboards disagree on the same number, when arbitrating between conflicting metric definitions, or when a readout depends on a metric nobody has validated.
---

# Defining metrics

The floor. Not a stage: everything above it inherits its errors, and a wrong
definition does not raise an error, it just returns the wrong number. This skill
produces four artifacts for one metric: a computation, a source of truth, a
registry entry, and a statement of how the metric will be gamed. A metric
missing any of the four is not ready to carry a readout.

## When two numbers disagree

The most common entry point: the same metric shows different values in two
places and nobody trusts either. Do not average them, and do not pick the
one closer to expectations. Trace each to its query and diff the definitions.
The difference is almost always one of five things, checked in this order:

1. **Window** – 7-day vs 28-day, calendar vs rolling, and the timezone the
   day boundary uses.
2. **Filter** – bots, internal traffic, test accounts, one market, one
   platform; applied in one query and not the other.
3. **Unit and dedup** – users vs sessions vs events, and whether repeats
   within the window count once or every time.
4. **Join** – a join that drops units with no activity, turning a rate's
   denominator into "active units" without anyone deciding that.
5. **Freshness** – one source lags the other; the numbers were never
   computed over the same days.

Name the discrepancy mechanically ("A excludes bounced sessions, B does
not"), then decide which definition serves the decision the metric exists
for, and register that one. The other query gets updated or deleted, not left
as a second opinion.

## Writing the definition

A definition is precise enough when someone could reimplement it from the
text alone and match the number. It states:

- **The computation.** Numerator, denominator, window, dedup rule, filters.
  "Activation rate: users who completed at least one core action within 7
  days of signup / users who signed up, excluding internal and bot accounts,
  UTC days."
- **The unit of analysis.** What one observation is: user, session, order,
  day. This is also what experiments randomise on, so a mismatch here
  becomes a broken analysis later.
- **The source of truth.** One table or model, named. When a dashboard and
  the source disagree, the source is right by definition and the dashboard
  is a bug.
- **The direction.** Which way is better. Sounds trivial; guardrails and
  automated checks need it explicit.

## The proxy bridge

Most product metrics stand in for an outcome the product cannot observe (a
purchase in someone else's store, long-run retention, revenue attributed
weeks later). If this metric is a proxy:

- **Name the bridge in every readout.** One sentence: this result is a
  change in X, here is what we currently believe X is worth in Y, and here
  is the assumption doing the work.
- **Validate the proxy on a schedule**, against something real: cohorts,
  panel data, whatever exists. Once a year, off-roadmap, non-negotiable.
- **Prefer metrics whose outcome you own.** Given two candidate framings of
  similar value, take the one that ends inside your own instrumentation.

## How it will be gamed

Before the metric is used to judge anything, write down how a well-meaning
team hits the number without creating the value it stands for. Every metric
has at least one; a metric whose gaming nobody can describe is a metric
nobody has thought about. Common patterns and worked examples are in
[reference/gaming.md](reference/gaming.md). The output is one or two
sentences in the registry entry's `gaming` field, plus the guardrail metric
that would catch it.

## The promotion gate

A metric is **trusted** – promotable to primary or guardrail duty in
experiments – only when the checklist in
[reference/promotion.md](reference/promotion.md) passes: definition,
source of truth, instrumentation validated end to end, gaming statement,
owner, and stability checked over enough history to know its variance.
Until then it is **provisional**: usable for exploration, barred from
readouts. Retired definitions become **deprecated**, kept in the registry so
old readouts remain interpretable.

## The registry entry

The registry is a JSONL file beside the prior store, one metric per line,
validated against `templates/metric-registry.schema.json`. Field-by-field
guidance and a worked example are in
[reference/registry-schema.md](reference/registry-schema.md). Read it back
with:

```
python -m gallop.priors registry --registry metrics.jsonl --status trusted
```

Experiments must take their primary metric from the registry, not from a
text box. That single rule is what makes the floor hold: it turns every
definition argument into a one-time cost instead of a per-readout one.

## Maintenance

The definition of success is maintained continuously, like calibrating a
scale you weigh things on every day, not set once in January:

- **Every ship changes the data.** A launched feature changes user mix and
  event volume; after a significant ship, check that the metric still means
  what it meant. This is the dashed loop on the method map closing.
- **Version changes.** When a definition changes, bump it explicitly, note
  the change date on any chart spanning it, and treat pre/post numbers as
  different series. Metric drift in the catalog is how last year's numbers
  stop matching without anyone deciding anything.
- **Alert on the floor, not the ceiling.** The two failures that ruin tests
  from below are events that stop firing on one platform and exposure logs
  that drift; alert on event volume, not just on metric values.

## Hand-back

To the question that routed here: a number the rest of the map can stand on.
State what changed (the definition, the source, or both), what the corrected
current value is, and which past readouts, if any, are now suspect. Then
re-enter `routing-questions` with the original question, which can now be
answered on a floor that holds.
