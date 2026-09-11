"""Build the generated half of the site.

Hand-authored pages (index, map, intake) are left untouched; this script
emits everything derived from repo sources, one HTML file per document, with
real URLs, rendering fine from file://.

  site/skills/index.html          from the skills/ directory
  site/skills/<name>/index.html   from skills/<name>/SKILL.md (+ references)
  site/theory/index.html          from site/content/theory.md
  site/install/index.html         from site/content/install.md
  site/about/index.html           from site/content/about.md
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
SITE_URL = "https://0trm.github.io/gallop/"
CHECK_ONLY = False   # set by --check; write() renders to memory instead of disk
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
    "defining-metrics": ("The floor", "A metric turned into a computation, a source of truth, a registry entry, and a statement of how it will be gamed"),
    "sizing-opportunities": ("Description", "A what-happened question turned into a localised, sized hypothesis, with the floor checked first and the gap never quoted as the prize"),
    "designing-experiments": ("Causation", "The four choices that cannot be repaired after launch, with the MDE from the prior store"),
    "reading-experiments": ("Causation", "Whether the result is a result: SRM, exposure, the sequential bound, CUPED, shrinkage"),
    "choosing-causal-designs": ("Causation", "The method that matches how assignment happened, and the exit that says there is no comparison group"),
    "automating-decisions": ("Prediction", "Whether a repeated decision belongs to a model, validated out of time, and the holdout that measures its impact"),
    "writing-readouts": ("The ceiling", "The decision rule first, the result last; the belief filed where the next question starts"),
}

COUNT_WORD = {6: "Six", 7: "Seven", 8: "Eight"}.get(len(POSITIONS), str(len(POSITIONS)))
N_POSITIONS = len({p for p, _ in POSITIONS.values()})

# One version in the tree, read rather than retyped, so the foot cannot go stale
# on the next tag. scripts/check_version.py keeps the four declarations in step.
VERSION = re.search(r'__version__ = "([^"]+)"',
                    (ROOT / "src/gallop/__init__.py").read_text()).group(1)

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
    return wrap_tables(md.render(markdown_text))


def wrap_tables(doc):
    """A markdown table is the one block that will not reflow at phone width.

    Give each its own scroll container so the page body never scrolls sideways,
    and tabindex so the container is reachable by keyboard (WCAG 2.1.1).
    """
    return re.sub(
        r"<table>.*?</table>",
        lambda m: ('<div class="scrollx" role="region" aria-label="Table" tabindex="0">'
                   f"{m.group(0)}</div>"),
        doc, flags=re.S)


def demote(doc, levels=1):
    """Push every heading down `levels`, so the page keeps a single h1.

    Markdown documents each open on an h1. Rendered under a page that already
    has one, a skill page ended up with as many as seven, and the reference
    docs inlined at the foot outranked the sections above them.
    """
    return re.sub(r"<(/?)h([1-5])>",
                  lambda m: f"<{m.group(1)}h{min(int(m.group(2)) + levels, 6)}>", doc)


def slug(text):
    t = html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "section"


def anchor_headings(doc):
    """Give every h2 an id and return (doc, [(id, text)]) for the contents."""
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


def short(label, limit=52):
    """The contents show the heading's head: the number without the word Step,
    the part before a colon, and past the limit the last comma or whole word
    that fits, never ending on a function word. The limit is the width of the
    rail, not of one strip row, so today every heading survives whole."""
    head = re.sub(r"^Step\s+", "", label.split(":")[0].strip())
    if len(head) > limit:
        cut = head[:limit]
        if "," in cut:
            cut = cut.rsplit(",", 1)[0]
        elif head[limit] != " ":
            cut = cut.rsplit(" ", 1)[0]
        head = cut
    head = re.sub(r"(\s+(the|a|an|and|or|of|to|in|on|for|with|this|that|is|are))+$",
                  "", head, flags=re.I)
    return head.rstrip(" ,\u00b7")


def rail(items, minimum=2):
    """The contents as the column beside the document rather than a strip over
    it. The strip had one row to spend, so it cut every heading to 34
    characters and the ten-section pages wrapped to a second row anyway. The
    column spells them out, holds the right third of the page that the
    document was leaving empty, and marks the section being read."""
    if len(items) < minimum:
        return ""
    links = "".join(f'<a href="#{i}">{short(t)}</a>' for i, t in items)
    return ('<nav class="rail" aria-label="Contents"><div class="railin">'
            f'<p class="lab">Contents</p>{links}</div></nav>')


def figure(name, caption, cls=""):
    src = FIGDIR / name
    if not src.exists():
        sys.exit(f"build: missing figure {src}; run site/figures.py")
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    klass = f"fig {cls}".strip()
    return f'<figure class="{klass}">{src.read_text().strip()}{cap}</figure>'


def place_figures(page_key, doc):
    for (page, prefix), (name, caption, *cls) in FIGURES.items():
        if page != page_key:
            continue
        if prefix.startswith("p:"):   # after the paragraph that starts with this markup
            pat = re.compile(r"(<p>" + re.escape(prefix[2:]) + r".*?</p>)", re.S)
        else:
            pat = re.compile(r'(<h2 id="[^"]*">' + re.escape(prefix) + r'[^<]*</h2>)')
        if not pat.search(doc):
            sys.exit(f"build: nothing starting {prefix!r} on {page_key} for {name}")
        doc = pat.sub(lambda m: m.group(1) + "\n" + figure(name, caption, *cls), doc, count=1)
    return doc


def footer(root):
    """The foot band: what the site is, where to read, where the source lives."""
    return f"""<footer class="band cells foot">
  <div>
    <a class="wm" href="{root}./">gallop</a>
    <p>Route the question before it becomes an analysis. Product data science as
    agent skills, with a Python package underneath.</p>
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
    <span>v{VERSION}</span>
    <a href="https://github.com/0trm/gallop/releases">Releases &#8599;</a>
    <span class="dim">MIT License &middot; 2026</span>
  </div>
