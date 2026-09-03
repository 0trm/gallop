# The embedded PDS

A day, a week, and a quarter inside the Purina Iberia product squad. One
data scientist, one stream of demand, two countries, and a purchase that
happens in a supermarket you do not own. This is the seat the six skills
were written for; the method map is the theory, this page is the practice.

## The room

Five people ship. The brand and category teams sit outside it, and their
requests still arrive.

- **Product manager.** Owns the roadmap for purina.es and purina.pt, the
  MyPurina loyalty flows, the vet and adoption services, sampling and
  coupon journeys, and the retailer click-out. The only source of demand
  this squad accepts.
- **Designer.** Owns the journeys in two languages against one design
  system. Wants to know where pet parents struggle and why, not which
  variant won.
- **Data engineers.** Own the event pipeline, the tables behind the metric
  catalog, and the joins to CRM and loyalty. Frequently one person,
  frequently shared with another market.
- **Developers.** Own the flags, the release train, and the front end.
  Often part vendor, which means your instrumentation requests are
  somebody's contracted scope.
- **Product data scientist.** You. Not the squad's analyst: the region's
  entire data function, which is why the refusals matter as much as the
  deliverables.
- **Outside the squad.** Brand and category teams own campaigns and media,
  and their measurement belongs to someone else. Their questions will
  still land on you. They go through the same gate, and most of them leave
  as a referral rather than an analysis.

## One stream, four exits

Every request from the roadmap runs through the same routing, and the
randomisation fork is only its last step. A request whose metric you do
not trust goes back to the measurement framework before anything else
happens. A request that asks what is happening, rather than what a change
did, is exploratory work, and it hands back a hypothesis rather than an
answer. A decision that gets made continuously rather than once is a
model. Only what survives all three reaches the fork, and the fork still
bites, because plenty of product work cannot be randomised: a CRM
programme whose tool cannot hold back a control, a coupon engine rebuild,
a site migration, a change the commercial team insists ships to every pet
parent at once, anything built before the flag existed.

## Three clocks

The day is the least interesting layer, and that is the point. The quarter
decides what the week works on; the week decides what the day watches. In
a one-person data function this is sharper still, because nobody else
notices that the quarter is empty: the day always looks full.

- **The day** runs on the platform health check and the standup. Catch
  breakage early, keep the squad from acting on numbers that are not yet
  numbers. Horizon: hours.
- **The week** runs on the sprint. Readouts become decisions, unstarted
  tests get an analysis plan, next sprint's tickets get their
  instrumentation. Horizon: two weeks.
- **The quarter** runs on the learning agenda. Which questions are worth
  traffic at all, given that you have very little of it. Horizon: a
  planning cycle.
- **The year** runs on the metric catalog. Definitions, the event
  contract, the loyalty joins. Nobody asks for this, and everything above
  it degrades without it.

## A day: Tuesday, mid-sprint

- **08:45 · Health check.** Not results: exposures against expectation,
  the sample ratio on each live test, guardrail alerts, and whether the
  Portuguese variant is receiving traffic at all, which is the failure
  that hides best. The platform does most of this; its willingness to do
  it is not the same as someone having looked, and you are that someone.
- **09:00 · The one deep task.** Ninety uninterrupted minutes on the
  week's real work: the redemption model, the interrupted time series on
  the migration, the sizing memo. This is the entire difference between a
  PDS and an analyst, and the day will try to take it from you before ten.
- **10:30 · Standup, fifteen minutes.** What you say: which tests are
  live, how many days remain, which tickets are blocked on
  instrumentation. What you do not say, ever, is an interim result. Hard
  to hold, because the platform will happily show the PM a curve on day
  three, and once a squad has seen a curve it has decided.
- **10:45 · The corridor.** "Can you check how the adoption pages did in
  Portugal last month?" This is where the intake gate earns its keep.
  Most corridor requests are description, and most descriptions are
  already in a dashboard or are the first half of a hypothesis worth
  writing into the agenda. The answer is rarely a pull. It is a link, or
  a question back: what would you do differently if the number were high?
- **11:30 · Backlog refinement.** The tickets being estimated for next
  sprint are where experiments are won or lost. Two things go on every
  one: the events it must fire, and whether it ships behind a flag. A
  feature refined without a flag is a feature you will be reading with
  interrupted time series in three months, explaining why the answer has
  assumptions in it.
