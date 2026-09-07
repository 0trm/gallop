# Why gallop

Product data science has two kinds of tooling, and neither does the whole job. Libraries carry the statistics and assume you already know which question you are answering: statsmodels estimates, dowhy identifies, causalml targets, and none of them has an opinion about whether the question deserved an analysis. Skill packs for product managers carry that judgment and contain no statistics at all. The place a number goes wrong sits between the two: a question that should have been a lookup becomes a deep dive, a metric nobody validated becomes a readout, a launch with no comparison group gets an effect size anyway.

gallop puts the routing and the rigour in the same place, as agent skills. A question arrives and the first skill runs one lookup against what the team already knows, three questions, and one gate on whether the metric can be trusted. Most questions leave there, and leaving there is the intended outcome. The rest get the method that matches how the treatment was assigned, sized from the effects the metric has actually produced rather than from a number that would be nice, and read out with the checks a wrong number needs to fail: sample ratio mismatch, exposure against eligibility, a sequential bound, variance reduction, shrinkage toward the prior. What the answer teaches is written back before the ticket closes, so the next question starts smaller.

It ships as skills rather than as a library because a skill is where the judgment lives. A library can compute a minimum detectable effect; it cannot decline to compute one for a metric nobody trusts. The Python package underneath is thin on purpose. It exists because six calculations must come out identical every time, and an agent improvising a sequential bound is the most reliable way to get a different answer each run.

## Who it is for

The data scientist embedded in a product team, and the analyst or product manager who runs tests without a platform doing the safety checks for them. Not for research scientists, or for anyone whose experimentation platform already fills in the detectable effect from a prior store. Those people have this problem solved.

## What it is not

Not an experimentation platform. It does not assign traffic, hold flags, or replace your warehouse. It assumes those exist and writes the part that decides whether the number they produced is true.

## What the logo means

The mark is one horse carrying one rider, drawn three times.

- **The horse is the measurement framework.** It carries everything, it sits underneath everyone, nobody looks at it while things are going well, and if it goes lame nothing arrives no matter how good the rider is.
- **The rider is the product data scientist.** Routing and judgment: which method the question deserves, what the answer would cost, how much confidence it can carry.
- **The three positions are one question moving through the map**, from description to cause to decision. One rider drawn three times, not three riders.
- **The destination is a decision.** Growth is what accumulates when enough of them are right.

The metaphor carries one idea and stays decorative for everything else: nothing arrives without the horse. A logo where every line has to mean something turns into a quiz.

## See also

- [The method map](../map/): the buckets, the layering, why measurement is a floor rather than a phase, and why theory is a ceiling rather than a report.
- [The intake](../intake/): the routing pass the rider runs on every request.
