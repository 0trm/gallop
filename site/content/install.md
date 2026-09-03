# Install

Three ways in, in order of least friction. The skills are the interface; the
Python package underneath exists because six calculations must be identical
every time.

## Claude Code plugin

```
/plugin marketplace add 0trm/gallop
/plugin install gallop@gallop
```

All six skills, invoked by name or picked up automatically when a question
matches one. The bundled scripts call the `gallop` package, so add
`pip install gallop` if you want the checks to run rather than be described.

## Any other agent, or none

A skill is a directory of markdown. Copy what you need:

```
git clone https://github.com/0trm/gallop
cp -r gallop/skills/reading-experiments .claude/skills/
```

Works with anything that reads Agent Skills, and reads fine as prose:
each `SKILL.md` is the procedure, the `reference/` files one level down are
the depth.

## The package

```
pip install gallop
```

`numpy`, `pandas`, `scipy`, nothing else. Every function takes and returns
arrays or DataFrames, never a database connection; SQL for the three
queries every readout needs ships as `string.Template` files in `sql/`.

Prove it works in fifteen seconds, no configuration, no warehouse:

```
python -m gallop.examples.quickstart
```

That runs one simulated experiment through every check: an MDE, the SRM
verdict, an exposure ratio, a CUPED-adjusted effect with an always-valid
interval, and the same effect shrunk toward a seeded prior store.

## The modules

| Module | What it computes |
|---|---|
| `gallop.power` | MDE, sample size, duration; two-proportion and continuous |
| `gallop.trust` | Sample ratio mismatch; exposure versus eligibility |
| `gallop.variance` | CUPED against a pre-period covariate |
| `gallop.sequential` | Always-valid confidence sequences; O'Brien-Fleming bounds |
| `gallop.shrink` | Empirical Bayes shrinkage toward the prior store |
| `gallop.priors` | The prior store and metric registry on disk, validated JSONL |

Each runs as a script too: `python -m gallop.trust srm --counts counts.csv`.

## What it is not

Not an experimentation platform. It does not assign traffic, hold flags, or
replace your warehouse. It routes the question, then runs the checks that
stop the answer being a confident wrong number.