- **14:00 · Design review.** The designer has three variants of the
  coupon claim step. You are not there to pick one. You are there to say
  what the funnel evidence supports, what each variant would have to move
  to be worth the traffic, and that at this volume three variants means a
  nine-week test rather than five, so pick one and make it a bigger
  change.
- **15:30 · The request that is not this squad's job.** A brand manager
  wants to know what the summer campaign did. It ran across both
  countries with nothing held back, so there is no comparison group and
  no honest answer at this squad's level. You say that, you point them at
  whoever owns media measurement, and you offer the one thing you can
  give: a holdout design for the next one, if they come before the plan
  is locked.
- **16:30 · Writing.** Tomorrow's readout, written before the numbers are
  final, with the decision rule first and the result pasted in last.
  Writing the interpretation after you see the number is how you end up
  interpreting the number.

The shape of a good day: one block of real work, one refinement session
that makes a future test possible, one request declined and replaced with
something better, and no interim results spoken out loud.

## A week: the sprint gives you the rhythm

A squad running a board already has a fixed week. The mistake is to let
analysis float outside it; attach each piece of the method to a ceremony
that already exists.

- **Monday · Planning, and the start gate.** Anything launching this
  sprint gets its analysis plan attached to the issue first: primary
  metric from the catalog, MDE, duration, guardrails, and the decision
  rule written as "if the interval excludes X we ship, otherwise we do
  not." No plan, no flag.
- **Tuesday · Readout.** Finished tests, in the room, with the PM and the
  designer present, and a decision recorded on the issue before anyone
  leaves. Effect size, interval, guardrails, then the one segment you
  pre-registered rather than the eleven the platform will happily slice
  for you. A readout that ends in "interesting, let us think about it"
  has failed, and the failure happened on Monday.
- **Wednesday · Refinement, then the non-randomised half of the job.**
  Instrumentation and flags onto next sprint's tickets in the morning; in
  the afternoon, the work that has no ticket: the ITS readout on the
  migration, the matched-cohort study on the loyalty base, the
  redemption forecast.
- **Thursday · The catalog and the pipeline.** Time with the data
  engineers on metric definitions and whatever is currently lying in the
  funnel. One afternoon a week here is what keeps every readout above it
  trustworthy, and it is the first thing that gets skipped.
- **Friday · The agenda and the archive.** Update the learning agenda
  with what the sprint answered and what it opened. Write the result onto
  the question issue so that in eight months someone can find out this
  was already tested.

A good platform makes peeking easier, not harder: anyone with a login sees
a live curve, so the classic defence, being the only person who can run
the query, is gone. Two replacements: configure the test as sequential up
front, so looking early is licensed rather than a violation; and agree
that a result is not a result until it appears in the Tuesday readout.
The second rule is social, and it is the one that actually holds.

What a full sprint looks like in volume: one or two live tests at a time,
one readout, one causal study in flight, two or three corridor requests
deflected, instrumentation on four or five tickets. If tests started keeps
climbing while tests read out does not, the programme is accumulating debt
rather than knowledge.

## The quarter: a list of questions, not tasks

A task backlog produces work. A question backlog produces knowledge, and
knowledge is the only thing that compounds across quarters. "Analyse the
coupon funnel" is a task and can be done badly forever; "does removing
the account step before coupon claim increase redemptions, or does it
just move people to a coupon they were never going to use in store?" is a
question, and it either gets answered or it does not.

Every entry carries: the question, written so two answers are imaginable;
the decision that changes on the answer, with a named owner; the method
bucket from the routing; the cost in traffic-weeks and which surface it
occupies; and the value, the size of the decision times how likely the
answer is to change it.

**The kill rule.** If nobody can name the decision that changes, the
question is curiosity. Curiosity is not worthless, it is just not fundable
with traffic, and it goes to the bottom of the list where it belongs.
Applying this out loud, in the room, once a quarter, is the most useful
thing a PDS does for a squad's focus.

