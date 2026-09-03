# Interference

The assumption every standard A/B analysis makes without saying so: one
unit's assignment does not change another unit's outcome (SUTVA). When it
fails, the control group is treated through the back door, the comparison
is between two treated groups of different intensity, and the estimate is
biased in a direction you can sometimes predict and often cannot. No sample
size fixes it. It is decided at design time or not at all.

## Where it lives

**Shared supply.** Marketplaces, delivery, inventory, ad budgets. Pay one
courier more and they take the jobs a control courier would have taken; the
treatment effect reads as the sum of a real effect and a transfer. The
canonical false win.

**Feeds and social surfaces.** Treated users post more, everyone's feed
changes, control users respond to treated content. Effects leak both ways.

**Ranking and recommendation.** One model variant's clicks train the shared
model, or the variants compete for the same slate positions.

**Word of mouth and shared devices.** Features visible between users
(collaboration, gifting, referrals) recruit the control arm into treatment.

**Capacity.** Anything that saturates: support queues, fraud review,
promo budgets. Treatment consumes shared capacity; control experiences the
shortage.

## The design responses

1. **Switchback.** Flip the entire system between arms on a randomised
   schedule (hours or days). Handles supply-side interference directly.
   Costs: temporal correlation (analyse at slice level), carry-over
   (leave burn-in gaps), and day-of-week confounds (balance the schedule).
2. **Cluster randomisation.** Assign whole markets, cities, or social
   clusters, chosen so interference is contained within a cluster.
   Costs: effective n = number of clusters; needs many clusters to power.
3. **Budget-split / slate-split designs.** For ads and ranking: split the
   constraint itself (separate budgets, interleaved slates) so arms stop
   competing for one pool.
4. **Accept and bound.** If interference is plausibly small (a mostly
   single-player surface with a weak social edge), run user-level anyway,
   say so in the plan, and treat the estimate as an upper bound in the
   direction the leak inflates it. Written down before launch, this is a
   legitimate call; discovered afterwards, it is an excuse.

## The design-time question

Ask it in one sentence at the review: **if we treat half the users, does
the other half's experience change through any shared resource?** Name the
resource or name "none". If a resource is named, the design is switchback
or cluster, and the duration arithmetic must be redone at the new unit,
which usually changes the answer to "is this testable at our traffic".
