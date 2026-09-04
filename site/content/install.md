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
`pip install gallop-pds` if you want the checks to run rather than be described.

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
pip install gallop-pds
```

`numpy`, `pandas`, `scipy`, nothing else. Every function takes and returns
arrays or DataFrames, never a database connection; SQL for the three
queries every readout needs ships as `string.Template` files in `sql/`.

Prove it works in fifteen seconds, no configuration, no warehouse:

```
python -m gallop.examples.quickstart
```

That runs one simulated experiment through every check. This is what it
prints:

```
gallop quickstart: one experiment through every check

1 · Size it before running it (gallop.power)
   at n=40,000 per arm on a 12.5% rate, the MDE is 0.66pp;
   detecting 0.35pp instead would need 140,159 per arm

2 · The trust gate (gallop.trust)
   SRM: chi2 0.16  p 0.689  -> pass
   exposure: pooled rate 97.00%  -> pass

3 · The effect, with CUPED (gallop.variance)
   raw    +0.292pp  se 0.234pp
   cuped  +0.306pp  se 0.227pp   variance reduction 6%

4 · An interval that survives peeking (gallop.sequential)
   always-valid 95% CI [-0.394pp, +1.005pp]   boundary |z| 3.08 (vs 1.96 fixed)
   significant under continuous monitoring: False

5 · Shrunk toward what this metric has done before (gallop.shrink + priors)
   prior from 8 readouts: mu +0.097pp   tau 0.065pp
   observed +0.306pp -> shrunk +0.113pp   (weight on data 0.08)

true simulated effect: +0.350pp. The shrunk estimate is the
one to write back to the store; the raw one is the winner's curse waiting.
```

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
replace your warehouse. It routes the question, then runs the
checks an answer has to pass before it ships.
