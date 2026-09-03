"""Empirical Bayes shrinkage: the winner's-curse correction.

A result that cleared the significance bar is, in expectation, an
overstatement: conditioning on crossing a threshold selects the draws noise
helped. Shrinking toward the distribution of effects this metric has actually
produced removes most of that bias, and the prior store is what makes the
prior empirical rather than asserted.

Normal-normal model. Prior N(mu, tau2) estimated from past effects by the
method of moments:

    mu   = mean(effects)
    tau2 = max( var(effects) - mean(se^2), 0 )

Posterior mean = w * effect + (1 - w) * mu, with w = tau2 / (tau2 + se^2).
When tau2 is 0 the past effects are indistinguishable from noise around mu
and the new result shrinks all the way to the prior mean, which is the model
saying this metric has never produced a distinguishable effect.

Effects must share a unit; the store records it and mixing units is refused.

Run:  python -m gallop.shrink eb --effect 0.031 --se 0.012 --store priors.jsonl --metric activation_rate
"""

from __future__ import annotations

import argparse

import numpy as np

# %% ------------------------------------------------------------------ shrink


def prior_from_effects(effects, ses):
    """Method-of-moments normal prior from past (effect, se) pairs."""
    effects = np.asarray(effects, float)
    ses = np.asarray(ses, float)
    if len(effects) < 3:
        raise ValueError(f"need at least 3 past effects to estimate a prior, got {len(effects)}")
    if len(effects) != len(ses):
        raise ValueError("effects and ses must be the same length")
    mu = float(effects.mean())
    tau2 = float(max(effects.var(ddof=1) - (ses**2).mean(), 0.0))
    return {"mu": mu, "tau2": tau2, "n_priors": len(effects)}


def empirical_bayes(effect, se, effects=None, ses=None, mu=None, tau2=None):
    """Shrink one (effect, se) toward the empirical prior.

    Pass past `effects` and `ses` (arrays, e.g. columns of gallop.priors.read)
    to estimate the prior, or `mu` and `tau2` directly.
    """
    if effects is not None:
        prior = prior_from_effects(effects, ses)
        mu, tau2 = prior["mu"], prior["tau2"]
    elif mu is None or tau2 is None:
        raise ValueError("pass effects+ses, or mu+tau2")
    else:
        prior = {"mu": float(mu), "tau2": float(tau2), "n_priors": None}
    se = float(se)
    if se <= 0:
        raise ValueError("se must be positive")
    w = tau2 / (tau2 + se**2)
    shrunk = w * effect + (1 - w) * mu
    post_var = (tau2 * se**2 / (tau2 + se**2)) if tau2 > 0 else 0.0
    return {
        **prior,
        "effect": float(effect),
        "se": se,
        "weight_on_data": float(w),
        "effect_shrunk": float(shrunk),
        "se_shrunk": float(np.sqrt(post_var)),
        "overstatement": float(effect - shrunk),
    }


def from_store(effect, se, store, metric, unit):
    """Shrink against a prior-store DataFrame (from gallop.priors.read).

    Uses only records for `metric` whose `unit` matches; mixing units would
    average percentage points with fractions and mean nothing.
    """
    rows = store[(store["metric"] == metric)]
    if rows.empty:
        raise ValueError(f"no records for metric {metric!r} in the store")
    mismatched = rows[rows["unit"] != unit]
    if len(mismatched):
        raise ValueError(
            f"{len(mismatched)} records for {metric!r} use unit(s) "
            f"{sorted(mismatched['unit'].unique())}, not {unit!r}; convert before shrinking")
    return empirical_bayes(effect, se, effects=rows["effect"], ses=rows["se"])


# %% --------------------------------------------------------------------- cli


def main(argv=None):
    p = argparse.ArgumentParser(prog="gallop.shrink", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("eb", help="shrink an effect toward the prior store")
    sp.add_argument("--effect", type=float, required=True)
    sp.add_argument("--se", type=float, required=True)
    sp.add_argument("--store", required=True, help="prior store JSONL")
    sp.add_argument("--metric", required=True)
    sp.add_argument("--unit", default="relative", choices=["absolute", "pp", "relative"])

    a = p.parse_args(argv)
    from gallop import priors
    r = from_store(a.effect, a.se, priors.read(a.store), a.metric, a.unit)
    print(f"  prior from {r['n_priors']} past readouts: mu {r['mu']:+.5f}   tau {np.sqrt(r['tau2']):.5f}")
    print(f"  observed {r['effect']:+.5f} (se {r['se']:.5f})   weight on data {r['weight_on_data']:.2f}")
    print(f"  shrunk   {r['effect_shrunk']:+.5f} (se {r['se_shrunk']:.5f})"
          f"   overstatement {r['overstatement']:+.5f}")


if __name__ == "__main__":
    main()
