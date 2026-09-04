import numpy as np
import pandas as pd
import pytest

from gallop import validate


def test_time_split_puts_every_test_date_after_every_train_date():
    dates = pd.date_range("2026-01-01", periods=100, freq="D")
    s = validate.time_split(dates, holdout_frac=0.2)
    assert s["n_test"] == 20 and s["n_train"] == 80
    assert dates[s["train"]].max() < dates[s["test"]].min()


def test_time_split_gap_excludes_the_label_horizon():
    dates = pd.date_range("2026-01-01", periods=100, freq="D")
    s = validate.time_split(dates, cutoff="2026-03-01", gap=30)
    assert s["test_start"] == pd.Timestamp("2026-03-01")
    assert s["train_end"] == pd.Timestamp("2026-01-29")
    assert s["n_train"] + s["n_test"] < 100


def test_time_split_refuses_an_empty_window():
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    with pytest.raises(ValueError, match="empty"):
        validate.time_split(dates, cutoff="2027-01-01")


def test_auc_matches_the_rank_statistic_by_hand():
    # Positives ranked 3rd and 4th of four: pairs (pos, neg) with pos > neg
    # are 4 of 4, so AUC is 1; swap one and it is 0.75.
    assert validate.auc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == 1.0
    assert validate.auc([0, 1, 0, 1], [0.1, 0.2, 0.8, 0.9]) == pytest.approx(0.75)


def test_leakage_screen_flags_the_outcome_under_another_name():
    rng = np.random.default_rng(0)
    y = rng.binomial(1, 0.3, 2000)
    X = pd.DataFrame({
        "cancel_reason_code": y * 3 + rng.normal(0, 0.05, 2000),   # the label, renamed
        "tenure": rng.normal(0, 1, 2000),                           # noise
        "plan": np.where(y == 1, "basic", "pro"),                   # non-numeric, skipped
    })
    s = validate.leakage_screen(X, y)
    assert s.loc[s["feature"] == "cancel_reason_code", "flagged"].item()
    assert not s.loc[s["feature"] == "tenure", "flagged"].item()
    assert s.attrs["skipped"] == ["plan"]


def test_baseline_lift_at_top_k_by_hand():
    # Two positives ranked first; base rate 0.2; top 20% precision 1.0 -> lift 5.
    y = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    score = np.linspace(1, 0, 10)
    r = validate.baseline_lift(y, score, k=0.2)
    assert r["n_targeted"] == 2
    assert r["precision_at_k"] == 1.0
    assert r["lift"] == pytest.approx(5.0)
    assert r["recall_at_k"] == 1.0
    assert r["auc"] == 1.0


def test_calibration_brier_by_hand_and_murphy_identity():
    y = [1, 0, 1, 0]
    s = [0.9, 0.1, 0.8, 0.2]
    r = validate.calibration(y, s, bins=10)
    # ((0.1)^2 + (0.1)^2 + (0.2)^2 + (0.2)^2) / 4
    assert r["brier"] == pytest.approx(0.025)
    assert r["brier_base"] == pytest.approx(0.25)
    assert r["brier_binned"] == pytest.approx(
        r["reliability"] - r["resolution"] + r["uncertainty"])


def test_calibration_of_the_base_rate_forecast_is_zero_skill():
    rng = np.random.default_rng(1)
    y = rng.binomial(1, 0.3, 5000)
    r = validate.calibration(y, np.full(5000, y.mean()), bins=10)
    assert r["skill"] == pytest.approx(0.0, abs=1e-9)
    assert r["ece"] == pytest.approx(0.0, abs=1e-9)
    assert r["resolution"] == 0.0


def test_qini_rewards_the_true_uplift_and_not_a_random_score():
    rng = np.random.default_rng(3)
    n = 20_000
    tau = rng.uniform(-0.05, 0.25, n)                 # true per-unit uplift
    arm = np.where(rng.random(n) < 0.5, "treatment", "control")
    p = np.clip(0.2 + (arm == "treatment") * tau, 0, 1)
    y = rng.binomial(1, p)
    good = validate.qini(y, tau, arm)
    bad = validate.qini(y, rng.random(n), arm)
    assert good["auqc"] > 0.01
    assert abs(bad["auqc"]) < 0.005
    assert good["uplift_at_k"] > good["ate"]
    assert good["ate"] == pytest.approx(tau.mean(), abs=0.02)


def test_qini_refuses_one_arm_or_three():
    with pytest.raises(ValueError, match="two arms"):
        validate.qini([1, 0, 1], [0.1, 0.2, 0.3], ["a", "a", "a"])
    with pytest.raises(ValueError, match="two arms"):
        validate.qini([1, 0, 1], [0.1, 0.2, 0.3], ["a", "b", "c"])


def test_mase_by_hand_non_seasonal_and_seasonal():
    # Naive in-sample MAE on [1,2,3,4] is 1; test MAE 0.5 -> MASE 0.5.
    r = validate.mase([1, 2, 3, 4], [5, 6], [5.5, 6.5], season=1)
    assert r["mase"] == pytest.approx(0.5)
    assert list(r["naive_forecast"]) == [4, 4]
    # Season 2 on [1,3,2,4]: |2-1|, |4-3| -> scale 1; naive test forecast repeats [2,4].
    r = validate.mase([1, 3, 2, 4], [3, 5, 4], [3, 5, 4], season=2)
    assert r["mase"] == 0.0
    assert list(r["naive_forecast"]) == [2, 4, 2]


def test_mase_verdict_at_or_above_one():
    r = validate.mase([1, 2, 3, 4], [5, 6], [3, 4], season=1)
    assert r["mase"] == pytest.approx(2.0)
    assert r["verdict"].startswith("NAIVE")
