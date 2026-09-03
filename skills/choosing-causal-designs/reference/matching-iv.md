# Matching, and instrumental variables

The two designs for self-selection, in descending order of how often they
apply. Both answer "did adopting X cause Y" when individuals chose X
themselves; both rest on assumptions stronger than the other designs in
this skill, and the readout must say so.

## Matching (and its regression cousins)

**The claim being made:** adopters and non-adopters differ *only* on things
you observed and matched. Selection on observables. Say the claim out loud
before running anything, because it is a strong one: the reason someone
adopted is usually the hardest thing to observe (motivation, intent, need).

**When it is defensible:**

- The selection mechanism is substantially captured by the observables:
  adoption driven by tenure, platform, plan, geography, prior usage, and
  you have all of those.
- Rich pre-treatment behaviour exists. Pre-period activity is the best
  proxy for the unobservables, for the same reason CUPED works: past
  behaviour absorbs stable individual differences.

**How to run it honestly:**

1. Match or weight on pre-treatment covariates only (propensity scores,
   nearest-neighbour, or plain stratification; the choice matters less
   than the covariate set).
2. **Report balance**, before and after matching, on every covariate. An
   unbalanced match is not a design.
3. Trim to common support: units with no counterpart on the other side
   get dropped, and the readout says which population remains.
4. **Sensitivity analysis**: how strong would an unobserved confounder
   need to be to erase the effect? If a confounder as strong as the best
   observed covariate would kill it, the result is fragile, and that
   sentence belongs in the readout.
5. Compare against the naive gap. If matching barely moves the raw
   difference, either selection is weak (good, argue it) or the
   observables miss the selection entirely (likely, admit it).

**The honest framing:** matching produces "the difference not explained by
what we could measure", which is an upper bound on the causal effect
whenever the unmeasured selection points the usual direction (the
motivated adopt). Say "upper bound" when that is what it is.

## Instrumental variables

**The shape:** something (the instrument) shifted uptake of the treatment
without touching the outcome through any other path. Effect = the outcome
shift attributable to the instrument, scaled by the uptake shift.

**Real instruments in product work are rare and mostly man-made:**

- **A randomised encouragement**: the prompt experiment from
  `designing-experiments` (randomise the nudge, instrument adoption with
  the nudge). The one instrument you can always manufacture, and the
  reason the trap case routes there.
- A staggered rollout's timing, where order was operationally arbitrary.
- An outage or eligibility quirk that blocked uptake for some users for
  reasons unrelated to them.

**The two conditions, both mandatory:**

1. **Relevance** – the instrument actually moves uptake, testably: report
   the first stage. A weak first stage (F < 10 as the classic screen)
   makes everything downstream noise amplified.
2. **Exclusion** – the instrument touches the outcome *only* through
   uptake. Untestable, and where candidates die: the prompt that annoys
   users touched the outcome twice.

**Interpretation:** IV estimates the effect on *compliers*, the units whose
uptake the instrument changed, not on everyone. For a prompt instrument
that is exactly the population the decision is about, which is why
encouragement designs are the clean case.

## Choosing between them

Ask what drives selection. Observable and measured → matching, with the
sensitivity analysis. Unobservable → IV if a real instrument exists,
otherwise this question has no comparison group yet; see
[no-comparison-group.md](no-comparison-group.md), and remember the
encouragement design converts "no instrument" into "instrument next
sprint".
