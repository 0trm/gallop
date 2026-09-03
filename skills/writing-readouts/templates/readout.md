# Readout · <experiment name>

<question issue link · flag name · dates run · readout date>

## The decision rule, as pre-registered

> If the interval excludes <X>, we ship; otherwise <kill | iterate>.
> Registered <date>, amended <date/none>.

## Trust gate

- SRM: <chi2, p, pass/fail> (alpha 0.001)
- Exposure: <pooled rate, differential p, verdict>

## Guardrails (read before the primary)

| Guardrail | Movement | Breach? |
|---|---|---|
| <crashes> | | |
| <latency> | | |
| <gaming guardrail from registry> | | |

## Primary metric: <registry name>

- Effect (raw): <value> <unit>, se <value>
- Interval under the licence held: <always-valid | fixed-horizon> 95% CI
  [<lo>, <hi>]
- CUPED: rho <r>, variance reduction <v%> <or: no pre-period covariate>
- Shrunk toward the prior (<k> past readouts): **<value>** – the planning
  number
- MDE this test could see: <value>
- <For causal designs: identifying assumption, one sentence; falsification
  checks run and their results>

## Pre-registered segment: <segment>

<effect, interval. Nothing else. Unregistered observations go below.>

## Decision

**<Ship | Kill | Iterate | Rollback | No-measurement>** – <one sentence:
how the rule dictated it, or why the human call diverged from the rule>.

<If the metric is a proxy: the bridge sentence. "This is a change in claim
rate; we currently value a claim at <Y> redemptions, and that assumption is
doing the work.">

## The belief

> <Lever, one step generalised · magnitude, shrunk · conditions it held
> under · the event that expires it.>

## Hypotheses opened

- <anything from unregistered cuts, phrased as next questions, not results>

## Filed

- Knowledge entry: <link> · Prior store id: <id> · Decision on issue: <link>
