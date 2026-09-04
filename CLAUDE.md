# Repo conventions

## The taxonomy is the gate

Six positions: routing, the measurement floor, three method buckets
(description, causation, prediction), and the theory ceiling. Every skill and
every module traces to exactly one; causation carries three skills, description
and prediction one each. A proposal that needs a seventh position is
refused, not accommodated. This repo has been built once before and abandoned at
53 documents; the rule exists because of that.

## Skills

- Gerund-form kebab-case directory names, matching the `name` field exactly.
- `SKILL.md` body under 500 lines. If it will not fit, cut coverage. Never split
  a skill to get under the limit; one skill per position.
- References sit exactly one level below `SKILL.md`. Never deeper: Claude
  partially reads files reached through a chain.
- Reference files are named for their content, `interference.md`, not `advanced.md`.
- Forward slashes everywhere.
- `python3 scripts/validate_skills.py` enforces all of the above. CI runs it.

## Python

- `numpy`, `pandas`, `scipy`. Nothing else in the runtime dependencies.
- `# %%` cell markers, so every module runs as a script and opens as a notebook.
- A function earns its place only if a skill calls it and an agent improvising it
  would plausibly get it wrong.
- No module imports a database driver. SQL lives in `sql/` as `.sql.tmpl`,
  substituted with `string.Template` from the standard library.

## The checks

```
pytest                              # package tests, one file per module
ruff check src tests scripts        # lint
python3 scripts/validate_skills.py  # skill limits
python3 scripts/run_evals.py        # eval structure; --run executes with the claude CLI
python3 site/build.py --check       # generated pages and README table in sync
```

All five run in CI. `site/build.py` (not the skill files' copies) is the one
source for skill positions and the README table.

## Assets

Nothing whose provenance is unclear enters the history. Git history is permanent
and deleting a file later does not remove it. See NOTICE.

## Prose

Flat and declarative. State the finding, give the evidence, give the fix. No
hype adjectives, no em dashes, no emoji in code or commit messages.
