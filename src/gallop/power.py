"""Power, MDE, sample size and duration for a two-arm test.

One family of closed forms for a two-sample difference in means. A proportion
metric is the same formula with sd = sqrt(p(1-p)), so every function takes
either `sd` (continuous) or `baseline_rate` (proportion), never both.

With the defaults (alpha 0.05 two-sided, power 0.80) the MDE reduces to the
planning rule of thumb 2.8 * sqrt(2 p (1-p) / n).

The closed form assumes the analysis unit is the randomisation unit, and it
lies for ratio metrics, heavy tails and capped metrics. Sizing from it when
those assumptions fail is a design question, not an arithmetic one; see the
designing-experiments skill.

Run:  python -m gallop.power mde --n 5000 --baseline-rate 0.10
"""

from __future__ import annotations

import argparse

import numpy as np
from scipy import stats

# %% ------------------------------------------------------------- closed forms


def _sd(sd: float | None, baseline_rate: float | None) -> float:
    if (sd is None) == (baseline_rate is None):
        raise ValueError("give exactly one of sd (continuous) or baseline_rate (proportion)")
    if baseline_rate is not None:
        if not 0 < baseline_rate < 1:
            raise ValueError("baseline_rate must be strictly between 0 and 1")
        return float(np.sqrt(baseline_rate * (1 - baseline_rate)))
    return float(sd)


def mde(n_per_arm, *, sd=None, baseline_rate=None, power=0.80, alpha=0.05):
    """Smallest absolute effect detectable at the stated power. Same unit as the metric."""
    s = _sd(sd, baseline_rate)
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    return float((z_alpha + z_beta) * s * np.sqrt(2.0 / n_per_arm))


def sample_size(effect, *, sd=None, baseline_rate=None, power=0.80, alpha=0.05):
    """Units per arm needed to detect an absolute `effect`. Inverse of mde()."""
    s = _sd(sd, baseline_rate)
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    return float(2 * ((z_alpha + z_beta) * s / abs(effect)) ** 2)


def power_at(n_per_arm, effect, *, sd=None, baseline_rate=None, alpha=0.05):
    """Power of a two-sided test at the given n and absolute effect."""
    s = _sd(sd, baseline_rate)
    se = s * np.sqrt(2.0 / n_per_arm)
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z = abs(effect) / se
    return float(stats.norm.sf(z_alpha - z) + stats.norm.cdf(-z_alpha - z))


def duration(effect, units_per_day, *, sd=None, baseline_rate=None, power=0.80,
             alpha=0.05, arms=2, eligible_share=1.0):
    """Days to reach the required sample, given daily eligible traffic.

    `units_per_day` is total new units entering the experiment surface per day;
    `eligible_share` is the fraction that actually enters assignment.
    """
    n = sample_size(effect, sd=sd, baseline_rate=baseline_rate, power=power, alpha=alpha)
    daily = units_per_day * eligible_share
    if daily <= 0:
        raise ValueError("units_per_day * eligible_share must be positive")
    return float(arms * n / daily)


# %% --------------------------------------------------------------------- cli


def main(argv=None):
    p = argparse.ArgumentParser(prog="gallop.power", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp, effect=False, n=False):
        if effect:
            sp.add_argument("--effect", type=float, required=True, help="absolute effect")
        if n:
            sp.add_argument("--n", type=float, required=True, help="units per arm")
        sp.add_argument("--sd", type=float)
        sp.add_argument("--baseline-rate", type=float)
        sp.add_argument("--power", type=float, default=0.80)
        sp.add_argument("--alpha", type=float, default=0.05)

    common(sub.add_parser("mde", help="smallest detectable absolute effect"), n=True)
    common(sub.add_parser("n", help="units per arm for an effect"), effect=True)
    sp = sub.add_parser("duration", help="days to reach the required sample")
    common(sp, effect=True)
    sp.add_argument("--units-per-day", type=float, required=True)
    sp.add_argument("--eligible-share", type=float, default=1.0)
    sp.add_argument("--arms", type=int, default=2)
    common(sub.add_parser("power", help="power at a given n and effect"), effect=True, n=True)

    a = p.parse_args(argv)
    kw = {"sd": a.sd, "baseline_rate": a.baseline_rate, "alpha": a.alpha}
    if a.cmd == "mde":
        print(f"mde (absolute): {mde(a.n, power=a.power, **kw):.6f}")
    elif a.cmd == "n":
        print(f"n per arm: {sample_size(a.effect, power=a.power, **kw):,.0f}")
    elif a.cmd == "duration":
        d = duration(a.effect, a.units_per_day, power=a.power, arms=a.arms,
                     eligible_share=a.eligible_share, **kw)
        print(f"days: {d:,.1f}")
    elif a.cmd == "power":
        print(f"power: {power_at(a.n, a.effect, **kw):.4f}")


if __name__ == "__main__":
    main()
