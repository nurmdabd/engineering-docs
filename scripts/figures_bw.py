"""
figures_bw.py -- black-and-white print copies of matplotlib figures, for build.py --print.

In a figure script:

    import sys; sys.path.insert(0, "<path to>/engineering-docs/scripts")
    from figures_bw import save

    save(fig, out_dir / "2020-21_1a_wave.png", dpi=170)

save() writes the colour figure, with each coloured curve given the dash of its hue (add_dashes), so the
colour and the grey copy look the same apart from colour and a caption can name both: "the dashed orange
curve". With DOC_PRINT=1 in the environment it writes only the grey copy, out_dir/print/NAME, which
build.py --print uses in place of the colour one:

    DOC_PRINT=1 python3 figures/_src/my_figures.py

What the grey copy changes:
- a coloured curve (more than 5 points) gets the dash of its hue: blue solid, orange dashed, red dotted,
  green dash-dot, purple short dashes, ...; legends get the same dashes. Straight segments, wires and
  arrows stay solid. A curve that already has a line style keeps it.
- coloured strokes, edges and arrows become black or dark grey; text becomes black.
- light fills keep their lightness; strong fills become a light grey (saves toner); colour maps become
  a light grey ramp.
- relabel={"old": "new"} rewrites figure text that names a colour, if any is left.
Name a curve by style and colour together in labels and captions ("dashed orange").
"""
import colorsys
import os
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.collections import Collection
from matplotlib.colors import ListedColormap, to_rgb, to_rgba
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Annotation, Text

PRINT = os.environ.get("DOC_PRINT") == "1"

# hue in degrees -> (grey level, dash) for coloured curves
HUES = [(0, (0.0, (0, (1.2, 1.8)))),            # red: dotted
        (30, (0.0, (0, (5, 2.5)))),             # orange: dashed
        (60, (0.35, (0, (8, 3)))),              # yellow / olive: long dashes, grey
        (130, (0.3, (0, (6, 2, 1.5, 2)))),      # green: dash-dot, dark grey
        (185, (0.0, (0, (6, 2, 1.5, 2, 1.5, 2)))),  # cyan / teal: dash-dot-dot
        (215, (0.0, "-")),                      # blue: solid
        (275, (0.3, (0, (2.5, 2)))),            # purple: short dashes, dark grey
        (330, (0.35, (0, (1.2, 1.8))))]         # pink / magenta: dotted, grey
LIGHT_GREYS = ListedColormap(plt.get_cmap("Greys")(np.linspace(0.0, 0.45, 256)))


def _lum(c):
    r, g, b = to_rgb(c)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _coloured(c):
    r, g, b = to_rgb(c)
    return max(r, g, b) - min(r, g, b) > 0.12


def _style(c):
    h = colorsys.rgb_to_hsv(*to_rgb(c))[0] * 360
    return min(HUES, key=lambda e: min(abs(h - e[0]), 360 - abs(h - e[0])))[1]


def _stroke(c):
    """Lines and edges: coloured ones become black or dark grey, greys keep their level."""
    v = _style(c)[0] if _coloured(c) else _lum(c)
    return (v, v, v, to_rgba(c)[3])


def _fill(c):
    """Fills: light tints keep their lightness; strong colours become a light grey."""
    v = _lum(c) if _lum(c) > 0.75 or not _coloured(c) else 0.82
    return (v, v, v, to_rgba(c)[3])


def _none(c):
    return isinstance(c, str) and c == "none"


def add_dashes(fig):
    """Give each solid coloured curve (more than 5 points) the dash of its hue, legend samples too."""
    for lg in fig.findobj(Legend):
        # legend samples are two-point lines, so give them the dash of their curve here
        for ln in lg.get_lines():
            c = ln.get_color()
            if _coloured(c) and ln.get_linestyle() == "-":
                ln.set_linestyle(_style(c)[1])
    for ln in fig.findobj(Line2D):
        c = ln.get_color()
        if _coloured(c) and ln.get_linestyle() == "-" and len(ln.get_xdata()) > 5:
            ln.set_linestyle(_style(c)[1])
    return fig


def to_bw(fig, relabel=None):
    """Turn every element of fig to greys in place (see the module docstring)."""
    add_dashes(fig)
    for ln in fig.findobj(Line2D):
        c = ln.get_color()
        ln.set_color(_stroke(c))
        for get, put in ((ln.get_markerfacecolor, ln.set_markerfacecolor),
                         (ln.get_markeredgecolor, ln.set_markeredgecolor)):
            m = get()
            if not _none(m):
                put(_fill(m) if _lum(m) > 0.75 else _stroke(m))
    patches = fig.findobj(Patch)
    # annotate() arrows are not in the figure's child tree, so collect them separately
    patches += [an.arrow_patch for an in fig.findobj(Annotation) if an.arrow_patch is not None]
    for pa in patches:
        pa.set_facecolor(_fill(pa.get_facecolor()))
        pa.set_edgecolor(_stroke(pa.get_edgecolor()))
    for tx in fig.findobj(Text):
        c = tx.get_color()
        tx.set_color("black" if _coloured(c) else _stroke(c))
        for old, new in (relabel or {}).items():
            if old in tx.get_text():
                tx.set_text(tx.get_text().replace(old, new))
    for co in fig.findobj(Collection):
        if getattr(co, "get_cmap", None) and co.get_array() is not None:
            co.set_cmap(LIGHT_GREYS)
            continue
        fcs, ecs = co.get_facecolor(), co.get_edgecolor()
        if len(fcs):
            co.set_facecolor([_fill(c) for c in fcs])
        if len(ecs):
            co.set_edgecolor([_stroke(c) for c in ecs])
    return fig


def save(fig, path, relabel=None, dashes=True, **savefig_kw):
    """Write fig to path; with DOC_PRINT=1, write the grey copy to path.parent/print/path.name instead.
    dashes=False keeps the colour figure's curves as drawn (the grey copy always gets the dashes)."""
    path = Path(path)
    if dashes and not PRINT:
        add_dashes(fig)
    if PRINT:
        to_bw(fig, relabel)
        path = path.parent / "print" / path.name
    path.parent.mkdir(parents=True, exist_ok=True)
    savefig_kw.setdefault("bbox_inches", "tight")
    fig.savefig(path, **savefig_kw)
    plt.close(fig)
    return path
