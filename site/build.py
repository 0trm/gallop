"""Build the generated half of the site.

Hand-authored pages (index, map, intake) are left untouched; this script
emits everything derived from repo sources, one HTML file per document, with
real URLs, rendering fine from file://.

  site/skills/index.html          from the skills/ directory
  site/skills/<name>/index.html   from skills/<name>/SKILL.md (+ references)
  site/theory/index.html          from site/content/theory.md
  site/practice/index.html        from site/content/practice.md
  site/install/index.html         from site/content/install.md
  README.md skills table          into the marked block

The build fails when a skills/ directory has no SKILL.md, when the position
table here and the directories on disk disagree, or (with --check) when the
committed output differs from a fresh build, which is how CI catches drift.

Run:  python3 site/build.py [--check]
Needs: markdown-it-py (the one dependency beyond the stdlib).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SKILLS = ROOT / "skills"
CONTENT = SITE / "content"

# The one place the six positions live. Build fails if this and skills/ drift.
POSITIONS = {
    "routing-questions": ("Routing", "Whether this becomes work at all, and which skill it becomes"),
    "defining-metrics": ("The floor", "A metric turned into a computation, a source of truth, and a statement of how it will be gamed"),
    "designing-experiments": ("Causation", "The four choices that cannot be repaired after launch, with the MDE from the prior store"),
    "reading-experiments": ("Causation", "Whether the result is a result: SRM, exposure, the sequential bound, CUPED, shrinkage"),
    "choosing-causal-designs": ("Causation", "The method that matches how assignment happened, and the exit that says there is no comparison group"),
    "writing-readouts": ("The ceiling", "The decision rule first, the result last; the belief filed where the next question starts"),
}

md = MarkdownIt("commonmark", {"typographer": False}).enable("table")


# %% ---------------------------------------------------------------- helpers


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def render(markdown_text):
    return md.render(markdown_text)


def page(*, title, description, body, root, active=None, extra_style=""):
    """The shared chrome: nav band, foot band, theme switch."""
    nav_items = [
        ("map/", "The map"), ("intake/", "The intake"), ("skills/", "Skills"),
        ("theory/", "Theory"), ("practice/", "Practice"), ("install/", "Install"),
    ]
    links = []
    for href, label in nav_items:
        cur = ' aria-current="page"' if active == href else ""
        links.append(f'<a href="{root}{href}"{cur}>{label}</a>')
    nav = "\n  ".join(links)
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{root}assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=Courier+Prime:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/gallop.css">
<link rel="stylesheet" href="{root}assets/doc.css">
{f'<style>{extra_style}</style>' if extra_style else ''}
</head>
<body>

<div class="band cells nav docnav">
  <a class="wm" href="{root}./">gallop</a>
  {nav}
  <span class="sw">
    <span class="mode">
      <button type="button" data-set="light" aria-pressed="true">Light</button>
      <button type="button" data-set="dark" aria-pressed="false">Dark</button>
    </span>
  </span>
</div>

{body}

<div class="cells foot">
  <span>gallop</span>
  <span class="dim">pre-1.0</span>
  <a href="https://github.com/0trm/gallop">github.com/0trm/gallop &#8599;</a>
  <span class="dim">MIT License &middot; 2026</span>
</div>

<script>
  (function () {{
    var root = document.documentElement;
    var buttons = document.querySelectorAll(".mode button");
    function apply(theme) {{
      root.dataset.theme = theme;
      buttons.forEach(function (b) {{
        b.setAttribute("aria-pressed", String(b.dataset.set === theme));
      }});
    }}
    try {{
      var saved = localStorage.getItem("gallop-theme");
      if (saved === "dark" || saved === "light") apply(saved);
    }} catch (e) {{}}
    buttons.forEach(function (b) {{
      b.addEventListener("click", function () {{
        apply(b.dataset.set);
        try {{ localStorage.setItem("gallop-theme", b.dataset.set); }} catch (e) {{}}
      }});
    }});
  }})();
</script>

</body>
</html>
"""


def write(path, content, emitted):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    emitted.append(path)


# %% ------------------------------------------------------------ skill pages


