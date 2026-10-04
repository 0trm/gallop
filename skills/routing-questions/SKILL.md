---
name: routing-questions
description: Routes an incoming product question to the method it deserves before any analysis starts. Asks who decides what on the answer, checks what the team already knows, whether the metric can be trusted, whether the question is description, a forecast or causation, whether the decision is made once or continuously, and who assigned the treatment. Use when a product, analytics, or experimentation request first arrives, when someone asks for a deep dive or a dashboard, or before opening a query editor on any question about impact, lift, or whether something worked.
---

# Routing questions

One decision, one lookup, three questions, one gate, run before any query is
written. The output is a routing decision and a filled intake record, never a
number. Many questions leave without an analysis, and that is the point: they
exit at the lookup as already answered, after it as curiosity, or at the gate
as metric work. Dying there is a good outcome, because the alternative was
shipping a wrong answer.

Run the whole pass even when the destination seems obvious. The pass takes a
minute; a mis-routed question costs a sprint.

## Step 0 · The decision: who decides what, on this answer?

Ask first: **who decides what differently, based on the answer?** A named
person and a named choice: "Priya, the checkout PM, keeps or reverts the
one-page checkout." The choice is what the person does in the product or
the business, never the analysis: "run an A/B test" or "measure it" is a
method, and the steps below choose the method. When the request already
says who decides, or that nobody has, answer from it and ask only when it does
not. A ticket someone filed for the work that names no decider already says:
the person who filed it, or the team it names, decides, and what they do with
the answer is the choice, even when the ticket does not say what that is.
Answer it and continue; raise the decision in the hand-back, not before the
route. The answer frames every
step after it: what counts as settled at the lookup, and what shape the
hand-back takes.

Four answers:

- **Firm.** The decider has named the choice. Continue.
- **Tentative.** A best guess at the choice and the person, not yet
  confirmed by them. A team or "leadership" is tentative until one person
  owns the call, and so is a ticket someone filed for the work. Continue;
  the record stays marked tentative.
- **None.** Nobody can name a choice that changes on the answer: the
  question came up in passing, or the request says nothing rides on it. The
  question is curiosity.
  Curiosity is not worthless, but it is not fundable with traffic or with
  analyst time.
- **Made.** The decision the answer would inform is already taken and will
  not be revisited: a large decision already made has a value of zero. A
  launch that already shipped is not made while keeping or reverting it is
  still open.

None and made still get the lookup, because an entry that settles the
question costs nothing to hand back. If the lookup does not settle it, say so
and route the question to the backlog, not to a method.

## Step 1 · The lookup

Before scoping anything, search the knowledge layer: the knowledge repo (past
reports and decisions) and the prior store (what each metric has actually
moved by). Read the prior store's entries for the question's metric.

When the project names knowledge bases, search each with your own tools (its
connector, or Read and Grep for a folder) before you answer. A document that
settles the question is linked in the intake record, which also says what
you searched.

Three outcomes:

- **Settled.** An entry answers this question and nothing since has expired
  it. Hand back the entry and stop. This is a lookup, not an analysis, and it
  is the cheapest exit on the map.
