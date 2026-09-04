# <What moved, in one line: metric, direction, size, window>

<date · surface(s) · requested by · the decision this unblocks>

**Against which baseline.** <Same period last year, trend, seasonal
pattern. The ordinary wobble (week-to-week sd) beside it, and whether
the move is outside it.>

**The floor, checked.** <Raw volumes by day for numerator and
denominator; what shipped in the window; the source-of-truth count;
the calendar. One line each, with the result. If any is live, the
record stops here and goes to defining-metrics.>

**Where it localised.**
- Mix or rate: <rate effect / mix effect, in metric units, and the
  share of each>
- Funnel step: <the step carrying most of the change, and its share>
- Segment: <the segment ranked first by contribution, with its raw and
  adjusted p, out of N cuts examined>

**The mechanism.**
> <If we change X, metric Y moves by about Z, because W. One sentence.
> If it cannot be written, there is no hypothesis yet.>

**The size.**
- Ceiling: <gap × units affected, per period>
- Anchored estimate: <prior-store mean and largest recorded effect for
  this metric, or "unanchored: no store">
- MDE at this surface's traffic: <value, at the longest affordable run>
- Assumptions, as line items: <affected share · capture share ·
  on-platform to business conversion, with source · horizon>

**Verdict.** <the floor first / not a question / a hypothesis worth
testing / too small to measure>

**Route.** <designing-experiments (randomise what) / choosing-causal-
designs (assignment already happened how) / defining-metrics / backlog>

---

Filing rules: one record per question, attached to the question issue.
It re-enters routing-questions at step 3 as a change question. It does
not contain an effect size, it does not recur, and the cuts examined are
never left out.