def skill_dirs():
    names = {d.name for d in SKILLS.iterdir() if d.is_dir()}
    if names != set(POSITIONS):
        sys.exit(f"build: skills on disk {sorted(names)} != position table "
                 f"{sorted(POSITIONS)}; update site/build.py POSITIONS")
    dirs = [SKILLS / name for name in POSITIONS]  # routing order, not alphabetical
    for d in dirs:
        if not (d / "SKILL.md").exists():
            sys.exit(f"build: {d} has no SKILL.md")
    return dirs


def build_skill_page(d, emitted):
    meta, body = frontmatter((d / "SKILL.md").read_text())
    name = meta.get("name", d.name)
    position, decides = POSITIONS[name]
    sections = []
    for sub in ("reference", "templates"):
        for f in sorted((d / sub).glob("*.md")):
            inner = render(f.read_text())
            label = "template" if sub == "templates" else "reference"
            sections.append(
                f'<details class="refdoc" id="ref-{f.stem}"><summary><span class="lab">{label}'
                f'</span> {f.name}</summary>\n{inner}\n</details>')
    scripts = sorted((d / "scripts").glob("*.py")) if (d / "scripts").exists() else []
    script_note = ""
    if scripts:
        items = "".join(
            f'<li><a href="https://github.com/0trm/gallop/blob/main/skills/{name}/scripts/{s.name}">'
            f"scripts/{s.name}</a></li>" for s in scripts)
        script_note = f'<div class="scripts"><p class="lab">Ships with</p><ul>{items}</ul></div>'
    header = f"""<div class="band">
  <div class="secthead">
    <p class="lab">{position}</p>
    <span class="dim">skills/{name}</span>
  </div>
  <div class="cells skillhead" style="grid-template-columns:2fr 1fr">
    <div>
      <h1 class="d" style="font-size:34px">{name}</h1>
      <p class="skdesc">{meta.get("description", "")}</p>
    </div>
    <div>
      <a class="cmd" href="https://github.com/0trm/gallop/tree/main/skills/{name}">
        <span>the source, ready to copy</span><span class="cp">GitHub &#8599;</span></a>
      {script_note}
    </div>
  </div>
</div>"""
    doc = f'<div class="band"><div class="doc">\n{render(body)}\n' + "\n".join(sections) + "</div></div>"
    # Cross-references between the markdown files become anchors to the
    # collapsed sections inlined above.
    doc = re.sub(r'href="(?:reference/|templates/)?([\w-]+)\.md"', r'href="#ref-\1"', doc)
    html = page(title=f"{name} · gallop", description=decides, root="../../",
                active="skills/", body=header + "\n" + doc)
    write(SITE / "skills" / name / "index.html", html, emitted)


def build_skills_index(dirs, emitted):
    rows = []
    for d in dirs:
        meta, _ = frontmatter((d / "SKILL.md").read_text())
        name = meta["name"]
        position, decides = POSITIONS[name]
        rows.append(f"""    <a class="skrow" href="{name}/">
      <span class="pos dim">{position}</span>
      <h3>{name}</h3>
      <p>{decides}.</p>
    </a>""")
    body = f"""<div class="band">
  <div class="secthead">
    <p class="lab">Six skills</p>
    <span class="dim">one position on the map each</span>
  </div>
  <div class="cells six sixlinks">
{chr(10).join(rows)}
  </div>
</div>
<div class="band"><div class="doc">
<p>Each skill covers one position on <a href="../map/">the method map</a> and one
failure mode. Together they run one question end to end: it arrives at
<code>routing-questions</code>, stands on the floor <code>defining-metrics</code>
maintains, gets its method from <code>designing-experiments</code> or
<code>choosing-causal-designs</code>, is believed or not by
<code>reading-experiments</code>, and is filed by <code>writing-readouts</code>
so the next question starts smaller.</p>
</div></div>"""
    style = """
  .sixlinks .skrow{display:block;color:inherit}
  .sixlinks .skrow:hover{background:var(--wash);text-decoration:none}
  .sixlinks h3{font-family:var(--mono);font-size:14px;font-weight:700;margin:0}
  .sixlinks p{margin:8px 0 0;font-size:12.5px;line-height:1.5;color:var(--body)}
  .sixlinks .pos{display:block;font-family:var(--sans);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px}
  .six{grid-template-columns:repeat(3,1fr)}
  .six > *{border-bottom:1px solid var(--line)}
  .six > *:nth-child(3n){border-right:0}
  .six > *:nth-child(n+4){border-bottom:0}
  @media (max-width:1080px){.six{grid-template-columns:1fr}
    .six > *{border-right:0;border-bottom:1px solid var(--line)!important}}"""
    html = page(title="The six skills · gallop",
                description="Six skills, one position on the method map each.",
                root="../", active="skills/", body=body, extra_style=style)
    write(SITE / "skills" / "index.html", html, emitted)


