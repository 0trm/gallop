# Choosing the randomisation unit

The unit is the thing the coin flip assigns. It fixes what the analysis may
treat as independent, so it is the first choice and the least repairable.

## The rule

Randomise on the unit that (a) experiences the treatment consistently and
(b) the primary metric is defined on. When those two disagree, the analysis
must aggregate to the randomisation unit, and the design must accept the
power cost of doing so.

## The options

**User (stable ID).** The default. Survives sessions and devices if the ID
does; check the identity join before trusting it. Anonymous or logged-out
traffic randomised on cookies leaks across devices and clears; if the
surface is pre-login, accept the dilution and note it, or move the test
post-login.

**Session or pageview.** Only when the treatment is genuinely stateless (a
ranking tweak, a latency change) and the metric is per-session. Never when
the user can notice the interface changing between visits: inconsistency is
itself a treatment, and not the one being tested.

**Cluster: city, market, store, team.** When the treatment cannot be held to
individuals (pricing a market, a courier bonus, anything word-of-mouth) or
when interference forces it (see interference.md). The effective sample size
is closer to the number of clusters than the number of users; a two-country
product has two clusters and therefore, for most designs, none to spare.

**Time slice (switchback).** The whole system flips between treatment and
control on a schedule. The standard answer for marketplaces and anything
with shared supply. Randomise the schedule, analyse at the time-slice
level, leave burn-in gaps between flips so carry-over from one period does
not contaminate the next.

## The mismatch that produces false positives

Randomise on users, analyse on sessions, and every user contributes several
correlated rows that the test treats as independent. The standard errors
shrink, the false positive rate multiplies, and nothing looks wrong in the
readout. Under a true null this can reject several times the nominal rate.

The fix is mechanical: aggregate to the randomisation unit before testing
(one row per user), or use a variance estimate that respects the clustering
(delta method or a bootstrap over units). What is not available is reading
the session-level t-test and hoping.

Ratio metrics hide the same trap: sessions-with-conversion / sessions is a
per-session metric under user randomisation. Aggregate to per-user rates, or
delta-method it. The naive interval can be roughly half the honest width.

## Practical checks

- Write the unit into the analysis plan as a sentence: "randomised on
  user_id from the assignment service; analysis aggregates to user."
- Confirm assignment is sticky: the same unit gets the same arm on every
  visit, across the whole test. Re-bucketing mid-test is an SRM in the
  making and an experience bug besides.
- Confirm the unit exists before exposure. Assigning at signup a treatment
  that changes the signup page is assigning downstream of treatment, and
  the arms are no longer comparable populations.
