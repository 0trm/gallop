# The floor first

Most sudden moves in a product metric are changes in what is counted, not
in what people did. This is the checklist that runs before any segment is
cut, and the tells that say which kind of move you are looking at.

## What to check, in order

1. **Raw event volumes by day.** The numerator event and the denominator
   event separately, not the rate. A rate stays flat while both halve, and
   a rate falls when only the denominator doubles. Plot both.
2. **Every step of the funnel together.** If landing views, starts and
   completions all fell by the same share on the same day and the step
   rates are flat, nothing in the flow changed. Either fewer people were
   counted or fewer people arrived. Both are upstream of the surface.
3. **What shipped in the window.** Tracking releases, tag-manager
   publishes, SDK and app-version rollouts, consent or cookie banner
   changes, redirects and URL changes on tracked pages, bot and internal
   traffic filters, sampling thresholds, a renamed event, a new surface
   nobody instrumented. A step change on a release day with no product
   change is tracking until proven otherwise.
4. **A source of truth the tracking does not touch.** Orders in the
   database, accounts created, invoices, support tickets. If the truth is
   flat while the measured number fell, the number fell and nothing else
   did. This one check settles most cases.
5. **The calendar.** Partial days at either end of the window, a timezone
   boundary that moved, late-arriving events, a backfill that has not run,
   a holiday in one market.
6. **The definition.** Did anyone change the metric's query, filter or
   window? `defining-metrics` keeps the registry; check the entry's notes
   and owner.

## The tells

- **Consent banners.** A new or stricter banner reduces the share of
  visitors who are measured, not the share who convert. Every client-side
  number falls together; server-side counts do not move.
- **App releases.** A drop confined to one platform and one app version,
  starting on the rollout day and growing with adoption, is an SDK or
  event bug in that version.
- **Numerator without denominator.** Completions fall, starts do not: a
  broken completion event, or a real flow problem. The source-of-truth
  count decides which.
- **Round-number cliffs.** A metric that fell to exactly zero for a
  segment, or a step that fell to a suspiciously round share, is a filter
  or a join, not behaviour.
- **Sampling.** Reports built on sampled data drift as traffic crosses
  the sampling threshold; the unsampled export disagrees.

## What to hand over

When the floor is live, the hand-back is a measurement finding, not a
behavioural hypothesis: which event, which day, which release, the
source-of-truth comparison, and the size of the counting error. It goes
to `defining-metrics`, which fixes the definition or the instrumentation
and re-enters the question once the number can be trusted. Analysing the
drop "in the meantime" produces a story about a bug.
