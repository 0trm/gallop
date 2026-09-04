"""Build the generated half of the site.

Hand-authored pages (index, map, intake) are left untouched; this script
emits everything derived from repo sources, one HTML file per document, with
real URLs, rendering fine from file://.

  site/skills/index.html          from the skills/ directory
  site/skills/<name>/index.html   from skills/<name>/SKILL.md (+ references)
  site/theory/index.html          from site/content/theory.md
  site/install/index.html         from site/content/install.md
  README.md skills table          into the marked block

Figures from site/figures/ (drawn by site/figures.py) are inlined after the
heading named in FIGURES, so they take the page's ink and theme with it.

The build fails when a skills/ directory has no SKILL.md, when the position
table here and the directories on disk disagree, or (with --check) when the
committed output differs from a fresh build, which is how CI catches drift.

Run:  python3 site/build.py [--check]
Needs: markdown-it-py (the one dependency beyond the stdlib).
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SKILLS = ROOT / "skills"
CONTENT = SITE / "content"
FIGDIR = SITE / "figures"

# GoatCounter on every page: cookieless, so no consent banner, and count.js
# skips localhost and file://, so local builds stay out of the numbers.
ANALYTICS = (
    '<script data-goatcounter="https://gallop.goatcounter.com/count"'
    ' async src="https://gc.zgo.at/count.js"></script>'
)

# (page, h2 text prefix) -> (figure file, caption). Inlined right after that h2.
FIGURES = {
    ("skills/reading-experiments", "3 · The effect"): ("peeking.svg",
        "Read a fixed-horizon test every day and the false-positive rate is not 5%. Simulated under a "
        "true null at alpha 0.05, 100,000 runs: about 14% at five looks, 28% at thirty."),
    ("skills/reading-experiments", "5 · Shrink toward"): ("shrinkage.svg",
        "The quickstart's own numbers. The prior is tight and the readout is noisy, so the weight on "
        "the data is 0.08 and the planning number is a third of the reported one."),
    ("skills/reading-experiments", "p:Apply <strong>CUPED</strong>"): ("cuped.svg",
        "CUPED's whole effect in one curve: the standard error falls by sqrt(1 minus rho squared), "
        "so a pre-period covariate at rho 0.7 buys the same precision as doubling the traffic."),
    ("theory", "The prior store"): ("prior-store.svg",
        "Illustrative: a hundred readouts on one metric. The mean is the honest prior; the MDE somebody "
        "wished for sits to the right of every effect the metric has ever produced."),
}

# The one place the skills' positions live. Build fails if this and skills/ drift.
POSITIONS = {
    "routing-questions": ("Routing", "Whether this becomes work at all, and which skill it becomes"),
    "defining-metrics": ("The floor", "A metric turned into a computation, a source of truth, and a statement of how it will be gamed"),
    "designing-experiments": ("Causation", "The four choices that cannot be repaired after launch, with the MDE from the prior store"),
    "reading-experiments": ("Causation", "Whether the result is a result: SRM, exposure, the sequential bound, CUPED, shrinkage"),
    "choosing-causal-designs": ("Causation", "The method that matches how assignment happened, and the exit that says there is no comparison group"),
    "automating-decisions": ("Prediction", "Whether a repeated decision belongs to a model, validated out of time, and the holdout that measures its impact"),
    "writing-readouts": ("The ceiling", "The decision rule first, the result last; the belief filed where the next question starts"),
}

COUNT_WORD = {6: "Six", 7: "Seven", 8: "Eight"}.get(len(POSITIONS), str(len(POSITIONS)))

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


def slug(text):
    t = html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "section"


def anchor_headings(doc):
    """Give every h2 an id and return (doc, [(id, text)]) for the contents strip."""
    seen, items = {}, []

    def sub(m):
        text = m.group(1)
        base = slug(text)
        n = seen.get(base, 0)
        seen[base] = n + 1
        i = base if n == 0 else f"{base}-{n + 1}"
        items.append((i, html.unescape(re.sub(r"<[^>]+>", "", text))))
        return f'<h2 id="{i}">{text}</h2>'

    return re.sub(r"<h2>(.*?)</h2>", sub, doc), items


def short(label, limit=34):
    """The strip shows the heading's head: before a colon, or the last comma that fits."""
    head = label.split(":")[0].strip()
    if len(head) > limit and "," in head[:limit]:
        head = head[:limit].rsplit(",", 1)[0].strip()
    return head


def toc(items, minimum=4):
    if len(items) < minimum:
        return ""
    links = "".join(f'<a href="#{i}">{short(t)}</a>' for i, t in items)
    return f'<nav class="toc" aria-label="Contents"><span class="lab">Contents</span>{links}</nav>\n'


def figure(name, caption):
    src = FIGDIR / name
    if not src.exists():
        sys.exit(f"build: missing figure {src}; run site/figures.py")
    return f'<figure class="fig">{src.read_text().strip()}<figcaption>{caption}</figcaption></figure>'


def place_figures(page_key, doc):
    for (page, prefix), (name, caption) in FIGURES.items():
        if page != page_key:
            continue
        if prefix.startswith("p:"):   # after the paragraph that starts with this markup
            pat = re.compile(r"(<p>" + re.escape(prefix[2:]) + r".*?</p>)", re.S)
        else:
            pat = re.compile(r'(<h2 id="[^"]*">' + re.escape(prefix) + r'[^<]*</h2>)')
        if not pat.search(doc):
            sys.exit(f"build: nothing starting {prefix!r} on {page_key} for {name}")
        doc = pat.sub(lambda m: m.group(1) + "\n" + figure(name, caption), doc, count=1)
    return doc


