# Orchestrating the skills

How the skills hand off to each other when an agent runs a product question
end to end. Any single skill stands alone; this file is the wiring.

## The path every question takes

```
question arrives
  └─ routing-questions            always first, even when the destination seems obvious
       ├─ exit: settled           hand back the knowledge-repo entry; stop
       ├─ exit: no_decision       nobody decides anything differently on the answer,
       │                          or the decision is already made; the backlog; stop.
       │                          Asked first; leaves after the lookup, unless the
       │                          lookup settles the question
       ├─ defining-metrics        the metric cannot be trusted; fix the floor,
       │                          then RE-ENTER routing with the original question.
       │                          The provisional exit (description only, signed
       │                          off, bounded defect, no belief filed) is the
       │                          one way past without fixing it first
       ├─ forming-hypotheses      exploratory work: the floor first, then the move
       │                          localised and sized; hands back a hypothesis, which
       │                          re-enters routing as a change question. A number
       │                          already in a dashboard is answered with the link
       ├─ building-models         a forecast a plan rests on, made once or every
       │                          period, or a ranking or an allocation decided
       │                          continuously. Validated out of time, then
       │                          designing-experiments before it claims impact
       ├─ designing-experiments   you control assignment
       ├─ choosing-causal-designs assignment already happened
       │      └─ (or the exit: no comparison group; say so; stop, and file the refusal)
       └─ before either causal route: no mechanism is the exit no_mechanism,
                                      no exposure log the exit no_exposure_log

experiment runs
  └─ reading-experiments          trust gate before the number, always
       └─ writing-reports         every verdict, including nulls, broken tests
                                  and refusals; the ticket closes only when the
                                  report, the belief and the prior-store record exist
```

## Rules that cross skill boundaries

- **The prior store is shared state.** `designing-experiments` reads it to
  size the MDE; `reading-experiments` shrinks toward it; `writing-reports`
  appends to it. One record per report, the same fields every time, kept where
  the team keeps its reports.
- **The intake record is the routing pass's shared state.** The question in
  the requester's words, the metric it rests on, every step's answer with its
  evidence, and the route it lands on, filled before any query is written.
- **One metric decides.** An intake names the metric the decision rests on,
  and may name others read beside it (also read) and guardrails, metrics that
  must not get worse. The gate decides on the first alone, as the skills gate
  the primary metric only; a metric beside it with no usable registry line is
  a mark on the outcome, never the floor.
- **The registry gates the pipeline.** An experiment's primary metric must
  be `trusted` in the metric registry. If it is not, the question belongs to
  `defining-metrics` first, whatever the requester asked for. The provisional
  exit does not reach here: it opens toward description, files no belief, and
  an experiment whose primary metric is provisional does not run.
- **Pre-registration binds the report.** `reading-experiments` reads
  against the plan `designing-experiments` filed: the decision rule, the one
  segment, the peeking policy. The absence of a plan weakens every check downstream, and
  the report says so.
- **The loop is not optional.** A question that produced a decision but no
  knowledge entry and no store record is unfinished work, whichever skill
  last touched it. A forecast made once, for a plan, is the exception: it has
  no effect size to store, so it closes with a knowledge entry holding the
  forecast, its interval and, once the window closes, the actual.
