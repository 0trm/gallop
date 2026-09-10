import pytest

from gallop import trust


def test_srm_reproduces_the_published_kohavi_example():
    # Kohavi, Tang & Xu, "Trustworthy Online Controlled Experiments":
    # 821,588 control vs 815,482 treatment at an intended 50/50 split is an
    # SRM with p about 1.8e-6.
    r = trust.srm({"control": 821_588, "treatment": 815_482})
    assert r["srm"] is True
    assert r["p"] == pytest.approx(1.8e-6, rel=0.05)


def test_srm_passes_a_clean_split_and_supports_unequal_shares():
    assert trust.srm({"c": 50_120, "t": 49_880})["srm"] is False
    r = trust.srm({"c": 90_000, "t": 10_060}, expected=[0.9, 0.1])
    assert r["srm"] is False


def test_srm_catches_small_imbalance_at_scale():
    # 0.4% imbalance at a million units looks like nothing on a dashboard.
    assert trust.srm({"c": 502_000, "t": 498_000})["srm"] is True


def test_exposure_dilution_and_differential():
    ok = trust.exposure_check({"c": 10_000, "t": 10_000}, {"c": 9_700, "t": 9_650})
    assert not ok["diluted"] and not ok["differential"]

    diluted = trust.exposure_check({"c": 10_000, "t": 10_000}, {"c": 6_000, "t": 6_050})
    assert diluted["diluted"] and not diluted["differential"]
    assert diluted["dilution_factor"] == pytest.approx(10_000 * 2 / 12_050, rel=1e-6)

    diff = trust.exposure_check({"c": 100_000, "t": 100_000}, {"c": 97_000, "t": 90_000})
    assert diff["differential"]
    assert "DIFFERENTIAL" in diff["verdict"]


def test_exposure_rejects_impossible_counts():
    with pytest.raises(ValueError):
        trust.exposure_check({"c": 100, "t": 100}, {"c": 101, "t": 90})


def test_srm_refuses_degenerate_counts_instead_of_reporting_pass():
    # A zero expected cell makes the chi-square nan; nan < alpha is False, so
    # before the guard these returned verdict "pass" on unusable input.
    with pytest.raises(ValueError):
        trust.srm({"a": 0, "b": 0})
    with pytest.raises(ValueError):
        trust.srm({"a": 100, "b": 300}, expected=[1.0, 0.0])
    with pytest.raises(ValueError):
        trust.srm({"a": -100, "b": 300})


def test_dilution_verdict_states_the_attenuation_not_the_exposure_rate():
    # 90% exposed leaves the ITT about 10% short, not 90%.
    r = trust.exposure_check({"a": 100_000, "b": 100_000}, {"a": 90_000, "b": 90_000})
    assert "attenuated ~10%" in r["verdict"]
    assert r["dilution_factor"] == pytest.approx(1 / 0.9)


def test_report_renders_both_checks_and_names_the_causes_on_a_failure():
    clean = trust.report(trust.srm({"control": 10_000, "treatment": 10_000}))
    assert "chi2 0.00" in clean and "pass" in clean
    assert "work the causes" not in clean

    failed = trust.report(trust.srm({"control": 10_000, "treatment": 9_400}))
    assert "STOP, DO NOT ANALYSE" in failed
    assert "work the causes in this order" in failed
    assert len([ln for ln in failed.splitlines() if ln.strip()[:1].isdigit()]) == len(trust.SRM_CAUSES)

    exposure = trust.report(trust.exposure_check({"a": 100_000, "b": 100_000},
                                                 {"a": 90_000, "b": 90_000}))
    assert "attenuated ~10%" in exposure
    assert "1.11" in exposure or "1.111" in exposure
