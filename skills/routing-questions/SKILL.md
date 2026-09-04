---
name: routing-questions
description: Routes an incoming product question to the method it deserves before any analysis starts. Checks what the team already knows, whether the metric can be trusted, whether the question is description or causation, whether the decision is made once or continuously, and who assigned the treatment. Use when a product, analytics, or experimentation request first arrives, when someone asks for a deep dive or a dashboard, or before opening a query editor on any question about impact, lift, or whether something worked.
---

# Routing questions

One lookup, three questions, one gate, run before any query is written. The
output is a routing decision and a filled intake record, never a number. Most
questions leave without an analysis, and that is the point: roughly one
request in five dies at the gate, and dying there is a good outcome, because
the alternative was shipping a wrong answer.

Run the whole pass even when the destination seems obvious. The pass takes a
minute; a mis-routed question costs a sprint.

## Step 0 · The lookup

Before scoping anything, search the theory layer: the knowledge repo (past
readouts and decisions) and the prior store (what each metric has actually
moved by). If the team keeps a gallop prior store, read it with:

```
python -m gallop.priors read --store <path> --metric <metric>
```

Three outcomes:

- **Settled.** An entry answers this question and nothing since has expired
  it. Hand back the entry and stop. This is a lookup, not an analysis, and it
  is the cheapest exit on the map.
- **Stale.** An entry exists but the product has changed under it (check the
  entry's `expires_on` condition and `conditions` field). The question enters
  with a prior instead of a blank page; carry the old effect size forward as
  the expectation.
- **New.** No entry. Continue.

## Step 0.5 · The kill rule

Ask: **who decides what differently, based on the answer?** A named person and
a named choice. If nobody can name the decision that changes, the question is
curiosity. Curiosity is not worthless, but it is not fundable with traffic or
with analyst time; say so and route it to the backlog, not to a method.

A large decision that is already made has a value of zero. Check that too.

## Step 1 · The gate: do I trust the metric?

Underneath everything: do I trust this metric and the definition of success?
Signals that the answer is no:

- Two dashboards disagree on the number and nobody can say which is right.
- The metric has no registry entry, no owner, or no stated source of truth.
- The event it is built on is known to be unreliable or recently changed.
- Nobody has written down how the metric gets gamed.

If any of these hold, **route to `defining-metrics`** and stop. The
measurement work is the actual work; every exit above the floor inherits a
wrong definition without ever raising an error. Do not run the analysis "in
the meantime".

## Step 2 · Description, or a change?

Read the question's own verbs.

- *What, where, how many, who, what happened* → **description.** Exploratory
  work: funnels, segmentation, deep dives, opportunity sizing. Hands back **a
  hypothesis**, not an answer. Route to **`sizing-opportunities`**: the floor
  first, then the move localised and sized; the hypothesis re-enters this
  routing at step 3 as a change question.
- *Because, caused, lift, impact, worth it, did it work* → **a change
  question.** Continue to step 3.

People routinely ask a causal question in the words of a descriptive one and
vice versa. Separating them is most of this step's value. A descriptive
request whose number already exists in a dashboard is answered with a link,
not a query.

## Step 3 · Decided once, or continuously?

- **Once** – a ship-or-kill call → continue to step 4.
- **Continuously** – per user, per day, at volume → this is **prediction**:
  a forecast, a ranking, an allocation. It belongs to statistical modeling,
  not to the causal branch: route to **`automating-decisions`**. Two rules
  travel with it: the model needs volume and a trustworthy measurement
  floor, and the model itself still needs an experiment before anyone
  claims it moved anything – a churn model that predicts beautifully says
  nothing about whether the campaign works.

## Step 4 · Who assigned the treatment?

The only true fork on the map.

- **You can randomise, or could still hold something back** → route to
  **`designing-experiments`**. Hands back an effect size.
- **Assignment already happened** – by launch date, geography, self-selection,
  a rollout to everyone → route to **`choosing-causal-designs`**. Hands back
  an effect size plus the assumptions it rests on.
- **No comparison group exists and none can be reconstructed** – e.g. a
  campaign that ran everywhere at once with nothing held back → the honest
  exit: say out loud that there is no defensible number at this level, refer
  the question to whoever owns the right data, and offer the one thing you
  can give: a holdout design for the next one, if they come before the plan
  is locked.

Before a launch ships, "can you randomise?" is a choice, not a fact. If the
question arrives pre-launch, push the fork upstream: hold out a slice of
users, stagger the rollout by market or cohort, or randomise the prompt
rather than the feature. A feature refined without a flag is a feature you
will be reading with interrupted time series in three months.

Watch for the trap case: "users who do X retain better, should we push
everyone to X?" The observed gap is self-selection, not effect. Route it to
`designing-experiments` (randomise the prompt), never to a comparison of
adopters against non-adopters.

## After the answer

Every routed question that produces a decision closes through
**`writing-readouts`**: the readout, the knowledge-repo entry, and the
prior-store record, filed before the ticket closes. Routing is not finished
until the loop is; a finished analysis whose result goes nowhere is the loop
staying open.

## The intake record

Fill `templates/jira-question-issue.md` (in this plugin's repo) as you route:
the question, the decision it unblocks, the lookup result, the metric's
registry status, the type, the assignment answer, the destination skill, and
the expected hand-back. If a field is empty, the question is not ready to be
ranked, which is a cheaper argument to have than the one about priorities.

## Worked routings

| The question as it arrives | Route | Why |
|---|---|---|
| "Mobile checkout conversion dropped four points. What happened?" | `sizing-opportunities` | Pure what-happened. The floor first, then funnel and segment until it localises; a sized hypothesis comes back |
| "Does the one-page checkout increase completion?" | `designing-experiments` | You control who sees which checkout |
| "We rolled new pricing to everyone in March. Did it help?" | `choosing-causal-designs` | Assignment already happened, non-randomly |
| "Users with notifications retain better. Push everyone to enable?" | `designing-experiments` | The trap case: randomise the prompt, not the outcome |
| "Which users get the win-back discount this week?" | `automating-decisions` | Decided continuously at volume; uplift, not propensity; the impact is an experiment |
| "Didn't we try this two years ago?" | the lookup | An entry, or a prior. Not an analysis |
| "Our activation number differs across two dashboards." | `defining-metrics` | A foundation crack; everything above it inherits the error |
| "What did the summer campaign do? It ran everywhere." | no comparison group | Say so; refer out; offer a holdout for the next one |

## Two rules that close the pass

**No mechanism, no test.** If the requester cannot write the mechanism – if
we change X, metric Y moves because Z – there is nothing to confirm or
falsify, and whatever comes back will be explained after the fact.

**No exposure log, no effect.** If nothing records who actually experienced
the change, no method downstream can recover the number. The first rule kills
the questions that were never going to teach anything; the second kills the
answers that were never going to be true.
