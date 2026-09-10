import numpy as np
import pandas as pd
import pytest

from gallop import explore, power


def seg(rows):
    return pd.DataFrame(rows, columns=["segment", "n", "y"])


def test_mix_rate_is_exact_and_names_simpsons_case():
    # Every segment improves (10->12%, 5->6%) while the total falls (9.0->8.4%),
    # because traffic shifted toward the weaker segment. By hand:
    # rate effect +0.016, mix effect -0.022, change -0.006.
    before = seg([("A", 800, 80), ("B", 200, 10)])
    after = seg([("A", 400, 48), ("B", 600, 36)])
    r = explore.mix_rate(before, after)
    assert r["change"] == pytest.approx(-0.006)
    assert r["rate_effect"] == pytest.approx(0.016)
    assert r["mix_effect"] == pytest.approx(-0.022)
    assert r["rate_effect"] + r["mix_effect"] == pytest.approx(r["change"])
    assert r["simpson"] is True
    assert r["n_cuts"] == 2
    # Centred mix contributions: B grew and converts below the whole, so it
    # drags; A shrank and converts above the whole, so its loss drags too.
    t = r["table"].set_index("segment")
    assert t.loc["B", "mix_contribution"] < 0 and t.loc["A", "mix_contribution"] < 0
    assert t["mix_contribution"].sum() == pytest.approx(-0.022)


def test_mix_rate_handles_a_segment_that_appears_and_reports_flags():
    before = seg([("A", 1000, 100)])
    after = seg([("A", 1000, 100), ("B", 1000, 10)])
    r = explore.mix_rate(before, after)
    assert r["simpson"] is False
    assert r["change"] == pytest.approx(0.055 - 0.10)
    assert set(r["table"]["segment"]) == {"A", "B"}
    assert {"p", "p_adj", "flagged"} <= set(r["table"].columns)


def test_funnel_steps_shares_by_hand():
    # Step 1 fell from 50% to 40%, step 2 stayed at 50%: step 1 carries all of it.
    before = pd.DataFrame({"step": ["view", "start", "complete"], "n": [1000, 500, 250]})
    after = pd.DataFrame({"step": ["view", "start", "complete"], "n": [1000, 400, 200]})
    r = explore.funnel_steps(before, after)
    assert r["overall_before"] == pytest.approx(0.25)
    assert r["overall_after"] == pytest.approx(0.20)
    assert r["largest_step"] == "start"
    shares = dict(zip(r["table"]["step"], r["table"]["share"]))
    assert shares["start"] == pytest.approx(1.0)
    assert shares["complete"] == pytest.approx(0.0, abs=1e-12)


def test_benjamini_hochberg_known_values():
    # Textbook: p = [0.01, 0.04, 0.03, 0.20] -> adjusted [0.04, 0.0533, 0.0533, 0.20]
    adj = explore.benjamini_hochberg([0.01, 0.04, 0.03, 0.20])
    assert adj == pytest.approx([0.04, 0.04 * 4 / 3, 0.04 * 4 / 3, 0.20])


def test_scan_segments_counts_every_cut_and_flags_the_planted_one():
    rng = np.random.default_rng(4)
    n = 60_000
    df = pd.DataFrame({
        "channel": rng.choice(list("abcdef"), n),
        "country": rng.choice(["ES", "IT", "PT", "FR"], n),
    })
    p = np.where(df["channel"] == "a", 0.02, 0.05)      # one weak channel
    df["y"] = rng.binomial(1, p)
    r = explore.scan_segments(df, y="y", by=["channel", "country"])
    assert r["n_cuts"] == 10
    t = r["table"].set_index(["dimension", "level"])
    assert t.loc[("channel", "a"), "flagged"]
    assert not t.loc[[("country", c) for c in ["ES", "IT", "PT", "FR"]], "flagged"].any()
    assert (t["p_adj"] >= t["p"] - 1e-12).all()
    assert r["table"].iloc[0].name == 0 and r["table"].iloc[0]["level"] == "a"


def test_size_opportunity_three_numbers_and_verdict():
    store = pd.DataFrame({
        "metric": ["m"] * 3, "unit": ["pp"] * 3, "effect": [0.5, -0.2, 0.8],
        "se": [0.1] * 3,
    })
    r = explore.size_opportunity(0.02, 100_000, baseline_rate=0.12, units_per_day=8000,
                                 store=store, metric="m", unit="pp")
    assert r["ceiling_units"] == pytest.approx(2000)
    assert r["anchored_mean"] == pytest.approx(np.mean([0.005, -0.002, 0.008]))
    assert r["anchored_max"] == pytest.approx(0.008)
    assert r["mde"] == pytest.approx(power.mde(8000 * 42 / 2, baseline_rate=0.12))
    assert r["measurable"] is True and r["fundable"] is True
    assert r["verdict"].startswith("WORTH A TEST")


def test_size_opportunity_too_small_and_unanchored():
    r = explore.size_opportunity(0.0005, 10_000, baseline_rate=0.12, units_per_day=500)
    assert r["measurable"] is False
    assert r["verdict"].startswith("TOO SMALL")
    r = explore.size_opportunity(0.02, 10_000, baseline_rate=0.12, units_per_day=8000)
    assert r["fundable"] is None and "unanchored" in r["verdict"]


def test_a_segment_present_in_only_one_period_is_flagged_not_hidden():
    # Nothing moved: the same segment at 100/1000, plus a new one at 100/1000.
    # The filler rate of 0 books the entry as a 2.5pp rate move, so the row
    # carries the flag that says the contribution is entry, not a rate change.
    before = [{"segment": "old", "n": 1000, "y": 100}]
    after = [{"segment": "old", "n": 1000, "y": 100},
             {"segment": "new", "n": 1000, "y": 100}]
    r = explore.mix_rate(before, after)
    assert r["change"] == pytest.approx(0.0)
    assert r["n_entering_exiting"] == 1
    row = r["table"].set_index("segment").loc["new"]
    assert bool(row["entered"]) and not bool(row["exited"])
    assert row["rate_contribution"] == pytest.approx(0.025)
    assert not bool(r["table"].set_index("segment").loc["old", "entered"])


def test_two_proportion_p_matches_the_pooled_z_test():
    # Reference: the pooled two-proportion z-test. 40/200 against 60/200 gives
    # p_pool = 0.25, se = sqrt(0.25 * 0.75 * (1/200 + 1/200)) and z = -0.10/se.
    from scipy import stats as st
    got = explore.two_proportion_p([40], [200], [60], [200])
    p_pool = 100 / 400
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / 200 + 1 / 200))
    expected = 2 * st.norm.sf(abs((0.30 - 0.20) / se))
    assert got[0] == pytest.approx(expected, rel=1e-12)
    # identical proportions cannot be distinguished
    assert explore.two_proportion_p([50], [200], [50], [200])[0] == pytest.approx(1.0)


def test_two_proportion_p_returns_one_for_an_empty_denominator():
    assert explore.two_proportion_p([0], [0], [10], [100])[0] == pytest.approx(1.0)
