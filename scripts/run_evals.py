"""Validate and run the skill evals in evals/.

Two modes:

  python3 scripts/run_evals.py
      Structure check only, no API calls. This is what CI runs: every eval
      names an existing skill, carries a query and an expected_behavior, and
      any bundled files are a dict of relative path -> content.

  python3 scripts/run_evals.py --run [--without-skill] [--model MODEL] [pattern]
      Execute each eval with the claude CLI. Builds a temp workspace per
      eval (bundled files written in, the skill copied into .claude/skills
      unless --without-skill), runs the query with `claude -p`, and prints
      the transcript beside the expected behavior for grading. Run with and
      without the skill: an eval earns its keep only if behavior visibly
      degrades without it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
SKILLS = ROOT / "skills"


def check(path):
    errors = []
    try:
        e = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]
    for key in ("skills", "query", "expected_behavior"):
        if not e.get(key):
            errors.append(f"missing or empty {key!r}")
    for s in e.get("skills", []):
        if not (SKILLS / s / "SKILL.md").exists():
            errors.append(f"names unknown skill {s!r}")
    files = e.get("files", {})
    if not isinstance(files, dict) or any(
            not isinstance(k, str) or not isinstance(v, str) or Path(k).is_absolute()
            for k, v in files.items()):
        errors.append("files must map relative paths to string contents")
    return errors


def run_one(path, without_skill=False, model=None):
    e = json.loads(path.read_text())
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        for rel, content in e.get("files", {}).items():
            dest = ws / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
        if not without_skill:
            for s in e["skills"]:
                shutil.copytree(SKILLS / s, ws / ".claude" / "skills" / s)
        cmd = ["claude", "-p", e["query"], "--permission-mode", "bypassPermissions"]
        if model:
            cmd += ["--model", model]
        out = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=600,
                             check=False)
    tag = "WITHOUT skill" if without_skill else "with skill"
    print(f"\n{'=' * 74}\n{path.name}  ({tag})\n{'=' * 74}")
    print(f"--- response ---\n{out.stdout.strip()}")
    if out.returncode != 0:
        print(f"--- stderr (exit {out.returncode}) ---\n{out.stderr.strip()}")
    print(f"--- expected ---\n{e['expected_behavior']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pattern", nargs="?", default="*.json", help="eval filename glob")
    ap.add_argument("--run", action="store_true", help="execute with the claude CLI")
    ap.add_argument("--without-skill", action="store_true", help="ablation: skill not loaded")
    ap.add_argument("--model", help="model override for --run")
    a = ap.parse_args(argv)

    paths = sorted(EVALS.glob(a.pattern))
    if not paths:
        print(f"no evals match {a.pattern!r} in {EVALS}")
        return 1
    failed = 0
    for p in paths:
        errors = check(p)
        if errors:
            failed += 1
            print(f"FAIL {p.name}: " + "; ".join(errors))
    print(f"{len(paths) - failed}/{len(paths)} evals structurally valid")
    if failed:
        return 1
    if a.run:
        if shutil.which("claude") is None:
            print("--run needs the claude CLI on PATH")
            return 1
        for p in paths:
            run_one(p, without_skill=a.without_skill, model=a.model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
