# Repo conventions

gallop is a theoretical framework: eight agent skills in markdown and the docs
site that presents them. The repository holds no package, plugin, server or
eval harness.

## The taxonomy is the gate

Six positions: routing, the measurement floor, three method buckets
(description, causation, prediction), and the knowledge ceiling. Every skill
traces to exactly one; causation carries three skills, description and
prediction one each. A proposal that needs a seventh position is refused, not
accommodated.

## Skills

- Gerund-form kebab-case directory names, matching the `name` field exactly.
- `SKILL.md` body under 500 lines. If it will not fit, cut coverage. Never split
  a skill to get under the limit; one skill per position.
- References sit exactly one level below `SKILL.md`. Never deeper: Claude
  partially reads files reached through a chain.
- Reference files are named for their content, `interference.md`, not `advanced.md`.
- Forward slashes everywhere.
- A skill states the method, never a command: the test, the threshold, the
  inputs and what to report.

## Site

`site/build.py` renders the skill pages, the knowledge, install and about pages,
and the README skills table from the skills and `site/content/`. Run it after
changing a skill, and `python3 site/build.py --check` before committing.

## Assets

Nothing whose provenance is unclear enters the history. Git history is permanent
and deleting a file later does not remove it. No font binaries, no inlined
font data, no icons of borrowed lineage.

No text, label, registry line or task id from a holdout enters the repository,
a pull request or a note.

## Prose

Flat and declarative. State the finding, give the evidence, give the fix. No
hype adjectives, no em dashes, no emoji in code or commit messages.

## Running the skills

`docs/orchestration.md` is the wiring: the path a question takes through the
skills and the state they share.
