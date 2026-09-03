"""The reading pass in one command: trust gate, CUPED effect, always-valid interval, shrinkage.

Inputs:
  --counts   csv with columns arm, assigned[, exposed]
  --data     unit-level csv: one row per randomisation unit
  --y --x --arm   metric, pre-period covariate, assignment columns in --data
  --store --metric --unit   optional prior store for shrinkage

Order is the skill's order: SRM, exposure, then the effect, then shrinkage.
A trust-gate failure stops the pass with exit code 1, because there is no
result to compute past it.

Usage:
  python run_checks.py --counts counts.csv --data units.csv \
      --y metric --x pre_metric --arm arm \
      [--control control] [--tau2 0.0001] [--alpha 0.05] \
      [--store priors.jsonl --metric activation_rate --unit pp]
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from gallop import priors, sequential, shrink, trust, variance


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--counts", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--y", required=True)
    ap.add_argument("--x", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--control")
    ap.add_argument("--expected", help="intended shares, e.g. 0.5,0.5")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--tau2", type=float, default=1e-4,
                    help="mixture prior variance for the always-valid bound")
    ap.add_argument("--store")
    ap.add_argument("--metric")
    ap.add_argument("--unit", choices=["absolute", "pp", "relative"], default="absolute")
    a = ap.parse_args(argv)

    cdf = pd.read_csv(a.counts)
    assigned = dict(zip(cdf["arm"], cdf["assigned"]))
    expected = [float(x) for x in a.expected.split(",")] if a.expected else None

    print("1 · SRM")
    s = trust.srm(assigned, expected=expected)
    print(trust.report(s))
    if s["srm"]:
        print("\nTRUST GATE FAILED: no result exists. Work the cause taxonomy.")
        return 1

    if "exposed" in cdf.columns:
        print("\n2 · Exposure")
        e = trust.exposure_check(assigned, dict(zip(cdf["arm"], cdf["exposed"])))
        print(trust.report(e))
        if e["differential"]:
            print("\nTRUST GATE FAILED: differential exposure. No result exists.")
            return 1
    else:
        print("\n2 · Exposure: no exposed column given. If exposure was not logged,")
        print("    say so in the readout; the estimate may be diluted toward zero.")

    print("\n3 · Effect (raw and CUPED)")
    df = pd.read_csv(a.data)
    r = variance.cuped(df[a.y], df[a.x], df[a.arm], control=a.control)
    print(f"   raw    {r['effect_raw']:+.6f}  se {r['se_raw']:.6f}  p {r['p_raw']:.4f}")
    print(f"   cuped  {r['effect_adjusted']:+.6f}  se {r['se_adjusted']:.6f}"
          f"  p {r['p_adjusted']:.4f}   variance reduction {r['variance_reduction']:.0%}"
          f" (rho {r['rho']:.2f})")

    n = min(r["n_control"], r["n_treatment"])
    sd_adj = r["se_adjusted"] * np.sqrt(n / 2)
    av = sequential.always_valid_ci(0.0, r["effect_adjusted"], sd_adj, n,
                                    tau2=a.tau2, alpha=a.alpha)
    lo, hi = av["ci"]
    flo, fhi = av["fixed_horizon_ci"]
    print(f"   fixed-horizon 95% CI  [{flo:+.6f}, {fhi:+.6f}]  (valid only if nobody peeked)")
    print(f"   always-valid CI       [{lo:+.6f}, {hi:+.6f}]  |z| bound {av['bound_z']:.2f}")
    print(f"   significant under continuous monitoring: {av['significant']}")

    if a.store and a.metric:
        print("\n4 · Shrinkage toward the prior store")
        try:
            sh = shrink.from_store(r["effect_adjusted"], r["se_adjusted"],
                                   priors.read(a.store), a.metric, a.unit)
        except ValueError as err:
            print(f"   not available: {err}")
        else:
            print(f"   prior: {sh['n_priors']} readouts, mu {sh['mu']:+.6f}, "
                  f"tau {np.sqrt(sh['tau2']):.6f}")
            print(f"   shrunk effect {sh['effect_shrunk']:+.6f}  (weight on data "
                  f"{sh['weight_on_data']:.2f}, overstatement {sh['overstatement']:+.6f})")
            print("   the shrunk number is the planning number and the one written back.")
    else:
        print("\n4 · Shrinkage: no store given; the raw estimate is unshrunk and, if it")
        print("    cleared a threshold, inflated in expectation.")

    print("\nNext: guardrails before the primary, the pre-registered segment only,")
    print("then writing-readouts files the entry and the prior-store record.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
