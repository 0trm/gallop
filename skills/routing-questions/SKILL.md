---
name: routing-questions
description: Routes an incoming product question to the method it deserves before any analysis starts. Checks what the team already knows, whether the metric can be trusted, whether the question is description or causation, whether the decision is made once or continuously, and who assigned the treatment. Use when a product, analytics, or experimentation request first arrives, when someone asks for a deep dive or a dashboard, or before opening a query editor on any question about impact, lift, or whether something worked.
---

# Routing questions

The front door. One lookup, three questions, one gate, run before any work starts.

Most questions leave without an analysis, and that is the point: a question the
team has already answered does not need an exit, and a question resting on a
metric nobody trusts is a measurement problem wearing an analysis costume.

## The exits

| Exit | Skill | Hands back |
|---|---|---|
| The metric is not trustworthy | `defining-metrics` | A number the rest of the map can stand on |
| Description | *(v1.1: `sizing-opportunities`)* | A hypothesis |
| Causation, and you can randomise | `designing-experiments` | An effect size |
| Causation, and assignment already happened | `choosing-causal-designs` | An effect size, plus its assumptions |
| Decided continuously, at volume | *(v1.1: `targeting-decisions`)* | A ranking or an allocation |
| Any of the above, once answered | `writing-readouts` | A belief, filed where the next question starts |

> **Status: stub.** Frontmatter is final; the routing pass is not yet written.
> The argument this encodes is in [the intake algorithm](https://0trm.github.io/gallop/intake/).
