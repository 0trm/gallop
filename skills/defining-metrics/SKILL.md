---
name: defining-metrics
description: Turns a metric name into a computation, a source of truth, a registry entry, and a written statement of how it will be gamed, then decides whether it is trustworthy enough to promote. Use when defining a north-star or guardrail metric, when two dashboards disagree on the same number, when arbitrating between conflicting metric definitions, or when a readout depends on a metric nobody has validated.
---

# Defining metrics

The floor. Not a stage: everything above it inherits its errors, and a wrong
definition does not raise an error, it returns a confident number.

> **Status: stub.** Frontmatter is final; the promotion gate is not yet written.
