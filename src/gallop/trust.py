"""The trust gate: sample ratio mismatch and exposure-versus-eligibility.

Two checks that run before any effect is read. Both are mechanical, with fixed
thresholds, which is why they are scripted rather than improvised.

srm             chi-squared goodness of fit on assignment counts, any number of
                arms. Alpha is 0.001, not 0.05: the check runs on every
                experiment ever analysed, and at 0.05 it would cry wolf and be
                switched off. A failure names the Fabijan cause taxonomy in the
                order to work it.
exposure_check  exposure counts against assignment counts. Low exposure dilutes
                the effect by a known factor; unequal exposure across arms is a
                trigger bug and invalidates the comparison outright.

Run:  python -m gallop.trust srm --counts counts.csv
      (csv columns: arm, assigned[, exposed])
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy import stats

# %% --------------------------------------------------------------------- srm

SRM_CAUSES = [
    ("Assignment", "bucketing bug, hash collision, or a variant filter applied upstream"),
    ("Execution", "one variant errors or times out, so its events never arrive"),
    ("Logging", "telemetry differs by variant, e.g. a slower page fires fewer beacons"),
    ("Experiment definition", "ramp changed mid-flight and the expected ratio was not updated"),
    ("Triggering", "the trigger condition is itself affected by treatment"),
    ("Interference", "units move between variants or share state, so counts leak"),
    ("Filtering", "a bot or outlier filter removes units at different rates by variant"),
]


def srm(counts, expected=None, alpha=0.001):
    """Chi-squared test that assignment counts match the intended split.

    `counts`: dict of arm -> assigned count, or a sequence of counts.
    `expected`: intended shares in the same order; equal split if omitted.
    """
    if isinstance(counts, dict):
        arms, obs = list(counts), np.array(list(counts.values()), float)
    else:
        obs = np.asarray(counts, float)
        arms = [f"arm_{i}" for i in range(len(obs))]
    if len(obs) < 2:
        raise ValueError("srm needs at least two arms")
    share = np.full(len(obs), 1 / len(obs)) if expected is None else np.asarray(expected, float)
    share = share / share.sum()
    exp = obs.sum() * share
    chi2 = float(((obs - exp) ** 2 / exp).sum())
    p = float(stats.chi2.sf(chi2, df=len(obs) - 1))
    failed = p < alpha
    return {
        "arms": arms,
        "observed": obs.tolist(),
        "observed_share": (obs / obs.sum()).tolist(),
        "expected_share": share.tolist(),
        "chi2": chi2,
        "p": p,
        "srm": failed,
        "verdict": "SRM: STOP, DO NOT ANALYSE" if failed else "pass",
    }


# %% ---------------------------------------------------------------- exposure


def exposure_check(assigned, exposed, min_rate=0.95, alpha=0.001):
    """Exposure counts against assignment counts, per arm.

    `assigned`, `exposed`: dicts of arm -> count, same keys.

    Two verdicts stack. A pooled exposure rate below `min_rate` means the
    intention-to-treat effect is attenuated by roughly that rate; the check
    reports the dilution factor to divide it back out, and whether the design
    should have logged exposure instead. An SRM test on the exposed counts
    (at the assignment split) catches differential triggering, which no
    dilution factor repairs.
    """
    arms = list(assigned)
    if set(exposed) != set(arms):
        raise ValueError("assigned and exposed must cover the same arms")
    a = np.array([assigned[k] for k in arms], float)
    e = np.array([exposed[k] for k in arms], float)
    if (e > a).any():
        raise ValueError("exposed count exceeds assigned count in some arm")
    rates = e / a
    pooled = float(e.sum() / a.sum())
    exposed_srm = srm(dict(zip(arms, e)), expected=a / a.sum(), alpha=alpha)
    diluted = pooled < min_rate
    if exposed_srm["srm"]:
        verdict = "DIFFERENTIAL EXPOSURE: the arms trigger unequally, do not analyse"
    elif diluted:
        verdict = f"diluted: ITT effect attenuated ~{pooled:.0%}, analyse exposed or scale"
    else:
        verdict = "pass"
    return {
        "arms": arms,
        "exposure_rate": rates.tolist(),
        "pooled_rate": pooled,
        "dilution_factor": float(1 / pooled) if pooled > 0 else np.inf,
        "exposed_srm_p": exposed_srm["p"],
        "differential": exposed_srm["srm"],
        "diluted": diluted,
        "verdict": verdict,
    }


# %% ------------------------------------------------------------------ report


def report(res):
    """Render either check's dict as lines a readout can paste."""
    lines = []
    if "expected_share" in res:  # srm
        for arm, o, s, x in zip(res["arms"], res["observed"], res["observed_share"],
                                res["expected_share"]):
            lines.append(f"  {arm:<12} {o:>12,.0f}  observed {s:.4f}  expected {x:.4f}")
        lines.append(f"  chi2 {res['chi2']:.2f}   p {res['p']:.3e}   {res['verdict']}")
        if res["srm"]:
            lines.append("  work the causes in this order, stopping at the first that fits:")
            lines += [f"    {i + 1}. {k}: {v}" for i, (k, v) in enumerate(SRM_CAUSES)]
    else:  # exposure
        for arm, r in zip(res["arms"], res["exposure_rate"]):
            lines.append(f"  {arm:<12} exposure rate {r:.4f}")
        lines.append(f"  pooled {res['pooled_rate']:.4f}   dilution x{res['dilution_factor']:.2f}"
                     f"   differential p {res['exposed_srm_p']:.3e}")
        lines.append(f"  {res['verdict']}")
    return "\n".join(lines)


# %% --------------------------------------------------------------------- cli


def _read_counts(path):
    df = pd.read_csv(path)
    need = {"arm", "assigned"}
    if not need <= set(df.columns):
        raise SystemExit(f"{path} needs columns arm, assigned[, exposed]")
    assigned = dict(zip(df["arm"], df["assigned"]))
    exposed = dict(zip(df["arm"], df["exposed"])) if "exposed" in df.columns else None
    return assigned, exposed


def main(argv=None):
    p = argparse.ArgumentParser(prog="gallop.trust", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("srm", help="sample ratio mismatch on assignment counts")
    sp.add_argument("--counts", required=True, help="csv with columns arm, assigned")
    sp.add_argument("--expected", help="comma-separated intended shares, e.g. 0.5,0.5")
    sp.add_argument("--alpha", type=float, default=0.001)
    sp = sub.add_parser("exposure", help="exposure vs eligibility, per arm")
    sp.add_argument("--counts", required=True, help="csv with columns arm, assigned, exposed")
    sp.add_argument("--min-rate", type=float, default=0.95)

    a = p.parse_args(argv)
    assigned, exposed = _read_counts(a.counts)
    if a.cmd == "srm":
        expected = [float(x) for x in a.expected.split(",")] if a.expected else None
        print(report(srm(assigned, expected=expected, alpha=a.alpha)))
    else:
        if exposed is None:
            raise SystemExit("exposure check needs an 'exposed' column")
        print(report(exposure_check(assigned, exposed, min_rate=a.min_rate)))


if __name__ == "__main__":
    main()
