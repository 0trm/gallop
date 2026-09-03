# Contributing

## What a good contribution looks like

**A skill covers one failure mode.** It names the confident wrong number it
prevents, fits one of the six positions (routing, the measurement floor,
description, causation, prediction, the theory ceiling), stays under 500
lines of `SKILL.md`, keeps references exactly one level deep, and ships with
at least one eval in `evals/` that demonstrably degrades without the skill
loaded. Fixes and sharpenings of the existing six are worth more than new
surface.

**A package function earns its place** only if a skill calls it and an agent
improvising it would plausibly get it wrong. It takes and returns arrays or
DataFrames, never a database connection, and comes with a test that
reproduces a number from a published source or a closed-form case.
Dependencies stay at numpy, pandas, scipy.

**A method dispute is a contribution.** If you think a check is wrong, a
threshold misjudged, or a design recommendation harmful, open an issue with
the method-dispute template. An argued position in the tracker is the point
of having one.

## What gets rejected

- Breadth without depth: a seventh bucket, a taxonomy extension, a skill
  that covers a topic rather than preventing a failure. The position count
  is a design decision; this repo was built once before and abandoned at 53
  documents, and the gate exists because of that.
- Restating what a capable model already knows. A skill earns its tokens by
  changing behaviour, which is what the evals test.
- New runtime dependencies, database drivers, or a CLI framework.
- Anything whose asset provenance is unclear. See NOTICE; git history is
  permanent.

## Running the checks

```bash
pip install -e ".[dev]" markdown-it-py
pytest                              # the package
ruff check src tests scripts        # lint
python3 scripts/validate_skills.py  # skill limits (500 lines, frontmatter, depth)
python3 scripts/run_evals.py        # eval structure
python3 site/build.py --check       # site and README in sync with the skills
```

CI runs all five; green locally means green in the PR.
