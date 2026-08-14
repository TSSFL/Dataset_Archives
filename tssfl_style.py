# -*- coding: utf-8 -*-
"""TSSFL Technology Stack - house style for charts, tables and reports.

Load it at the top of any SageMathCell on www.tssfl.com:

    load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tssfl_style.py")

Then a survey question becomes one line:

    counts(df, "How_often_do_you_use_the_library")

Design rules this module enforces, because they are what used to go wrong:

* **The credit never touches the data.** `finish()` measures the title and
  footer bands in inches and hands the plot only what is left, so nothing is
  ever placed on top of anything else.
* **Long labels are read, not rotated.** `tidy()` strips ODK/KoBo group
  prefixes and underscores; the bar helpers flip to horizontal when the
  category names are long, instead of turning them 90 degrees.
* **Nothing is coloured by accident.** Three validated categorical palettes
  ship here, but every helper takes `colors=`, so a script that already has a
  colour scheme it wants to show off keeps it untouched.
* **One axis.** There is deliberately no dual-axis helper. Two measures on two
  scales invent a correlation that is not in the data; use two panels, or
  `dumbbell()` when the gap between them is the point.

Nothing here needs installing - it is matplotlib and pandas only.
"""

from __future__ import annotations

import textwrap

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

__all__ = [
    "use", "palette", "colors", "tidy", "wrap", "finish", "figure",
    "bars", "counts", "grouped_bars", "likert", "donut", "dumbbell",
    "line", "scatter", "heatmap", "distribution", "boxes", "panels",
    "table", "crosstab", "summary", "show_html", "scale_order", "SCALES",
    "label_bars",
    "PALETTES", "SEQUENTIAL", "DIVERGING", "STATUS", "INK", "INK_2",
    "MUTED", "GRID", "BAND", "SURFACE", "SITE",
]

SITE = "www.tssfl.com"

# --------------------------------------------------------------------------
# Palettes
#
# Each categorical palette below was checked for colour-vision separation
# rather than chosen by eye: every adjacent pair clears CVD deltaE 8 and
# normal-vision deltaE 15 (OKLab x100) on a white surface. Slot order is part
# of the guarantee, so take colours from the front - do not shuffle them.
# --------------------------------------------------------------------------
PALETTES = {
    # The forum's own blue leads. Worst adjacent pair: CVD 8.9, normal 23.8.
    "tssfl": ["#096EFF", "#f97316", "#10B981", "#f59e0b",
              "#ec4899", "#15803d", "#7c3aed", "#e11d48"],
    # Softer, print-friendly. Worst adjacent pair: CVD 9.1, normal 19.6.
    "vivid": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
              "#e87ba4", "#008300", "#4a3aa7", "#e34948"],
    # Highest separation of the three, and the most striking on a projector.
    # Worst adjacent pair: CVD 10.1, normal 28.8.
    "bold": ["#e11d48", "#0891b2", "#f59e0b", "#7c3aed",
             "#059669", "#ea580c", "#2563eb", "#db2777"],
}

# One hue, light to dark, for magnitude (heatmaps, choropleths, ordered bins).
SEQUENTIAL = {
    "blue":    ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5",
                "#2a78d6", "#1c5cab", "#104281"],
    "teal":    ["#ccfbf1", "#99f6e4", "#5eead4", "#2dd4bf",
                "#14b8a6", "#0f766e", "#134e4a"],
    "amber":   ["#fef3c7", "#fde68a", "#fcd34d", "#fbbf24",
                "#f59e0b", "#b45309", "#78350f"],
    "magenta": ["#fce7f3", "#fbcfe8", "#f9a8d4", "#f472b6",
                "#ec4899", "#be185d", "#831843"],
}

# Two hues that read as opposite, with a neutral middle that reads as nothing.
DIVERGING = {
    "blue_red":   ["#1c5cab", "#3987e5", "#9ec5f4", "#f0efec",
                   "#f5a3a3", "#e34948", "#b91c1c"],
    "teal_amber": ["#0f766e", "#14b8a6", "#99f6e4", "#f0efec",
                   "#fcd34d", "#f59e0b", "#b45309"],
}

# Reserved: these mean good/bad. Never reuse one as "series 4".
STATUS = {"good": "#0ca30c", "warning": "#fab219",
          "serious": "#ec835a", "critical": "#d03b3b"}

# Chrome and ink. Text always wears these, never a series colour.
INK = "#0f172a"        # primary text
INK_2 = "#475569"      # secondary text
MUTED = "#94a3b8"      # axis ticks, credit line
GRID = "#e2e8f0"       # hairline gridline
BAND = "#f8fafc"       # alternating row band
SURFACE = "#ffffff"    # chart surface

_ACTIVE = "tssfl"


def palette(name=None):
    """Return a palette by name; with no argument, the active one."""
    if name is None:
        name = _ACTIVE
    if isinstance(name, (list, tuple)):
        return list(name)
    if name not in PALETTES:
        raise KeyError(f"unknown palette {name!r}; have {sorted(PALETTES)}")
    return list(PALETTES[name])


