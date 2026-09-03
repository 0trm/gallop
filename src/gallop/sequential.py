"""Sequential inference: always-valid confidence sequences and group-sequential bounds.

Peeking at a fixed-horizon test inflates both the false positive rate and the
reported effect size. Two licensed alternatives, each priced in power:

  msprt_bound       mixture sequential probability ratio test with a normal
                    mixing prior of variance tau2. ALWAYS VALID: look as often
                    as you like, forever, and type I error stays below alpha.
                    always_valid_ci() inverts it into a confidence sequence.
  obf_bounds        O'Brien-Fleming group-sequential z boundaries for a FIXED
                    look schedule, calibrated by simulation. Void if a look is
                    added; cheaper in power than mSPRT if the schedule holds.

If nobody will actually look before the horizon, a pre-registered fixed
horizon beats both.

Run:  python -m gallop.sequential bound --n 5000 --sd 1.0
"""

from __future__ import annotations

import argparse

import numpy as np

# %% ------------------------------------------------------------------- msprt


def msprt_bound(n_per_arm, sd, tau2=0.01, alpha=0.05):
    """z-statistic boundary of the normal-mixture SPRT at the current n.

    With V = 2 sd^2 / n the mixture likelihood ratio rejects when

        |z| >= sqrt( 2 (V+tau2)/tau2 * [ log(1/alpha) + 0.5 log((V+tau2)/V) ] )

    tau2 is a prior on plausible squared effect sizes: too small and the
    boundary never closes, too large and early stopping is lost. The boundary
    is wide early by construction and never collapses to 1.96.
    """
    v = 2 * sd**2 / n_per_arm
    return float(np.sqrt(2 * (v + tau2) / tau2 * (np.log(1 / alpha) + 0.5 * np.log((v + tau2) / v))))


def always_valid_ci(mean_control, mean_treatment, sd, n_per_arm, tau2=0.01, alpha=0.05):
    """Always-valid interval for the difference in means at the current n.

    The confidence sequence is diff +- bound * se. Valid at every n
    simultaneously: it can be recomputed after every unit arrives and the
    union of misses over all time is still below alpha.
    """
    se = sd * np.sqrt(2.0 / n_per_arm)
    z = msprt_bound(n_per_arm, sd, tau2, alpha)
    diff = mean_treatment - mean_control
    return {
        "effect": float(diff),
        "se": float(se),
        "bound_z": z,
        "ci": (float(diff - z * se), float(diff + z * se)),
        "significant": bool(abs(diff) > z * se),
        "fixed_horizon_ci": (float(diff - 1.959964 * se), float(diff + 1.959964 * se)),
    }


# %% --------------------------------------------------------- group sequential


def calibrate_obf(n_looks, alpha=0.05, n_sims=40_000, seed=0):
    """Constant c such that P(|z_k| > c / sqrt(k/K) at any look | null) = alpha.

    The z-statistics across equally spaced looks are Brownian motion scaled at
    times k/K; c is found by bisection on simulated paths. Simulation is also
    the honest method for any non-standard schedule.
    """
    rng = np.random.default_rng(seed)
    inc = rng.normal(0, 1, (n_sims, n_looks)) / np.sqrt(n_looks)
    t = np.arange(1, n_looks + 1) / n_looks
    z = np.cumsum(inc, axis=1) / np.sqrt(t)
    lo, hi = 1.0, 6.0
    for _ in range(40):
        c = (lo + hi) / 2
        crossed = (np.abs(z) > c / np.sqrt(t)).any(axis=1).mean()
        lo, hi = (c, hi) if crossed > alpha else (lo, c)
    return float((lo + hi) / 2)


def obf_bounds(n_looks, alpha=0.05, n_sims=40_000, seed=0):
    """O'Brien-Fleming z boundaries for `n_looks` equally spaced looks.

    Hard to cross early, close to the fixed-horizon critical value at the end.
    The schedule is part of the design: adding a look voids the calibration.
    """
    c = calibrate_obf(n_looks, alpha, n_sims, seed)
    t = np.arange(1, n_looks + 1) / n_looks
    return (c / np.sqrt(t)).tolist()


# %% --------------------------------------------------------------------- cli


def main(argv=None):
    p = argparse.ArgumentParser(prog="gallop.sequential", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("bound", help="always-valid z boundary at the current n")
    sp.add_argument("--n", type=float, required=True, help="units per arm so far")
    sp.add_argument("--sd", type=float, required=True)
    sp.add_argument("--tau2", type=float, default=0.01)
    sp.add_argument("--alpha", type=float, default=0.05)
    sp = sub.add_parser("obf", help="O'Brien-Fleming boundaries for a look schedule")
    sp.add_argument("--looks", type=int, required=True)
    sp.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    if a.cmd == "bound":
        z = msprt_bound(a.n, a.sd, a.tau2, a.alpha)
        print(f"always-valid |z| boundary at n={a.n:,.0f}: {z:.3f}  (fixed horizon: 1.960)")
    else:
        bs = obf_bounds(a.looks, a.alpha)
        for k, b in enumerate(bs, 1):
            print(f"  look {k}/{a.looks}: |z| > {b:.3f}")


if __name__ == "__main__":
    main()
