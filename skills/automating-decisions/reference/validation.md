# Validation

What has to be true before an offline number means anything, in the order
the skill checks it.

## Split by time

Production scores units whose outcome has not happened yet, using a model
fit on units whose outcome has. Validation has to look the same: fit on
rows before a cutoff, score rows on or after it.

`gallop.validate.time_split` takes the row dates and returns the masks.
Two details an improvised split gets wrong:

- **The gap.** A unit whose label window straddles the cutoff carries
  information from after it. Leave a gap the length of the label horizon
  (`gap` in days) between the last training row and the first test row:
  a 30-day churn label needs a 30-day gap.
- **Several cutoffs.** One cutoff gives one estimate. Three or four rolling
  cutoffs give a sense of how stable the lift is across seasons, which is
  the thing that decides whether the model survives the year.

Random k-fold cross-validation on time-ordered data is the most common
reason a model that scored 0.9 offline scores 0.6 live. It is not a
validation and the skill treats a number from it as unvalidated.

## The leakage taxonomy

A feature is leaking when it carries the outcome, or information from
after it, into the training set. `gallop.validate.leakage_screen` ranks
features by how well each separates the outcome on its own and flags
anything above a threshold; a single feature with an AUC of 0.97 has
almost never earned it. The kinds, in the order to check:

- **The outcome under another name.** A cancellation reason, a refund
  flag, a "last active" date computed after the churn window closed.
- **Recorded after the outcome.** Fields written by the process the
  outcome triggers: a win-back email sent because the user churned, a
  support ticket opened at cancellation.
- **Aggregates that include the test window.** A 90-day average computed
  over the whole table before the split, so training rows contain test
  outcomes.
- **Duplicates across the split.** The same user on both sides, with a
  near-identical feature row.
- **A proxy of the label.** Not leakage strictly, but a feature the
  decision can act on only after the outcome, such as "payment failed".

A flagged feature is removed or explained; explained means a sentence
saying why it is available at scoring time and not downstream of the
outcome.

## The operating point

A decision acts on the top k of a ranking. Everything about the model
that matters happens there, and AUC, which averages over every possible k,
says little about it. `gallop.validate.baseline_lift` reports, at the k
the decision uses:

- **Precision at k**: the outcome rate among the targeted units.
- **The base rate**: the outcome rate among everyone.
- **Lift**: precision over base rate. A lift of 1 is a coin toss dressed
  as a model; a lift of 3 at the top decile on a 8% base rate means the
  targeted units convert at 24%.
- **Recall at k**: the share of all outcomes the targeted set captures,
  which bounds how much any policy acting on that set can move the metric.

If k is not yet chosen, report lift at two or three candidate points and
let the cost of the treatment choose. Lift always falls as k grows.

## Calibration

A ranking needs no calibration. A threshold, an expected value or a
budget allocation does: "treat everyone above 30%" is only a decision if
30% means 30%. `gallop.validate.calibration` returns:

- A **reliability table**: mean score against observed rate, per bin. The
  bins should sit on the diagonal.
- The **Brier score**, mean squared error of the probabilities, against
  the Brier score of always forecasting the base rate. The skill score
  `1 - brier / brier_base` is the share of the base-rate error the model
  removes; at or below zero the model is worse than the base rate.
- The **Murphy decomposition**: reliability (calibration error, lower is
  better), resolution (how far the bins' observed rates sit from the base
  rate, higher is better) and uncertainty (the base rate's own variance,
  fixed). Brier = reliability − resolution + uncertainty.
- **Expected calibration error**, the weighted mean gap between score and
  observed rate across bins.

Calibration drifts before ranking does. It is the first production check
to schedule.

## Volume

For a classifier, the out-of-time window needs enough positives that the
lift at k has an interval narrower than the lift itself. A working rule:
a few hundred positive outcomes in the test window; at the top decile
that gives a few dozen targeted positives, the least that separates a
lift of 2 from a lift of 1. Below that, the model cannot be told from the
base rate and the verdict is not fundable. The hand-back at that volume
is a rule on one or two fields, with the metric it is judged on and the
volume at which a model becomes checkable.
