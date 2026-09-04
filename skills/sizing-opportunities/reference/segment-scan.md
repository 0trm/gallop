# The segment scan

What a segment result is, what it is not, and the discipline that keeps a
deep dive from finding whatever it went looking for.

## The forking paths

Six dimensions with six or seven levels each is forty cuts. At the usual
threshold, two of forty look significant when nothing is happening, and
the analyst who stops at the first one has found noise. The defence is
mechanical and it is in `gallop.explore`:

- **Every cut is counted.** The scan reports how many segments it
  examined. That number goes in the hand-back next to the result, so the
  reader can judge one striking segment against the forty it was picked
  from.
- **False-discovery adjustment.** Benjamini-Hochberg across all cuts,
  with the adjusted p beside the raw one. A raw p of 0.02 that is the
  smallest of forty adjusts to about 0.8; it is not evidence of anything.
- **Ranked by contribution, not by swing.** A segment of four thousand
  units that lost a point moved a total of two hundred thousand by
  almost nothing. Contribution to the total change is the sort order;
  the segment's own change is a detail.

## What a segment result is

A hypothesis with a location: "the payment step on Android in Spain fell
from 3.8% to 2.9%; if a wallet integration broke in the last release,
fixing it recovers about a tenth of the total drop". It goes into the
hand-back as a hypothesis, sized by its contribution, and it is tested
before anyone calls it the cause. An unregistered segment found while
exploring is a hypothesis for the next test, the same rule
`reading-experiments` applies to unregistered segments in a readout.

## What it is not

- **Not the cause.** A segment where the metric fell is where the fall
  shows, not why it happened.
- **Not an effect size.** "Users who did X convert 4x" is a gap between
  two populations that chose themselves. The gap is not what making
  everyone do X would produce; see sizing.
- **Not a finding, on its own.** Without the count of cuts and the
  adjustment, a striking segment is an anecdote with a p-value.

## Which segments

- **Behavioural over demographic.** What users did (arrived from search,
  used the wallet, opened the app twice) suggests a mechanism. Who they
  are (age band, country, plan) suggests a stereotype and rarely a lever.
- **Cohort over period.** Retention read by calendar period mixes users
  of every age; read it by signup cohort or the mix shift masquerades as
  a trend.
- **Survivors.** A segment defined by an outcome (users still active in
  month three) has already selected on the thing being measured. Segment
  on what was true at the start.
- **Averages hide distributions.** A mean session length rising because
  a few bots spent hours is not engagement. Look at the median and the
  tails before segmenting the mean.

## When to stop cutting

When the change has localised to a step and a segment that together
carry most of it, and a mechanism can be written in one sentence. Cutting
past that point finds smaller segments with larger swings and less
meaning. Time-box the scan and hand back what is localised; the next
segment is the next question, not this one.
