# Propensity versus uplift

Two models that look alike on a dashboard and target different people.

## The four kinds of unit

Cross whether a unit responds without the treatment with whether it
responds with it:

| | Responds if treated | Does not respond if treated |
|---|---|---|
| **Responds if untreated** | Sure thing | Sleeping dog |
| **Does not respond if untreated** | Persuadable | Lost cause |

The treatment only earns its cost on persuadables. It is wasted on sure
things, wasted on lost causes, and harmful on sleeping dogs, the users a
retention email reminds to cancel.

A **propensity model** estimates the chance of the outcome. Its top decile
is full of sure things (about to convert anyway) or, for a churn model,
lost causes (leaving whatever you send). Persuadables sit in the middle of
the list, where a top-k policy never reaches them.

An **uplift model** estimates the difference the treatment makes:
P(outcome | treated) minus P(outcome | not treated), per unit. Its top
decile is the persuadables, and its bottom decile, when negative, is the
sleeping dogs, the people the campaign should skip.

## What uplift needs

Randomised rows. Every unit in the training data was assigned the
treatment or the control at random, and the outcome was logged for both
arms. That is the only data in which the arm is independent of everything
else about the unit, so the model can learn the difference rather than the
targeting.

Observational rows cannot supply it. If marketing sent the offer to
whoever looked risky, the treated and untreated units differ in exactly
the ways that predict the outcome, and a model fit on them learns
marketing's rule. It will confidently reproduce last quarter's targeting.

If no randomised data exists, the experiment comes first. Route to
`designing-experiments`: randomise the offer across the eligible
population, log exposure, run long enough for the outcome to mature, and
train the uplift model on those rows. The experiment doubles as the
impact readout of the untargeted campaign, which is the baseline the model
later has to beat.

## Fitting it

Any of the standard constructions works and none is in the package:

- Two models, one per arm, uplift as the difference of their predictions.
  Simple; the difference of two noisy estimates is noisier still.
- One model with the arm as a feature and interactions, uplift as the
  prediction with the arm flipped.
- The class-variable transformation, which turns uplift into a single
  classification target when the arms are balanced.

The choice matters less than the validation.

## Reading the Qini curve

`gallop.validate.qini` ranks the randomised rows by score, targets the
top share, and counts the outcomes gained over what the control rate
predicts for that many units. The curve runs from zero to the whole
population's incremental outcomes; the diagonal is random targeting. Area
above the diagonal is the model's value, and a curve that rises, peaks and
falls says the bottom of the list contains sleeping dogs: stop targeting
where the curve peaks, not at a round percentage.

Precision at k, AUC and calibration are propensity metrics. Reported for
an uplift model they measure the wrong thing.

## When propensity is still the right model

When the question is who will do something rather than whom to treat:
fraud scoring, demand at a location, support routing, capacity. Nobody
intervenes on the unit scored, so the correlation the model learned is
the one that holds. The line to draw: if the score decides who receives a
treatment meant to change the outcome, the model has to be uplift.
