---
name: designing-experiments
description: Designs an A/B test around the four choices that cannot be repaired after launch: the randomisation unit and whether units interfere, the minimum detectable effect sized from prior experiments rather than from a wish, exposure logging rather than eligibility logging, and a decision rule written before traffic starts. Use when planning, powering, or pre-registering an experiment, when deciding whether a question is testable at the available traffic, or when a feature is about to ship without a flag.
---

# Designing experiments

Four choices, none of which a bigger sample can fix afterwards. The output is
an analysis plan attached to the ticket before the flag exists: unit, MDE,
duration, guardrails, logging spec, and a decision rule. No plan, no flag.

Precondition: the primary metric comes from the registry with `trusted`
status (`python -m gallop.priors registry --registry metrics.jsonl --status
trusted`). If it is not there, this question belongs to `defining-metrics`
first. And the hypothesis has a mechanism: if we change X, metric Y moves
because Z. No mechanism, no test.

## Choice 1 · The randomisation unit, and interference

Pick the unit the treatment actually touches, then check whether treating
one unit changes another unit's experience. The full decision guides are
[reference/randomisation-unit.md](reference/randomisation-unit.md) and
[reference/interference.md](reference/interference.md); the short form:

- Default to the **user** (stable ID, consistent across sessions and
  devices). Randomising sessions or pageviews when the metric is per-user
  breaks the analysis before it starts.
- If units share supply, a feed, a market, an inventory, or each other's
  attention, the control group gets treated through the back door and the
  effect reads larger than it is. That is **switchback or cluster
  randomisation, decided now or never**. No sample size fixes interference.
- One live test per surface, in its own layer. Splitting the same scarce
  audience across concurrent tests buys the same answers with wider
  intervals plus an interaction risk nobody will notice.

## Choice 2 · The MDE, from the prior store

The minimum detectable effect is a fact about traffic and history, not an
ambition. Compute it before anyone commits to the test:

```
python skills/designing-experiments/scripts/size_test.py \
  --store priors.jsonl --metric activation_rate \
  --baseline-rate 0.12 --units-per-day 8000
```

The script reads what this metric has actually moved by across past tests,
computes the MDE at the available traffic (the arithmetic is
`2.8 × sqrt(2p(1-p)/n)` at the usual thresholds), and returns a verdict:
fundable, or not at this traffic. Without a store, use `python -m
gallop.power mde` and say out loud that the target is unanchored.

Honest priors are humbling: most experiments move nothing, so the prior mean
is roughly zero and typical true effects are a fraction of what gets
proposed. If the MDE at your traffic is a 16% relative lift, a copy tweak is
not a hypothesis, it is a hope. The design responses, in order of value:

1. **Test a bigger swing.** Propose changes large enough to plausibly clear
   the MDE. Saying which those are, before design work starts, is the job.
2. **Spend effort on variance, not on more traffic.** A pre-period covariate
   for CUPED (plan the covariate now; it must be fully determined before
   first exposure), a primary metric with a higher base rate, denominators
   you control, targeting the segment where the effect should be largest.
3. **Move the primary metric closer to the change.** The nearer metric is
   powered; keep the deeper one as a directional guardrail and say in the
   plan that it is underpowered.
4. **Decide without a test, and write that down.** The most valuable
   sentence in the quarter: this question is not answerable at our traffic
   in under four months, so make the change bigger, pick a nearer metric,
   or decide it untested and record that we did.

Duration falls out of the same arithmetic (`size_test.py` prints it). A test
needing seven weeks will contain a holiday or a season; randomisation
handles it, interpretation does not. An effect measured across Christmas is
an effect measured across Christmas; the plan should say so.

## Choice 3 · Log exposure, not eligibility

The most common bug in the chain and the one that survives longest. If the
log records who was *bucketed* rather than who actually *saw* the variant,
the estimate is diluted toward zero and nothing downstream flags it,
because the test looks exactly like a test that ran.

- Define the exposure event now: the moment a unit actually experiences the
  treatment surface, fired identically in both arms (control fires it on
  seeing the control surface).
- Give the data engineers a specification, not a request: event name,
  parameters, when it fires, and the query the readout will run. "We will
  add tracking later" means the first weeks of data do not exist and a
  six-week test now needs eight.
- Ask for alerting on event volume. The two failures that ruin tests from
  below are a sample ratio mismatch and an event that stops firing on one
  platform; both are visible in volume within a day if anyone is looking.

## Choice 4 · The decision rule, before launch

Written on the ticket before traffic starts, in the form: *if the interval
excludes X, we ship; otherwise we do not.* Plus:

- **Guardrails attached up front**: crashes, latency, refunds,
  unsubscribes, and the gaming guardrail from the metric's registry entry.
  A guardrail breach means rollback, and a rollback is the system working.
- **Peeking policy decided now.** If anyone will look before the horizon
  (they will; the platform shows everyone a curve), the test is sequential
  from the start: `python -m gallop.sequential bound` for always-valid
  monitoring or `obf` for a fixed look schedule. Deciding this after
  looking is not available.
- **One pre-registered segment**, chosen from the mechanism, not eleven
  chosen from the readout.
- The full pre-registration template is
  [reference/pre-registration.md](reference/pre-registration.md).

## The design review, thirty seconds

Before the flag flips, the plan states: unit and interference call; MDE,
its source, and duration; exposure event and who owns its alerting;
decision rule, guardrails, peeking policy, segment. If any line is blank,
the test is not designed yet. If all are filled, file the plan on the
ticket; `reading-experiments` will hold the readout to exactly this plan,
and `writing-readouts` will file what it taught.
