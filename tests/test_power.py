import numpy as np
import pytest

from gallop import power


def test_continuous_sample_size_reproduces_cohen_medium_effect():
    # Classic closed-form result: d = 0.5 sd, alpha 0.05 two-sided, power 0.80
    # needs 2 * ((1.959964 + 0.841621) * 1 / 0.5)^2 = 62.79 per arm.
    n = power.sample_size(0.5, sd=1.0)
    assert n == pytest.approx(62.79, abs=0.02)


def test_proportion_mde_matches_planning_rule_of_thumb():
    # At the defaults the MDE is 2.8016 * sqrt(2 p (1-p) / n), the 2.8 rule
    # the traffic-ceiling arithmetic in designing-experiments uses.
    p, n = 0.10, 5000
    expected = 2.8016 * np.sqrt(2 * p * (1 - p) / n)
    assert power.mde(n, baseline_rate=p) == pytest.approx(expected, rel=1e-3)


def test_roundtrips():
    m = power.mde(5000, sd=1.0)
    assert power.power_at(5000, m, sd=1.0) == pytest.approx(0.80, abs=1e-6)
    assert power.sample_size(m, sd=1.0) == pytest.approx(5000, rel=1e-6)


def test_duration_scales_with_traffic_and_arms():
    d = power.duration(0.01, units_per_day=10_000, baseline_rate=0.10)
    n = power.sample_size(0.01, baseline_rate=0.10)
    assert d == pytest.approx(2 * n / 10_000)
    assert power.duration(0.01, 10_000, baseline_rate=0.10, eligible_share=0.5) == pytest.approx(2 * d)


def test_sd_and_rate_are_mutually_exclusive():
    with pytest.raises(ValueError):
        power.mde(1000, sd=1.0, baseline_rate=0.1)
    with pytest.raises(ValueError):
        power.mde(1000)
