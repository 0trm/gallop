"""The exploratory pass in one command: the move, mix versus rate, the funnel, the segments, the size.

Inputs:
  --segments   csv with columns period, segment, n, y (one row per period and segment;
               an optional dimension column splits several cuts of the same total)
  --before --after   the two period values to compare
  --funnel     optional csv with columns period, step, n, listed in step order
  --store --metric --unit --baseline-rate --units-per-day   optional, for the sizing
  --gap --n-affected   override the default sizing (the change itself, on the after
               period's units)

The floor is not scripted: raw volumes, what shipped, the source of truth
and the calendar are checked by hand first, and this pass means nothing
until they are.

Usage:
  python size_opportunity.py --segments segments.csv --before 2026-07 --after 2026-08 \
      [--dimension-col dimension] [--funnel funnel.csv] [--alpha 0.05] \
      [--store priors.jsonl --metric checkout_rate --unit pp \
       --baseline-rate 0.034 --units-per-day 7000 --max-weeks 6]
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from gallop import explore


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--segments", required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--period-col", default="period")
    ap.add_argument("--segment-col", default="segment")
    ap.add_argument("--dimension-col", default="dimension",
                    help="if present in the csv, each dimension is decomposed on its own")
    ap.add_argument("--funnel")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--store"); ap.add_argument("--metric")
    ap.add_argument("--unit", default="pp", choices=["absolute", "pp", "relative"])
    ap.add_argument("--baseline-rate", type=float); ap.add_argument("--sd", type=float)
    ap.add_argument("--units-per-day", type=float); ap.add_argument("--eligible-share", type=float, default=1.0)
    ap.add_argument("--max-weeks", type=float, default=6.0)
    ap.add_argument("--gap", type=float); ap.add_argument("--n-affected", type=float)
    a = ap.parse_args(argv)

    df = pd.read_csv(a.segments)
    dims = [None]
    if a.dimension_col in df.columns:
        dims = list(df[a.dimension_col].unique())

    print("0 · The floor: raw volumes, what shipped, a source of truth, the calendar.")
    print("    Not scripted. If any is live, stop here: defining-metrics owns it.")

    first = None
    total_cuts = 0
    for dim in dims:
        d = df if dim is None else df[df[a.dimension_col] == dim]
        b = d[d[a.period_col].astype(str) == str(a.before)]
        af = d[d[a.period_col].astype(str) == str(a.after)]
        if b.empty or af.empty:
            sys.exit(f"no rows for --before {a.before!r} or --after {a.after!r}")
        r = explore.mix_rate(b, af, segment=a.segment_col, alpha=a.alpha)
        total_cuts += r["n_cuts"]
        if first is None:
            first = r
            print(f"\n1 · The move: {r['rate_before']:.3%} -> {r['rate_after']:.3%}, "
                  f"{r['change'] * 100:+.3f}pp ({a.before} to {a.after})")
            print("    State the baseline it is judged against and the ordinary wobble; a move")
            print("    inside the wobble is not a question.")
        label = f" by {dim}" if dim else ""
        print(f"\n2 · Mix or rate{label}")
        print(f"    rate effect {r['rate_effect'] * 100:+.3f}pp   mix effect {r['mix_effect'] * 100:+.3f}pp"
              f"   ({r['n_cuts']} cuts, {r['n_flagged']} flagged at BH {a.alpha})")
        if r["simpson"]:
            print("    SIMPSON'S CASE: every segment that moved went against the total. A mix move.")
        elif abs(r["mix_effect"]) > abs(r["rate_effect"]):
            print("    mix dominates: the population changed, not the surface. Look upstream.")
        else:
            print("    rate dominates: the segments changed. Look at the surface and the step.")
        t = r["table"].head(6)
        print(f"    top segments by contribution to the change (share of {r['change'] * 100:+.3f}pp):")
        for _, row in t.iterrows():
            sh = row["contribution"] / r["change"] if r["change"] else float("nan")
            print(f"      {row['segment']!s:<22} {row['rate_before']:.2%} -> {row['rate_after']:.2%}"
                  f"   contribution {row['contribution'] * 100:+.3f}pp ({sh:.0%})"
                  f"   p {row['p']:.3f}  adj {row['p_adj']:.2f}{'  FLAGGED' if row['flagged'] else ''}")

    if a.funnel:
        f = pd.read_csv(a.funnel)
        b = f[f[a.period_col].astype(str) == str(a.before)]
        af = f[f[a.period_col].astype(str) == str(a.after)]
        r = explore.funnel_steps(b, af)
        print(f"\n3 · The funnel: overall {r['overall_before']:.3%} -> {r['overall_after']:.3%}"
              f" ({r['relative_change']:+.1%}); largest step: {r['largest_step']}")
        for _, row in r["table"].iterrows():
            print(f"      {row['step']!s:<22} {row['rate_before']:.2%} -> {row['rate_after']:.2%}"
                  f"   share of change {row['share']:.0%}")
    else:
        print("\n3 · The funnel: no --funnel given. Localise to a step before cutting by segment.")

    print(f"\n4 · Cuts examined so far: {total_cuts}. Expected significant under nothing at all,"
          f" at alpha {a.alpha}: {a.alpha * total_cuts:.1f}. Declare the count in the hand-back.")

    gap = a.gap if a.gap is not None else abs(first["change"])
    n_aff = a.n_affected
    if n_aff is None:
        d0 = df if dims == [None] else df[df[a.dimension_col] == dims[0]]
        n_aff = float(d0[d0[a.period_col].astype(str) == str(a.after)]["n"].sum())
    store = None
    if a.store:
        from gallop import priors
        store = priors.read(a.store)
    s = explore.size_opportunity(gap, n_aff, baseline_rate=a.baseline_rate, sd=a.sd,
                                 units_per_day=a.units_per_day, eligible_share=a.eligible_share,
                                 max_weeks=a.max_weeks, store=store, metric=a.metric, unit=a.unit)
    print(f"\n5 · The size (gap {gap * 100:.3f}pp on {n_aff:,.0f} units a period)")
    print(f"    ceiling: {s['ceiling_units']:,.0f} units a period if the whole gap closes")
    if s["anchored_mean"] is not None:
        print(f"    anchored: {s['n_priors']} readouts on {a.metric!r}, mean {s['anchored_mean'] * 100:+.3f}pp,"
              f" largest {s['anchored_max'] * 100:.3f}pp -> {s['anchored_units']:,.0f} units at the mean")
    else:
        print("    anchored: UNANCHORED. No store, or no records for this metric and unit.")
    if s["mde"] is not None:
        print(f"    MDE at {s['n_per_arm']:,.0f} per arm over {a.max_weeks:.0f} weeks: {s['mde'] * 100:.3f}pp")
    print(f"    verdict: {s['verdict']}")
    print("\nNext: write the mechanism in one sentence, fill templates/hypothesis.md, and")
    print("re-enter routing-questions at step 3. This is a hypothesis, not an effect.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
