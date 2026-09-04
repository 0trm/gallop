# Sizing

The number a roadmap weighs, and the three ways it goes wrong: the whole
gap is assumed to close, the estimate is anchored on nothing, and the
size is quoted without the traffic that would be needed to see it.

## Three numbers, always all three

`gallop.explore.size_opportunity` returns them together:

1. **The ceiling.** Gap times the units affected: every affected unit
   moves the full distance. It is the upper bound and it is presented as
   one. "If mobile checkout matched desktop, that is 1,900 orders a
   month" is a ceiling, and the sentence should say so.
2. **The anchored estimate.** From the prior store, for this metric: the
   mean effect past changes produced (the planning number, usually a
   small fraction of the ceiling, sometimes zero) and the largest effect
   ever recorded (the most a test could plausibly find). A change that
   would need to beat every effect this metric has ever produced is
   priced as a long shot, whatever the ceiling says. Without a store the
   estimate is unanchored, and the hand-back says so in those words.
3. **The MDE at the surface's traffic.** `gallop.power` at the longest run
   the surface can afford. Sizing a change nobody could measure is
   sizing a belief.

## The verdicts

- **Largest recorded effect at or above the MDE.** A test can find what
  this lever produces. Route to `designing-experiments` with the anchored
  mean as the expectation and the ceiling as the upper bound.
- **Ceiling below the MDE.** Even total success is invisible at this
  traffic. Decide without a test and write that down, or propose a change
  big enough to be seen; a copy tweak on a surface with a sixteen percent
  MDE is a hope, not a hypothesis.
- **Anchored mean near zero, ceiling large.** The usual case. The
  opportunity is real and the lever is unproven; the test is worth
  funding if the ceiling justifies the traffic, and the expectation stays
  at the anchored mean until the readout says otherwise.

## The gap is not the prize

"Users who add a payment method in their first session convert at 41%
against 9%." The 32-point gap multiplied by every signup is not the value
of forcing the step. The two groups differed before the behaviour: the
ones who added a card had already decided. The ceiling for a mandatory
step is not the gap, and the realistic size comes from what onboarding
changes have moved before, from the prior store, or from nothing. The
hypothesis is the step, randomised, with signups as a guardrail, because
a mandatory step also loses people. This is the trap case from
`routing-questions`, seen from the sizing side, and it is the single most
common way a roadmap number is wrong by an order of magnitude.

## Assumptions visible

An opportunity estimate is a chain of assumptions, and the hand-back lists
them as line items with their values: the affected share, the capture
share, the conversion from the on-platform metric to the business number,
the horizon. Then, when the readout lands under the estimate, the
conversation is about which assumption was wrong rather than about
whether the estimate was right. The line everyone skips is the last
conversion: on-platform behaviour into an off-platform business claim
(sessions into sales, signups into revenue, redemptions into retained
customers). It is usually the least certain number in the chain and it
belongs on the page with its source.

## Cost on the same page

A sized opportunity is half a decision. The other half is what the change
costs: engineering time, the surface it occupies, the tests it displaces,
the guardrail it risks. The verdict a PM needs is the two side by side,
and it is the PDS's to write, because nobody else in the room has both
numbers.
