# The metric registry, field by field

One JSONL file, one metric per line, diffable in a pull request. The contract
is `templates/metric-registry.schema.json`; `gallop.priors` validates every
line on read and fails loudly with the line number on a malformed entry.

## Fields

| Field | Required | What goes in it |
|---|---|---|
| `name` | yes | Snake-case, the key the prior store uses. Never reuse a name for a changed definition; version it (`activation_rate_v2`) |
| `definition` | yes | The computation: numerator, denominator, window, dedup, filters, timezone. Precise enough to reimplement |
| `source` | yes | The one table or model that is the source of truth |
| `unit_of_analysis` | yes | What one observation is: `user`, `session`, `order`, `day`. Experiments randomise on this |
| `direction` | yes | `increase_good` or `decrease_good` |
| `role` | no | `primary`, `guardrail`, or `diagnostic`: how experiments may use it |
| `gaming` | yes | How the metric gets hit without the value being created, and the guardrail that catches it |
| `status` | yes | `trusted`, `provisional`, or `deprecated`. Only trusted metrics carry a readout |
| `owner` | no | The person who answers for the definition |
| `notes` | no | Stability facts (typical weekly swing, seasonality), proxy bridge, version history |

## A worked entry

```json
{"name": "activation_rate",
 "definition": "users with >=1 core action (save, share, or publish) within 7 days of signup / signups; excludes internal accounts and known bots; UTC day boundaries; user counted once",
 "source": "warehouse.marts.user_activation",
 "unit_of_analysis": "user",
 "direction": "increase_good",
 "role": "primary",
 "gaming": "widen the qualifying action list, or day-6 nudges that move activation inside the window without moving week-4 retention; guardrail: week-4 retention of activated users",
 "status": "trusted",
 "owner": "0trm",
 "notes": "weekly swing ~0.4pp under no intervention; signup mix shifts seasonally in September; v1 since 2026-05"}
```

## Reading it

```
python -m gallop.priors registry --registry metrics.jsonl
python -m gallop.priors registry --registry metrics.jsonl --status trusted
```

The second form is what `designing-experiments` runs: an experiment's primary
metric must come back from that filter. If it does not, the experiment is
blocked on `defining-metrics`, not on more traffic.

## Conventions

- The registry lives in version control next to the prior store. Changes go
  through review; the reviewer is the owner.
- A definition change is a new version, not an edit: deprecate the old entry
  (set `status`), add the new one under a versioned name, and note the
  changeover date on any chart or readout that spans it.
- The registry is append-friendly but not append-only: `status` and `notes`
  may be edited in place. History lives in git, which is one of the two
  reasons the format is JSONL. The other is that a registry nobody can
  review in a pull request is a registry that goes stale.