# %% ---------------------------------------------------------- content pages


def build_content_page(stem, title, description, emitted):
    src = CONTENT / f"{stem}.md"
    if not src.exists():
        sys.exit(f"build: missing {src}")
    body = f'<div class="band"><div class="doc">\n{render(src.read_text())}\n</div></div>'
    html = page(title=f"{title} · gallop", description=description, root="../",
                active=f"{stem}/", body=body)
    write(SITE / stem / "index.html", html, emitted)


# %% ------------------------------------------------------------ README table


README_BEGIN = "<!-- skills-table:begin (generated by site/build.py; do not edit) -->"
README_END = "<!-- skills-table:end -->"


def readme_table(dirs):
    lines = ["| Skill | What it decides | Reach for it when |", "|---|---|---|"]
    for d in dirs:
        meta, _ = frontmatter((d / "SKILL.md").read_text())
        name = meta["name"]
        _, decides = POSITIONS[name]
        desc = meta.get("description", "")
        m = re.search(r"Use when ([^.]*)\.", desc)
        when = m.group(1) if m else ""
        lines.append(f"| [`{name}`](skills/{name}/SKILL.md) | {decides} | {when} |")
    return "\n".join(lines)


def build_readme(dirs):
    path = ROOT / "README.md"
    text = path.read_text()
    if README_BEGIN not in text or README_END not in text:
        sys.exit(f"build: README.md is missing the {README_BEGIN} ... {README_END} block")
    block = f"{README_BEGIN}\n{readme_table(dirs)}\n{README_END}"
    new = re.sub(re.escape(README_BEGIN) + r".*?" + re.escape(README_END), block, text, flags=re.DOTALL)
    return path, new


# %% -------------------------------------------------------------------- main


def main(argv=None):
    ap = argparse.ArgumentParser(description="build the generated half of the site")
    ap.add_argument("--check", action="store_true",
                    help="fail if committed output differs from a fresh build")
    a = ap.parse_args(argv)

    dirs = skill_dirs()
    emitted = []
    if a.check:
        before = {}
        targets = [SITE / "skills", SITE / "theory", SITE / "practice", SITE / "install"]
        for t in targets:
            for f in t.rglob("*.html") if t.exists() else []:
                before[f] = f.read_text()

    for d in dirs:
        build_skill_page(d, emitted)
    build_skills_index(dirs, emitted)
    build_content_page("theory", "The theory layer",
                       "The prior store and the knowledge repo: the only object that compounds.", emitted)
    build_content_page("practice", "The practice",
                       "A day, a week, and a quarter in the embedded product data science seat.", emitted)
    build_content_page("install", "Install",
                       "Claude Code plugin, manual copy, or pip.", emitted)
    readme_path, readme_new = build_readme(dirs)

    if a.check:
        after = {f: f.read_text() for f in emitted}
        stale = [str(f.relative_to(ROOT)) for f, c in after.items() if before.get(f) != c]
        extra = [str(f.relative_to(ROOT)) for f in before if f not in after]
        if readme_path.read_text() != readme_new:
            stale.append("README.md (skills table)")
        if stale or extra:
            sys.exit("build --check: stale or orphaned output, run python3 site/build.py "
                     "and commit:\n  " + "\n  ".join(stale + extra))
        print(f"check OK: {len(emitted)} generated pages current, README table current")
    else:
        readme_path.write_text(readme_new)
        print(f"built {len(emitted)} pages, refreshed README table")


if __name__ == "__main__":
    main()
