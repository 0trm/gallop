# Pre-registration

The analysis plan, written before the flag flips, attached to the ticket
that launches the test. Its purpose is to make the readout a comparison
against commitments rather than a negotiation with hindsight. Everything in
it is short; all of it is binding.

## The template

```
EXPERIMENT        <name, ticket link, flag name>
MECHANISM         if we change <X>, <metric> moves because <Z>
UNIT              randomised on <unit>; analysis aggregates to <unit>
INTERFERENCE      shared resource: <named, or "none">; design: <user | cluster | switchback>
ARMS & SPLIT      <arms and intended ratio>
PRIMARY METRIC    <registry name, trusted status confirmed on YYYY-MM-DD>
MDE               <value> (<source: prior store n=<k> | unanchored>)
POWER / ALPHA     0.80 / 0.05 unless stated; sequential: <none | always-valid | OBF k looks>
DURATION          <days>, from <units/day>; calendar events in window: <named>
EXPOSURE EVENT    <event name>; fires when <moment>; both arms; volume alert owned by <who>
GUARDRAILS        <crashes, latency, refunds, unsubscribes, + gaming guardrail from registry>
SEGMENT           one, pre-registered: <segment, chosen from the mechanism>
DECISION RULE     if the interval excludes <X>, ship; else <kill | iterate>
                  guardrail breach ⇒ rollback, readout still written
READOUT DATE      <the Tuesday it will be read, in the room>
```

## The rules the template encodes

**The decision rule is a number, not a mood.** "If the interval excludes a
0.2pp lift we ship" survives contact with an ambiguous result;
"significant and meaningful" does not. Write the rule so that both possible
readouts lead to a named action.

**The peeking policy is part of the design.** If the platform will show
anyone a curve before the horizon, the test is sequential from day one
(always-valid bounds if looks are unscheduled, group-sequential if they are
fixed), and the plan says which. The social half of the rule matters as
much: nothing counts as a result until the scheduled readout, whatever the
curve does on day three.

**One segment.** Chosen because the mechanism predicts a difference there,
not because the platform offers eleven cuts. Anything found in an
unregistered segment is a hypothesis for the next test, never a result of
this one.

**Guardrails are read before the primary.** The order is part of the plan:
trust gate, guardrails, then the primary metric. A win on the primary with
a guardrail breach is a rollback, not a negotiation.

**Amendments are dated.** Reality intervenes: traffic shifts, a bug forces
a restart. Amend the plan in writing, with the date and the reason, before
the readout. An amended plan is honest; a retrofitted one is fiction.

## Why this is worth a page of ceremony

Five of the six steps of an experiment can hand back a wrong number
without the readout looking any different. Every line above pins one
of those steps to a commitment made while nobody knew the answer. Written
after the numbers are visible, the same lines are just the story of what
happened; the entire value is in the timestamp.
