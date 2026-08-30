#!/usr/bin/env python3
"""Enforce the published Agent Skills limits, so they are checked rather than remembered.

https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
Exits non-zero on any violation, so CI fails.
"""
# %%
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

MAX_BODY_LINES = 500        # published guidance: keep the SKILL.md body under 500 lines
MAX_NAME_CHARS = 64
MAX_DESC_CHARS = 1024
NAME_RE = re.compile(r"^[a-z0-9-]+$")
RESERVED = ("anthropic", "claude")


def split_frontmatter(text: str):
    """Return (frontmatter, body). Frontmatter is None when the file has none."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 5 :]


def scalar(fm: str, key: str):
    """Read one top-level scalar. Skills use flat frontmatter, so this is enough."""
    m = re.search(rf"^{key}:[ \t]*(.+?)[ \t]*$", fm, re.M)
    return m.group(1).strip().strip("\"'") if m else None


def check(skill_md: Path) -> list[str]:
    rel = skill_md.relative_to(ROOT)
    errs = []
    text = skill_md.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)

    if fm is None:
        return [f"{rel}: no YAML frontmatter"]

    name = scalar(fm, "name")
    if not name:
        errs.append(f"{rel}: frontmatter has no 'name'")
    else:
        if len(name) > MAX_NAME_CHARS:
            errs.append(f"{rel}: name is {len(name)} chars, limit {MAX_NAME_CHARS}")
        if not NAME_RE.match(name):
            errs.append(f"{rel}: name '{name}' must be lowercase letters, numbers, hyphens")
        if any(w in name.lower() for w in RESERVED):
            errs.append(f"{rel}: name '{name}' contains a reserved word")
        if name != skill_md.parent.name:
            errs.append(f"{rel}: name '{name}' != directory '{skill_md.parent.name}'")

    desc = scalar(fm, "description")
    if not desc:
        errs.append(f"{rel}: frontmatter has no 'description'")
    elif len(desc) > MAX_DESC_CHARS:
        errs.append(f"{rel}: description is {len(desc)} chars, limit {MAX_DESC_CHARS}")

    n_lines = len(body.strip().splitlines())
    if n_lines > MAX_BODY_LINES:
        errs.append(f"{rel}: body is {n_lines} lines, limit {MAX_BODY_LINES}")

    # References must sit exactly one level below SKILL.md: Claude partially reads
    # files reached through a chain, so a nested reference loses content.
    for link in re.findall(r"\]\(([^)]+)\)", body):
        if link.startswith(("http://", "https://", "#")):
            continue
        if "\\" in link:
            errs.append(f"{rel}: '{link}' uses a backslash; paths must be forward slashes")
        if link.count("/") > 1:
            errs.append(f"{rel}: '{link}' is nested deeper than one level")
    return errs


def main() -> int:
    skills = sorted(SKILLS.glob("*/SKILL.md"))
    if not skills:
        print("no skills found", file=sys.stderr)
        return 1

    errs = [e for s in skills for e in check(s)]
    for e in errs:
        print(f"FAIL  {e}", file=sys.stderr)
    if errs:
        print(f"\n{len(errs)} problem(s) across {len(skills)} skills", file=sys.stderr)
        return 1
    print(f"OK  {len(skills)} skills pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