</footer>"""


def page(*, title, description, body, root, url="", active=None, extra_style=""):
    """The shared chrome: skip link, nav band, foot band, theme switch. The
    contents belong to the document, so they are built into the body."""
    nav_items = [
        ("map/", "The map"), ("intake/", "The intake"), ("skills/", "Skills"),
        ("theory/", "Theory"), ("install/", "Install"), ("about/", "About"),
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
<meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{SITE_URL}{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="gallop">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(description, quote=True)}">
<meta property="og:url" content="{SITE_URL}{url}">
<meta name="twitter:card" content="summary">
<script>
  /* Before paint. Read at the foot instead, a remembered dark theme arrives
     after the light page is already on screen, on every navigation. */
  (function () {{
    try {{
      var t = localStorage.getItem("gallop-theme");
      if (t === "dark" || t === "light") document.documentElement.dataset.theme = t;
    }} catch (e) {{}}
  }})();
</script>
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
<nav class="band cells nav" aria-label="Site">
  <a class="wm" href="{root}./">gallop</a>
  <button type="button" class="menu" aria-expanded="false" aria-label="Menu"><span class="bars"></span></button>
  {nav}
  <span class="sw">
    <span class="theme" role="group" aria-label="Theme">
      <button type="button" data-set="light" aria-pressed="true" aria-label="Light theme"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="3.6"/><path d="M10 1.5v2.5M10 16v2.5M1.5 10H4M16 10h2.5M4 4l1.8 1.8M14.2 14.2 16 16M4 16l1.8-1.8M14.2 5.8 16 4"/></svg></button>
      <button type="button" data-set="dark" aria-pressed="false" aria-label="Dark theme"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M16 12.6A6.8 6.8 0 0 1 7.4 4a6.8 6.8 0 1 0 8.6 8.6z"/></svg></button>
    </span>
  </span>
</nav>
<main id="main">
{body}
</main>

{footer(root)}

<script>
  document.querySelectorAll(".snip .copy").forEach(function (b) {{
    if (!navigator.clipboard) {{ b.hidden = true; return; }}
    b.addEventListener("click", function () {{
      var pre = b.closest(".snip").querySelector("pre").cloneNode(true);
      pre.querySelectorAll(".p").forEach(function (g) {{ g.remove(); }});
      navigator.clipboard.writeText(pre.textContent.replace(/^ /gm, "")).then(function () {{
        b.textContent = "Copied";
        setTimeout(function () {{ b.textContent = "Copy"; }}, 1600);
      }});
    }});
  }});
  (function () {{
    var nav = document.querySelector(".nav"), btn = nav && nav.querySelector(".menu");
    if (!btn) return;
    function set(open) {{
      nav.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", String(open));
    }}
    btn.addEventListener("click", function () {{ set(!nav.classList.contains("open")); }});
    nav.addEventListener("keydown", function (e) {{
      if (e.key === "Escape" && nav.classList.contains("open")) {{ set(false); btn.focus(); }}
    }});
  }})();
  (function () {{
    // a link into a reference document lands on a collapsed block, which the
    // browser scrolls to and leaves shut. Open the one being pointed at.
    function openTarget() {{
      var el = location.hash && document.getElementById(location.hash.slice(1));
      if (el && el.tagName === "DETAILS" && !el.open) {{
        el.open = true;
        el.scrollIntoView();
      }}
    }}
    addEventListener("hashchange", openTarget);
    openTarget();
  }})();
  (function () {{
    // the contents mark the section the reader is in: the last heading to have
    // crossed the top of the viewport, rechecked on a frame rather than on
    // every scroll event.
    var rail = document.querySelector(".rail");
    if (!rail) return;
    var links = [].slice.call(rail.querySelectorAll("a"));
    var heads = links.map(function (a) {{
      return document.getElementById(a.getAttribute("href").slice(1));
    }});
    var queued = false;
    function mark() {{
      queued = false;
      var at = -1;   // above the first heading nothing is marked
      for (var j = 0; j < heads.length; j++) {{
        if (heads[j] && heads[j].getBoundingClientRect().top <= 96) at = j;
      }}
      links.forEach(function (a, k) {{
        if (k === at) a.setAttribute("aria-current", "true");
        else a.removeAttribute("aria-current");
      }});
    }}
    addEventListener("scroll", function () {{
      if (!queued) {{ queued = true; requestAnimationFrame(mark); }}
    }}, {{passive: true}});
    mark();
  }})();
  (function () {{
    var root = document.documentElement;
    var buttons = document.querySelectorAll(".theme button");
    function apply(theme) {{
      root.dataset.theme = theme;
      buttons.forEach(function (b) {{
        b.setAttribute("aria-pressed", String(b.dataset.set === theme));
      }});
    }}
    apply(root.dataset.theme === "dark" ? "dark" : "light");   // the head set it
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


RENDERED: dict[Path, str] = {}   # every page this run built, path -> html


def write(path, content, emitted):
    """Record the render; only touch disk outside --check.

    --check used to call the same builders and let them write, so it repaired
    the staleness it was reporting: the run failed, the tree was silently
    fixed, and a second run passed with nothing committed.
    """
    RENDERED[path] = content
    emitted.append(path)
    if CHECK_ONLY:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


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
            inner = demote(render(f.read_text()))
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
      <div class="snip"><div class="bar"><span class="path"><span class="cur"></span>shell</span><button type="button" class="copy">Copy</button></div><pre><span class="p">$</span> git clone https://github.com/0trm/gallop
<span class="p">$</span> cp -r gallop/skills/{name} .claude/skills/</pre></div>
      <a class="btn" href="https://github.com/0trm/gallop/tree/main/skills/{name}">
        <span>Read the source on GitHub</span><span class="arr">&#8599;</span></a>
      {script_note}
    </div>
  </div>
</div>"""
    main_html, items = anchor_headings(render(body))
    main_html = place_figures(f"skills/{name}", main_html)
    # anchor_headings and place_figures both key off h2, so drop the document
    # title only after they have run. The hero above carries position, name and
    # description; rendered again here it was the same words at the same size.
    main_html = re.sub(r"<h1>.*?</h1>\n?", "", main_html, count=1)
    doc = (f'<div class="band docgrid">{rail(items)}<div class="doc">\n{main_html}\n'
           + "\n".join(sections) + "</div></div>")
    # Cross-references between the markdown files become anchors to the
    # collapsed sections inlined above.
    doc = re.sub(r'href="(?:reference/|templates/)?([\w-]+)\.md"', r'href="#ref-\1"', doc)
    out = page(title=f"{name} · gallop", description=decides, root="../../",
               url=f"skills/{name}/", active="skills/",
               body=header + "\n" + doc)
    write(SITE / "skills" / name / "index.html", out, emitted)


