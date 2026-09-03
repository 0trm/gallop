# Variance reduction at readout

## CUPED

Deng, Xu, Kohavi & Walker (2013). Adjust the metric by a pre-experiment
covariate that treatment cannot have touched:

    Y_adj = Y - theta (X - mean(X)),   theta = Cov(Y,X) / Var(X)

Var(Y_adj) = Var(Y)(1 - rho²): the entire benefit is the squared pre/post
correlation, so measure rho before promising anyone a number. At rho 0.7 the
required sample halves; at rho 0.2 the gain is cosmetic.

```
python -m gallop.variance cuped --data units.csv --y metric --x pre_metric --arm arm
```

**The validity rule, in one sentence:** the covariate must be fully
determined before the first unit was exposed, and defined identically for
every unit, including units with no history (impute a constant, usually the
mean; never drop them).

**Failure modes, in order of danger:**

1. **Contaminated covariate.** X computed over a window that overlaps the
   experiment, or otherwise touched by treatment. The only failure that
   biases the estimate rather than weakening it: CUPED then subtracts part
   of the true effect. If the covariate window's end is not provably before
   first exposure, do not use it.
2. **Per-arm theta.** Theta and mean(X) must be estimated pooled across
   arms. Estimated per arm, each theta fits its own arm's noise and most of
   the variance reduction is thrown away (`gallop.variance` pools; a
   hand-rolled version often does not).
3. **Missing pre-period.** New users have no history. Coverage c of the
   covariate cuts the reduction by roughly c²; with 40% coverage, expect
   ~16% of the nominal gain. Report the effective rho, not the rho among
   covered users.

The natural covariate is the same metric over an equal-length pre-period.
Anything pre-treatment and correlated works; the same metric is usually the
most correlated thing available.

## The alternatives

**Post-stratification** on a discrete covariate (platform, country,
tenure): weight each stratum by its pooled share. Wins over CUPED only when
the covariate is genuinely categorical or must be fixed before launch.

**Triggered analysis**: restrict to units that could have been affected at
all. Not a variance trick on the same population; it changes the estimand
to the effect on the triggered subset. Legitimate and often what the
decision wants, but say which population the number is about.

**What is not on the list:** collecting more traffic. At readout the sample
is what it is; the levers above are the only ones left, which is why the
covariate is planned at design time.
