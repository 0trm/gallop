import numpy as np
import pytest

from gallop import variance


def _experiment(n=40_000, rho=0.7, effect=0.05, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(10, 2, 2 * n)
    arm = np.array(["control"] * n + ["treatment"] * n)
    noise = np.sqrt(1 - rho**2)
    y = 5 + rho * (x - 10) / 2 + rng.normal(0, noise, 2 * n) + (arm == "treatment") * effect
    return y, x, arm


def test_variance_reduction_is_rho_squared():
    # Deng et al. (2013): Var(Y_adj) = Var(Y) (1 - rho^2).
    y, x, arm = _experiment(rho=0.7)
    r = variance.cuped(y, x, arm)
    assert r["variance_reduction"] == pytest.approx(r["rho"] ** 2, abs=0.01)
    assert r["variance_reduction"] == pytest.approx(0.49, abs=0.02)
    assert r["se_adjusted"] < r["se_raw"]


def test_cuped_is_unbiased_and_recovers_the_effect():
    y, x, arm = _experiment(effect=0.05, seed=3)
    r = variance.cuped(y, x, arm)
    assert r["effect_adjusted"] == pytest.approx(0.05, abs=3 * r["se_adjusted"])


def test_control_label_flips_the_sign():
    y, x, arm = _experiment(effect=0.05, seed=1)
    a = variance.cuped(y, x, arm, control="control")
    b = variance.cuped(y, x, arm, control="treatment")
    assert a["effect_adjusted"] == pytest.approx(-b["effect_adjusted"])


def test_requires_exactly_two_arms():
    y, x, arm = _experiment(n=300)
    with pytest.raises(ValueError):
        variance.cuped(y, x, np.where(np.arange(600) % 3 == 0, "c", arm))
