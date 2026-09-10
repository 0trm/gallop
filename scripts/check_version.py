"""Fail unless pyproject.toml, plugin.json, marketplace.json and gallop.__version__
all carry the version given as the only argument (the release tag, v-prefix stripped).
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def find(pattern, path, flags=0):
    """The captured version, or exit naming the file whose version line moved."""
    m = re.search(pattern, (ROOT / path).read_text(), flags)
    if not m:
        sys.exit(f"{path}: no version line matching {pattern!r}")
    return m.group(1)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: check_version.py <tag>   (a leading v is stripped)")
    tag = sys.argv[1].removeprefix("v")
    versions = {
        "pyproject.toml": find(r'^version = "([^"]+)"', "pyproject.toml", re.MULTILINE),
        ".claude-plugin/plugin.json": json.loads(
            (ROOT / ".claude-plugin/plugin.json").read_text())["version"],
        ".claude-plugin/marketplace.json": json.loads(
            (ROOT / ".claude-plugin/marketplace.json").read_text())["plugins"][0]["version"],
        "src/gallop/__init__.py": find(r'__version__ = "([^"]+)"', "src/gallop/__init__.py"),
    }
    bad = {k: v for k, v in versions.items() if v != tag}
    if bad:
        sys.exit(f"tag {tag} does not match: " + ", ".join(f"{k}={v}" for k, v in bad.items()))
    print(f"version {tag} consistent across {len(versions)} files")


if __name__ == "__main__":
    main()
