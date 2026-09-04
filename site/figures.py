"""Draw the site's figures as inline SVG.

One ink, hairlines, the sans face for labels: the figures wear the page's
CSS variables, so they theme with the switch and stay crisp at any width.
Every chart is computed, not drawn by eye; the three from reading-experiments
call the same gallop functions the skill does.

  site/figures/peeking.svg        false-positive rate against number of looks
  site/figures/cuped.svg          standard-error factor against rho
  site/figures/shrinkage.svg      the quickstart's raw and shrunk estimate
  site/figures/prior-store.svg    what a hundred readouts on one metric look like
  site/figures/skills-map.svg     the six skills placed on the method map

Run:  python3 site/figures.py      (then site/build.py inlines them)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from gallop.shrink import empirical_bayes

OUT = Path(__file__).resolve().parent / "figures"
W = 840  # one unit is one pixel at the doc column's full width


# %% ---------------------------------------------------------------- helpers


def svg(height, body, label):
    return (f'<svg viewBox="0 0 {W} {height}" role="img" aria-label="{label}">\n'
            f"{body}\n</svg>\n")


def text(x, y, s, cls="", anchor="start", extra=""):
    c = f' class="{cls}"' if cls else ""
    return f'<text x="{x:.1f}" y="{y:.1f}"{c} text-anchor="{anchor}"{extra}>{s}</text>'


def path(pts, cls):
    d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts))
    return f'<path class="{cls}" d="{d}"/>'


class Axes:
    """A plot area with linear scales; grid lines are recessive hairlines."""

    def __init__(self, x0, x1, y0, y1, left=56, right=24, top=28, bottom=44, height=300):
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1
        self.l, self.r, self.t, self.b = left, W - right, top, height - bottom
        self.height = height

    def x(self, v):
        return self.l + (v - self.x0) / (self.x1 - self.x0) * (self.r - self.l)

    def y(self, v):
        return self.b - (v - self.y0) / (self.y1 - self.y0) * (self.b - self.t)

    def frame(self, xticks, yticks, xfmt=str, yfmt=str, xlabel="", ylabel=""):
        out = []
        for v in yticks:
            y = self.y(v)
            out.append(f'<line class="grid" x1="{self.l}" y1="{y:.1f}" x2="{self.r}" y2="{y:.1f}"/>')
            out.append(text(self.l - 8, y + 4, yfmt(v), "dimt", "end"))
        out.append(f'<line class="ax" x1="{self.l}" y1="{self.b}" x2="{self.r}" y2="{self.b}"/>')
        for v in xticks:
            x = self.x(v)
            out.append(f'<line class="ax" x1="{x:.1f}" y1="{self.b}" x2="{x:.1f}" y2="{self.b + 4}"/>')
            out.append(text(x, self.b + 17, xfmt(v), "dimt", "middle"))
        if xlabel:
            out.append(text(self.r, self.b + 34, xlabel, "lab", "end"))
        if ylabel:
            out.append(text(self.l, self.t - 12, ylabel, "lab"))
        return "\n".join(out)


# %% ---------------------------------------------------------------- peeking


def peeking():
    """Simulate a null A/B test read at k equally spaced looks, alpha 0.05."""
    rng = np.random.default_rng(0)
    inc, sims = 60, 100_000
    z = np.cumsum(rng.standard_normal((sims, inc)), axis=1) / np.sqrt(np.arange(1, inc + 1))
    looks = [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30]
    fpr = []
    for k in looks:
        idx = np.array([inc * j // k for j in range(1, k + 1)]) - 1
        fpr.append(float((np.abs(z[:, idx]) > 1.959964).any(axis=1).mean()))
    ax = Axes(1, 30, 0, 0.30, height=300)
    body = [ax.frame([1, 5, 10, 15, 20, 30], [0, .05, .10, .15, .20, .25, .30],
                     yfmt=lambda v: f"{v:.0%}", xlabel="looks at the data during the run",
                     ylabel="false positives under a true null")]
    body.append(path([(ax.x(k), ax.y(f)) for k, f in zip(looks, fpr)], "ln"))
    body.append(f'<line class="dash thin ax" x1="{ax.l}" y1="{ax.y(.05):.1f}" x2="{ax.r}" y2="{ax.y(.05):.1f}"/>')
    body.append(text(ax.r, ax.y(.05) - 6, "the 5% you signed up for", "dimt", "end"))
    for k, f in zip(looks, fpr):
        body.append(f'<circle class="dot" cx="{ax.x(k):.1f}" cy="{ax.y(f):.1f}" r="3.5"/>')
    for k, f, dx, dy in ((1, fpr[0], 10, 4), (5, fpr[4], 10, 4), (14, fpr[8], 10, 4), (30, fpr[-1], -8, 4)):
        i = looks.index(k if k != 14 else 15)
        anchor = "end" if k == 30 else "start"
        body.append(text(ax.x(looks[i]) + dx, ax.y(fpr[i]) + dy, f"{looks[i]} look{'s' if looks[i] > 1 else ''}: {fpr[i]:.0%}", "", anchor))
    return svg(300, "\n".join(body),
               "False-positive rate of a fixed-horizon test read repeatedly during the run, "
               f"rising from 5% at one look to about {fpr[-1]:.0%} at thirty looks."), fpr


# %% ------------------------------------------------------------------- cuped


def cuped():
    rho = np.linspace(0, 1, 101)
    factor = np.sqrt(1 - rho**2)
    ax = Axes(0, 1, 0, 1, height=300)
    body = [ax.frame([0, .2, .4, .6, .8, 1], [0, .25, .5, .75, 1],
                     xfmt=lambda v: f"{v:.1f}", yfmt=lambda v: f"{v:.2f}",
                     xlabel="correlation between the pre-period covariate and the outcome",
                     ylabel="standard error after CUPED, as a share of before")]
    body.append(path([(ax.x(r), ax.y(f)) for r, f in zip(rho, factor)], "ln"))
    for r in (.5, .7, .9):
        f = float(np.sqrt(1 - r**2))
        body.append(f'<line class="grid dash" x1="{ax.x(r):.1f}" y1="{ax.y(f):.1f}" x2="{ax.x(r):.1f}" y2="{ax.b}"/>')
        body.append(f'<circle class="dot" cx="{ax.x(r):.1f}" cy="{ax.y(f):.1f}" r="3.5"/>')
        body.append(text(ax.x(r) - 8, ax.y(f) - 8, f"rho {r:.1f}: se x{f:.2f}", "", "end"))
    return svg(300, "\n".join(body),
               "The standard error after CUPED as a share of the raw standard error, "
               "sqrt(1 minus rho squared): 0.87 at rho 0.5, 0.71 at 0.7, 0.44 at 0.9.")


# %% --------------------------------------------------------------- shrinkage


def shrinkage():
    """The quickstart's own numbers: prior mu 0.097pp, tau 0.065pp; raw +0.306pp se 0.227pp."""
    mu, tau, eff, se = 0.097, 0.065, 0.306, 0.227
    r = empirical_bayes(eff, se, mu=mu, tau2=tau**2)
    ax = Axes(-0.4, 1.0, 0, 1, left=200, right=24, top=24, bottom=44, height=220)
    body = [ax.frame([-.4, -.2, 0, .2, .4, .6, .8, 1.0], [], xfmt=lambda v: f"{v:+.1f}pp",
                     xlabel="effect on the metric, percentage points")]
    # the prior: a band two tau wide either side of mu
    body.append(f'<rect class="wash" x="{ax.x(mu - 2 * tau):.1f}" y="{ax.t}" '
                f'width="{ax.x(mu + 2 * tau) - ax.x(mu - 2 * tau):.1f}" height="{ax.b - ax.t}"/>')
    body.append(f'<line class="ax dash" x1="{ax.x(mu):.1f}" y1="{ax.t}" x2="{ax.x(mu):.1f}" y2="{ax.b}"/>')
    body.append(text(ax.x(mu), ax.t - 8, f"what this metric usually does: {mu:+.2f}pp, tau {tau:.3f}", "dimt", "middle"))
    rows = [("raw readout", eff, se, 62), ("shrunk toward the prior", r["effect_shrunk"], r["se_shrunk"], 122)]
    for name, e, s, y in rows:
        body.append(text(ax.l - 14, y + 4, name, "", "end"))
        body.append(f'<line class="ln" x1="{ax.x(e - 1.96 * s):.1f}" y1="{y}" x2="{ax.x(e + 1.96 * s):.1f}" y2="{y}"/>')
        body.append(f'<circle class="dot-o" cx="{ax.x(e):.1f}" cy="{y}" r="5"/>')
        body.append(text(ax.x(e), y - 12, f"{e:+.3f}pp", "mono", "middle"))
    # the arrow from raw to shrunk
    body.append(f'<path class="ax" marker-end="url(#fh)" d="M{ax.x(eff):.1f} {rows[0][3] + 8} '
                f'L{ax.x(r["effect_shrunk"]):.1f} {rows[1][3] - 10}"/>')
    body.insert(0, '<defs><marker id="fh" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" '
                   'markerUnits="userSpaceOnUse"><path d="M0 0L8 4L0 8z" class="dot"/></marker></defs>')
    body.append(text(ax.r, rows[1][3] + 26, f"weight on the data {r['weight_on_data']:.2f}; "
                     f"the readout overstated by {r['overstatement']:+.3f}pp", "dimt", "end"))
    return svg(220, "\n".join(body),
               f"The quickstart's raw readout of {eff:+.3f}pp with its interval, shrunk to "
               f"{r['effect_shrunk']:+.3f}pp toward a prior of {mu:+.3f}pp, because the prior is tight "
               f"and the readout is noisy.")