def colors(n, name=None):
    """First `n` slots of a palette.

    Past 8 the guarantee is gone, so rather than invent hues we repeat and
    say so - that is the signal to fold the tail into "Other" or to facet.
    """
    p = palette(name)
    if n > len(p):
        import warnings
        warnings.warn(
            f"{n} categories but only {len(p)} validated colours - colours "
            "will repeat. Group the small categories into 'Other', or use "
            "panels(), so identity stays readable.", stacklevel=2)
        p = (p * (n // len(p) + 1))
    return p[:n]


def use(name="tssfl", base=11.0, dpi=110):
    """Apply the house look. Call once at the top of a script.

    Everything here is a default, not a lock - any script can override any
    rcParam afterwards, or pass `colors=` to a helper.
    """
    global _ACTIVE
    _ACTIVE = name if isinstance(name, str) else _ACTIVE
    p = palette(name)
    mpl.rcParams.update({
        "font.family": "sans-serif",
        # Nimbus Sans is Helvetica-metric and present on the SageCell server;
        # DejaVu is matplotlib's own and always there. Both are complete.
        "font.sans-serif": ["Nimbus Sans", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": base,
        "figure.dpi": dpi,
        "savefig.dpi": 150,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "savefig.bbox": None,          # finish() reserves its own margins
        "text.color": INK,
        "axes.labelcolor": INK_2,
        "axes.labelsize": base - 0.5,
        "axes.titlesize": base + 2,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "axes.titlepad": 12,
        "axes.edgecolor": GRID,
        "axes.linewidth": 1.0,
        "axes.grid": False,
        "axes.axisbelow": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": mpl.cycler(color=p),
        "grid.color": GRID,
        "grid.linewidth": 1.0,
        "grid.linestyle": "-",          # dashed grids read as thresholds
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "xtick.labelsize": base - 1,
        "ytick.labelsize": base - 1,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "xtick.major.pad": 7,
        "ytick.major.pad": 7,
        "legend.frameon": False,
        "legend.fontsize": base - 0.5,
        "lines.linewidth": 2.0,
        "lines.markersize": 7,
        "lines.solid_capstyle": "round",
        "patch.linewidth": 0,
        "figure.figsize": (10.5, 6.0),
    })
    return p


# --------------------------------------------------------------------------
# Labels
# --------------------------------------------------------------------------
# Ordered response scales. Survey answers sorted alphabetically read as
# "Agree, Disagree, Strongly agree, Strongly disagree", which is nonsense on a
# chart; if the observed categories match one of these, use its order instead.
SCALES = [
    ["strongly disagree", "disagree", "neutral", "undecided", "not sure",
     "agree", "strongly agree"],
    ["never", "rarely", "sometimes", "often", "always"],
    ["not at all", "a little", "somewhat", "a lot", "very much"],
    ["very poor", "poor", "fair", "average", "good", "very good",
     "excellent"],
    ["very unlikely", "unlikely", "likely", "very likely"],
    ["very dissatisfied", "dissatisfied", "satisfied", "very satisfied"],
    ["none", "primary", "secondary", "certificate", "diploma", "degree",
     "masters", "phd"],
    ["daily", "weekly", "monthly", "quarterly", "yearly", "never"],
    ["no", "yes"],
]


def scale_order(values):
    """Order survey categories by their scale, alphabetically only as a last
    resort.

    Returns the categories arranged sensibly. Matching ignores case and
    underscores, so "Strongly_Agree" and "strongly agree" are the same thing.
    """
    seen = [v for v in pd.unique(pd.Series(list(values)).dropna())]

    def key(v):
        return str(v).replace("_", " ").strip().lower()

    keys = {key(v): v for v in seen}
    for scale in SCALES:
        if set(keys) <= set(scale):                # every category is on it
            return [keys[k] for k in scale if k in keys]
    return sorted(seen, key=lambda v: str(v))


def tidy(name, max_words=None):
    """Turn an ODK/KoBo field name into something a reader can read.

    ``group_da25q48/What_are_your_percep_s_teaching_knowledge/Our_teacher_
    presents_y_and_systematically`` becomes ``Our teacher presents y and
    systematically`` - KoBo's own mid-word truncation survives, because
    inventing the missing letters would be worse than showing them missing.
    """
    if not isinstance(name, str):
        return name
    if name.startswith("Unnamed:"):               # pandas' unnamed index col
        return "Column " + name.split(":")[-1].strip()
    s = name.split("/")[-1]                       # drop the group path
    s = s.replace("_", " ").replace(".", " ").strip()
    s = " ".join(s.split())                       # collapse runs of spaces
    # SHOUTED database headings read better as words: QUANTITYORDERED is not
    # a sentence, but neither should the axis shout it back at the reader.
    if s.isupper() and len(s) > 3:
        s = s.capitalize()
    if max_words:
        parts = s.split(" ")
        if len(parts) > max_words:
            s = " ".join(parts[:max_words]) + "..."
    # A name that carries a capital of its own - "pH", "mRNA", "EC", a
    # chemical symbol - is already written the way its field writes it.
    # Only capitalise what is plainly a lower-case phrase.
    if s[1:] != s[1:].lower():
        return s
    return s[:1].upper() + s[1:] if s else s


def wrap(text, width=28):
    """Wrap a label onto as few lines as will hold it."""
    return "\n".join(textwrap.wrap(str(text), width=width)) or str(text)


def _tidy_index(idx, width=None):
    out = [tidy(i) for i in idx]
    if width:
        out = [wrap(o, width) for o in out]
    return out


def _long(labels, limit=14):
    """True when these labels want horizontal bars rather than rotation."""
    return max((len(str(l)) for l in labels), default=0) > limit


# --------------------------------------------------------------------------
# The layout contract
# --------------------------------------------------------------------------
def figure(width=10.5, height=6.0, **kw):
    """A figure and one axes, house defaults applied."""
    return plt.subplots(figsize=(width, height), **kw)


def finish(fig, title=None, subtitle=None, source=None, site=SITE,
           legend=None, note=None, left=0.055, right=0.965, gap=None):
    """Reserve the margins, then write into them. Never over the plot.

    This is the whole answer to the watermark landing on the data: the bands
    are measured in inches, the plot is given the space that is left, and the
    text is placed in the space that was reserved for it.

    legend
        Either a list of matplotlib handles, or a list of ``(label, colour)``
        pairs, which is usually easier at the call site.
    """
    H, W = fig.get_figheight(), fig.get_figwidth()

    # Wrap the title block to the width actually available, or a long
    # subtitle runs off the right edge and loses its last words.
    avail_in = max(2.0, (right - left) * W)
    title_lines = (textwrap.wrap(title, int(avail_in * 8.6)) if title else [])
    sub_lines = (textwrap.wrap(subtitle, int(avail_in * 12.4))
                 if subtitle else [])

    # Band heights in inches, so they do not change with figure size.
    top_in = 0.16                                  # breathing room
    if title:
        top_in += 0.14 + 0.34 * len(title_lines)   # accent rule + title
    if subtitle:
        top_in += 0.24 * len(sub_lines)
    if legend:
        top_in += 0.34
    top_in += 0.18

    # Equal-aspect axes (pies, maps) cannot be shrunk by tight_layout, so
    # their own titles ride up into the band reserved above them. Reserve
    # the extra room here rather than leaving the title block to collide.
    if gap is None:
        titled = any(a.get_title() for a in fig.axes)
        fixed = any(a.get_aspect() == 1.0 for a in fig.axes)
        gap = 0.34 if (titled and fixed) else 0.0
    top_in += gap
    bottom_in = 0.42 if (source or site or note) else 0.10
    if note:
        bottom_in += 0.22

    top = 1.0 - top_in / H
    bottom = bottom_in / H
    try:
        fig.tight_layout(rect=(left, bottom, right, top))
    except Exception:                              # some 3-D axes refuse
        fig.subplots_adjust(left=left + 0.02, right=right,
                            top=top, bottom=bottom + 0.06)

    y = 1.0 - 0.16 / H                             # walk down from the top
    if title:
        fig.add_artist(Rectangle((left, y - 0.075 / H), 0.048, 0.011,
                                 facecolor=palette()[0], edgecolor="none",
                                 transform=fig.transFigure))
        y -= (0.14 + 0.30) / H
        for ln in title_lines:
            fig.text(left, y, ln, fontsize=16.5, fontweight="bold",
                     color=INK, va="top")
            y -= 0.34 / H
        y += 0.34 / H - 0.06 / H
    if subtitle:
        y -= 0.26 / H
        for ln in sub_lines:
            fig.text(left, y, ln, fontsize=11.5, color=INK_2, va="top")
            y -= 0.24 / H
        y += 0.24 / H - 0.04 / H
    if legend:
        y -= 0.30 / H
        handles = []
        for item in legend:
            if isinstance(item, (tuple, list)) and len(item) == 2:
                lab, col = item
                handles.append(Line2D([], [], marker="o", ls="", ms=10,
                                      color=col, mec=SURFACE, mew=2,
                                      label=lab))
            else:
                handles.append(item)
        fig.legend(handles=handles, loc="upper left",
                   bbox_to_anchor=(left - 0.023, y + 0.26 / H),
                   ncol=min(len(handles), 5), frameon=False,
                   fontsize=11, handletextpad=0.5, columnspacing=1.8)

    foot = 0.20 / H
    if note:
        fig.text(left, foot + 0.22 / H, note, fontsize=9.5, color=INK_2)
    if source:
        fig.text(left, foot, source, fontsize=9.5, color=MUTED)
    if site:
        fig.text(right, foot, site, fontsize=9.5, color=MUTED, ha="right")
    return fig


def _grid(ax, axis="y"):
    ax.grid(True, axis=axis, color=GRID, lw=1.0, ls="-")
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left" if axis == "y" else "bottom"].set_visible(False)
    keep = "bottom" if axis == "y" else "left"
    ax.spines[keep].set_color(GRID)
    ax.tick_params(length=0)


def _annotate(ax, rects, values, horizontal, fmt="{:g}", pad=0.01):
    """Label the end of every bar, outside it, so nothing is ever clipped."""
    span = (ax.get_xlim() if horizontal else ax.get_ylim())
    room = (span[1] - span[0]) * pad
    for r, v in zip(rects, values):
        if horizontal:
            ax.text(r.get_width() + room, r.get_y() + r.get_height() / 2,
                    fmt.format(v), va="center", ha="left",
                    fontsize=11.5, color=INK_2)
        else:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + room,
                    fmt.format(v), ha="center", va="bottom",
                    fontsize=11.5, color=INK_2)


def label_bars(ax, total=None, pct=False, fmt="{:g}", fontsize=11.5,
               color=INK_2, skip_zero=True, horizontal=None, pad=0.012,
               collide=True):
    """Label bars on any axes - including ones seaborn or pandas drew.

    This exists because the usual hand-rolled version goes wrong in three
    ways at once: it labels the zero-height bars that a sparse `hue` leaves
    behind, it writes the count and the percentage as two separate rotated
    annotations that land on each other, and it never checks whether the
    labels actually fit.

    Here: empty bars get nothing, count and share are one string, and if two
    labels would overlap the later one is dropped rather than drawn on top.
    Anything dropped is still readable from the axis, so nothing is lost.

    total
        Denominator for percentages. Defaults to the sum of the bar heights,
        which is what "share of responses" almost always means - passing
        ``len(df)`` instead is the classic way to get percentages that do
        not add to 100.
    """
    rects = [p for p in ax.patches if hasattr(p, "get_height")]
    if not rects:
        return ax
    if horizontal is None:                     # infer from the bars' shape
        horizontal = bool(np.median([r.get_width() for r in rects]) >
                          np.median([r.get_height() for r in rects]))
    values = [(r.get_width() if horizontal else r.get_height()) for r in rects]
    if total is None:
        total = sum(v for v in values if v) or 1

    span = (ax.get_xlim() if horizontal else ax.get_ylim())
    room = (span[1] - span[0]) * pad
    placed = []
    fig = ax.figure
    fig.canvas.draw()                          # extents need a renderer

    for r, v in zip(rects, values):
        if skip_zero and not v:
            continue
        s = fmt.format(v)
        if pct:
            s += f"  ({100.0 * v / total:.1f}%)"
        if horizontal:
            t = ax.text(r.get_width() + room,
                        r.get_y() + r.get_height() / 2, s, va="center",
                        ha="left", fontsize=fontsize, color=color)
        else:
            t = ax.text(r.get_x() + r.get_width() / 2,
                        r.get_height() + room, s, ha="center", va="bottom",
                        fontsize=fontsize, color=color)
        if not collide:
            placed.append(t)
            continue
        try:
            box = t.get_window_extent(fig.canvas.get_renderer())
        except Exception:
            placed.append(t)
            continue
        box = box.expanded(1.06, 1.06)
        if any(box.overlaps(b) for b in placed):
            t.remove()                          # would collide - let it go
        else:
            placed.append(box)
    return ax


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------
def bars(labels, values, ax=None, color=None, horizontal=None, label=True,
         fmt="{:g}", sort=True, width=0.62):
    """One series of categories. Flips horizontal when the names are long."""
    labels = [tidy(l) for l in labels]
    values = list(values)
    if sort:
        order = np.argsort(values)[::-1]
        labels = [labels[i] for i in order]
        values = [values[i] for i in order]
    if horizontal is None:
        horizontal = _long(labels)
    if ax is None:
        _, ax = figure(10.5, max(3.4, 0.52 * len(labels) + 2.0)
                       if horizontal else 6.0)
    col = color or palette()[0]

    if horizontal:
        pos = np.arange(len(labels))[::-1]         # biggest at the top
        rects = ax.barh(pos, values, height=width, color=col)
        ax.set_yticks(pos)
        ax.set_yticklabels(labels)
        ax.set_xlim(0, max(values) * 1.16)
        _grid(ax, "x")
    else:
        pos = np.arange(len(labels))
        rects = ax.bar(pos, values, width=width, color=col)
        ax.set_xticks(pos)
        ax.set_xticklabels([wrap(l, 14) for l in labels])
        ax.set_ylim(0, max(values) * 1.14)
        _grid(ax, "y")
    if label:
        _annotate(ax, rects, values, horizontal, fmt)
    return ax


def counts(df, column, ax=None, color=None, horizontal=None, pct=True,
           top=None, dropna=True, order=None, **kw):
    """Frequency of one survey column - the commonest chart on the forum."""
    s = df[column].dropna() if dropna else df[column]
    vc = s.value_counts()
    if top:
        vc = vc.head(int(top))
    if order is not False:                         # scale order beats count
        vc = vc.reindex(order or scale_order(vc.index)).dropna()
    total = int(vc.sum())
    fmt = "{:g}"
    kw.setdefault("sort", order is False)
    ax = bars(list(vc.index), list(vc.values), ax=ax, color=color,
              horizontal=horizontal, fmt=fmt, **kw)
    if pct:                                        # count and share together
        rects = [p for p in ax.patches]
        vals = list(vc.values)
        horiz = ax.get_yticklabels() and len(rects) and \
            rects[0].get_width() != rects[0].get_height() and \
            ax.get_xlim()[1] > ax.get_ylim()[1]
        for r, v in zip(rects, vals):
            txt = f"{v:g}  ({100 * v / total:.1f}%)"
            if r.get_width() > r.get_height():     # horizontal bar
                r_x = r.get_width() + (ax.get_xlim()[1] - ax.get_xlim()[0]) * .01
                ax.text(r_x, r.get_y() + r.get_height() / 2, txt,
                        va="center", ha="left", fontsize=11.5, color=INK_2)
            else:
                r_y = r.get_height() + (ax.get_ylim()[1] - ax.get_ylim()[0]) * .01
                ax.text(r.get_x() + r.get_width() / 2, r_y, txt,
                        ha="center", va="bottom", fontsize=11.5, color=INK_2)
        for t in list(ax.texts):                   # drop the plain duplicates
            if t.get_text().replace(".", "").isdigit():
                t.remove()
    return ax


def grouped_bars(df, column, by, ax=None, cols=None, pct=False, width=0.78,
                 order=None, by_order=None, max_groups=6):
    """Counts of `column` split by `by` - replaces seaborn countplot loops.

    Guards the failure mode that makes these charts unreadable: when `by` has
    many levels and the cross-tab is mostly zeros, every bar becomes a
    hairline. Past `max_groups` levels the tail is folded into "Other", and a
    mostly-empty table is reported as such - `heatmap(pd.crosstab(...))`
    shows a sparse cross-tab far better than grouped bars ever will.
    """
    ct = pd.crosstab(df[column], df[by])
    ct = ct.reindex(index=order or scale_order(ct.index),
                    columns=by_order or scale_order(ct.columns))
    ct = ct.fillna(0)

    if len(ct.columns) > max_groups:               # fold the tail into Other
        keep = ct.sum().nlargest(int(max_groups) - 1).index.tolist()
        other = ct.drop(columns=keep).sum(axis=1)
        ct = ct[keep]
        ct["Other"] = other
    sparsity = float((ct.values == 0).mean())
    if sparsity > 0.5:
        import warnings
        warnings.warn(
            f"{sparsity:.0%} of this cross-tab is zero, so the bars will be "
            "thin and mostly empty. heatmap(pd.crosstab(df[column], df[by])) "
            "reads much better for sparse tables.", stacklevel=2)
    if pct:
        ct = (ct.T / ct.sum(axis=1).replace(0, np.nan)).T * 100
    cats = _tidy_index(ct.index)
    groups = [tidy(g) for g in ct.columns]
    cols = cols or colors(len(groups))
    horizontal = _long(cats)

    if ax is None:
        h = max(3.6, 0.42 * len(cats) * len(groups) + 2.2)
        _, ax = figure(11.0, h if horizontal else 6.2)

    n = len(groups)
    step = width / n
    base = np.arange(len(cats))
    for i, (g, col) in enumerate(zip(ct.columns, cols)):
        off = (i - (n - 1) / 2) * step
        vals = ct[g].values
        if horizontal:
            ax.barh(base[::-1] + off, vals, height=step * 0.9, color=col,
                    label=tidy(g))
        else:
            ax.bar(base + off, vals, width=step * 0.9, color=col,
                   label=tidy(g))
    if horizontal:
        ax.set_yticks(base[::-1])
        ax.set_yticklabels(cats)
        _grid(ax, "x")
    else:
        ax.set_xticks(base)
        ax.set_xticklabels([wrap(c, 14) for c in cats])
        _grid(ax, "y")
    return ax, list(zip(groups, cols))


def likert(df, questions, order, ax=None, cols=None, labels=None):
    """Diverging stacked bars - the right chart for agree/disagree scales.

    `order` runs from most negative to most positive. Negative categories are
    laid to the left of a zero line and positive to the right, so the balance
    of opinion is the shape of the chart rather than something to compute.
    """
    order = list(order)
    n = len(order)
    mid = n // 2
    if cols is None:
        d = DIVERGING["blue_red"]
        idx = np.linspace(0, len(d) - 1, n).round().astype(int)
        cols = [d[i] for i in idx][::-1]
    labels = labels or [tidy(q) for q in questions]

    rows = []
    for q in questions:
        vc = df[q].value_counts()
        tot = vc.sum() or 1
        rows.append([100.0 * vc.get(o, 0) / tot for o in order])
    data = np.array(rows)

    if ax is None:
        _, ax = figure(11.5, max(3.2, 0.62 * len(questions) + 2.2))

    # Start each row so that the midpoint of the middle category sits at 0.
    if n % 2:
        starts = -(data[:, :mid].sum(axis=1) + data[:, mid] / 2)
    else:
        starts = -data[:, :mid].sum(axis=1)

    y = np.arange(len(questions))[::-1]
    left = starts.copy()
    for j, (o, c) in enumerate(zip(order, cols)):
        ax.barh(y, data[:, j], left=left, height=0.62, color=c,
                label=tidy(o), edgecolor=SURFACE, linewidth=2)
        for yy, ll, vv in zip(y, left, data[:, j]):
            if vv >= 7:                            # only when it fits
                ax.text(ll + vv / 2, yy, f"{vv:.0f}%", ha="center",
                        va="center", fontsize=9.5, color=SURFACE,
                        fontweight="bold")
        left = left + data[:, j]

    ax.axvline(0, color=INK_2, lw=1.2, zorder=5)
    ax.set_yticks(y)
    ax.set_yticklabels([wrap(l, 34) for l in labels])
    ax.set_xlabel("Share of responses (%)")
    _grid(ax, "x")
    ax.set_axisbelow(True)
    return ax, list(zip([tidy(o) for o in order], cols))


def _readable_on(hex_color):
    """Ink or white, whichever is legible on this fill."""
    r, g, b = mpl.colors.to_rgb(hex_color)

    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    lum = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return SURFACE if lum < 0.42 else INK


def donut(labels, values, ax=None, cols=None, hole=0.58, fmt="{pct:.1f}%",
          explode=None, startangle=90, labels_outside=False, centre=None,
          centre_note="Responses", counterclock=False, shadow=False):
    """Part-to-whole. Deliberately flexible, because the variants are the point.

    `hole=0` gives a plain pie, `explode=0.06` pulls every wedge out (or pass
    a sequence for individual offsets), `labels_outside=True` moves the values
    beyond the rim with leader lines for thin slices. Label colour is chosen
    per wedge for contrast, so a value never disappears into a pale fill.
    """
    labels = [tidy(l) for l in labels]
    values = [float(v) for v in values]
    cols = cols or colors(len(values))
    if ax is None:
        _, ax = figure(7.4, 6.0)
    total = float(sum(values)) or 1.0

    if explode is None:
        expl = None
    elif np.isscalar(explode):
        expl = [float(explode)] * len(values)
    else:
        expl = list(explode)

    wedges, _ = ax.pie(
        values, colors=cols, startangle=startangle,
        counterclock=counterclock, explode=expl, shadow=shadow,
        wedgeprops=dict(width=(1 - hole) if hole else None,
                        edgecolor=SURFACE, linewidth=2.5))
    ax.set(aspect="equal")

    for i, (w, v) in enumerate(zip(wedges, values)):
        if not v:
            continue
        ang = np.deg2rad((w.theta1 + w.theta2) / 2)
        text = fmt.format(pct=100 * v / total, value=v, label=labels[i])
        share = v / total
        if labels_outside or share < 0.05:         # too thin to hold a label
            x, y = np.cos(ang), np.sin(ang)
            ax.annotate(text, xy=(x * 0.98, y * 0.98),
                        xytext=(x * 1.28, y * 1.18),
                        ha="left" if x >= 0 else "right", va="center",
                        fontsize=10.5, color=INK_2,
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
        else:
            off = (expl[i] if expl else 0)
            r = (1 - (1 - hole) / 2) if hole else 0.62
            ax.text((r + off) * np.cos(ang), (r + off) * np.sin(ang), text,
                    ha="center", va="center", fontsize=10.5,
                    color=_readable_on(cols[i % len(cols)]),
                    fontweight="bold")

    if hole and centre is not False:
        ax.text(0, 0.08, centre if centre is not None else f"{total:,.0f}",
                ha="center", va="center", fontsize=22, fontweight="bold",
                color=INK)
        if centre_note:
            ax.text(0, -0.14, centre_note, ha="center", va="center",
                    fontsize=10.5, color=MUTED)
    if labels_outside:
        ax.set_xlim(-1.55, 1.55)
        ax.set_ylim(-1.35, 1.35)
    return ax, list(zip(labels, cols))


def dumbbell(labels, left_values, right_values, ax=None,
             left_name="Before", right_name="After", cols=None, fmt="{:+.1f}"):
    """Two comparable measures per category, on ONE axis.

    Use this wherever a dual-axis chart is tempting: the connector's length is
    the difference, so the quantity of interest is read directly.
    """
    labels = [tidy(l) for l in labels]
    a, b = np.asarray(left_values, float), np.asarray(right_values, float)
    gap = b - a
    order = np.argsort(gap)
    labels = [labels[i] for i in order]
    a, b, gap = a[order], b[order], gap[order]
    c1, c2 = (cols or palette()[:2])[:2]

    if ax is None:
        _, ax = figure(11.0, max(3.4, 0.58 * len(labels) + 2.2))
    lo = min(a.min(), b.min())
    hi = max(a.max(), b.max())
    room = (hi - lo) * 0.18
    ax.set_xlim(lo - room * 0.4, hi + room * 1.5)

    y = np.arange(len(labels))
    for i in range(len(labels)):
        if i % 2 == 0:
            ax.add_patch(Rectangle((ax.get_xlim()[0], i - 0.5),
                                   ax.get_xlim()[1] - ax.get_xlim()[0], 1.0,
                                   facecolor=BAND, edgecolor="none", zorder=0))
        ax.plot([a[i], b[i]], [i, i], color=GRID, lw=7,
                solid_capstyle="round", zorder=2)
        ax.plot(a[i], i, "o", ms=12, color=c1, mec=SURFACE, mew=2.5, zorder=4)
        ax.plot(b[i], i, "o", ms=12, color=c2, mec=SURFACE, mew=2.5, zorder=4)
        ax.text(max(a[i], b[i]) + room * 0.22, i, fmt.format(gap[i]),
                va="center", ha="left", fontsize=10.5, fontweight="bold",
                color=INK_2, zorder=5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_ylim(-0.7, len(labels) - 0.3)
    _grid(ax, "x")
    ax.set_axisbelow(False)
    return ax, [(left_name, c1), (right_name, c2)]


def line(df, x=None, ys=None, ax=None, cols=None, markers=False,
         label_ends=True):
    """Trends over time or an ordered axis, with the ends labelled."""
    ys = list(ys or [c for c in df.columns if c != x])
    xs = df[x] if x else df.index
    cols = cols or colors(len(ys))
    if ax is None:
        _, ax = figure(10.8, 6.0)
    for c, col in zip(ys, cols):
        ax.plot(xs, df[c], color=col, lw=2.2,
                marker="o" if markers else None, ms=6,
                mec=SURFACE, mew=1.5)
        if label_ends:
            ax.text(list(xs)[-1], list(df[c])[-1], "  " + tidy(c),
                    va="center", ha="left", fontsize=10.5, color=col,
                    fontweight="bold")
    if label_ends:                                  # room for the end labels
        ax.margins(x=0.16)
    _grid(ax, "y")
    return ax, list(zip([tidy(c) for c in ys], cols))


def scatter(df, x, y, hue=None, ax=None, cols=None, fit=False, size=46):
    """Two continuous measures, optionally split by a category."""
    if ax is None:
        _, ax = figure(9.6, 6.2)
    # A dense cloud drawn at full opacity is a solid blob; thin the marks
    # rather than the data so the shape of the distribution survives.
    n_pts = len(df.dropna(subset=[x, y]))
    if n_pts > 400:
        size = min(size, max(10, 46 * (400.0 / n_pts) ** 0.5))
        alpha, edge = 0.45, 0.0
    else:
        alpha, edge = 0.9, 1.4
    if hue is None:
        ax.scatter(df[x], df[y], s=size, color=palette()[0],
                   edgecolor=SURFACE, linewidth=edge, alpha=alpha)
        legend = None
    else:
        groups = list(pd.unique(df[hue].dropna()))
        # Past three series the all-pairs separation guarantee lapses, and a
        # scatter puts every pair side by side - so cap it here.
        if len(groups) > 3:
            import warnings
            warnings.warn(
                f"{len(groups)} groups in a scatter - only the first 3 slots "
                "are separable when every pair is adjacent. Consider "
                "panels() instead.", stacklevel=2)
        cols = cols or colors(len(groups))
        for g, col in zip(groups, cols):
            m = df[hue] == g
            ax.scatter(df.loc[m, x], df.loc[m, y], s=size, color=col,
                       edgecolor=SURFACE, linewidth=edge, alpha=alpha,
                       label=tidy(g))
        legend = list(zip([tidy(g) for g in groups], cols))
    if fit:
        ok = df[[x, y]].dropna()
        m, b = np.polyfit(ok[x], ok[y], 1)
        xx = np.linspace(ok[x].min(), ok[x].max(), 100)
        ax.plot(xx, m * xx + b, color=INK_2, lw=1.8, ls="--", zorder=1)
        r = float(np.corrcoef(ok[x], ok[y])[0, 1])
        ax.text(0.985, 0.03, f"r = {r:.2f}", transform=ax.transAxes,
                ha="right", fontsize=10.5, color=INK_2)
    ax.set_xlabel(tidy(x))
    ax.set_ylabel(tidy(y))
    _grid(ax, "y")
    ax.grid(True, axis="x", color=GRID, lw=1.0)
    return ax, legend


def heatmap(matrix, ax=None, ramp="blue", fmt="{:.2f}", diverging=None,
            cbar=True, labels=True, order=True):
    """A matrix - correlations, or a cross-tab. One hue, light to dark.

    A cross-tab of survey answers arrives in alphabetical order, which puts
    "Strongly agree" between "Disagree" and "Strongly disagree"; `order=True`
    restores the scale. Pass `order=False` to keep the matrix as given, which
    is what you want for a correlation matrix.
    """
    m = matrix if isinstance(matrix, pd.DataFrame) else pd.DataFrame(matrix)
    if order:
        m = m.reindex(index=scale_order(m.index),
                      columns=scale_order(m.columns))
    steps = DIVERGING[diverging] if diverging else SEQUENTIAL[ramp]
    cmap = mpl.colors.LinearSegmentedColormap.from_list("tssfl", steps)
    if ax is None:
        _, ax = figure(max(7.0, 0.72 * len(m.columns) + 3.4),
                       max(5.0, 0.62 * len(m.index) + 2.6))
    vmax = float(np.nanmax(np.abs(m.values))) if diverging else None
    im = ax.imshow(m.values, cmap=cmap, aspect="auto",
                   vmin=-vmax if diverging else None,
                   vmax=vmax if diverging else None)
    ax.set_xticks(range(len(m.columns)))
    ax.set_xticklabels([wrap(tidy(c), 12) for c in m.columns])
    ax.set_yticks(range(len(m.index)))
    ax.set_yticklabels([tidy(i) for i in m.index])
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(len(m.columns) + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(m.index) + 1) - 0.5, minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2.5)
    ax.grid(which="major", visible=False)
    if labels:
        lim = np.nanmax(np.abs(m.values)) or 1
        for i in range(len(m.index)):
            for j in range(len(m.columns)):
                v = m.values[i, j]
                if pd.isna(v):
                    continue
                # white on the dark end, ink on the light end
                dark = abs(v) / lim > 0.55 if diverging else v / lim > 0.55
                ax.text(j, i, fmt.format(v), ha="center", va="center",
                        fontsize=9.5, color=SURFACE if dark else INK_2)
    if cbar:
        cb = ax.figure.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        cb.outline.set_visible(False)
        cb.ax.tick_params(length=0, labelsize=9.5, colors=MUTED)
    return ax


def distribution(series, ax=None, bins=24, color=None, rug=False, mean=True):
    """One continuous variable: histogram, with the mean marked."""
    s = pd.Series(series).dropna()
    if ax is None:
        _, ax = figure(9.6, 5.6)
    col = color or palette()[0]
    ax.hist(s, bins=int(bins), color=col, edgecolor=SURFACE, linewidth=1.2)
    if mean:
        mu = s.mean()
        ax.axvline(mu, color=INK_2, lw=1.8, ls="--")
        ax.text(mu, ax.get_ylim()[1] * 0.97, f"  mean {mu:,.1f}",
                va="top", ha="left", fontsize=10.5, color=INK_2)
    if rug:
        ax.plot(s, np.full(len(s), 0), "|", color=col, alpha=0.5, ms=8)
    ax.set_xlabel(tidy(getattr(s, "name", "") or ""))
    ax.set_ylabel("Count")
    _grid(ax, "y")
    return ax


def boxes(df, columns=None, by=None, ax=None, cols=None):
    """Compare distributions across categories, without hiding the spread."""
    if by is not None:
        groups = [(g, sub.dropna()) for g, sub in df.groupby(by)[columns]]
        data = [v.values for _, v in groups]
        names = [tidy(g) for g, _ in groups]
    else:
        columns = list(columns or df.select_dtypes("number").columns)
        data = [df[c].dropna().values for c in columns]
        names = [tidy(c) for c in columns]
        # Only a concern when the boxes are different variables sharing one
        # axis. With `by`, every box is the same variable in a different
        # group, and one group being far tighter than another is the finding,
        # not a scale problem.
        spans = [float(np.nanmax(d)) - float(np.nanmin(d))
                 for d in data if len(d)]
        if spans and max(spans) > 100 * max(min(spans), 1e-9):
            import warnings
            warnings.warn(
                "these columns differ by more than 100x in range - on one "
                "axis the small ones collapse to a line. Use panels(), or "
                "plot them separately.", stacklevel=2)
    cols = cols or colors(len(data))
    if ax is None:
        _, ax = figure(max(8.0, 1.5 * len(data) + 3.0), 5.8)
    bp = ax.boxplot(data, patch_artist=True, widths=0.52,
                    medianprops=dict(color=SURFACE, linewidth=2),
                    whiskerprops=dict(color=MUTED, linewidth=1.4),
                    capprops=dict(color=MUTED, linewidth=1.4),
                    flierprops=dict(marker="o", markersize=4,
                                    markerfacecolor=MUTED,
                                    markeredgecolor="none", alpha=0.6))
    for patch, col in zip(bp["boxes"], cols):
        patch.set_facecolor(col)
        patch.set_edgecolor("none")
    ax.set_xticks(range(1, len(names) + 1))
    ax.set_xticklabels([wrap(n, 14) for n in names])
    _grid(ax, "y")
    return ax


def panels(n, ncols=3, width=11.5, height=3.1, **kw):
    """Small multiples - the honest answer to "too many series in one chart"."""
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(width, height * nrows), **kw)
    axes = np.atleast_1d(axes).ravel()
    for a in axes[n:]:
        a.set_visible(False)
    return fig, axes[:n]


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------
_TABLE_CSS = """
<style>
.tssfl-t{{border-collapse:separate;border-spacing:0;font-family:
 'Nimbus Sans',Helvetica,Arial,system-ui,sans-serif;font-size:15.5px;
 color:{ink};width:100%;margin:14px 0 6px 0;
 box-shadow:0 1px 2px rgba(15,23,42,.06);border-radius:10px;overflow:hidden}}
.tssfl-t caption{{caption-side:top;text-align:left;font-weight:700;
 font-size:17px;color:{ink};padding:0 0 4px 2px}}
.tssfl-t thead th{{background:{head};color:#fff;font-weight:600;
 text-align:left;padding:12px 16px;white-space:nowrap;border:0;
 font-size:15px}}
.tssfl-t thead th.num,.tssfl-t td.num{{text-align:right;
 font-variant-numeric:tabular-nums}}
.tssfl-t tbody td{{padding:11px 16px;border-top:1px solid {grid}}}
.tssfl-t tbody tr:nth-child(even){{background:{band}}}
.tssfl-t tbody tr:hover{{background:{hover}}}
.tssfl-t tfoot td{{padding:10px 14px;border-top:2px solid {grid};
 font-weight:700;background:{band}}}
.tssfl-cap{{font-size:12.5px;color:{muted};margin:0 0 16px 2px}}
</style>
"""


def table(df, title=None, source=None, site=SITE, index=False, head=None,
          fmt=None, total=False, highlight=None, max_rows=60,
          as_html=False):
    """A DataFrame as an HTML table that is actually pleasant to read.

    Numeric columns are right-aligned with tabular figures so digits line up,
    which is the one place `tabular-nums` genuinely belongs.
    """
    d = df.copy()
    if index:
        d = d.reset_index()
    truncated = len(d) > max_rows
    if truncated:
        d = d.head(int(max_rows))

    head = head or palette()[0]
    css = _TABLE_CSS.format(ink=INK, head=head, grid=GRID, band=BAND,
                            hover="#eef4ff", muted=MUTED)

    def cell(v, col):
        if fmt and col in fmt:
            try:
                return fmt[col].format(v)
            except Exception:
                return str(v)
        if isinstance(v, float):
            return f"{v:,.2f}"
        if isinstance(v, (int, np.integer)):
            return f"{v:,}"
        return "" if pd.isna(v) else str(v)

    numeric = {c for c in d.columns
               if pd.api.types.is_numeric_dtype(d[c])}
    out = [css, '<table class="tssfl-t">']
    if title:
        out.append(f"<caption>{title}</caption>")
    out.append("<thead><tr>")
    for c in d.columns:
        cls = ' class="num"' if c in numeric else ""
        out.append(f"<th{cls}>{tidy(c)}</th>")
    out.append("</tr></thead><tbody>")
    for _, row in d.iterrows():
        mark = ""
        if highlight is not None and highlight(row):
            mark = ' style="background:#fff7ed"'
        out.append(f"<tr{mark}>")
        for c in d.columns:
            cls = ' class="num"' if c in numeric else ""
            out.append(f"<td{cls}>{cell(row[c], c)}</td>")
        out.append("</tr>")
    out.append("</tbody>")
    if total:
        out.append("<tfoot><tr>")
        for i, c in enumerate(d.columns):
            if c in numeric:
                out.append(f'<td class="num">{cell(d[c].sum(), c)}</td>')
            else:
                out.append(f"<td>{'Total' if i == 0 else ''}</td>")
        out.append("</tr></tfoot>")
    out.append("</table>")

    foot = []
    if truncated:
        foot.append(f"Showing {max_rows:,} of {len(df):,} rows.")
    if source:
        foot.append(source)
    if site:
        foot.append(site)
    if foot:
        out.append(f'<p class="tssfl-cap">{"  ·  ".join(foot)}</p>')
    html = "".join(out)
    return html if as_html else show_html(html)


def crosstab(df, rows, cols, pct=None, title=None, **kw):
    """A cross-tabulation, optionally as row or column percentages."""
    ct = pd.crosstab(df[rows], df[cols], margins=True, margins_name="All")
    if pct in ("row", "index"):
        ct = ct.div(ct["All"], axis=0) * 100
    elif pct in ("col", "column", "columns"):
        ct = ct.div(ct.loc["All"], axis=1) * 100
    ct.index.name = tidy(rows)
    ct.columns.name = tidy(cols)
    f = {c: "{:.1f}%" for c in ct.columns} if pct else None
    return table(ct.round(1), title=title or
                 f"{tidy(rows)} by {tidy(cols)}", index=True, fmt=f, **kw)


def summary(df, columns=None, title="Summary statistics", **kw):
    """describe(), rearranged into something you would put in a report."""
    d = df[list(columns)] if columns else df.select_dtypes("number")
    s = pd.DataFrame({
        "Variable": [tidy(c) for c in d.columns],
        "N": d.notna().sum().values,
        "Mean": d.mean().values,
        "SD": d.std().values,
        "Min": d.min().values,
        "Median": d.median().values,
        "Max": d.max().values,
    })
    return table(s, title=title, fmt={c: "{:,.2f}" for c in
                                      ("Mean", "SD", "Min", "Median", "Max")},
                 **kw)


def show_html(html):
    """Display HTML in SageCell, a notebook, or fall back to returning it."""
    try:
        from IPython.display import HTML, display
        display(HTML(html))
        return None
    except Exception:
        return html


# Applying the style on load is the point - one line in a cell and every
# chart in it looks right. Call use("bold") or use("vivid") to change it.
use("tssfl")
