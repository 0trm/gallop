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
