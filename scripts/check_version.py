"""Fail unless pyproject.toml, plugin.json, marketplace.json and gallop.__version__
all carry the version given as the only argument (the release tag, v-prefix stripped).
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    tag = sys.argv[1]
    versions = {
        "pyproject.toml": re.search(
            r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.MULTILINE).group(1),
        ".claude-plugin/plugin.json": json.loads(
            (ROOT / ".claude-plugin/plugin.json").read_text())["version"],
        ".claude-plugin/marketplace.json": json.loads(
            (ROOT / ".claude-plugin/marketplace.json").read_text())["plugins"][0]["version"],
        "src/gallop/__init__.py": re.search(
            r'__version__ = "([^"]+)"', (ROOT / "src/gallop/__init__.py").read_text()).group(1),
    }
    bad = {k: v for k, v in versions.items() if v != tag}
    if bad:
        sys.exit(f"tag {tag} does not match: " + ", ".join(f"{k}={v}" for k, v in bad.items()))
    print(f"version {tag} consistent across {len(versions)} files")


if __name__ == "__main__":
    main()