def build_skills_index(dirs, emitted):
    rows = []
    for d in dirs:
        meta, _ = frontmatter((d / "SKILL.md").read_text())
        name = meta["name"]
        position, decides = POSITIONS[name]
        rows.append(f"""    <a class="skrow" href="{name}/">
      <span class="pos dim">{position}</span>
      <h2>{name}</h2>
      <p>{decides}.</p>
    </a>""")
    body = f"""<div class="band">
  <div class="secthead">
    <p class="lab">{COUNT_WORD} skills</p>
  </div>
  <div class="doc skhead">
    <h1>The skills</h1>
    <p class="lede">A skill is a decision procedure your agent runs with you: the questions in
    order, the checks that have to pass, and the exit that says this one cannot be answered.
    {COUNT_WORD} of them across {N_POSITIONS} positions on the method map;
    causation carries three.</p>
  </div>
  <div class="doc mapfig">
    {figure("skills-map.svg", "Where each skill sits. Each name is a link.")}
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
so the next question starts smaller. A what-happened question leaves the path
for <code>sizing-opportunities</code> and comes back as a sized hypothesis; a
decision made continuously, at volume, leaves it for
<code>automating-decisions</code> and comes back for the experiment that
measures the model's impact.</p>
</div></div>"""
    style = """
  .skhead{padding-bottom:0}
  .skhead h1{margin-bottom:12px}
  .skhead .lede{margin:0;font-size:16px;line-height:1.6;color:var(--body);max-width:72ch}
  .mapfig{padding-top:28px;padding-bottom:8px}
  .sixlinks .skrow{display:block;color:inherit}
  .sixlinks .skrow:hover{background:var(--wash);text-decoration:none}
  .sixlinks h2{font-family:var(--mono);font-size:15px;font-weight:700;margin:0;
    text-transform:none;letter-spacing:0;border-top:0;padding-top:0}
  .sixlinks p{margin:8px 0 0;font-size:14px;line-height:1.5;color:var(--body)}
  .sixlinks .pos{display:block;font-family:var(--sans);font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px}
  .skillgrid{grid-template-columns:repeat(4,1fr)}
  .skillgrid > *{border-bottom:1px solid var(--line)}
  .skillgrid > *:nth-child(4n){border-right:0}
  .skillgrid > *:nth-child(n+5){border-bottom:0}
  @media (max-width:1080px){.skillgrid{grid-template-columns:1fr}
    .skillgrid > *{border-right:0;border-bottom:1px solid var(--line)!important}}"""
    out = page(title="The skills · gallop",
               description=f"{COUNT_WORD} skills across {N_POSITIONS} positions "
                           f"on the method map, one position each.",
               root="../", url="skills/", active="skills/", body=body, extra_style=style)
    write(SITE / "skills" / "index.html", out, emitted)


