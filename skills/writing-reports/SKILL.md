---
name: writing-reports
description: Writes an experiment or analysis report with the decision rule first and the result last, converts the finding into a durable belief rather than a number, and files both the knowledge-repo entry and the prior-store record before the ticket closes. Use when a test finishes, when documenting a shipped or killed decision, when writing up a null result or a rollback, or when a question needs an entry someone can find in a year.
---

# Writing reports

The ceiling. A report answers one question and dies with the ticket; a
belief is what the next three questions start from. This skill produces
three artifacts, and the ticket does not close until all three exist: the
report, the knowledge-repo entry, and the prior-store record. A forecast
made once, for a plan, closes with the knowledge entry alone (Done, defined).

Write the report skeleton **before the numbers are final**, with the
decision rule first and the result pasted in last. Writing the
interpretation after seeing the number is how you end up interpreting the
number.

## 1 · The report

Template: [templates/report.md](templates/report.md). The order is the
argument:

1. **The decision rule, verbatim from the pre-registration.** The report
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

A null report follows the identical template. "No detectable effect above
0.4pp (MDE), interval [−0.1, +0.5]" is a finding; report the interval and
the MDE, never the word "flat" alone. A report that ends in "interesting,
let us think about it" has failed, and the failure happened at design time
when the decision rule was not written.

## 2 · The belief

The report's number dies with the ticket. What survives is one sentence
of knowledge: not "variant B won, +2.1% on checkout completion" but "this
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

The write that makes the next test cheaper. Append one record to the
prior store, never edit one:

```json
{"id": "2026-09-signup-form-simplify", "metric": "activation_rate",
 "date": "2026-09-03", "surface": "signup", "design": "experiment",
 "effect": 0.0021, "unit": "pp", "se": 0.0009, "n_per_arm": 41000,
 "decision": "ship",
 "conditions": "September traffic mix, pre-redesign flow",
 "expires_on": "signup flow redesign"}
```

Rules every record follows:

- **The shrunk effect** is what gets recorded, with its se. Recording raw
  winners re-inflates the very store that exists to deflate them.
- **Nulls and losses are appended too.** A store holding only wins is a
  prior that says everything works; the honest prior mean is near zero
  and only the losses keep it there.
- **Corrections supersede.** A later reanalysis appends a new record with
  `supersedes`; nothing is edited. The store is a log.
- **`design` is honest**: an ITS effect is recorded as `its`, so future
  sizing can weight it accordingly.
- **A provisional metric writes nothing.** A number produced under the
  `defining-metrics` provisional exit is a hypothesis, not a decision: it
  states its expiry in the report and gets no store record and no
  knowledge entry. The store is what every later question reads, and a
  definition nobody validated does not get to write to it.
- **A forecast made once writes no record.** It has no effect size. Its
  knowledge entry holds the forecast, its interval and the plan it set, and
  the actual goes beside them once the window closes.

## Done, defined

The ticket closes when: the report is filed on the question issue, the
belief is in the knowledge repo with its expiry event, the record is in
the prior store, and the decision (ship, kill, iterate, rollback,
no-measurement) is written on the issue by name. A forecast made once, for
a plan, closes with the knowledge entry alone: it holds the forecast and its
interval, the actual is added once the window closes, and the plan the
number set is written on the issue. It has no decision rule to read against
and no effect size to store, so no report and no prior-store record. The loop
this closes is the only object in the system that gets more valuable the
longer it runs; measure the quarter by decisions produced and entries filed,
not by wins.