- **Stale.** An entry exists but the product has changed under it (check the
  entry's `expires_on` condition and `conditions` field). The question enters
  with a prior instead of a blank page; carry the old effect size forward as
  the expectation.
- **New.** No entry. Continue.

## Step 2 · The gate: do I trust the metric?

Underneath everything: do I trust this metric and the definition of success?
Signals that the answer is no:

- Two dashboards disagree on the number and nobody can say which is right.
- The metric has no registry entry, no owner, or no stated source of truth.
- The event it is built on is known to be unreliable or recently changed.
  A break someone suspects and nobody has confirmed is not yet a signal: the
  question is the move itself, and step 3 takes it.
- Nobody has written down how the metric gets gamed.

If any of these hold, **route to `defining-metrics`** and stop. The
measurement work is the actual work; every exit above the floor inherits a
wrong definition without ever raising an error. Do not run the analysis "in
the meantime".

One narrow exception, and it never reaches a forecast or a test: exploratory work may run
on a provisional metric when a named person signs off, the defect is bounded
and cannot change the answer, and the result files no belief. An
unreconciled discrepancy is not a bounded defect, so the two-dashboards case
above is not eligible. The reason goes on the registry line as `blocked` or
`deferred`, which is what turns the refusal into the floor's backlog rather
than losing it. Conditions in `defining-metrics`; an experiment's primary
metric has no such exit.

## Step 3 · Description, a forecast, or a change?

Read the question's own verbs, and the time they point to.

- *What, where, how many, who, what happened* → **description.** Exploratory
  work: funnels, segmentation, deep dives, opportunity sizing. Hands back **a
  hypothesis**, not an answer. Route to **`forming-hypotheses`**: the floor
  first, then the move localised and sized; the hypothesis re-enters this
  routing at step 4 as a change question, with the same decision.
- *What will it be, how many will we get, where will it land*: one metric's
  value in a window that has not happened yet, wanted so someone can set a
  plan on it (a hiring plan, a budget, a target, stock) → **a forecast.**
  This is **prediction**: route to **`building-models`**, whether the
  forecast is made once or every period; step 4 is not asked. It hands back
  a point and an interval under no change, and the model still needs volume,
  history and a trusted floor. A change planned inside the window is a
  second question: the forecast routes here, the change through its own
  intake.
- *Because, caused, lift, impact, worth it, did it work*, about a change
  someone made or plans to make → **a change question.** Continue to step 4.
  Who gets what, per user or per item (a ranking, an allocation), is a change
  question too: acting on the list is the change, and step 4 decides whether
  it recurs.

People routinely ask a causal question in the words of a descriptive one and
vice versa. Separating them is most of this step's value. A move with no known
change behind it, where nothing shipped, is description even when the request
asks what caused it: sizing localises it before anyone names a cause. So is a
move put down to a suspected change nobody has confirmed, a release or a
tracking change that "may be related": sizing confirms and scopes the move,
then lines it up with what changed. A request for the numbers as they stand,
to size what a planned change puts at stake, is description too: sizing hands
back the stakes, and the change re-enters at step 4 if anyone asks what it would
do. A descriptive request whose number already exists in a dashboard is
answered with the dashboard's link, not a query, even when the request asks for
SQL. *How many* is description until it points past today: how many signups
came in last quarter is description; how many will come in next quarter is a
forecast.

## Step 4 · Decided once, or continuously?

- **Once** – a ship-or-kill call → continue to step 5.
- **Continuously** – per user, per day, at volume → this is **prediction**:
  a ranking or an allocation. It belongs to statistical modeling,
  not to the causal branch: route to **`building-models`**. Two rules
  travel with it: the model needs volume and a trustworthy measurement
  floor, and the model itself still needs an experiment before anyone
  claims it moved anything – a churn model that predicts beautifully says
  nothing about whether the campaign works.

A choice made per user or per item, many times, at volume (each Monday's
recipients, each day's prices) is continuous, even when the request asks for
one test. A keep-or-kill on a programme, even one reviewed every year, is
once.

## Step 5 · Who assigned the treatment?

The only true fork on the map.

- **You can randomise, or could still hold something back** → route to
  **`designing-experiments`**. Hands back an effect size. A change that has
  not shipped is here, even one planned for everyone.
- **Assignment already happened** – the change has shipped: by launch date,
  geography, self-selection, a rollout to everyone → route to
  **`choosing-causal-designs`**. Hands back an effect size plus the
  assumptions it rests on.
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
**`writing-reports`**: the report, the knowledge-repo entry, and the
prior-store record, filed before the ticket closes. A forecast made once, for
a plan, closes with the knowledge entry alone. Routing is not finished
until the loop is; a finished analysis whose result goes nowhere is the loop
staying open.

## The intake record

Fill the intake record in the team's issue tracker as you route: the
question, the decision it informs and who makes it, the lookup result,
the metric's registry status, the type, the assignment answer, the
destination skill, and the expected hand-back. If a field is empty, the
question is not ready to be ranked, which is a cheaper argument to have than
the one about priorities.

## Worked routings

| The question as it arrives | Route | Why |
|---|---|---|
| "Mobile checkout conversion dropped four points. What happened?" | `forming-hypotheses` | Pure what-happened. The floor first, then funnel and segment until it localises; a sized hypothesis comes back |
| "Does the one-page checkout increase completion?" | `designing-experiments` | You control who sees which checkout |
| "We rolled new pricing to everyone in March. Did it help?" | `choosing-causal-designs` | Assignment already happened, non-randomly |
| "Users with notifications retain better. Push everyone to enable?" | `designing-experiments` | The trap case: randomise the prompt, not the outcome |
| "Which users get the win-back discount this week?" | `building-models` | Decided continuously at volume; uplift, not propensity; the impact is an experiment |
| "Didn't we try this two years ago?" | the lookup | An entry, or a prior. Not an analysis |
| "Our activation number differs across two dashboards." | `defining-metrics` | A foundation crack; everything above it inherits the error |
| "What did the summer campaign do? It ran everywhere." | no comparison group | Say so; refer out; offer a holdout for the next one |
| "Do users in cities use us differently than rural users?" | the backlog | It came up in a meeting; nobody decides anything differently on the answer |
| "How many trial signups will we get next quarter? The hiring plan is set on it." | `building-models` | A forecast a plan rests on: a point and an interval under no change; step 4 is not asked |

## Two rules that close the pass

**No mechanism, no test.** If the requester cannot write the mechanism – if
we change X, metric Y moves because Z – there is nothing to confirm or
falsify, and whatever comes back will be explained after the fact.

**No exposure log, no effect.** If nothing records who actually experienced
the change, no method downstream can recover the number. A proxy for who was
exposed (support tickets, a list someone reconstructs from memory, the
accounts that "look like" the ones picked) is no exposure log. The first rule
kills the questions that were never going to teach anything; the second kills
the answers that were never going to be true.
