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
