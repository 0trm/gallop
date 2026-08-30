#!/usr/bin/env python3
"""Keep assets with unclear provenance out of the repository, and out of its history.

Git history is permanent: deleting a font binary in a later commit does not remove
it. So this runs in CI and on every Pages build rather than being a rule someone
remembers. What it enforces is written up in NOTICE.
"""
# %%
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Font binaries: the design references Chicago and Monaco, neither of which this
# repo may redistribute. @font-face resolves them with local() only.
FONT_SUFFIXES = {".woff", ".woff2", ".ttf", ".otf", ".eot", ".ttc", ".dfont"}

# Inlined fonts are the same problem wearing a data URI. The source documents
# carried ~18KB of base64 each before they were sanitised for this repo.
INLINE_FONT = re.compile(r"data:(?:application/)?font[-/]|data:application/x-font")

TEXT_SUFFIXES = {".html", ".css", ".md", ".py", ".json", ".yml", ".yaml", ".svg", ".txt", ".tmpl", ".sql"}
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache", ".ruff_cache"}


def walk():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def main() -> int:
    problems = []

    for p in walk():
        rel = p.relative_to(ROOT)

        if p.suffix.lower() in FONT_SUFFIXES:
            problems.append(f"{rel}: font binary. See NOTICE: fonts resolve via local() only.")
            continue

        if p.suffix.lower() not in TEXT_SUFFIXES:
            continue

        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        # check_assets.py itself defines these patterns, so it is not its own subject.
        if rel.as_posix() == "scripts/check_assets.py":
            continue

        if INLINE_FONT.search(text):
            problems.append(f"{rel}: inlined font data URI. Strip it; keep local() and the Google Fonts link.")

        for m in re.finditer(r"[\w./-]*(?:fonts?/[\w-]+\.(?:woff2?|ttf|otf))", text):
            problems.append(f"{rel}: references a font file that does not ship ({m.group(0)}).")

    for line in problems:
        print(f"FAIL  {line}", file=sys.stderr)
    if problems:
        print(f"\n{len(problems)} asset problem(s). NOTICE explains the rule.", file=sys.stderr)
        return 1

    print("OK  no font binaries, no inlined fonts, no dangling font references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
