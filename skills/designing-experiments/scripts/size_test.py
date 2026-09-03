"""Size a test from the prior store: MDE at the available traffic, duration, verdict.

Reads what the metric has actually moved by across past readouts, computes
the detectable effect at the traffic on offer, and says whether the test is
fundable. The verdict logic is the traffic-ceiling argument: if the MDE at a
sensible duration exceeds what this metric has ever produced, the test is not
underpowered, the question is untestable as posed.

Usage:
  python size_test.py --store priors.jsonl --metric activation_rate \
      --baseline-rate 0.12 --units-per-day 8000 [--max-weeks 6] [--unit pp]

Without --store the MDE is still computed, flagged as unanchored.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from gallop import power, priors


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", help="prior store JSONL; omit to size unanchored")
    ap.add_argument("--metric", required=True)
    ap.add_argument("--unit", default="pp", choices=["absolute", "pp", "relative"],
                    help="unit prior-store effects are recorded in for this metric")
    ap.add_argument("--baseline-rate", type=float, help="for a proportion metric")
    ap.add_argument("--sd", type=float, help="for a continuous metric")
    ap.add_argument("--units-per-day", type=float, required=True)
    ap.add_argument("--eligible-share", type=float, default=1.0)
    ap.add_argument("--max-weeks", type=float, default=6.0,
                    help="longest run the surface can afford")
    a = ap.parse_args(argv)

    daily = a.units_per_day * a.eligible_share
    n_at_max = daily * a.max_weeks * 7 / 2  # per arm, two arms
    kw = {"baseline_rate": a.baseline_rate, "sd": a.sd}
    mde_abs = power.mde(n_at_max, **kw)
    scale = 100 if a.unit == "pp" else 1
    print(f"traffic: {daily:,.0f} eligible units/day; at {a.max_weeks:.0f} weeks, "
          f"n per arm = {n_at_max:,.0f}")
    print(f"MDE at {a.max_weeks:.0f} weeks (80% power, alpha 0.05): "
          f"{mde_abs * scale:.3f}{'pp' if a.unit == 'pp' else ''}")
    if a.baseline_rate:
        print(f"  as a relative lift on {a.baseline_rate:.1%}: {mde_abs / a.baseline_rate:.1%}")

    if not a.store:
        print("\nno prior store given: the MDE above is a fact, but any effect target")
        print("is unanchored. Record readouts with gallop.priors to fix that.")
        return 0

    df = priors.read(a.store, metric=a.metric)
    if df.empty:
        print(f"\nprior store has no records for {a.metric!r}: target is unanchored.")
        return 0
    df = df[df["unit"] == a.unit]
    effects = df["effect"].to_numpy(float)
    print(f"\nprior store: {len(effects)} readouts on {a.metric!r} ({a.unit})")
    print(f"  effects: mean {effects.mean() * scale:+.3f}, sd {effects.std(ddof=1) * scale:.3f}, "
          f"|max| {np.abs(effects).max() * scale:.3f}")

    biggest = float(np.abs(effects).max())
    if biggest <= 0:
        print("verdict: NOT FUNDABLE (no past effect to size against)")
        return 1
    days_for_biggest = power.duration(biggest, a.units_per_day,
                                      eligible_share=a.eligible_share, **kw)
    print(f"  detecting the largest effect ever recorded ({biggest * scale:.3f}) "
          f"needs {days_for_biggest:,.0f} days at this traffic")

    if mde_abs <= biggest:
        print(f"\nverdict: FUNDABLE. Effects this metric has produced are detectable "
              f"within {a.max_weeks:.0f} weeks.")
        return 0
    print(f"\nverdict: NOT FUNDABLE AT THIS TRAFFIC. The MDE ({mde_abs * scale:.3f}) exceeds "
          f"anything this metric has produced ({biggest * scale:.3f}).")
    print("options, in order: make the change bigger; cut variance (CUPED, nearer")
    print("metric, targeted segment); or decide without a test and write that down.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