The split that survives contact with reality: sixty percent
roadmap-driven, thirty percent foundational and PDS-initiated (metric
definitions, proxy validation, the study nobody asked for; first to be
cut, most expensive to have cut), ten percent held open, because something
urgent will happen and if you have not reserved for it, it eats the
foundational thirty. Six to ten questions a quarter is a realistic agenda
at this traffic level. Twenty is a wish list, and a wish list has the
same practical effect as no agenda at all.

**Keeping it out of the ticket graveyard.** The tracker will turn
questions into tasks unless you stop it: one issue per question, never a
sub-task of the feature that prompted it, because sub-tasks die with
their parent and the question outlives the feature. The workflow ends at
Decided or Archived-with-a-reason; there is no Done. The readout is
attached to the question, not to the ticket that ran it. And a feature
ticket is not done when the code merges: it is done when the events fire
in staging, the metric exists in the catalog, and the flag is configured.
Getting that into the team's shared definition of done is a ten-minute
retro conversation, and it removes the single most common cause of a test
starting a sprint late.

## Mid-quarter arrivals

It always does. Redemptions fall in Portugal; a retailer changes their
feed; someone senior saw a chart. The agenda only holds if there is a
visible, boring procedure for a new arrival, with a cost attached:

1. **The gate.** Do I trust the metric and the definition of success? If
   not, nothing else in the request is worth starting. Roughly one
   request in five dies here, and dying here is a good outcome, because
   the alternative was a confident wrong answer.
2. **The type.** Description, or a change? People routinely ask the
   second in the words of the first, and separating them is most of the
   value of the conversation.
3. **The cadence.** Decided once, or continuously? Once lands in the
   causal branch. Continuously is a model, and the model still needs an
   experiment before anyone claims it moved anything.
4. **Assignment.** Who assigned the treatment? A flag that could have
   held someone back is an experiment. Already shipped: match the method
   to how it shipped.

**The displacement rule.** Anything entering the quarter displaces
something already in it, and the PM names what. Not you. A backlog that
only grows is not a priority list, and it makes the one data person the
one who decides what never happens.

A large share of good intake ends without a query: the number already
exists and the person did not know where; the question was answered in a
readout eight months ago; or the honest response is that none of these
designs fit and there is no comparison group here, said out loud rather
than shipped as a number anyway.

## The traffic ceiling

One region gives you one audience, and every question spends some of it.
That single fact reaches further than any analysis choice: it decides
which ideas are worth designing, how many can run at once, and how long
the squad waits for an answer.

The arithmetic, once, so the squad stops arguing about it: for a two-arm
test at eighty percent power and the usual threshold, the smallest effect
you can detect is roughly `2.8 × sqrt(2p(1−p)/n)`, with `p` the baseline
rate and `n` the users per arm. On a four percent baseline with fifteen
thousand users per arm, a decent three weeks on a good surface here, that
is about 0.6 points, a sixteen percent relative lift. The same idea is a
fundable experiment on one of your surfaces and an untestable opinion on
another.

What follows from it:

- **Test bigger swings.** If only a sixteen percent relative change is
  visible, a copy refinement is not a hypothesis, it is a hope. You are
  the person who says which changes are big enough, before design work
  starts.
- **One live test per surface, and fewer of them.** Splitting the same
  scarce audience across concurrent tests buys the same answers with
  wider intervals and an interference risk nobody will notice.
- **Spend effort on variance, not on more traffic.** Pre-period
  covariates, a primary metric with a higher base rate, denominators you
  control, targeting the segment where the effect should be largest.
  These are the only levers that make a small audience behave like a
  bigger one.
- **Move the primary metric closer to the change.** Coupon claim rather
  than redemption, redemption rather than anything downstream of a
  supermarket. Keep the deeper metric as a guardrail, underpowered and
  directional, and say in the readout that it is.
- **Long runs collect calendar.** A seven-week test contains a holiday, a
  season, or back-to-school. Randomisation handles it; interpretation
  does not. An effect measured across Christmas is an effect measured
  across Christmas, and the readout should say so.
- **Two markets do not rescue each other.** The smaller one is a small
  fraction of the audience, so pooling buys little power and adds
  heterogeneity. Pooled primary, country cut pre-registered as secondary,
  and honesty that the small market alone will almost never be powered.
  The failure to avoid is reading both separately and reporting whichever
  looks better.

