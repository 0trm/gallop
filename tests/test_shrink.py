import numpy as np
import pandas as pd
import pytest

from gallop import shrink


def test_normal_normal_posterior_closed_form():
    # Prior N(0.01, 0.0004), observation 0.05 with se 0.02:
    # w = 0.0004 / (0.0004 + 0.0004) = 0.5, posterior mean 0.03.
    r = shrink.empirical_bayes(0.05, 0.02, mu=0.01, tau2=0.0004)
    assert r["weight_on_data"] == pytest.approx(0.5)
    assert r["effect_shrunk"] == pytest.approx(0.03)
    assert r["se_shrunk"] == pytest.approx(np.sqrt(0.0002))


def test_prior_from_effects_method_of_moments():
    effects = [0.02, 0.00, 0.04, -0.02, 0.01]
    ses = [0.01] * 5
    p = shrink.prior_from_effects(effects, ses)
    assert p["mu"] == pytest.approx(np.mean(effects))
    assert p["tau2"] == pytest.approx(np.var(effects, ddof=1) - 0.0001)


def test_tau2_floors_at_zero_and_shrinks_fully():
    # Past effects indistinguishable from noise: everything shrinks to mu.
    r = shrink.empirical_bayes(0.05, 0.01, effects=[0.001, -0.001, 0.0005],
                               ses=[0.05, 0.05, 0.05])
    assert r["tau2"] == 0.0
    assert r["effect_shrunk"] == pytest.approx(r["mu"])


def test_recovers_true_effects_better_than_raw_on_average():
    # The winner's curse, corrected: across many noisy readouts of true
    # effects drawn from the prior, shrinkage cuts the mean squared error.
    rng = np.random.default_rng(2)
    true = rng.normal(0.01, 0.02, 300)
    se = 0.02
    observed = true + rng.normal(0, se, 300)
    shrunk = [shrink.empirical_bayes(o, se, effects=observed, ses=[se] * 300)["effect_shrunk"]
              for o in observed]
    assert np.mean((np.array(shrunk) - true) ** 2) < np.mean((observed - true) ** 2)


def test_from_store_refuses_mixed_units():
    store = pd.DataFrame({
        "metric": ["m"] * 4, "effect": [0.01, 0.02, 0.0, 0.01],
        "se": [0.01] * 4, "unit": ["pp", "pp", "pp", "relative"],
    })
    with pytest.raises(ValueError, match="unit"):
        shrink.from_store(0.02, 0.01, store, "m", "pp")


def test_needs_three_priors():
    with pytest.raises(ValueError, match="at least 3"):
        shrink.empirical_bayes(0.05, 0.01, effects=[0.01, 0.02], ses=[0.01, 0.01])
