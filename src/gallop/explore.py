"""What happened, decomposed: mix versus rate, funnel steps, segments with the cuts declared, the size.

The description bucket hands back a hypothesis, and the arithmetic behind
a defensible one is what an agent improvising it plausibly gets wrong:

mix_rate          Kitagawa decomposition of a rate change across segments into
                  a rate effect and a mix effect, exact, with every segment's
                  share of each, period-on-period tests with the
                  Benjamini-Hochberg adjustment, and Simpson's case named.
funnel_steps      the change in overall conversion split across funnel steps
                  by the log of each step's rate ratio; the shares sum to one.
scan_segments     every segment against the rest, cross-sectionally: the gap,
                  the units at stake if it matched the whole, the adjusted p,
                  and the number of cuts examined beside the flags.
size_opportunity  the ceiling, the prior-anchored estimate from the store, and
                  the MDE at the surface's traffic, with the verdict.

Run:  python -m gallop.explore mix --segments segments.csv --before 2026-07 --after 2026-08
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy import stats

# %% ---------------------------------------------------------------- helpers


def two_proportion_p(y1, n1, y2, n2):
    """Two-sided pooled z-test on two proportions."""
    y1, n1, y2, n2 = (np.asarray(v, float) for v in (y1, n1, y2, n2))
    with np.errstate(divide="ignore", invalid="ignore"):
        p = (y1 + y2) / (n1 + n2)
        se = np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
        z = (y2 / n2 - y1 / n1) / se
    p_val = 2 * stats.norm.sf(np.abs(z))
    return np.where(np.isfinite(p_val), p_val, 1.0)


def benjamini_hochberg(p):
    """Adjusted p-values controlling the false discovery rate."""
    p = np.asarray(p, float)
    m = len(p)
    if m == 0:
        return p
    order = np.argsort(p)
    ranked = p[order] * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(adj, 1.0)
    return out


def _counts(df, segment, n, y):
    d = pd.DataFrame(df)[[segment, n, y]].copy()
    d = d.groupby(segment, as_index=True)[[n, y]].sum()
    if (d[n] < 0).any() or (d[y] < 0).any() or (d[y] > d[n]).any():
        raise ValueError("counts must satisfy 0 <= y <= n in every segment")
    return d


# %% --------------------------------------------------------------- mix_rate


def mix_rate(before, after, *, segment="segment", n="n", y="y", alpha=0.05):
    """Decompose a rate change across segments into a rate effect and a mix effect.

    `before` and `after` hold one row per segment with the denominator `n`
    and the numerator count `y`. The two effects sum exactly to the change
    (Marshall-Edgeworth weights), and each segment's mix contribution is
    centred on the overall rate, so a growing low-rate segment reads as
    the drag it is. `simpson` is True when every segment that changed
    moved against the total.
    """
    b = _counts(before, segment, n, y)
    a = _counts(after, segment, n, y)
    idx = b.index.union(a.index)
    b = b.reindex(idx, fill_value=0)
    a = a.reindex(idx, fill_value=0)
    if b[n].sum() == 0 or a[n].sum() == 0:
        raise ValueError("each period needs a non-zero denominator")
    sb, sa = b[n] / b[n].sum(), a[n] / a[n].sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        rb = (b[y] / b[n]).fillna(0.0)
        ra = (a[y] / a[n]).fillna(0.0)
    r_before = float(b[y].sum() / b[n].sum())
    r_after = float(a[y].sum() / a[n].sum())
    change = r_after - r_before
    # Marshall-Edgeworth weights, so the two effects sum exactly to the change.
    # Mix contributions are centred on the overall rate: a segment's share
    # moving matters by how far its rate sits from the whole, and the
    # centring changes nothing in the sum because the share changes sum to 0.
    rate_c = (ra - rb) * (sa + sb) / 2
    mix_c = (sa - sb) * ((ra + rb) / 2 - (r_before + r_after) / 2)
    p = two_proportion_p(b[y], b[n], a[y], a[n])
    p_adj = benjamini_hochberg(p)
    table = pd.DataFrame({
        "segment": idx, "n_before": b[n].to_numpy(), "n_after": a[n].to_numpy(),
        "share_before": sb.to_numpy(), "share_after": sa.to_numpy(),
        "rate_before": rb.to_numpy(), "rate_after": ra.to_numpy(),
        "rate_contribution": rate_c.to_numpy(), "mix_contribution": mix_c.to_numpy(),
        "contribution": (rate_c + mix_c).to_numpy(), "p": p, "p_adj": p_adj,
        "flagged": p_adj < alpha,
    })
    table = table.reindex(table["contribution"].abs().sort_values(ascending=False).index)
    table = table.reset_index(drop=True)
    moved = (ra != rb) & (b[n] > 0) & (a[n] > 0)
    simpson = bool(change != 0 and moved.any()
                   and (np.sign(ra - rb)[moved] == -np.sign(change)).all())
    return {
        "rate_before": r_before, "rate_after": r_after, "change": float(change),
        "rate_effect": float(rate_c.sum()), "mix_effect": float(mix_c.sum()),
        "rate_share": float(rate_c.sum() / change) if change != 0 else float("nan"),
        "table": table, "simpson": simpson, "n_cuts": len(idx),
        "n_flagged": int(table["flagged"].sum()), "alpha": alpha,
    }


# %% ------------------------------------------------------------ funnel_steps


def funnel_steps(before, after, *, step="step", n="n"):
    """Split the change in overall conversion across funnel steps.

    `before` and `after` list the steps in order with the count reaching
    each. Overall conversion is last over first, a product of step rates,
    so its log change is the sum of the steps' log rate changes and each
    step's share of the total is exact.
    """
    b = pd.DataFrame(before); a = pd.DataFrame(after)
    if list(b[step]) != list(a[step]):
        raise ValueError("the two periods must list the same steps in the same order")
    nb = b[n].to_numpy(float); na = a[n].to_numpy(float)
    if len(nb) < 2:
        raise ValueError("a funnel needs at least two steps")
    if (nb <= 0).any() or (na <= 0).any():
        raise ValueError("every step needs a positive count in both periods")
    rb = nb[1:] / nb[:-1]; ra = na[1:] / na[:-1]
    log_change = np.log(ra / rb)
    total = float(np.log((na[-1] / na[0]) / (nb[-1] / nb[0])))
    share = log_change / total if total != 0 else np.full(len(log_change), np.nan)
    table = pd.DataFrame({
        "step": list(b[step])[1:], "rate_before": rb, "rate_after": ra,
        "log_change": log_change, "share": share,
    })
    largest = table.iloc[int(np.argmax(np.abs(log_change)))]["step"] if total != 0 else None
    return {
        "overall_before": float(nb[-1] / nb[0]), "overall_after": float(na[-1] / na[0]),
        "relative_change": float((na[-1] / na[0]) / (nb[-1] / nb[0]) - 1),
        "log_change": total, "table": table, "largest_step": largest,
    }


# %% ----------------------------------------------------------- scan_segments


def scan_segments(df, *, y, by, n=None, alpha=0.05):
    """Every segment against the rest, across one or more dimensions.

    Pass unit-level rows (`y` in {0, 1}) or aggregated rows with a count
    column `n`. For each level of each dimension in `by`: its rate, the
    gap to the whole, the units at stake if it matched the whole, the
    two-proportion p against the rest and its Benjamini-Hochberg
    adjustment. `n_cuts` is the number of segments examined, and it goes
    in the hand-back beside any flag.
    """
    d = pd.DataFrame(df)
    by = [by] if isinstance(by, str) else list(by)
    if n is None:
        d = d.assign(_n=1, _y=d[y].astype(float))
    else:
        d = d.assign(_n=d[n].astype(float), _y=d[y].astype(float))
    N, Y = float(d["_n"].sum()), float(d["_y"].sum())
    if N == 0:
        raise ValueError("no units")
    overall = Y / N
    rows = []
    for dim in by:
        g = d.groupby(dim)[["_n", "_y"]].sum()
        for level, r in g.iterrows():
            rest_n, rest_y = N - r["_n"], Y - r["_y"]
            rate = r["_y"] / r["_n"] if r["_n"] else float("nan")
            p = float(two_proportion_p(r["_y"], r["_n"], rest_y, rest_n)) if rest_n > 0 else 1.0
            rows.append({"dimension": dim, "level": level, "n": int(r["_n"]), "rate": rate,
                         "gap": rate - overall, "units_at_stake": (overall - rate) * r["_n"],
                         "p": p})
    table = pd.DataFrame(rows)
    table["p_adj"] = benjamini_hochberg(table["p"])
    table["flagged"] = table["p_adj"] < alpha
    table = table.reindex(table["units_at_stake"].abs().sort_values(ascending=False).index)
    table = table.reset_index(drop=True)
    return {
        "overall": overall, "table": table, "n_cuts": len(table),
        "n_flagged": int(table["flagged"].sum()), "expected_false": float(alpha * len(table)),
        "alpha": alpha,
    }


# %% -------------------------------------------------------- size_opportunity


def size_opportunity(gap, n_affected, *, baseline_rate=None, sd=None, units_per_day=None,
                     eligible_share=1.0, max_weeks=6.0, store=None, metric=None,
                     unit="absolute"):
    """The ceiling, the prior-anchored estimate, and the MDE, with the verdict.

    `gap` is absolute, in the metric's units (a fraction for a proportion);
    `n_affected` is the units per period the change would touch. `store` is
    a prior-store DataFrame (gallop.priors.read) whose effects for `metric`
    are converted from `unit` to absolute for the comparison.
    """
    from gallop import power
    gap = abs(float(gap)); n_affected = float(n_affected)
    out = {"gap": gap, "n_affected": n_affected, "ceiling_units": gap * n_affected}

    if store is not None:
        if metric is None:
            raise ValueError("metric is required to read the store")
        rows = store[(store["metric"] == metric) & (store["unit"] == unit)]
        eff = rows["effect"].to_numpy(float)
        if unit == "pp":
            eff = eff / 100
        elif unit == "relative":
            if baseline_rate is None:
                raise ValueError("relative effects need baseline_rate to become absolute")
            eff = eff * baseline_rate
        if len(eff):
            out.update({"n_priors": len(eff), "anchored_mean": float(eff.mean()),
                        "anchored_max": float(np.abs(eff).max()),
                        "anchored_units": float(max(eff.mean(), 0.0) * n_affected)})
        else:
            out.update({"n_priors": 0, "anchored_mean": None, "anchored_max": None,
                        "anchored_units": None})
    else:
        out.update({"n_priors": None, "anchored_mean": None, "anchored_max": None,
                    "anchored_units": None})

    if units_per_day is not None:
        n_per_arm = units_per_day * eligible_share * max_weeks * 7 / 2
        out["mde"] = power.mde(n_per_arm, sd=sd, baseline_rate=baseline_rate)
        out["n_per_arm"] = n_per_arm
    else:
        out["mde"] = None

    mde, amax = out["mde"], out["anchored_max"]
    if mde is None:
        verdict = "unsized: no traffic given, so the MDE is unknown"
    elif gap < mde:
        verdict = "TOO SMALL TO MEASURE: the ceiling is below the MDE; decide without a test, or make the change bigger"
    elif amax is None:
        verdict = "measurable, unanchored: no prior store; a test could see the ceiling but nothing says what this lever produces"
    elif amax >= mde:
        verdict = "WORTH A TEST: this metric has produced effects the surface can detect; route to designing-experiments"
    else:
        verdict = "LONG SHOT: nothing this metric has produced would be visible at this traffic; a bigger change, or decide untested"
    out["measurable"] = None if mde is None else bool(gap >= mde)
    out["fundable"] = None if (mde is None or amax is None) else bool(amax >= mde)
    out["verdict"] = verdict
    return out


# %% --------------------------------------------------------------------- cli


def _period_frames(path, period_col, before, after):
    df = pd.read_csv(path)
    b = df[df[period_col].astype(str) == str(before)]
    a = df[df[period_col].astype(str) == str(after)]
    if b.empty or a.empty:
        raise SystemExit(f"no rows for --before {before!r} or --after {after!r} in {path}")
    return b, a


def main(argv=None):
    p = argparse.ArgumentParser(prog="gallop.explore", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("mix", help="mix versus rate decomposition between two periods")
    sp.add_argument("--segments", required=True, help="csv: period, segment, n, y")
    sp.add_argument("--before", required=True); sp.add_argument("--after", required=True)
    sp.add_argument("--period-col", default="period"); sp.add_argument("--segment-col", default="segment")
    sp.add_argument("--alpha", type=float, default=0.05)

    sp = sub.add_parser("funnel", help="split a conversion change across funnel steps")
    sp.add_argument("--funnel", required=True, help="csv: period, step, n, in step order")
    sp.add_argument("--before", required=True); sp.add_argument("--after", required=True)
    sp.add_argument("--period-col", default="period")

    sp = sub.add_parser("scan", help="every segment against the rest, cross-sectionally")
    sp.add_argument("--data", required=True)
    sp.add_argument("--y", required=True)
    sp.add_argument("--by", required=True, help="comma-separated dimension columns")
    sp.add_argument("--n", help="count column for aggregated rows")
    sp.add_argument("--alpha", type=float, default=0.05)

    sp = sub.add_parser("size", help="ceiling, anchored estimate, MDE, verdict")
    sp.add_argument("--gap", type=float, required=True, help="absolute, in metric units")
    sp.add_argument("--n-affected", type=float, required=True)
    sp.add_argument("--baseline-rate", type=float); sp.add_argument("--sd", type=float)
    sp.add_argument("--units-per-day", type=float); sp.add_argument("--eligible-share", type=float, default=1.0)
    sp.add_argument("--max-weeks", type=float, default=6.0)
    sp.add_argument("--store"); sp.add_argument("--metric")
    sp.add_argument("--unit", default="pp", choices=["absolute", "pp", "relative"])

    a = p.parse_args(argv)
    def fmt(v):
        return f"{v:.4f}"

    if a.cmd == "mix":
        b, af = _period_frames(a.segments, a.period_col, a.before, a.after)
        r = mix_rate(b, af, segment=a.segment_col, alpha=a.alpha)
        print(f"  rate {r['rate_before']:.4%} -> {r['rate_after']:.4%}   change {r['change'] * 100:+.3f}pp")
        print(f"  rate effect {r['rate_effect'] * 100:+.3f}pp   mix effect {r['mix_effect'] * 100:+.3f}pp"
              f"   ({r['n_cuts']} cuts, {r['n_flagged']} flagged at BH {a.alpha})")
        if r["simpson"]:
            print("  SIMPSON'S CASE: every segment that moved went against the total; this is a mix move")
        print(r["table"].to_string(index=False, float_format=fmt))
    elif a.cmd == "funnel":
        b, af = _period_frames(a.funnel, a.period_col, a.before, a.after)
        r = funnel_steps(b, af)
        print(f"  overall {r['overall_before']:.4%} -> {r['overall_after']:.4%}"
              f"   relative change {r['relative_change']:+.2%}   largest step: {r['largest_step']}")
        print(r["table"].to_string(index=False, float_format=fmt))
    elif a.cmd == "scan":
        df = pd.read_csv(a.data)
        r = scan_segments(df, y=a.y, by=[c.strip() for c in a.by.split(",")], n=a.n, alpha=a.alpha)
        print(f"  overall {r['overall']:.4%}   {r['n_cuts']} cuts examined, {r['n_flagged']} flagged"
              f" at BH {a.alpha} (expected false at alpha: {r['expected_false']:.1f})")
        print(r["table"].to_string(index=False, float_format=fmt))
    elif a.cmd == "size":
        store = None
        if a.store:
            from gallop import priors
            store = priors.read(a.store)
        r = size_opportunity(a.gap, a.n_affected, baseline_rate=a.baseline_rate, sd=a.sd,
                             units_per_day=a.units_per_day, eligible_share=a.eligible_share,
                             max_weeks=a.max_weeks, store=store, metric=a.metric, unit=a.unit)
        print(f"  ceiling: gap {r['gap']:.5f} x {r['n_affected']:,.0f} units = {r['ceiling_units']:,.1f} units")
        if r["anchored_mean"] is not None:
            print(f"  anchored: {r['n_priors']} readouts, mean {r['anchored_mean']:+.5f}, largest {r['anchored_max']:.5f}"
                  f" -> {r['anchored_units']:,.1f} units at the mean")
        else:
            print("  anchored: unanchored (no store, or no records for this metric and unit)")
        if r["mde"] is not None:
            print(f"  MDE at {r['n_per_arm']:,.0f} per arm: {r['mde']:.5f}")
        print(f"  verdict: {r['verdict']}")


if __name__ == "__main__":
    main()
