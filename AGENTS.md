# Orchestrating the skills

How the skills hand off to each other when an agent runs a product question
end to end. Any single skill stands alone; this file is the wiring.

## The path every question takes

```
question arrives
  └─ routing-questions            always first, even when the destination seems obvious
       ├─ exit: settled           hand back the knowledge-repo entry; stop
       ├─ exit: curiosity         no decision changes on the answer; backlog; stop
       ├─ defining-metrics        the metric cannot be trusted; fix the floor,
       │                          then RE-ENTER routing with the original question
       ├─ sizing-opportunities    exploratory work: the floor first, then the move
       │                          localised and sized; hands back a hypothesis, which
       │                          re-enters routing as a change question
       ├─ automating-decisions    decided continuously, at volume: a forecast, a
       │                          ranking, an allocation. Validated out of time,
       │                          then designing-experiments before it claims impact
       ├─ designing-experiments   you control assignment
       └─ choosing-causal-designs assignment already happened
              └─ (or the exit: no comparison group; say so; stop, and file the refusal)

experiment runs
  └─ reading-experiments          trust gate before the number, always
       └─ writing-readouts        every verdict, including nulls, broken tests
                                  and refusals; the ticket closes only when the
                                  readout, the belief and the prior-store record exist
```

## Rules that cross skill boundaries

- **The prior store is shared state.** `designing-experiments` reads it to
  size the MDE; `reading-experiments` shrinks toward it; `writing-readouts`
  appends to it. One JSONL file, schema in `templates/prior-store.schema.json`,
  read and written only through `gallop.priors`.
- **The registry gates the pipeline.** An experiment's primary metric must
  be `trusted` in the metric registry. If it is not, the question belongs to
  `defining-metrics` first, whatever the requester asked for.
- **Pre-registration binds the readout.** `reading-experiments` reads
  against the plan `designing-experiments` filed: the decision rule, the one
  segment, the peeking policy. No plan weakens every check downstream and
  the readout says so.
- **The loop is not optional.** A question that produced a decision but no
  knowledge entry and no store record is unfinished work, whichever skill
  last touched it.

## The package underneath

Skills call `python -m gallop.<module>` (power, trust, variance, sequential,
shrink, priors, validate, explore) and four bundled scripts:
`skills/designing-experiments/scripts/size_test.py`,
`skills/reading-experiments/scripts/run_checks.py`,
`skills/automating-decisions/scripts/validate_model.py` and
`skills/sizing-opportunities/scripts/size_opportunity.py`. If the package is not
installed, `pip install gallop-pds` (or from source,
`pip install git+https://github.com/0trm/gallop`); do not improvise the
statistics the modules exist to pin down.
