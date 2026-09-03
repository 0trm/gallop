---
name: writing-readouts
description: Writes an experiment or analysis readout with the decision rule first and the result last, converts the finding into a durable belief rather than a number, and files both the knowledge-repo entry and the prior-store record before the ticket closes. Use when a test finishes, when documenting a shipped or killed decision, when writing up a null result or a rollback, or when a question needs an entry someone can find in a year.
---

# Writing readouts

The ceiling. A readout answers one question and dies with the ticket; a
belief is what the next three questions start from. This skill produces
three artifacts, and the ticket does not close until all three exist: the
readout, the knowledge-repo entry, and the prior-store record.

Write the readout skeleton **before the numbers are final**, with the
decision rule first and the result pasted in last. Writing the
interpretation after seeing the number is how you end up interpreting the
number.

## 1 · The readout

Template: [templates/readout.md](templates/readout.md). The order is the
argument:

1. **The decision rule, verbatim from the pre-registration.** The readout
   is a comparison against a commitment, not a story about a number.
2. **The trust gate verdict** (SRM, exposure), one line each.
3. **Guardrails**, before the primary, in the plan's order.
4. **The primary**: effect, interval under the licence actually held
   (fixed-horizon or always-valid), the CUPED note, and the shrunk
   estimate beside the raw one. For causal designs: the identifying
   assumption and the falsification checks, in the same breath as the
   number.
5. **The pre-registered segment.** Only that one. Unregistered findings go
   in "hypotheses opened", not in results.
6. **The decision**, as the rule dictates. If the rule and the human
   decision diverge (it happens), record both and why: that divergence is
   information about the rule.
7. **The proxy bridge**, if the metric is a proxy: one sentence naming
   what this result is assumed to be worth in the thing actually cared
   about.

A null readout follows the identical template. "No detectable effect above
0.4pp (MDE), interval [−0.1, +0.5]" is a finding; report the interval and
the MDE, never the word "flat" alone. A readout that ends in "interesting,
let us think about it" has failed, and the failure happened at design time
when the decision rule was not written.

## 2 · The belief

The readout's number dies with the ticket. What survives is one sentence
of theory: not "variant B won, +2.1% on checkout completion" but "this
product responds to friction removal at the payment step, worth about two
points, and it held for six weeks." Write the belief with:

- **The lever**, generalised one honest step beyond the variant tested.
  One step: "friction at payment", not "all friction everywhere".
- **The magnitude**, shrunk, as an expectation for planning.
- **The conditions** it held under: season, mix, market, ramp.
- **The expiry event**: the ship or shift that would invalidate it, named
  concretely ("expires if the checkout flow is redesigned"), because a
  stale belief keeps answering a question nobody re-asked.

## 3 · The knowledge-repo entry

Template: [templates/knowledge-entry.md](templates/knowledge-entry.md).
One searchable entry per question, holding the question, the decision it
unblocked, the design, the number, the belief, and what you would do
differently. Attach it to the question issue, not the feature ticket:
tickets get archived by the board; the question is what someone searches
in a year. Losses, nulls, broken tests and refusals are written with
exactly the care of wins; an archive of wins is a marketing document,
and an archive that records what did not work is the thing that stops
the team paying twice for the same lesson.

## 4 · The prior-store record

The write that makes the next test cheaper. Append, never edit:

```
python -m gallop.priors append --store priors.jsonl --json '{
  "id": "2026-09-signup-form-simplify", "metric": "activation_rate",
  "date": "2026-09-03", "surface": "signup", "design": "experiment",
  "effect": 0.0021, "unit": "pp", "se": 0.0009, "n_per_arm": 41000,
  "decision": "ship",
  "conditions": "September traffic mix, pre-redesign flow",
  "expires_on": "signup flow redesign"}'
```

Rules the schema enforces or the discipline requires:

- **The shrunk effect** is what gets recorded, with its se. Recording raw
  winners re-inflates the very store that exists to deflate them.
- **Nulls and losses are appended too.** A store holding only wins is a
  prior that says everything works; the honest prior mean is near zero
  and only the losses keep it there.
- **Corrections supersede.** A later reanalysis appends a new record with
  `supersedes`; nothing is edited. The store is a log.
- **`design` is honest**: an ITS effect is recorded as `its`, so future
  sizing can weight it accordingly.

## Done, defined

The ticket closes when: the readout is filed on the question issue, the
belief is in the knowledge repo with its expiry event, the record is in
the prior store, and the decision (ship, kill, iterate, rollback,
no-measurement) is written on the issue by name. The loop this closes is
the only object in the system that gets more valuable the longer it runs;
measure the quarter by decisions produced and entries filed, not by wins.
