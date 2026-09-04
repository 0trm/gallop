---
name: sizing-opportunities
description: Turns a what-happened question into a localised, sized hypothesis: rules out the measurement floor before any behavioural story, decomposes a moved metric into mix and rate, splits the change across funnel steps, scans segments with the number of cuts declared, and sizes the opportunity as a ceiling and a prior-anchored estimate against the MDE, then hands the hypothesis back to routing as a change question. Use when a metric moved and someone asks what happened, when asked for a deep dive, a funnel or segment analysis, a root cause, or an opportunity size before a roadmap commitment, or when an observed gap between two groups is about to be quoted as the value of closing it.
---

# Sizing opportunities

The description position on the map: the box that asks what is happening.
It tells you that checkout completion fell nine points for mobile users in
Germany. It cannot tell you why, and it is not supposed to. What it hands
back is a hypothesis worth testing, a guess with a shape: if we change X,
metric Y moves by about Z, because W. Its failure mode is being mistaken
for causation, and its wasted form is the deep dive that ends in a
dashboard nobody decides from.

Two exits are cheaper than any analysis and come first. A number that
already exists in a dashboard is answered with a link. A recurring number
someone needs weekly is a dashboard the data engineers own: build it once,
hand over the link, and mean it. What remains is a question, and it ends
here as a hypothesis with a size, routed back through `routing-questions`
as a change question.

The arithmetic is scripted. Given segment counts for two periods:

```
python skills/sizing-opportunities/scripts/size_opportunity.py \
  --segments segments.csv --before 2026-07 --after 2026-08 \
  [--funnel funnel.csv] \
  [--store priors.jsonl --metric checkout_rate --baseline-rate 0.034 --units-per-day 7000]
```

Or individually via `python -m gallop.explore`.

## 0 · The floor, before any story

A sudden move is instrumentation more often than behaviour, and a
behavioural story told about a tracking change is the most expensive
wrong answer this position produces. Before a single segment is cut:

- **Raw volumes, not the rate.** Did the numerator event and the
  denominator event each fire at their usual volume, day by day? A rate
  hides a denominator that halved. When every step of a funnel falls by
  the same share on the same day and the step rates stay flat, the flow
  did not change; what is counted did, or who arrived.
- **What shipped.** A tracking release, a tag-manager publish, an SDK or
  app version, a consent banner, a redirect, a bot filter, anywhere in
  the window. A step change on a release day with no product change is
  tracking until proven otherwise.
- **A source of truth.** A count the tracking does not touch: orders in
  the database, accounts created, revenue booked. If it is flat while the
  measured number fell, the number fell and nothing else did.
- **The calendar.** Partial days, a timezone boundary, late-arriving data,
  a backfill that has not landed.

If any of these is live, the question belongs to `defining-metrics` and
there is no behavioural story yet. The checklist and the tells:
[reference/floor-first.md](reference/floor-first.md).

## 1 · What moved, against which baseline

State the movement as a number against a baseline that could have been
wrong: the same period a year ago, the trend, the seasonal pattern, never
just last week. Beside it, the ordinary wobble: the metric's week-to-week
standard deviation over the last year. A move inside the wobble is not a
question; say so and stop. A move outside it gets a date range and a
direction, and the work below.

## 2 · Mix, or rate

A rate metric moves for two reasons that call for different owners: the
segments got better or worse (a rate effect), or the population shifted
toward segments with different rates (a mix effect). Decompose before
cutting (`gallop.explore.mix_rate`): the two effects sum exactly to the
change, and each segment's share of each is on the table. Simpson's case
is common enough to check for by name: every segment improved and the
total fell, because traffic shifted toward a low-converting segment. A
mix move points at acquisition and traffic, not at the surface; a rate
move points at the surface. One tell before believing a rate move: a
rate effect of about the same size in every cell of a view is a mix shift
in some other dimension, seen from the wrong side. Mechanics:
[reference/decomposition.md](reference/decomposition.md).

## 3 · Where in the funnel

Overall conversion is the product of step rates, so its change splits
across steps (`funnel_steps`): each step's share of the log change, and
the step that carries most of it. Localise to a step before cutting by
segment. Forty segments across six steps is two hundred and forty cuts,
and something is always wrong in two hundred and forty cuts.