# %% ------------------------------------------------------------- prior store


def prior_store():
    """Illustrative: a hundred readouts on one metric, most of them near zero."""
    rng = np.random.default_rng(1)
    effects = np.concatenate([rng.normal(0.02, 0.22, 88), rng.normal(0.55, 0.2, 12)])
    edges = np.arange(-0.8, 1.61, 0.2)
    counts, _ = np.histogram(effects, edges)
    wish = 1.5
    ax = Axes(-0.8, 1.6, 0, 40, height=300)
    body = [ax.frame([-.8, -.4, 0, .4, .8, 1.2, 1.6], [0, 10, 20, 30, 40], xfmt=lambda v: f"{v:+.1f}",
                     xlabel="effect each readout produced, percentage points",
                     ylabel="readouts on this metric, out of a hundred")]
    for lo, c in zip(edges[:-1], counts):
        if c == 0:
            continue
        x0, x1 = ax.x(lo) + 1, ax.x(lo + 0.2) - 1
        body.append(f'<rect class="hbar" x="{x0:.1f}" y="{ax.y(c):.1f}" width="{x1 - x0:.1f}" height="{ax.b - ax.y(c):.1f}"/>')
    m = effects.mean()
    body.append(f'<line class="ax dash" x1="{ax.x(m):.1f}" y1="{ax.t}" x2="{ax.x(m):.1f}" y2="{ax.b}"/>')
    body.append(text(ax.x(m) - 8, ax.t + 4, f"mean {m:+.2f}pp: the honest prior", "", "end"))
    body.append(f'<line class="ax dash" x1="{ax.x(wish):.1f}" y1="{ax.t}" x2="{ax.x(wish):.1f}" y2="{ax.b}"/>')
    body.append(text(ax.x(wish) - 8, ax.t + 4, f"an MDE of {wish:.1f}pp, which nothing here has ever produced", "", "end"))
    mx = effects.max()
    top = counts[int((mx - edges[0]) // 0.2)]
    body.append(text(ax.x(mx), ax.y(top) - 10, f"largest ever: {mx:+.2f}pp", "dimt", "middle"))
    return svg(300, "\n".join(body),
               "A histogram of a hundred readouts on one metric, most within a quarter of a point of zero, "
               "with the mean marked as the honest prior and a wished-for MDE of 1.5pp marked far to the "
               "right of anything the metric has ever produced. Illustrative data.")


# %% -------------------------------------------------------------- skills map


def skills_map():
    """The method map, reduced to the objects a skill sits on."""
    def box(x, y, w, h, title, skills, key=None):
        out = [f'<rect class="node" x="{x}" y="{y}" width="{w}" height="{h}"/>']
        if key:
            out.append(f'<rect class="node" x="{x}" y="{y}" width="12" height="{h}" fill="url(#{key})"/>')
        out.append(text(x + 24, y + 24, title, "t-title"))
        for i, s in enumerate(skills):
            out.append(f'<a href="{s}/"><text class="sk" x="{x + 24}" y="{y + 48 + i * 20}">{s}</text></a>')
        return "\n".join(out)
    b = ['<defs>'
         '<marker id="sm" markerWidth="9" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
         '<path d="M0 0L9 4L0 8z" class="dot"/></marker>'
         '<pattern id="ph" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="1" class="dot"/></pattern>'
         '<pattern id="pv" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="1" height="3" class="dot"/></pattern>'
         '<pattern id="px" width="4" height="4" patternUnits="userSpaceOnUse"><path d="M0 4L4 0M-1 1L1 -1M3 5L5 3" class="ax"/></pattern>'
         '</defs>']
    # theory band, the ceiling
    b.append('<rect class="node" x="40" y="20" width="760" height="56"/>')
    b.append('<rect class="node" x="40" y="20" width="12" height="56"/>')
    b.append(text(64, 44, "Theory layer", "t-title"))
    b.append(text(64, 64, "the ceiling: what each decision taught, and the prior it left", "dimt"))
    b.append('<a href="writing-readouts/"><text class="sk" x="780" y="54" text-anchor="end">writing-readouts</text></a>')
    # measurement band, the floor
    b.append('<rect class="node" x="40" y="404" width="760" height="56"/>')
    b.append('<rect class="dot" x="40" y="404" width="12" height="56"/>')
    b.append(text(64, 428, "Measurement framework", "t-title"))
    b.append(text(64, 448, "the floor: the definition of success, and whether the number can be trusted", "dimt"))
    b.append('<a href="defining-metrics/"><text class="sk" x="780" y="438" text-anchor="end">defining-metrics</text></a>')
    # routing
    b.append(box(40, 172, 224, 116, "Routing", ["routing-questions"]))
    b.append(text(64, 268, "one lookup, three questions, one gate", "dimt"))
    # the diamond
    b.append('<polygon class="node" points="356,230 420,190 484,230 420,270"/>')
    b.append(text(420, 226, "can you", "t-q", "middle"))
    b.append(text(420, 241, "randomize?", "t-q", "middle"))
    # the two causal boxes
    b.append(box(540, 112, 260, 96, "Experimentation", ["designing-experiments", "reading-experiments"], "pv"))
    b.append(box(540, 260, 260, 76, "Causal inference", ["choosing-causal-designs"], "px"))
    # arrows
    b.append('<path class="ax" marker-end="url(#sm)" d="M264 230H350"/>')
    b.append('<path class="ax" marker-end="url(#sm)" d="M484 230H512V160H534"/>')
    b.append('<path class="ax" marker-end="url(#sm)" d="M484 230H512V298H534"/>')
    b.append(text(496, 150, "yes", "t-edge"))
    b.append(text(496, 292, "no", "t-edge"))
    b.append('<path class="ax dash" marker-end="url(#sm)" d="M420 76V184"/>')
    b.append('<path class="ax dash" marker-end="url(#sm)" d="M420 404V276"/>')
    b.append('<path class="ax dash" marker-end="url(#sm)" d="M670 208V254"/>')
    return svg(480, "\n".join(b),
               "The six skills placed on the method map: writing-readouts on the theory layer across the top, "
               "defining-metrics on the measurement framework across the bottom, routing-questions at the "
               "entry before the can-you-randomize diamond, designing-experiments and reading-experiments on "
               "the experimentation box, choosing-causal-designs on the causal inference box.")


# %% -------------------------------------------------------------------- main


def main():
    OUT.mkdir(exist_ok=True)
    peek, fpr = peeking()
    files = {
        "peeking.svg": peek, "cuped.svg": cuped(), "shrinkage.svg": shrinkage(),
        "prior-store.svg": prior_store(), "skills-map.svg": skills_map(),
    }
    for name, content in files.items():
        (OUT / name).write_text(content)
        print(f"wrote {OUT / name}")
    print("peeking fpr:", {k: round(v, 3) for k, v in zip([1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30], fpr)})


if __name__ == "__main__":
    main()
