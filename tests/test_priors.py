import json
from pathlib import Path

import pytest

from gallop import priors

GOOD = {
    "id": "2026-08-checkout-cta", "metric": "activation_rate", "date": "2026-08-15",
    "design": "experiment", "effect": 0.0021, "unit": "pp", "se": 0.0009,
    "n_per_arm": 41000, "decision": "ship",
}


def test_roundtrip(tmp_path):
    store = tmp_path / "priors.jsonl"
    priors.append(store, GOOD)
    df = priors.read(store)
    assert len(df) == 1
    assert df.loc[0, "effect"] == pytest.approx(0.0021)
    # The file itself is one JSON object per line, diffable.
    assert json.loads(store.read_text().strip()) == GOOD


@pytest.mark.parametrize("mutation", [
    {"effect": None}, {"unit": "percent"}, {"design": "vibes"},
    {"n_per_arm": 41000.5}, {"date": "Aug 15"}, {"extra_field": 1},
])
def test_rejects_malformed_records(tmp_path, mutation):
    rec = {**GOOD, **mutation}
    rec = {k: v for k, v in rec.items() if v is not None}
    if "effect" in mutation:
        rec.pop("effect", None)  # missing required field
    with pytest.raises(ValueError):
        priors.append(tmp_path / "p.jsonl", rec)


def test_duplicate_id_refused_and_supersedes_drops_the_old_record(tmp_path):
    store = tmp_path / "priors.jsonl"
    priors.append(store, GOOD)
    with pytest.raises(ValueError, match="already"):
        priors.append(store, GOOD)
    correction = {**GOOD, "id": "2026-09-checkout-cta-corrected", "date": "2026-09-01",
                  "effect": 0.0009, "supersedes": GOOD["id"]}
    priors.append(store, correction)
    df = priors.read(store)
    assert df["id"].tolist() == ["2026-09-checkout-cta-corrected"]
    # Append-only on disk: both lines are still there.
    assert len(store.read_text().strip().splitlines()) == 2


def test_window_keeps_most_recent_per_metric(tmp_path):
    store = tmp_path / "priors.jsonl"
    for i in range(6):
        priors.append(store, {**GOOD, "id": f"r{i}", "date": f"2026-0{i + 1}-01"})
    df = priors.read(store, window=3)
    assert df["id"].tolist() == ["r3", "r4", "r5"]


def test_malformed_line_fails_with_line_number(tmp_path):
    store = tmp_path / "priors.jsonl"
    priors.append(store, GOOD)
    store.open("a").write(json.dumps({**GOOD, "id": "bad", "unit": "percent"}) + "\n")
    with pytest.raises(ValueError, match=":2:"):
        priors.read(store)


def test_registry_roundtrip_and_status_filter(tmp_path):
    reg = tmp_path / "registry.jsonl"
    entry = {
        "name": "activation_rate", "definition": "activated users / signups, 7-day window",
        "source": "warehouse.marts.activation", "unit_of_analysis": "user",
        "direction": "increase_good", "role": "primary",
        "gaming": "widen the definition of activated", "status": "trusted",
    }
    reg.write_text(json.dumps(entry) + "\n" + json.dumps(
        {**entry, "name": "clicks", "status": "provisional"}) + "\n")
    assert len(priors.read_registry(reg)) == 2
    assert priors.read_registry(reg, status="trusted")["name"].tolist() == ["activation_rate"]


def test_published_contract_matches_the_packaged_schema():
    # templates/ at the repo root is the published contract; the packaged copy
    # under src/gallop/templates is what validation reads. They must be equal.
    root = Path(__file__).resolve().parents[1] / "templates"
    pkg = Path(priors.__file__).parent / "templates"
    for name in ("prior-store.schema.json", "metric-registry.schema.json"):
        assert json.loads((root / name).read_text()) == json.loads((pkg / name).read_text()), (
            f"{name} differs between templates/ and src/gallop/templates/")
