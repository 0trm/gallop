import numpy as np
import pytest
from scipy import stats

from gallop import sequential


def test_obf_constant_matches_the_published_table():
    # O'Brien-Fleming two-sided alpha 0.05, five equally spaced looks:
    # the published final-look constant is 2.04 (boundaries 4.56 ... 2.04).
    c = sequential.calibrate_obf(5, alpha=0.05, n_sims=200_000, seed=1)
    assert c == pytest.approx(2.04, abs=0.03)
    b = sequential.obf_bounds(5, n_sims=200_000, seed=1)
    assert b[0] == pytest.approx(2.04 * np.sqrt(5), abs=0.10)
    assert b[-1] == pytest.approx(2.04, abs=0.03)


def test_msprt_boundary_closed_form_and_shape():
    # Direct evaluation of the mixture likelihood-ratio boundary.
    n, sd, tau2, alpha = 5000, 1.0, 0.01, 0.05
    v = 2 * sd**2 / n
    expected = np.sqrt(2 * (v + tau2) / tau2 * (np.log(1 / alpha) + 0.5 * np.log((v + tau2) / v)))
    assert sequential.msprt_bound(n, sd, tau2, alpha) == pytest.approx(float(expected))
    # Wide at small n, and never below the fixed-horizon 1.96 at any n: the
    # z-boundary grows like sqrt(log n) again at large n, which is the price
    # of validity over unbounded looks.
    bounds = [sequential.msprt_bound(n, 1.0) for n in (100, 1000, 10_000, 1_000_000)]
    assert bounds[0] > bounds[1]
    assert min(bounds) > 1.96


def test_msprt_holds_alpha_under_continuous_monitoring():
    # Peek after every batch under a true null; the crossing rate must stay
    # below alpha, where a naive 1.96 rule inflates far past it.
    rng = np.random.default_rng(0)
    sims, batches, batch = 400, 40, 50
    crossed_msprt = crossed_naive = 0
    for _ in range(sims):
        a = rng.normal(0, 1, (batches, batch)).reshape(-1)
        b = rng.normal(0, 1, (batches, batch)).reshape(-1)
        hit_m = hit_n = False
        for k in range(1, batches + 1):
            n = k * batch
            z = abs(b[:n].mean() - a[:n].mean()) / np.sqrt(2 / n)
            hit_m = hit_m or z > sequential.msprt_bound(n, 1.0)
            hit_n = hit_n or z > stats.norm.ppf(0.975)
        crossed_msprt += hit_m
        crossed_naive += hit_n
    assert crossed_msprt / sims <= 0.05
    assert crossed_naive / sims > 0.10


def test_always_valid_ci_wraps_the_boundary():
    r = sequential.always_valid_ci(0.10, 0.16, sd=1.0, n_per_arm=5000)
    se = np.sqrt(2 / 5000)
    assert r["effect"] == pytest.approx(0.06)
    assert r["ci"][1] - r["ci"][0] == pytest.approx(2 * r["bound_z"] * se)
    width_av = r["ci"][1] - r["ci"][0]
    width_fh = r["fixed_horizon_ci"][1] - r["fixed_horizon_ci"][0]
    assert width_av > width_fh
