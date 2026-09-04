# Decomposition

Two identities that turn "the metric moved" into "this is what moved it".
Both are exact, so the shares they produce sum to the change and nothing
is left to interpretation.

## Mix versus rate

A rate over a population is a weighted average of segment rates:

    R = Σ s_i · r_i        s_i = share of units in segment i, r_i = its rate

Between two periods it changes because rates changed or shares changed:

    ΔR = Σ (r_i' − r_i) · (s_i + s_i')/2               the rate effect
       + Σ (s_i' − s_i) · ((r_i + r_i')/2 − R̄)         the mix effect

with R̄ the average of the two overall rates. `gallop.explore.mix_rate`
computes both from segment counts, and the two sum exactly to the change.
The centring on R̄ costs nothing in the sum (share changes sum to zero)
and makes each segment's term readable: a growing segment that converts
below the whole drags the total down, a shrinking one that converts above
it drags too. Each segment contributes a term to each effect, and those
terms are the ranking that matters: a segment's contribution to the
total, not the size of its own swing.

**Reading the output.**

- **Rate effect dominates.** Segments got better or worse. The surface,
  the flow, the product is where to look next, and the funnel step
  decomposition says where.
- **Mix effect dominates.** The population changed. Acquisition, a
  campaign, a channel shift, a market launch, a bot wave. No segment did
  it; the traffic did. The hypothesis is about who arrives, and the owner
  is upstream of the surface.
- **Simpson's case.** Every segment improved and the total fell. This is
  a pure mix move and the function flags it by name, because it is the
  case most often reported backwards.

One cut at a time. A decomposition by channel and another by platform
each explain the whole change on their own terms; they are two views, not
two halves. A shift in one dimension shows up in every other dimension's
view as a rate effect, spread across the cells: when paid social's share
triples, every platform cell now carries more paid-social traffic and
every platform cell's rate falls by about the same amount. The tell is
uniformity. A rate effect that is the same size in every cell of a view
is a mix shift in some other dimension, and the view that shows it as a
mix effect is the one that found the cause.

## Funnel steps

Overall conversion is a product of step rates:

    C = n_K / n_1 = Π r_k        r_k = n_k / n_{k−1}

so its change in logs is a sum:

    log(C'/C) = Σ log(r_k'/r_k)

`gallop.explore.funnel_steps` reports each step's term and its share of
the total. The step with the largest share is where the change happened,
and it is the step to cut by segment; the other steps are noise for this
question. When two steps carry opposite signs (one improved, one got
worse) both are reported, because a redesign that helps one step and
hurts the next is a common shape.

Log shares are exact but can exceed one in magnitude when steps offset
each other; read the sign and the size together.

## What decomposition cannot do

It says where, not why. A rate effect in the payment step on Android is a
location, and the mechanism (a broken wallet integration, a new fee, a
competitor's launch) is the hypothesis the next step writes. And it
inherits the floor: decomposing a tracking change produces a precise
location for a bug.
