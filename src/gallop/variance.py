"""CUPED: variance reduction from a pre-experiment covariate.

Deng, Xu, Kohavi & Walker (2013). Adjust the metric by a covariate that
treatment cannot have touched:

    Y_adj = Y - theta * (X - mean(X))      theta = Cov(Y, X) / Var(X)

Var(Y_adj) = Var(Y) * (1 - rho^2), so the reduction is the squared pre/post
correlation and nothing else. Theta and mean(X) are estimated POOLED across
arms; per-arm estimation throws most of the benefit away by fitting each arm's
own noise.

The validity rule, in one sentence: the covariate must be fully determined
before the first unit was exposed, and defined identically for every unit
including those with no history. A contaminated covariate is the one failure
that produces a wrong answer rather than a weaker one.

Run:  python -m gallop.variance cuped --data exp.csv --y metric --x pre_metric --arm arm
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy import stats

# %% ------------------------------------------------------------------- cuped


def cuped(y, x, assignment, control=None):
    """Difference in means with and without the CUPED adjustment.

    `y`: metric per unit. `x`: pre-period covariate per unit. `assignment`:
    per-unit arm labels, exactly two distinct values. `control` names the
    control label; if omitted, the lexicographically first label is control.

    Returns raw and adjusted effect, se and p, plus theta, rho and the
    variance reduction actually achieved.
    """
    y = np.asarray(y, float)
    x = np.asarray(x, float)
    arm = np.asarray(assignment)
    labels = sorted(pd.unique(arm).tolist())
    if len(labels) != 2:
        raise ValueError(f"cuped needs exactly two arms, got {labels}")
    if control is None:
        control = labels[0]
    elif control not in labels:
        raise ValueError(f"control {control!r} not in arms {labels}")
    treat = next(b for b in labels if b != control)
    mask_t = arm == treat

    theta = float(np.cov(y, x, ddof=1)[0, 1] / np.var(x, ddof=1))
    rho = float(np.corrcoef(y, x)[0, 1])
    y_adj = y - theta * (x - x.mean())

    def diff(v):
        a, b = v[~mask_t], v[mask_t]
        se = float(np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)))
        eff = float(b.mean() - a.mean())
        _t, p = stats.ttest_ind(b, a, equal_var=False)
        return eff, se, float(p)

    eff_r, se_r, p_r = diff(y)
    eff_a, se_a, p_a = diff(y_adj)
    return {
        "control": control,
        "treatment": treat,
        "n_control": int((~mask_t).sum()),
        "n_treatment": int(mask_t.sum()),
        "theta": theta,
        "rho": rho,
        "effect_raw": eff_r,
        "se_raw": se_r,
        "p_raw": p_r,
        "effect_adjusted": eff_a,
        "se_adjusted": se_a,
        "p_adjusted": p_a,
        "variance_reduction": float(1 - np.var(y_adj, ddof=1) / np.var(y, ddof=1)),
    }


# %% --------------------------------------------------------------------- cli


def main(argv=None):
    p = argparse.ArgumentParser(prog="gallop.variance", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("cuped", help="CUPED-adjusted effect from a unit-level csv")
    sp.add_argument("--data", required=True, help="csv with one row per unit")
    sp.add_argument("--y", required=True, help="metric column")
    sp.add_argument("--x", required=True, help="pre-period covariate column")
    sp.add_argument("--arm", required=True, help="assignment column, two values")
    sp.add_argument("--control", help="control label; default lexicographic first")

    a = p.parse_args(argv)
    df = pd.read_csv(a.data)
    r = cuped(df[a.y], df[a.x], df[a.arm], control=a.control)
    print(f"  {r['treatment']} vs {r['control']}"
          f"   n {r['n_treatment']:,}/{r['n_control']:,}   rho {r['rho']:.3f}")
    print(f"  raw    effect {r['effect_raw']:+.6f}   se {r['se_raw']:.6f}   p {r['p_raw']:.4f}")
    print(f"  cuped  effect {r['effect_adjusted']:+.6f}   se {r['se_adjusted']:.6f}"
          f"   p {r['p_adjusted']:.4f}")
    print(f"  variance reduction {r['variance_reduction']:.1%}  (theory: rho^2 ="
          f" {r['rho'] ** 2:.1%})")


if __name__ == "__main__":
    main()
