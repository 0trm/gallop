"""The validation pass in one command: the out-of-time window, leakage, lift, calibration, Qini.

Inputs:
  --data     csv with one row per scored unit
  --y        outcome column (0/1)
  --score    the model's score column
  --date     date column; --cutoff is the start of the out-of-time window
  --k        the operating point, as a share of the window (default 0.1)
  --arm --control   optional: randomised arm column, for the Qini curve
  --features        optional: comma-separated feature columns to screen

The scores in the window must come from a model fit on rows before the
cutoff. The script cannot check that; if they were fit on all rows, nothing
below is a validation and the verdict says so.

Usage:
  python validate_model.py --data scored.csv --y churned --score p_churn \
      --date week --cutoff 2026-07-01 --k 0.1 \
      [--arm arm --control control] [--features tenure,logins_30d] [--bins 10]
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from gallop import validate

MIN_POSITIVES = 200  # below this the window cannot separate a model from the base rate


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", required=True)
    ap.add_argument("--y", required=True)
    ap.add_argument("--score", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--cutoff", required=True, help="first date of the out-of-time window")
    ap.add_argument("--k", type=float, default=0.1)
    ap.add_argument("--arm")
    ap.add_argument("--control")
    ap.add_argument("--features", help="comma-separated columns to screen for leakage")
    ap.add_argument("--bins", type=int, default=10)
    a = ap.parse_args(argv)

    df = pd.read_csv(a.data)
    split = validate.time_split(df[a.date], cutoff=a.cutoff)
    w = df[split["test"]]
    positives = int(w[a.y].sum())
    print("1 · The out-of-time window")
    print(f"   {split['n_train']:,} rows before {split['cutoff'].date()}, "
          f"{split['n_test']:,} rows on or after it, {positives:,} positives in the window")
    print("   the scores in the window must come from a model fit on the rows before it;")
    print("   if they were fit on all rows, stop here: nothing below is a validation.")
    if positives < MIN_POSITIVES:
        print(f"\nNOT FUNDABLE AT THIS VOLUME: {positives} positives in the window, "
              f"fewer than {MIN_POSITIVES}.")
        print("   The window cannot separate a model from the base rate. Hand back a rule.")
        return 1

    if a.features:
        print("\n2 · Leakage screen")
        cols = [c.strip() for c in a.features.split(",")]
        s = validate.leakage_screen(w[cols], w[a.y])
        for _, r in s.iterrows():
            flag = "  FLAGGED" if r["flagged"] else ""
            print(f"   {r['feature']:<24} univariate auc {r['auc']:.3f}{flag}")
        if s["flagged"].any():
            print("   explain every flagged feature before the numbers below count.")
    else:
        print("\n2 · Leakage screen: no --features given; screen them before believing the lift.")

    print(f"\n3 · Lift at the operating point (top {a.k:.0%})")
    lift = validate.baseline_lift(w[a.y], w[a.score], k=a.k)
    print(f"   targeted {lift['n_targeted']:,} of {lift['n']:,}   precision {lift['precision_at_k']:.1%}"
          f"   base rate {lift['base_rate']:.1%}   lift {lift['lift']:.2f}   recall {lift['recall_at_k']:.1%}")
    print(f"   auc {lift['auc']:.3f} (reported, not the validation)")

    print(f"\n4 · Calibration ({a.bins} bins)")
    cal = validate.calibration(w[a.y], w[a.score], bins=a.bins)
    print(f"   brier {cal['brier']:.4f}   base-rate brier {cal['brier_base']:.4f}"
          f"   skill {cal['skill']:+.3f}   ece {cal['ece']:.3f}")
    print(f"   reliability {cal['reliability']:.4f}   resolution {cal['resolution']:.4f}")
    if cal["skill"] <= 0:
        print("   the scores are worse than the base rate as probabilities; rank with them, do not price.")

    if a.arm:
        print("\n5 · Qini on the randomised rows")
        q = validate.qini(w[a.y], w[a.score], w[a.arm], control=a.control)
        print(f"   overall uplift {q['ate']:+.4f}   top-{a.k:.0%} uplift {q['uplift_at_k']:+.4f}"
              f"   area over random {q['auqc']:+.4f}   peak at {q['peak_fraction']:.0%} targeted")
    else:
        print("\n5 · Qini: no --arm given. If this score decides who gets a treatment, it needs")
        print("    uplift on randomised rows, and precision at k measures the wrong thing.")

    ok = lift["lift"] > 1.0
    print()
    if not ok:
        print("NOT VALIDATED: the model does not beat the base rate at the operating point.")
        return 1
    print(f"VALIDATED OFFLINE: lift {lift['lift']:.2f} at the top {a.k:.0%}, out of time from "
          f"{split['cutoff'].date()}.")
    print("Impact is still unmeasured. Next: designing-experiments, the model against the")
    print("current rule behind a holdout; that readout, not this lift, goes in the prior store.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
