# How metrics get gamed

Goodhart's law, made operational: when a measure becomes a target, it stops
measuring. The registry requires a `gaming` statement because the failure is
predictable before it happens, and predicting it names the guardrail. None of
these require bad faith; each is a reasonable team optimising exactly what it
was told to optimise.

## The patterns

**Widen the numerator.** The cheapest game. "Activated" grows to
include lighter and lighter actions; the rate climbs while the behaviour it
stood for does not. Guardrail: pin the qualifying action list in the
definition and version any change.

**Shrink the denominator.** Filter out the users least likely to convert
(bots today, then low-intent channels, then a whole platform) and the rate
rises with no change in anyone's behaviour. Guardrail: report the
denominator's absolute size next to every rate.

**Move volume across the boundary.** A 7-day activation window teaches teams
to cram nudges into day 6 and steal from day 8. The metric improves; the
user's month does not. Guardrail: a longer-window twin of the same metric,
read directionally.

**Cannibalise the neighbour.** Clicks on the promoted module go up because
clicks on the module below it went down. Any surface-level metric can be fed
by its neighbours. Guardrail: a same-page total, so reshuffling nets to zero
unless something real happened.

**Harvest intent instead of creating it.** Attribution games: intercept users
who would have converted anyway (branded search, checkout interstitials) and
book them as caused. Guardrail: incrementality checks by experiment, not by
attribution model.

**Degrade the unmeasured.** Push the measured number by spending something
the registry does not watch: latency, support load, refund rate, trust.
Guardrail: the standing guardrail set (crashes, latency, refunds,
unsubscribes) attached to every experiment by default.

**Ship the prompt, not the product.** Any metric countable as "users who did
X once" is inflatable with a modal. The lift is real, the value is not, and
retention of the prompted cohort shows it. Guardrail: cohort retention of
prompted vs organic users on the same action.

## Writing the statement

One or two sentences in the registry `gaming` field, concrete enough to
recognise when it starts happening:

> `activation_rate` – gamed by widening the qualifying action list or by
> day-6 nudges that move activation inside the window without changing
> week-4 retention. Guardrail: week-4 retention of activated users, and the
> action list is versioned.

If no plausible gaming exists, write why. That is rare and worth recording;
it usually means the metric is very close to actual value exchange, which is
also the argument for its promotion.