def footer(root):
    """The foot band: what the site is, where to read, where the source lives."""
    return f"""<footer class="band cells foot">
  <div>
    <a class="wm" href="{root}./">gallop</a>
    <p>Route the question before it becomes an analysis. Product data science as
    agent skills, with a thin Python package underneath.</p>
  </div>
  <div>
    <p class="lab">Read</p>
    <a href="{root}map/">The method map</a>
    <a href="{root}intake/">The intake</a>
    <a href="{root}theory/">The theory layer</a>
  </div>
  <div>
    <p class="lab">Use</p>
    <a href="{root}skills/">The skills</a>
    <a href="{root}install/">Install</a>
    <a href="https://github.com/0trm/gallop">Source on GitHub &#8599;</a>
  </div>
  <div>
    <p class="lab">Project</p>
    <span>pre-1.0, moving fast</span>
    <a href="https://github.com/0trm/gallop/releases">Releases &#8599;</a>
    <span class="dim">MIT License &middot; 2026</span>
  </div>
</footer>"""


def page(*, title, description, body, root, active=None, extra_style="", contents=""):
    """The shared chrome: skip link, nav band, contents strip, foot band, theme switch."""
    nav_items = [
        ("map/", "The map"), ("intake/", "The intake"), ("skills/", "Skills"),
        ("theory/", "Theory"), ("install/", "Install"),
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
{ANALYTICS}
</head>
<body>

<a class="skip" href="#main">Skip to content</a>
<nav class="band cells nav docnav" aria-label="Site">
  <a class="wm" href="{root}./">gallop</a>
  {nav}
  <span class="sw">
    <span class="mode">
      <button type="button" data-set="light" aria-pressed="true">Light</button>
      <button type="button" data-set="dark" aria-pressed="false">Dark</button>
    </span>
  </span>
</nav>
{contents}
<main id="main">
{body}
</main>

{footer(root)}

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
      <a class="btn" href="https://github.com/0trm/gallop/tree/main/skills/{name}">
        <span>Copy the source on GitHub</span><span class="arr">&#8599;</span></a>
      {script_note}
    </div>
  </div>
</div>"""
    main_html, items = anchor_headings(render(body))
    main_html = place_figures(f"skills/{name}", main_html)
    doc = f'<div class="band"><div class="doc">\n{main_html}\n' + "\n".join(sections) + "</div></div>"
    # Cross-references between the markdown files become anchors to the
    # collapsed sections inlined above.
    doc = re.sub(r'href="(?:reference/|templates/)?([\w-]+)\.md"', r'href="#ref-\1"', doc)
    out = page(title=f"{name} · gallop", description=decides, root="../../",
               active="skills/", body=header + "\n" + doc, contents=toc(items))
    write(SITE / "skills" / name / "index.html", out, emitted)


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
    <p class="lab">{COUNT_WORD} skills</p>
  </div>
  <div class="doc mapfig">
    {figure("skills-map.svg", "Where each skill sits. The ceiling and the floor are bands because every "
            "question touches them; the three causal skills split on who assigned the treatment; "
            "the prediction skill sits below the path, where modeling serves the decision. "
            "Each name is a link.")}
  </div>
</div>
<div class="band">
  <div class="cells skillgrid sixlinks">
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
so the next question starts smaller. A decision made continuously, at volume,
leaves the path for <code>automating-decisions</code> and comes back to it for
the experiment that measures the model's impact.</p>
</div></div>"""
    style = """
  .mapfig{padding-top:28px;padding-bottom:8px}
  .sixlinks .skrow{display:block;color:inherit}
  .sixlinks .skrow:hover{background:var(--wash);text-decoration:none}
  .sixlinks h3{font-family:var(--mono);font-size:15.5px;font-weight:700;margin:0}
  .sixlinks p{margin:8px 0 0;font-size:14px;line-height:1.5;color:var(--body)}
  .sixlinks .pos{display:block;font-family:var(--sans);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px}
  .skillgrid{grid-template-columns:repeat(4,1fr)}
  .skillgrid > *{border-bottom:1px solid var(--line)}
  .skillgrid > *:nth-child(4n){border-right:0}
  .skillgrid > *:nth-child(n+5){border-bottom:0}
  @media (max-width:1080px){.skillgrid{grid-template-columns:1fr}
    .skillgrid > *{border-right:0;border-bottom:1px solid var(--line)!important}}"""
    out = page(title="The skills · gallop",
               description=f"{COUNT_WORD} skills, one position on the method map each.",
               root="../", active="skills/", body=body, extra_style=style)
    write(SITE / "skills" / "index.html", out, emitted)


# %% ---------------------------------------------------------- content pages


def build_content_page(stem, title, description, emitted):
    src = CONTENT / f"{stem}.md"
    if not src.exists():
        sys.exit(f"build: missing {src}")
    inner, items = anchor_headings(render(src.read_text()))
    inner = place_figures(stem, inner)
    body = f'<div class="band"><div class="doc">\n{inner}\n</div></div>'
    out = page(title=f"{title} · gallop", description=description, root="../",
               active=f"{stem}/", body=body, contents=toc(items))
    write(SITE / stem / "index.html", out, emitted)


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
        targets = [SITE / "skills", SITE / "theory", SITE / "install"]
        for t in targets:
            for f in t.rglob("*.html") if t.exists() else []:
                before[f] = f.read_text()

    for d in dirs:
        build_skill_page(d, emitted)
    build_skills_index(dirs, emitted)
    build_content_page("theory", "The theory layer",
                       "The prior store and the knowledge repo: the only object that compounds.", emitted)
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
