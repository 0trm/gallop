# Evals

Three scenarios per skill. Each is a JSON file with `skills`, `query`,
`files` (workspace contents), and `expected_behavior`. An eval earns its
place only if behaviour visibly degrades without the skill loaded; the
mechanical checks a capable model already performs unprompted are not worth
an eval, which is a finding from running these, not a guess (see below).

## Running

```bash
python3 scripts/run_evals.py                       # structure check (CI runs this)
python3 scripts/run_evals.py --run                 # execute all, with skill
python3 scripts/run_evals.py --run --without-skill # the ablation
python3 scripts/run_evals.py "routing-*" --run --model opus
```

`--run` builds a temp workspace per eval (bundled files written in, the
skill copied into `.claude/skills` unless ablated) and prints the transcript
beside `expected_behavior` for grading. Grading is by reading; there is no
judge model.

## What discriminates, from the first full run (2026-09-03, Sonnet)

All 18 passed with the skill loaded. The ablations showed a pattern worth
keeping in mind when writing new evals:

- **Mechanical checks do not discriminate.** The baseline model catches a
  blatant SRM, knows peeking inflates error rates, and names self-selection
  unprompted. An eval built on those tests nothing.
- **Judgment discriminates.** Without the skill the model funds the
  untestable test with an "acceptable false negative", proceeds with a
  decline analysis on an unreconciled metric, treats p = 0.01 assignment
  counts as a defect to hedge around rather than a pass at the 0.001
  convention, and hand-waves a winner's-curse discount instead of computing
  the shrinkage. The refusals, thresholds and verdicts are the content.

Two skill fixes came out of the run: the SRM eval was rewritten as an
alpha-discipline case, and the causal-designs selection table gained the
guard against reading an everywhere-at-once campaign as ITS.

## The prediction skill's evals, from the second run (2026-09-04)

Three evals for `automating-decisions`, run with and without the skill on
Sonnet. Two findings worth keeping:

- **Run the ablation on Sonnet, explicitly.** The claude CLI's default
  model is whatever the user last set, and a first pass ran on a stronger
  model that already refused the model-as-evidence claim and built the
  holdout unprompted. On Sonnet the baseline offers a propensity-matched
  "directional" number for the deck, thresholds the propensity score
  without naming the sure-things and lost-causes problem, and plans the
  model at any volume; with the skill it does none of those. Pass
  `--model sonnet` so the ablation measures the skill and not the model.
- **Size the not-fundable case below the skill's own rule.** The first
  draft of the volume eval gave 300 conversions a month, which is 900
  positives in a three-month window and fundable by the skill's own
  threshold; the model applied the rule correctly and reached the wrong
  verdict for the eval. Resized to 45 a month. The rerun also showed the
  model routing round the rule with pooled rolling folds and "validate as
  data accrues", so the skill now says outright that rolling folds do not
  create outcomes and that a thinner model with a warning is the failure
  the verdict exists to prevent.
