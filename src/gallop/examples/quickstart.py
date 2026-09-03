"""The five-minute path: every check once, against synthetic data.

One simulated experiment on a 12% activation rate with a real +0.35pp effect,
plus a seeded prior store. No configuration, no credentials, no warehouse.

Run:  python -m gallop.examples.quickstart
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from gallop import power, priors, sequential, shrink, trust, variance

RULE = "=" * 74


def main():
    rng = np.random.default_rng(7)

    # -- the experiment: user-level activation with a pre-period covariate
    n = 40_000
    true_effect = 0.0035
    x = rng.beta(2, 14, 2 * n)                      # pre-period activation propensity
    arm = np.array(["control"] * n + ["treatment"] * n)
    p_unit = np.clip(x + (arm == "treatment") * true_effect, 0, 1)
    y = rng.binomial(1, p_unit).astype(float)

    print(RULE)
    print("gallop quickstart: one experiment through every check")
    print(RULE)

    print("\n1 · Size it before running it (gallop.power)")
    m = power.mde(n, baseline_rate=0.125)
    print(f"   at n={n:,} per arm on a 12.5% rate, the MDE is {m * 100:.2f}pp;")
    print(f"   detecting {true_effect * 100:.2f}pp instead would need "
          f"{power.sample_size(true_effect, baseline_rate=0.125):,.0f} per arm")

    print("\n2 · The trust gate (gallop.trust)")
    assigned = {"control": n, "treatment": n - int(rng.integers(0, 120))}
    exposed = {k: int(v * 0.97) for k, v in assigned.items()}
    s = trust.srm(assigned)
    print(f"   SRM: chi2 {s['chi2']:.2f}  p {s['p']:.3f}  -> {s['verdict']}")
    e = trust.exposure_check(assigned, exposed)
    print(f"   exposure: pooled rate {e['pooled_rate']:.2%}  -> {e['verdict']}")

    print("\n3 · The effect, with CUPED (gallop.variance)")
    r = variance.cuped(y, x, arm, control="control")
    print(f"   raw    {r['effect_raw'] * 100:+.3f}pp  se {r['se_raw'] * 100:.3f}pp")
    print(f"   cuped  {r['effect_adjusted'] * 100:+.3f}pp  se {r['se_adjusted'] * 100:.3f}pp"
          f"   variance reduction {r['variance_reduction']:.0%}")

    print("\n4 · An interval that survives peeking (gallop.sequential)")
    sd_adj = r["se_adjusted"] * np.sqrt(n / 2)
    av = sequential.always_valid_ci(0.0, r["effect_adjusted"], sd_adj, n, tau2=1e-4)
    lo, hi = av["ci"]
    print(f"   always-valid 95% CI [{lo * 100:+.3f}pp, {hi * 100:+.3f}pp]"
          f"   boundary |z| {av['bound_z']:.2f} (vs 1.96 fixed)")
    print(f"   significant under continuous monitoring: {av['significant']}")

    print("\n5 · Shrunk toward what this metric has done before (gallop.shrink + priors)")
    with tempfile.TemporaryDirectory() as td:
        store_path = Path(td) / "priors.jsonl"
        past = [0.0009, -0.0004, 0.0021, 0.0013, -0.0011, 0.0028, 0.0006, 0.0016]
        for i, eff in enumerate(past):
            priors.append(store_path, {
                "id": f"2026-{i + 1:02d}-activation-test", "metric": "activation_rate",
                "date": f"2026-{i + 1:02d}-15", "design": "experiment", "effect": eff,
                "unit": "pp", "se": 0.0011, "n_per_arm": 35_000, "decision": "ship" if eff > 0.001 else "no-ship",
            })
        store = priors.read(store_path)
        sh = shrink.from_store(r["effect_adjusted"], r["se_adjusted"], store,
                               "activation_rate", "pp")
    print(f"   prior from {sh['n_priors']} readouts: mu {sh['mu'] * 100:+.3f}pp"
          f"   tau {np.sqrt(sh['tau2']) * 100:.3f}pp")
    print(f"   observed {sh['effect'] * 100:+.3f}pp -> shrunk {sh['effect_shrunk'] * 100:+.3f}pp"
          f"   (weight on data {sh['weight_on_data']:.2f})")

    print(f"\n{RULE}")
    print(f"true simulated effect: {true_effect * 100:+.3f}pp. The shrunk estimate is the")
    print("one to write back to the store; the raw one is the winner's curse waiting.")
    print(RULE)


if __name__ == "__main__":
    main()