## 4 · Segments, with the count declared

Cut the localised step by segment, ranked by contribution to the total
change, never by the size of the segment's own swing: a small segment that
halved moved the total less than a large one that slipped a point. Every
cut examined is counted, and the count goes in the hand-back beside the
false-discovery adjustment (`mix_rate` flags the period-on-period changes,
`scan_segments` the cross-sectional gaps), because in forty cuts at the
usual threshold two look significant under nothing at all. Prefer
behavioural segments (what users did) to demographic ones (who they are);
the first suggests a mechanism, the second suggests a stereotype. What a
segment result is and is not:
[reference/segment-scan.md](reference/segment-scan.md).

An interesting segment is a hypothesis for a test, filed as one. It is
not a finding, and it is not the cause.

## 5 · The gap is not the prize

Sizing turns a localised hypothesis into a number a roadmap can weigh,
and three numbers are needed every time (`size_opportunity`):

- **The ceiling.** The whole gap closes for everyone affected. It is the
  most the change could be worth, and it is almost never what the change
  is worth.
- **The anchored estimate.** What this metric has actually moved by in
  the prior store when someone pulled a lever: the mean effect, which is
  the planning number, and the largest ever recorded, which is the most a
  test could plausibly find. Without a store, say the estimate is
  unanchored.
- **The MDE at the surface's traffic.** From `gallop.power`, at the
  longest run the surface can afford.

The verdict follows from the three. Largest recorded effect at or above
the MDE: a test is worth funding, route to `designing-experiments`.
Ceiling below the MDE: nothing measurable is at stake; decide without a
test and write that down, or make the change bigger. Gap between
self-selected groups: the ceiling is not the gap at all, because the
groups differed before the behaviour, and the hypothesis is a prompt or a
nudge to be randomised, never a comparison of adopters against the rest.
Assumptions stay visible, so that when the readout lands under the
estimate the argument is about which assumption was wrong. The rest,
including the off-platform conversion everyone skips:
[reference/sizing.md](reference/sizing.md).

## 6 · The hand-back

One record, [templates/hypothesis.md](templates/hypothesis.md): what moved
and against what baseline; the floor checks run; where it localised (mix
or rate, step, segment); the mechanism in one sentence; the three sizing
numbers and the verdict; the number of cuts examined; and the route. It
re-enters `routing-questions` at step 3 as a change question. It is not a
report, it does not recur, and it does not contain an effect size.

## The verdict

One of four, stated plainly:

- **The floor first** → `defining-metrics`; no behavioural story until
  the measurement is cleared.
- **Not a question** → inside the ordinary wobble, already in a dashboard
  (a link), or no decision changes on the answer (the backlog).
- **A hypothesis worth testing** → sized, with its three numbers, routed
  to the causal branch.
- **Too small to measure** → decide without a test, written down, or a
  bigger change proposed.

## Worked requests

| The request as it arrives | Verdict | Why |
|---|---|---|
| "Signups dropped 18% since Tuesday. Root cause by tonight?" | the floor first | Every funnel step fell together on a release day with flat step rates; tracking or arrivals, not the flow |
| "Conversion fell from 3.5% to 3.2%. Which segment did it?" | decompose first | If the mix shifted, no segment did it; rank by contribution, declare the cuts |
| "Users who add a payment method convert 4x. Size making it mandatory." | the gap is not the prize | Self-selection; anchor on what onboarding changes have moved, randomise the step |
| "Can you do a deep dive on retention for leadership?" | not a question | No decision named; ask what would change on the answer, then scope or backlog |
| "How did the adoption pages do in Portugal last month?" | a link | The number exists; a recurring number is a dashboard the data engineers own |
| "Is a 2% lift on checkout worth a quarter of engineering?" | size it | Ceiling, anchored estimate, MDE; the verdict is a number against a cost |
| "Mobile checkout fell four points. What happened?" | a hypothesis | Floor, baseline, mix or rate, step, segment; then a sized hypothesis to test |
| "Our conversion is below the industry benchmark. Opportunity?" | not a question yet | A benchmark is a different population; localise a gap you own before sizing it |
