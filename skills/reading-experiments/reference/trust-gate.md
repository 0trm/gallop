# The trust gate

Two mechanical checks that run before any effect is read. Both exist because
their failure modes produce readouts indistinguishable from healthy ones.

## Sample ratio mismatch

The check: chi-square goodness of fit of assignment counts against the
intended split.

```
python -m gallop.trust srm --counts counts.csv        # columns: arm, assigned
```

**Alpha is 0.001, not 0.05, deliberately.** The check runs on every
experiment ever analysed; at 0.05 it would fire on one healthy test in
twenty, be ignored within a quarter, and protect nothing. At 0.001 a firing
means the test is broken, with high confidence.

**Why there is no correction.** An SRM means units left (or never entered)
one arm non-randomly. The remaining populations differ in whatever made
those units leave, which is usually correlated with the outcome. Reweighting
cannot recover a comparison that randomisation no longer underwrites.

**The cause taxonomy** (Fabijan et al.), worked in order, stopping at the
first that fits:

1. **Assignment** – bucketing bug, hash collision, a variant filter upstream.
2. **Execution** – one variant errors or times out; its events never arrive.
3. **Logging** – telemetry differs by variant; a slower page fires fewer
   beacons.
4. **Experiment definition** – the ramp changed mid-flight and the expected
   ratio was not updated. (The one benign cause: fix the expectation, not
   the test.)
5. **Triggering** – the trigger condition is itself affected by treatment.
6. **Interference** – units move between variants or share state.
7. **Filtering** – a bot or outlier filter removes units at different rates
   by variant.

Check daily during the run, not once at the end: an SRM caught on day two
costs two days; caught at readout it costs the whole test.

## Exposure versus eligibility

The check: exposure counts per arm against assignment counts.

```
python -m gallop.trust exposure --counts counts.csv   # columns: arm, assigned, exposed
```

Two distinct failures:

**Differential exposure** (the exposed counts fail an SRM at the assignment
split): the arms trigger unequally, which is a bug in the trigger or the
surface, and the comparison is invalid outright. Treat exactly like an SRM.

**Uniform dilution** (both arms under-exposed at the same rate r): the
intention-to-treat estimate is attenuated by roughly r. Two honest readings:

- ITT as measured, labelled "diluted by exposure at r".
- The exposed-only comparison, if exposure is logged symmetrically in both
  arms (control fires the event on seeing the control surface). If only the
  treatment arm logs exposure, the exposed subsets are not comparable and
  scaling ITT by 1/r is the safer statement.

The deeper fix belongs to design: log exposure, not eligibility, and alert
on event volume so a dark platform or country is visible within a day. A
test that "ran fine" with a 60% exposure rate was a test on a 40% smaller
effect than anyone thought they were testing.