# %% ---------------------------------------------------------- content pages


def build_content_page(stem, title, label, description, emitted):
    src = CONTENT / f"{stem}.md"
    if not src.exists():
        sys.exit(f"build: missing {src}")
    inner, items = anchor_headings(render(src.read_text()))
    inner = place_figures(stem, inner)
    # The title and the opening paragraph become a header band, so a content
    # page opens the way a skill page does: a label, the name, one description,
    # then the document. Lifted after the figures are placed, which key off the
    # headings and the paragraphs around them.
    h1 = re.search(r"<h1>(.*?)</h1>\n?", inner, re.S)
    lede = re.search(r"<p>(.*?)</p>\n?", inner, re.S)
    if not h1 or not lede:
        sys.exit(f"build: {src.name} needs a title and an opening paragraph")
    inner = inner.replace(h1.group(0), "", 1).replace(lede.group(0), "", 1)
    header = f"""<div class="band">
  <div class="secthead">
    <p class="lab">{label}</p>
  </div>
  <div class="cells pagehead">
    <div>
      <h1 class="d" style="font-size:34px">{h1.group(1)}</h1>
      <p class="skdesc">{lede.group(1)}</p>
    </div>
  </div>
</div>"""
    body = (f'{header}\n<div class="band docgrid">{rail(items)}'
            f'<div class="doc">\n{inner.lstrip()}\n</div></div>')
    out = page(title=f"{title} · gallop", description=description, root="../",
               url=f"{stem}/", active=f"{stem}/", body=body)
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

    global CHECK_ONLY
    CHECK_ONLY = a.check
    targets = [SITE / "skills", SITE / "theory", SITE / "install", SITE / "about"]

    dirs = skill_dirs()
    emitted = []
    for d in dirs:
        build_skill_page(d, emitted)
    build_skills_index(dirs, emitted)
    build_content_page("theory", "The theory layer", "The ceiling",
                       "The prior store and the knowledge repo: the only object that compounds.", emitted)
    build_content_page("about", "About", "The project",
                       "Why the routing and the rigour live in one place, and who it is for.",
                       emitted)
    build_content_page("install", "Install", "Setup",
                       "Claude Code plugin, manual copy, or pip.", emitted)
    readme_path, readme_new = build_readme(dirs)

    if a.check:
        stale = [str(f.relative_to(ROOT)) for f, c in RENDERED.items()
                 if not f.exists() or f.read_text() != c]
        on_disk = {f for t in targets if t.exists() for f in t.rglob("*.html")}
        extra = sorted(str(f.relative_to(ROOT)) for f in on_disk - set(RENDERED))
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
