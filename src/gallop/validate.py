"""Validation for a model that will make decisions: out of time, against the baseline, calibrated.

The package does not fit models; any library does that. What an agent
improvising the validation plausibly gets wrong is pinned here:

time_split      the out-of-time cut, with a gap for the label horizon. A
                random split on time-ordered data is not a validation.
leakage_screen  features that separate the outcome on their own, which is
                usually the outcome or something logged after it.
baseline_lift   precision at the operating point against the base rate. The
                decision acts on the top k; AUC alone is not a validation.
calibration     reliability table, Brier score with its Murphy decomposition,
                expected calibration error, against the base-rate forecast.
qini            the uplift curve on randomised rows: outcomes gained by
                targeting the top share by score, against random targeting.
mase            forecast error scaled by the in-sample seasonal naive. At or
                above 1 the naive did as well and is the forecast.

Run:  python -m gallop.validate lift --data scored.csv --y churned --score p_churn --k 0.1
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy import stats

# %% ------------------------------------------------------------------- split


def time_split(dates, holdout_frac=0.2, cutoff=None, gap=0):
    """Boolean masks for an out-of-time validation.

    Rows dated on or after `cutoff` (default: the last `holdout_frac` of the
    date range by row count) are the test window. Rows dated within `gap`
    days before the cutoff are excluded from training, so that a label
    window straddling the cutoff cannot leak the test period into the fit.
    """
    d = pd.to_datetime(pd.Series(np.asarray(dates)).reset_index(drop=True))
    if d.isna().any():
        raise ValueError("dates contain missing or unparseable values")
    if cutoff is None:
        if not 0 < holdout_frac < 1:
            raise ValueError("holdout_frac must be between 0 and 1")
        cutoff = d.sort_values().iloc[int(np.floor(len(d) * (1 - holdout_frac)))]
    cutoff = pd.Timestamp(cutoff)
    if gap < 0:
        raise ValueError("gap must be non-negative days")
    train = (d < cutoff - pd.Timedelta(days=gap)).to_numpy()
    test = (d >= cutoff).to_numpy()
    if train.sum() == 0 or test.sum() == 0:
        raise ValueError(f"cutoff {cutoff.date()} leaves an empty train or test window")
    return {
        "cutoff": cutoff, "gap_days": gap, "train": train, "test": test,
        "n_train": int(train.sum()), "n_test": int(test.sum()),
        "train_end": d[train].max(), "test_start": d[test].min(),
    }


# %% ---------------------------------------------------------------- leakage


def auc(y, score):
    """Area under the ROC curve by the Mann-Whitney rank statistic."""
    y = np.asarray(y, float)
    s = np.asarray(score, float)
    pos = y == 1
    n1, n0 = int(pos.sum()), int((~pos).sum())
    if n1 == 0 or n0 == 0:
        raise ValueError("auc needs both outcomes present")
    r = stats.rankdata(s)
    return float((r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def leakage_screen(X, y, threshold=0.95):
    """Rank numeric features by how well each separates the outcome alone.

    A single feature at or above `threshold` (AUC either direction) is
    flagged: it is usually the outcome under another name, or a field
    written after the outcome. Non-numeric columns are skipped and listed.
    """
    X = pd.DataFrame(X)
    y = np.asarray(y, float)
    rows, skipped = [], []
    for c in X.columns:
        col = X[c]
        if not pd.api.types.is_numeric_dtype(col):
            skipped.append(str(c))
            continue
        col = pd.to_numeric(col, errors="coerce").astype(float)
        col = col.fillna(col.median() if col.notna().any() else 0.0)
        a = auc(y, col.to_numpy())
        sep = max(a, 1 - a)
        rows.append({"feature": str(c), "auc": sep, "flagged": bool(sep >= threshold)})
    out = pd.DataFrame(rows, columns=["feature", "auc", "flagged"])
    out = out.sort_values("auc", ascending=False).reset_index(drop=True)
    out.attrs["skipped"] = skipped
    return out


# %% ------------------------------------------------------------------- lift


def baseline_lift(y, score, k=0.1):
    """Precision, lift and recall when the decision acts on the top `k` share by score."""
    y = np.asarray(y, float)
    s = np.asarray(score, float)
    if len(y) != len(s) or len(y) == 0:
        raise ValueError("y and score must be the same non-zero length")
    if not 0 < k <= 1:
        raise ValueError("k must be in (0, 1]")
    n = len(y)
    n_k = max(1, round(k * n))
    order = np.argsort(-s, kind="stable")
    top = y[order[:n_k]]
    base = float(y.mean())
    prec = float(top.mean())
    return {
        "k": k, "n": n, "n_targeted": n_k, "precision_at_k": prec, "base_rate": base,
        "lift": prec / base if base > 0 else float("nan"),
        "recall_at_k": float(top.sum() / y.sum()) if y.sum() > 0 else float("nan"),
        "auc": auc(y, s) if 0 < y.sum() < n else float("nan"),
    }


# %% ------------------------------------------------------------ calibration


def calibration(y, score, bins=10):
    """Reliability table, Brier score and its Murphy decomposition.

    Brier = reliability - resolution + uncertainty holds exactly for the
    binned forecast (each score replaced by its bin's mean score); the
    unbinned Brier is reported beside it. `skill` is 1 - brier / brier_base,
    the share of the base-rate forecast's error the model removes.
    """
    y = np.asarray(y, float)
    s = np.asarray(score, float)
    if len(y) != len(s) or len(y) == 0:
        raise ValueError("y and score must be the same non-zero length")
    if s.min() < 0 or s.max() > 1:
        raise ValueError("scores must be probabilities in [0, 1]")
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.searchsorted(edges, s, side="right") - 1, 0, bins - 1)
    base = float(y.mean())
    n = len(y)
    rows = []
    rel = res = ece = brier_binned = 0.0
    for b in range(bins):
        m = idx == b
        nb = int(m.sum())
        if nb == 0:
            continue
        ms, ob = float(s[m].mean()), float(y[m].mean())
        rows.append({"bin": b, "lo": edges[b], "hi": edges[b + 1], "n": nb,
                     "mean_score": ms, "observed_rate": ob})
        rel += nb * (ms - ob) ** 2
        res += nb * (ob - base) ** 2
        ece += nb * abs(ms - ob)
        brier_binned += float(((ms - y[m]) ** 2).sum())
    brier = float(((s - y) ** 2).mean())
    brier_base = base * (1 - base)
    return {
        "table": pd.DataFrame(rows), "brier": brier, "brier_binned": brier_binned / n,
        "brier_base": brier_base,
        "skill": 1 - brier / brier_base if brier_base > 0 else float("nan"),
        "reliability": rel / n, "resolution": res / n, "uncertainty": brier_base,
        "ece": ece / n, "base_rate": base,
    }


# %% ------------------------------------------------------------------- qini


def qini(y, score, arm, control=None, k=0.1, n_points=10):
    """The Qini curve: incremental outcomes from targeting the top share by score.

    Rows must come from a randomised assignment with exactly two arms.
    Q(t) = Y_treated(t) - Y_control(t) * N_treated(t) / N_control(t) among
    the top t of the ranking (Radcliffe). The curve is scaled by the total
    number of units; the diagonal from 0 to Q(1) is random targeting, and
    `auqc` is the area between the curve and that diagonal.
    """
    y = np.asarray(y, float)
    s = np.asarray(score, float)
    arm = np.asarray(arm)
    if not (len(y) == len(s) == len(arm)) or len(y) == 0:
        raise ValueError("y, score and arm must be the same non-zero length")
    arms = sorted(set(arm.tolist()))
    if len(arms) != 2:
        raise ValueError(f"qini needs exactly two arms, got {arms}")
    if control is None:
        control = "control" if "control" in arms else arms[0]
    if control not in arms:
        raise ValueError(f"control {control!r} not among arms {arms}")
    t = arm != control
    n, nt, nc = len(y), int(t.sum()), int((~t).sum())
    if nt == 0 or nc == 0:
        raise ValueError("both arms must have units")

    order = np.argsort(-s, kind="stable")
    yo, to = y[order], t[order]
    cum_t = np.cumsum(to)
    cum_c = np.cumsum(~to)
    cum_yt = np.cumsum(yo * to)
    cum_yc = np.cumsum(yo * ~to)
    with np.errstate(divide="ignore", invalid="ignore"):
        q = np.where(cum_c > 0, cum_yt - cum_yc * cum_t / cum_c, 0.0) / n
    frac = np.arange(1, n + 1) / n
    q_total = float(q[-1])
    random_line = frac * q_total
    auqc = float(np.trapezoid(q - random_line, frac)) if hasattr(np, "trapezoid") \
        else float(np.trapz(q - random_line, frac))
    ate = float(y[t].mean() - y[~t].mean())

    n_k = max(1, round(k * n))
    top = order[:n_k]
    tt = t[top]
    uplift_k = float(y[top][tt].mean() - y[top][~tt].mean()) if tt.any() and (~tt).any() \
        else float("nan")

    pts = np.unique(np.clip((np.arange(1, n_points + 1) * n / n_points).round().astype(int), 1, n))
    curve = pd.DataFrame({"fraction": frac[pts - 1], "incremental": q[pts - 1],
                          "random": random_line[pts - 1]})
    return {
        "curve": curve, "auqc": auqc, "ate": ate, "incremental_total": q_total,
        "uplift_at_k": uplift_k, "k": k,
        "peak_fraction": float(frac[int(np.argmax(q))]),
        "n_treated": nt, "n_control": nc,
    }


# %% ------------------------------------------------------------------- mase


def mase(y_train, y_test, forecast, season=1):
    """Mean absolute scaled error against the in-sample seasonal naive.

    The scale is the naive's mean absolute error over the training history
    (Hyndman & Koehler). Also reports the seasonal naive's own error on the
    test window, the baseline the model competes with on those dates.
    """
    tr = np.asarray(y_train, float)
    te = np.asarray(y_test, float)
    fc = np.asarray(forecast, float)
    m = int(season)
    if m < 1:
        raise ValueError("season must be a positive integer")
    if len(tr) <= m:
        raise ValueError(f"training history ({len(tr)}) must exceed the season ({m})")
    if len(te) != len(fc) or len(te) == 0:
        raise ValueError("y_test and forecast must be the same non-zero length")
    scale = float(np.mean(np.abs(tr[m:] - tr[:-m])))
    if scale == 0:
        raise ValueError("the seasonal naive has zero in-sample error; the series is periodic")
    mae = float(np.mean(np.abs(te - fc)))
    naive = np.array([tr[len(tr) - m + (i % m)] for i in range(len(te))])
    return {
        "mase": mae / scale, "mae": mae, "mae_naive_insample": scale,
        "mae_naive_test": float(np.mean(np.abs(te - naive))),
        "naive_forecast": naive, "season": m,
        "verdict": "beats the seasonal naive" if mae / scale < 1
        else "NAIVE DID AS WELL: the seasonal naive is the forecast",
    }


# %% --------------------------------------------------------------------- cli


def main(argv=None):
    p = argparse.ArgumentParser(prog="gallop.validate", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("lift", help="precision and lift at the top k")
    sp.add_argument("--data", required=True)
    sp.add_argument("--y", required=True)
    sp.add_argument("--score", required=True)
    sp.add_argument("--k", type=float, default=0.1)

    sp = sub.add_parser("calibrate", help="reliability table and Brier decomposition")
    sp.add_argument("--data", required=True)
    sp.add_argument("--y", required=True)
    sp.add_argument("--score", required=True)
    sp.add_argument("--bins", type=int, default=10)

    sp = sub.add_parser("screen", help="univariate leakage screen on feature columns")
    sp.add_argument("--data", required=True)
    sp.add_argument("--y", required=True)
    sp.add_argument("--features", required=True, help="comma-separated columns")
    sp.add_argument("--threshold", type=float, default=0.95)

    sp = sub.add_parser("qini", help="uplift curve on randomised rows")
    sp.add_argument("--data", required=True)
    sp.add_argument("--y", required=True)
    sp.add_argument("--score", required=True)
    sp.add_argument("--arm", required=True)
    sp.add_argument("--control")
    sp.add_argument("--k", type=float, default=0.1)

    sp = sub.add_parser("mase", help="forecast error against the seasonal naive")
    sp.add_argument("--data", required=True, help="csv in time order")
    sp.add_argument("--y", required=True, help="actuals column")
    sp.add_argument("--forecast", required=True, help="forecast column, read on test rows")
    sp.add_argument("--train-rows", type=int, required=True,
                    help="rows from the top that are training history")
    sp.add_argument("--season", type=int, default=1)

    a = p.parse_args(argv)
    df = pd.read_csv(a.data)

    if a.cmd == "lift":
        r = baseline_lift(df[a.y], df[a.score], k=a.k)
        print(f"  top {a.k:.0%}: {r['n_targeted']:,} of {r['n']:,} units")
        print(f"  precision {r['precision_at_k']:.1%}   base rate {r['base_rate']:.1%}"
              f"   lift {r['lift']:.2f}   recall {r['recall_at_k']:.1%}   auc {r['auc']:.3f}")
    elif a.cmd == "calibrate":
        r = calibration(df[a.y], df[a.score], bins=a.bins)
        print(r["table"].to_string(index=False, float_format=lambda v: f"{v:.3f}"))
        print(f"  brier {r['brier']:.4f}   base-rate brier {r['brier_base']:.4f}"
              f"   skill {r['skill']:+.3f}   ece {r['ece']:.3f}")
        print(f"  reliability {r['reliability']:.4f}   resolution {r['resolution']:.4f}"
              f"   uncertainty {r['uncertainty']:.4f}")
    elif a.cmd == "screen":
        cols = [c.strip() for c in a.features.split(",")]
        r = leakage_screen(df[cols], df[a.y], threshold=a.threshold)
        for _, row in r.iterrows():
            print(f"  {row['feature']:<24} auc {row['auc']:.3f}{'  FLAGGED' if row['flagged'] else ''}")
        if r.attrs.get("skipped"):
            print(f"  skipped (non-numeric): {', '.join(r.attrs['skipped'])}")
    elif a.cmd == "qini":
        r = qini(df[a.y], df[a.score], df[a.arm], control=a.control, k=a.k)
        print(r["curve"].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
        print(f"  overall uplift {r['ate']:+.4f}   top-{a.k:.0%} uplift {r['uplift_at_k']:+.4f}"
              f"   area over random {r['auqc']:+.4f}   peak at {r['peak_fraction']:.0%}")
    elif a.cmd == "mase":
        tr = df[a.y].iloc[:a.train_rows]
        te = df[a.y].iloc[a.train_rows:]
        fc = df[a.forecast].iloc[a.train_rows:]
        r = mase(tr, te, fc, season=a.season)
        print(f"  mae {r['mae']:.4f}   naive mae in-sample {r['mae_naive_insample']:.4f}"
              f"   naive mae on test {r['mae_naive_test']:.4f}")
        print(f"  MASE {r['mase']:.3f}   {r['verdict']}")


if __name__ == "__main__":
    main()
