"""Fail unless pyproject.toml, plugin.json, marketplace.json and gallop.__version__
all carry the same version.

  check_version.py            they must agree with each other; pyproject wins
  check_version.py <tag>      they must all equal <tag>, a leading v stripped

CI runs the first on every push, so a bump that misses a file fails there.
release.yml runs the second, so a tag that names a version nobody declared
fails before anything is published.
"""

# %%
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
    if len(sys.argv) > 2:
        sys.exit("usage: check_version.py [tag]")
    versions = {
        "pyproject.toml": find(r'^version = "([^"]+)"', "pyproject.toml", re.MULTILINE),
        ".claude-plugin/plugin.json": json.loads(
            (ROOT / ".claude-plugin/plugin.json").read_text())["version"],
        ".claude-plugin/marketplace.json": json.loads(
            (ROOT / ".claude-plugin/marketplace.json").read_text())["plugins"][0]["version"],
        "src/gallop/__init__.py": find(r'__version__ = "([^"]+)"', "src/gallop/__init__.py"),
    }
    if len(sys.argv) == 2:
        tag, label = sys.argv[1].removeprefix("v"), f"tag {sys.argv[1]}"
    else:
        tag, label = versions["pyproject.toml"], "pyproject.toml"
    bad = {k: v for k, v in versions.items() if v != tag}
    if bad:
        sys.exit(f"{label} says {tag}, but: "
                 + ", ".join(f"{k}={v}" for k, v in bad.items()))
    print(f"version {tag} consistent across {len(versions)} files")


if __name__ == "__main__":
    main()
