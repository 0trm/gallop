# The theory layer

The band across the top of [the map](../map/), drawn as a band because every
box touches it. It is not a stage and it is not a method: it is where the map
keeps what it learned, and it is the only object in the whole system that
gets more valuable the longer a team runs it. Everything else on the map
answers a question and stops. The ceiling is where the answers accumulate
into something the next question can stand on.

It has two halves, and they are different kinds of object.

## The knowledge repo

Prose. One searchable entry per question, holding the design, the number,
the decision, and what you would do differently, with the losses written up
as carefully as the wins. The repo is what a person reads before proposing
anything.

The unit is the question, not the ticket. Tickets get closed and archived by
the board; a question outlives the feature that prompted it, and eight
months later somebody proposes the same test. The entry is what turns that
moment from a re-run into a lookup.

What an entry has to contain:

- **The question**, written so that two different answers were imaginable.
  If you cannot picture being surprised, it was not a question.
- **The decision it unblocked**: what changed on the answer, and who made
  the call. A named person, a named choice.
- **The method**: which bucket it landed in from the routing, and the
  design. Half of a roadmap's questions turn out not to be randomisable,
  and the entry is where that gets found out once instead of quarterly.
- **The number**, shrunk, with its interval, or the honest statement that
  no defensible number existed.
- **The belief**: the sentence that outlives the readout. Not "variant B
  won, +2.1% on checkout completion", which dies with the ticket, but
  "this product responds to friction removal at the payment step, about
  two points, and it held for six weeks", which the next three questions
  start from.

## The prior store

A table. For each metric, the distribution of effects the last hundred
tests actually produced. The store is what sizes the next test, and what
the last readout gets shrunk toward.

The store earns its keep twice per experiment:

1. **At design time**, the minimum detectable effect stops being a wish.
   The store says what this metric has actually moved by; a test powered
   for a lift nobody at this company has ever produced was decided before
   it launched. Effects are small and most ideas do nothing: seventy to
   ninety percent of experiments are killed or neutral everywhere it has
   been measured, so the honest prior mean is roughly zero, and only a
   store that records the losses keeps it there.
2. **At readout**, raw winners are inflated: a result reported because it
   crossed a threshold is, in expectation, an overstatement, and the
   overstatement grows as power falls. Empirical Bayes shrinkage toward
   the store's distribution is the correction, and the shrunk number is
   what gets written back, so the store deflates rather than inflates.

## The format is the discipline

The store is an **append-only JSONL file**, one record per readout,
validated on write. That is not a storage detail; each property is doing a
job:

- **JSONL, in version control**, because the store must be reviewable in a
  pull request. A store nobody can diff is a store that goes stale, and
  staleness is precisely the ceiling's failure mode.
- **Append-only**, because the store is a log of what tests produced. A
  correction is a new record carrying `supersedes`, never an edit; the
  history of being wrong is part of what the store knows.
- **Validated on write**, because a malformed record would flow into a
  shrinkage estimate without an error. The contract is published as JSON
  Schema:
  [prior-store.schema.json](https://github.com/0trm/gallop/blob/main/templates/prior-store.schema.json)
  and
  [metric-registry.schema.json](https://github.com/0trm/gallop/blob/main/templates/metric-registry.schema.json),
  and `gallop.priors` enforces it.

A record is thirteen flat fields:

```
id · metric · date · surface · design · effect · unit · se · n_per_arm
decision · conditions · expires_on · supersedes
```

`effect` and `se` are what shrinkage needs; `metric` plus `effect` across
records is the distribution design reads. The rest is what makes an entry
legible to a person a year later, which is the whole claim of the layer.

## Dated, conditioned, and expiring

A wrong metric returns a wrong number without an error; a stale belief
keeps answering a question nobody re-asked. The two failure modes
mirror each other, floor and ceiling, and the defence is structural rather
than a matter of diligence:

- Every entry carries a **date** and the **conditions** it held under:
  season, mix, market, ramp.
- Every entry names its **expiry event**: not a date somebody has to
  remember, but the concrete ship or shift that would invalidate it.
  "Expires if the checkout flow is redesigned." Whoever redesigns the
  checkout should trip over that line.

This is why a dated entry with an expiry condition beats a quarterly
write-up. The quarterly document is true on the day it is written and
decays invisibly from then on; nothing in it says which paragraphs died
when the March release changed the funnel. The entry expires itself, at
the moment the world changes, because the thing that changed the world is
named in the entry.

The loop on the map closes through this layer: what ships changes the
data, and the ship that contradicts a belief is the event that expires it.

## Why this is the part worth keeping

Skip the theory layer and every quarter starts from zero: the team re-runs
a test somebody ran two years ago, argues from memory about what a banner
is worth, and powers each experiment as though it had never seen an effect
size at this company before. The cost is not one wasted test; it is that
nothing compounds.

Run it, and the write-back is a condition of shipping rather than an act
of virtue: nothing reaches every user without a link back to the
experiment that justified it, and the readout that closes the test writes
the belief in the same motion. The skills in this repo exist to run one
question around that loop; the layer is what makes the second question
cheaper than the first.
