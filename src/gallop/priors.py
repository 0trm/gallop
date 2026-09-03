"""The prior store and the metric registry on disk.

Both are append-friendly JSONL, one JSON object per line, validated on write
against the schemas in gallop/templates/. JSONL because the store must be
reviewable in a pull request; a store nobody can diff goes stale, which is the
failure mode the theory layer exists to prevent.

The store is a log, windowed on read. A correction is a new record carrying
`supersedes`, never an edit. `expires_on` names the event that would
invalidate the entry rather than a date somebody has to remember.

Validation is done here in about thirty lines (required keys, types, enums,
no unknown keys) rather than by the jsonschema package, so the runtime
dependencies stay at numpy, pandas, scipy. The schema files remain the
published contract for anything else that writes to the store.

Run:  python -m gallop.priors read --store priors.jsonl --metric activation_rate
"""

from __future__ import annotations

import argparse
import json
import re
from importlib import resources
from pathlib import Path

import pandas as pd

# %% -------------------------------------------------------------- validation

_TYPES = {"string": str, "number": (int, float), "integer": int, "object": dict}


def _schema(name):
    with resources.files("gallop.templates").joinpath(name).open() as f:
        return json.load(f)


def validate(record, schema_name="prior-store.schema.json"):
    """Check a dict against one of the packaged schemas. Raises ValueError."""
    sch = _schema(schema_name)
    props = sch["properties"]
    errors = []
    for key in sch["required"]:
        if key not in record:
            errors.append(f"missing required field {key!r}")
    for key, value in record.items():
        if key not in props:
            errors.append(f"unknown field {key!r}")
            continue
        spec = props[key]
        expected = _TYPES[spec["type"]]
        if not isinstance(value, expected) or isinstance(value, bool):
            errors.append(f"{key!r} must be {spec['type']}, got {type(value).__name__}")
            continue
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"{key!r} must be one of {spec['enum']}, got {value!r}")
        if "pattern" in spec and not re.fullmatch(spec["pattern"], value):
            errors.append(f"{key!r} must match {spec['pattern']}, got {value!r}")
    if errors:
        raise ValueError(f"invalid {sch['title']}: " + "; ".join(errors))
    return record


# %% ------------------------------------------------------------- prior store


def append(path, record):
    """Validate a record and append it to the store. Returns the record."""
    validate(record, "prior-store.schema.json")
    p = Path(path)
    existing = {r["id"] for _, r in _iter_records(p)} if p.exists() else set()
    if record["id"] in existing:
        raise ValueError(f"id {record['id']!r} already in {path}; corrections use supersedes")
    with p.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def _iter_records(p):
    with Path(p).open() as f:
        for i, line in enumerate(f, 1):
            if line.strip():
                yield i, json.loads(line)


def read(path, metric=None, window=100):
    """The store as a DataFrame: superseded records dropped, windowed on read.

    `window` keeps the most recent records per metric, by date then file
    order. Every record is validated; a malformed line fails loudly with its
    line number rather than flowing into a shrinkage estimate.
    """
    rows = []
    for i, rec in _iter_records(path):
        try:
            validate(rec, "prior-store.schema.json")
        except ValueError as e:
            raise ValueError(f"{path}:{i}: {e}") from None
        rows.append(rec)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    superseded = set(df["supersedes"].dropna()) if "supersedes" in df.columns else set()
    df = df[~df["id"].isin(superseded)]
    if metric is not None:
        df = df[df["metric"] == metric]
    df = df.assign(_order=range(len(df))).sort_values(["metric", "date", "_order"])
    df = df.groupby("metric", group_keys=False).tail(window).drop(columns="_order")
    return df.reset_index(drop=True)


# %% ---------------------------------------------------------------- registry


def read_registry(path, status=None):
    """The metric registry as a DataFrame, optionally filtered by status."""
    rows = []
    for i, rec in _iter_records(path):
        try:
            validate(rec, "metric-registry.schema.json")
        except ValueError as e:
            raise ValueError(f"{path}:{i}: {e}") from None
        rows.append(rec)
    df = pd.DataFrame(rows)
    if status is not None and not df.empty:
        df = df[df["status"] == status].reset_index(drop=True)
    return df


# %% --------------------------------------------------------------------- cli


def main(argv=None):
    p = argparse.ArgumentParser(prog="gallop.priors", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("append", help="validate and append one record")
    sp.add_argument("--store", required=True)
    sp.add_argument("--json", required=True, help="the record as a JSON object")
    sp = sub.add_parser("read", help="print the windowed store")
    sp.add_argument("--store", required=True)
    sp.add_argument("--metric")
    sp.add_argument("--window", type=int, default=100)
    sp = sub.add_parser("registry", help="print the metric registry")
    sp.add_argument("--registry", required=True)
    sp.add_argument("--status")

    a = p.parse_args(argv)
    if a.cmd == "append":
        rec = append(a.store, json.loads(a.json))
        print(f"appended {rec['id']} to {a.store}")
    elif a.cmd == "read":
        print(read(a.store, metric=a.metric, window=a.window).to_string(index=False))
    else:
        print(read_registry(a.registry, status=a.status).to_string(index=False))


if __name__ == "__main__":
    main()