The most valuable sentence you will say this quarter: that question is
not answerable at our traffic in less than four months, so let us either
make the change bigger, pick a different metric, or decide it without a
test and write down that we did.

## The outcome you cannot see

The purchase happens in a supermarket you do not own. A pet parent reads
a feeding guide, claims a coupon, compares two formats, and then buys the
bag at a retailer, at a vet clinic, or on a marketplace. Your product
almost never sees the transaction. Every readout you write therefore
contains a bridge from something you can observe to something you care
about, and the bridge is usually unexamined.

What you can observe, ranked by how much it is worth: a **redeemed
coupon** (tied to a real purchase, the best signal you have, and the
reason coupon journeys deserve more of the experimentation budget than
their traffic share suggests); a **loyalty scan** (real, but
self-selected: usable within members, dangerous as a market read); a
**click-out to a retailer** (a click; treating it as a sale is the most
common unexamined error in this kind of squad); **sampling requests and
leads** (intent at best).

Four defences:

1. **Name the bridge in every readout.** One sentence: this result is a
   change in claim rate, here is what we currently believe claim rate is
   worth in redemptions, and here is the assumption doing the work.
2. **Validate the proxy once a year against something real.** Redemption
   cohorts, matched loyalty members, whatever panel or sell-out data the
   market can give you. Never on a roadmap, always worth an afternoon.
3. **Prefer tests whose outcome you own.** Given two candidate
   experiments of similar value, run the one that ends in a coupon or a
   subscription rather than a click-out.
4. **Accept the ceiling and say where the question belongs.** Whether
   digital moved national sell-out is not answerable by a product squad's
   instrumentation; it belongs to whoever holds panel data and the mix
   model. Routing it there is a better answer than a number you cannot
   defend.

## What each person needs from you

- **The PM** needs sizing before commitment and a decision rule before
  launch, with the assumptions visible, so a readout under the estimate
  becomes a conversation about which assumption was wrong rather than
  about whether you were right. You need back: to be in refinement,
  because refinement is where a flag either gets added or does not.
- **The designer** needs to know where pet parents struggle and why: a
  funnel, a session replay, a segment cut, not a p-value. You need back:
  fewer, larger variants.
- **The data engineers** need specifications, not requests, and a sprint
  of notice: event names, parameters, the catalog definition, the query
  the readout will run. You need back: exposure logs you can trust and
  alerting on event volume, because the two failures that ruin tests here
  are a sample ratio mismatch and an event that stopped firing on one
  country's site.
- **The developers** need to know that the flag matters and why, in one
  sentence. You need back: the flag by default, stable assignment across
  sessions and devices, and no "we will add tracking later", because
  later means the first weeks of data do not exist.

## The eight ways this goes wrong

1. **Peeking.** The platform shows a curve to anyone. Fix: sequential
   design up front, and a rule that nothing counts until Tuesday.
2. **Underpowered read as null.** "No difference" when you mean "we could
   not have seen it." Fix: report the interval and the MDE, every time.
3. **Sample ratio mismatch.** Often one country's arm. Fix: check daily,
   treat a failure as invalidating.
4. **Questions closed as Done.** The tracker eats the knowledge. Fix:
   question issues, and no Done in the workflow.
5. **A click-out called a sale.** Fix: name the bridge, or report the
   click as a click.
6. **Country cherry-pick.** Two markets, one looks better. Fix:
   pre-register pooled primary, country secondary.
7. **Metric drift in the catalog.** A definition changes and last year's
   numbers stop matching. Fix: version it, and note it on charts that
   span the change.
8. **The one-person dashboard desk.** Every recurring number someone
   needs weekly becomes yours. Fix: build it once, hand over the link,
   protect the deep block.

## The loop closes, and here it closes tighter

What ships changes the data. In a squad running one or two tests at a
time on a single region's traffic, that sentence has teeth: the loyalty
onboarding you shipped in March is the reason the April baseline moved,
and a test that runs six weeks is a test whose pre-period is being
overwritten by your own roadmap while it runs. There is no second market
to check against and no larger sample to hide in. The definition of
success has to be maintained continuously, like calibrating a scale you
weigh things on every day, and the calibration is your job, because there
is nobody else to do it.
