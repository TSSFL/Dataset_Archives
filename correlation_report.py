# -*- coding: utf-8 -*-
"""Correlations, group comparison and PCA for a table of measurements.

Logic only - the data lives wherever you keep it. Run it from a SageMathCell
by naming your data first, then loading this file:

    SHEET_ID = "<the sheet id from its URL>"

    load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/correlation_report.py")

Any of these will do, whichever suits where the data actually sits:

    SHEET_ID   a Google Sheets id; the sheet must be link-readable
    SHEET_NAME the tab, if not the first one                  (optional)
    CSV_URL    a direct CSV link - Dropbox, KoBoToolbox, a web server
    XLSX_URL   a direct .xlsx link

**No data location appears in this file, and none ever should.**

WHAT IT PRODUCES
----------------
1. Correlation_Report.html / .pdf   the whole analysis, charts included
2. Correlation_Matrices.xlsx        one sheet per group, plus the pooled one
3. Summary_Statistics.csv           n, mean, SD, min, median, max per group
4. Strongest_Correlations.csv       every pair, r, p and n, strongest first

WHAT IT ASSUMES ABOUT THE SHEET
-------------------------------
A block of numeric columns - the parameters - and, optionally, a column to
the left holding a label only on the row where a new group starts, the way a
person writes a sheet by hand:

    Petrol St |    | T    | pH  | ...      <- the header names the first group
              | 1  | 29.8 | 6.9 | ...
              | 2  | 30.4 | 7.0 | ...
    Dumping   |    |      |     |          <- a bare label starts a new group
              | 1  | 30.1 | 7.3 | ...

Name that column as GROUP_COL and the groups are carried down the rows for
you; the separator rows are dropped. With no GROUP_COL the whole table is one
group and the group comparison is skipped.
"""

_needed = ("SHEET_ID", "CSV_URL", "XLSX_URL")
if not any(n in globals() for n in _needed):
    raise NameError(
        "correlation_report.py does not carry data locations - define one in "
        "the cell before loading it.\n\n"
        '    SHEET_ID = "<the sheet id from its URL>"\n'
        "  or\n"
        '    CSV_URL  = "https://www.dropbox.com/scl/fi/.../data.csv?dl=1"\n'
    )

import base64
import datetime
import io
import itertools
import urllib.parse
import urllib.request

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from weasyprint import HTML

load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tssfl_style.py")

use("tssfl")

# --- TSSFL brand --------------------------------------------------------
BLUE, EMERALD, AMBER = "#096EFF", "#10B981", "#f59e0b"
ROSE, VIOLET = "#e11d48", "#7c3aed"

# --- settings the cell may override -------------------------------------
TITLE = globals().get("TITLE", "Correlation report")
SUBJECT = globals().get("SUBJECT", "")
SHEET_NAME = globals().get("SHEET_NAME", "")
GROUP_COL = globals().get("GROUP_COL", "")
# A hand-written sheet names the first group in the column header itself and
# then labels only the later ones. Whatever the header says is the default.
FIRST_GROUP = globals().get("FIRST_GROUP", "")
PARAMETERS = globals().get("PARAMETERS", None)
UNITS = globals().get("UNITS", {})
NAMES = globals().get("NAMES", {})
ALPHA = float(globals().get("ALPHA", 0.05))
# Correlations below this are noise for reporting purposes; they still appear
# in the matrix and the CSV, just not in the "what actually correlates" list.
MIN_R = float(globals().get("MIN_R", 0.30))

# Chemical symbols and the two field measurements, spelled out. Anything not
# listed keeps the column name it arrived with.
DEFAULT_NAMES = {
    "T": "Temperature", "Temp": "Temperature",
    "pH": "pH", "EC": "Electrical conductivity",
    "TDS": "Total dissolved solids", "DO": "Dissolved oxygen",
    "Cd": "Cadmium", "Pb": "Lead", "Cr": "Chromium", "Cu": "Copper",
    "Zn": "Zinc", "Fe": "Iron", "Mn": "Manganese", "Ni": "Nickel",
    "As": "Arsenic", "Hg": "Mercury", "Co": "Cobalt", "Al": "Aluminium",
}


def rnd(value, places=0):
    """round(), guaranteed to give back a plain Python float.

    This file is exec'd into the namespace it is loaded into, and on a
    SageMathCell that namespace has Sage's round(), which returns a
    RealDoubleElement. pandas keeps a column of those as objects, and an
    object column cannot be rounded, correlated or written out as a number.
    """
    return float(np.round(float(value), places))


def esc(value):
    """Text into HTML."""
    return (str("" if value is None else value)
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def full_name(col):
    """"Cd" -> "Cadmium (Cd)", so a reader who is not a chemist can follow."""
    long = NAMES.get(col, DEFAULT_NAMES.get(col, ""))
    return "%s (%s)" % (long, col) if long and long != col else str(col)


def axis_name(col):
    """A short axis label, with the unit if the cell supplied one."""
    unit = UNITS.get(col, "")
    return "%s (%s)" % (col, unit) if unit else str(col)


# =======================================================================
#  1. Read the data
# =======================================================================
def _read():
    if "CSV_URL" in globals():
        return pd.read_csv(io.BytesIO(urllib.request.urlopen(CSV_URL).read()))
    if "XLSX_URL" in globals():
        return pd.read_excel(io.BytesIO(urllib.request.urlopen(XLSX_URL).read()))
    url = ("https://docs.google.com/spreadsheets/d/" + SHEET_ID +
           "/gviz/tq?tqx=out:csv")
    if SHEET_NAME:
        url += "&sheet=" + urllib.parse.quote(SHEET_NAME)
    return pd.read_csv(io.BytesIO(urllib.request.urlopen(url).read()))


raw = _read()
raw.columns = [str(c).strip() for c in raw.columns]

# The parameters: every numeric column, unless the cell named them. A column
# pandas auto-named ("Unnamed: 1") is a sample number someone typed down the
# side of the sheet, not a measurement.
if PARAMETERS:
    PARAMS = [c for c in PARAMETERS if c in raw.columns]
    missing = [c for c in PARAMETERS if c not in raw.columns]
    if missing:
        raise KeyError("PARAMETERS not in the sheet: %s. It has: %s"
                       % (", ".join(missing), ", ".join(raw.columns)))
else:
    PARAMS = [c for c in raw.columns
              if not str(c).startswith("Unnamed:")
              and c != GROUP_COL
              and pd.api.types.is_numeric_dtype(pd.to_numeric(raw[c],
                                                              errors="coerce"))
              and pd.to_numeric(raw[c], errors="coerce").notna().sum()
              >= 0.5 * len(raw)]
if len(PARAMS) < 2:
    raise ValueError("need at least two numeric columns to correlate; found "
                     "%s" % (", ".join(PARAMS) or "none"))

data = raw.copy()
for c in PARAMS:
    data[c] = pd.to_numeric(data[c], errors="coerce")

# The group column, carried down. A row that is blank across every parameter
# is the separator that carried the label, and goes once it has been read.
if GROUP_COL and GROUP_COL in data.columns:
    label = data[GROUP_COL].astype(str).str.strip().replace(
        {"": np.nan, "nan": np.nan, "None": np.nan})
    data["Group"] = label.ffill().fillna(FIRST_GROUP or GROUP_COL)
    GROUPED = True
else:
    data["Group"] = TITLE
    GROUPED = False

data = data.dropna(subset=PARAMS, how="all").reset_index(drop=True)
GROUPS = [g for g in pd.unique(data["Group"]) if data["Group"].eq(g).sum() >= 3]
GROUPED = GROUPED and len(GROUPS) > 1

print("Read %d samples and %d parameters%s."
      % (len(data), len(PARAMS),
         "" if not GROUPED else " across %d groups: %s"
         % (len(GROUPS), ", ".join(str(g) for g in GROUPS))))


# =======================================================================
#  2. Correlations, with a p-value on every one
# =======================================================================
def p_value(r, n):
    """Two-sided p for a Pearson r, from the t distribution.

    scipy ships with Sage, but this file should not fall over on a plain
    Python kernel that lacks it, so the survival function is optional and the
    report says so rather than printing a number it could not compute.
    """
    if n < 3 or not np.isfinite(r) or abs(r) >= 1.0:
        return 0.0 if abs(r) >= 1.0 else np.nan
    try:
        from scipy import stats
    except ImportError:
        return np.nan
    t = abs(r) * np.sqrt((n - 2) / (1.0 - r * r))
    return float(2.0 * stats.t.sf(t, n - 2))


def pairs_of(frame, label):
    """Every pair of parameters, with r, p and n. Strongest first."""
    rows = []
    for a, b in itertools.combinations(PARAMS, 2):
        ok = frame[[a, b]].dropna()
        n = len(ok)
        if n < 3 or ok[a].nunique() < 2 or ok[b].nunique() < 2:
            continue
        r = float(np.corrcoef(ok[a], ok[b])[0, 1])
        rows.append({"Group": label, "Parameter 1": a, "Parameter 2": b,
                     "r": rnd(r, 3), "p": rnd(p_value(r, n), 4), "n": int(n)})
    out = pd.DataFrame(rows)
    return (out.reindex(out["r"].abs().sort_values(ascending=False).index)
            .reset_index(drop=True)) if len(out) else out


CORR = {"All samples": data[PARAMS].corr()}
if GROUPED:
    for g in GROUPS:
        CORR[str(g)] = data.loc[data["Group"] == g, PARAMS].corr()

all_pairs = pd.concat(
    [pairs_of(data, "All samples")]
    + ([pairs_of(data[data["Group"] == g], str(g)) for g in GROUPS]
       if GROUPED else []),
    ignore_index=True)

pooled = all_pairs[all_pairs["Group"] == "All samples"]
notable = pooled[(pooled["r"].abs() >= MIN_R)].copy()
significant = notable[notable["p"] <= ALPHA] if notable["p"].notna().any() \
    else notable


# =======================================================================
#  3. Charts
# =======================================================================
SRC = "Source: %s." % (SUBJECT or TITLE)
charts = []


def keep(fig, name):
    fig.savefig(name, dpi=150, facecolor=SURFACE)
    charts.append(name)
    return fig


# --- the correlation matrix ---------------------------------------------
# A correlation runs from -1 through nothing to +1, so it wears a diverging
# ramp with a neutral middle, fixed to the full scale - never a sequential
# one, which would paint "no relationship" as a colour.
n_mat = 1 + (len(GROUPS) if GROUPED else 0)
fig, axes = panels(n_mat, ncols=min(n_mat, 2), width=6.6 * min(n_mat, 2),
                   height=5.0)
for ax_i, (name, matrix) in zip(axes, CORR.items()):
    # No colour bar: every cell already carries its number, the scale is
    # fixed at -1 to +1 on all four panels, and four identical bars would be
    # four times the ink for nothing.
    heatmap(matrix, ax=ax_i, diverging="blue_red", order=False,
            fmt="{:.2f}", cbar=False, labels=True)
    n_here = (len(data) if name == "All samples"
              else int(data["Group"].eq(name).sum()))
    ax_i.set_title("%s  (n = %d)" % (name, n_here), fontsize=12)
finish(fig, "How the parameters move together",
       "Pearson correlation, on the same -1 to +1 scale in every panel. Red "
       "is a positive relationship, blue a negative one, pale is none. Each "
       "panel is its own correlation - compare the patterns, not the cells.",
       source=SRC)
keep(fig, "corr_matrix.png")
plt.show()

# --- what actually correlates -------------------------------------------
# Positive is red and negative is blue, the same way round as the matrix
# above. Two charts in one report may not disagree about what a colour means.
POS, NEG = "#b91c1c", "#1c5cab"
if len(pooled):
    top = pooled.head(12).iloc[::-1]
    fig, ax = figure(11.4, 0.46 * len(top) + 3.2)
    signs = [POS if v > 0 else NEG for v in top["r"]]
    ax.barh(range(len(top)), top["r"], height=0.62, color=signs)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(["%s / %s" % (a, b) for a, b
                        in zip(top["Parameter 1"], top["Parameter 2"])],
                       fontsize=10.5)
    ax.set_xlim(-1, 1)
    ax.set_xlabel("Pearson r")
    ax.axvline(0, color=MUTED, lw=1.2)
    for i, (v, p) in enumerate(zip(top["r"], top["p"])):
        star = "" if pd.isna(p) else (" *" if p <= ALPHA else "")
        ax.text(v + (0.03 if v > 0 else -0.03), i, "%.2f%s" % (v, star),
                va="center", ha="left" if v > 0 else "right",
                fontsize=10.5, color=INK_2)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.xaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.axvline(MIN_R, color=MUTED, lw=1, ls=":")
    ax.axvline(-MIN_R, color=MUTED, lw=1, ls=":")
    finish(fig, "What actually correlates, over all samples",
           "The %d strongest of the %d pairs, over all %d samples. The dotted "
           "rules mark |r| of %.2f - %d pair%s reach%s it. An asterisk marks "
           "p of %.2f or less."
           % (len(top), len(pooled), len(data), MIN_R, len(notable),
              "" if len(notable) == 1 else "s",
              "es" if len(notable) == 1 else "", ALPHA),
           legend=[("Positive", POS), ("Negative", NEG)], source=SRC)
    keep(fig, "corr_top.png")
    plt.show()

# --- the strongest pair, drawn ------------------------------------------
if len(notable):
    a, b = notable.iloc[0]["Parameter 1"], notable.iloc[0]["Parameter 2"]
    fig, ax = figure(10.2, 6.4)
    if GROUPED and len(GROUPS) <= 3:
        _, legend = scatter(data, a, b, hue="Group", ax=ax, fit=True)
    else:
        _, legend = scatter(data, a, b, ax=ax, fit=True)
    ax.set_xlabel(axis_name(a))
    ax.set_ylabel(axis_name(b))
    finish(fig, "%s against %s" % (full_name(a), full_name(b)),
           "The strongest relationship in the data, r = %.2f over %d samples. "
           "A line of best fit is drawn through all of them together."
           % (notable.iloc[0]["r"], int(notable.iloc[0]["n"])),
           legend=legend, source=SRC)
    keep(fig, "corr_pair.png")
    plt.show()

# --- how the groups differ ----------------------------------------------
# One panel per parameter, because the parameters are on wildly different
# scales - conductivity in thousands, cadmium in hundredths. On one axis the
# metals would collapse onto the zero line.
if GROUPED:
    group_cols = colors(len(GROUPS))
    fig, axes = panels(len(PARAMS), ncols=4, width=13.6, height=3.6)
    logged = []
    for ax_i, col in zip(axes, PARAMS):
        boxes(data, col, by="Group", ax=ax_i, cols=group_cols)
        # A trace metal runs over two or three orders of magnitude and a few
        # high samples flatten every box to a line. Where the spread is that
        # wide, and nothing sits at or below zero, read it on a log scale.
        vals = data[col].dropna()
        vals = vals[vals > 0]
        if len(vals) and vals.min() > 0 and vals.max() / vals.min() >= 20:
            ax_i.set_yscale("log")
            # A group whose samples are all at the detection floor draws a
            # box of zero height; give the axis a little room either side so
            # it is a visible line and not part of the frame.
            ax_i.set_ylim(vals.min() * 0.62, vals.max() * 1.6)
            logged.append(col)
        ax_i.set_title(full_name(col) + ("  (log)" if col in logged else ""),
                       fontsize=11.5)
        ax_i.set_ylabel(UNITS.get(col, ""))
        ax_i.set_xticklabels([wrap(str(g), 14) for g in GROUPS], fontsize=9)
    finish(fig, "The same parameters, group by group",
           "Box is the middle half of the samples, the line inside it the "
           "median, the whiskers the rest bar outliers. Each panel has its "
           "own scale - the parameters are not comparable to each other.%s"
           % ("" if not logged else
              " %s %s read on a logarithmic scale, marked (log), because "
              "their samples span more than twenty-fold."
              % (", ".join(logged), "is" if len(logged) == 1 else "are")),
           legend=list(zip([str(g) for g in GROUPS], group_cols)), source=SRC)
    keep(fig, "corr_groups.png")
    plt.show()

# --- PCA ----------------------------------------------------------------
# Standardised, because the parameters have no common unit; computed by SVD
# so the file needs nothing beyond numpy.
pca_frame = data[PARAMS].dropna()
pca_groups = data.loc[pca_frame.index, "Group"]
if len(pca_frame) > len(PARAMS):
    X = pca_frame.to_numpy(dtype=float)
    sd = X.std(axis=0, ddof=0)
    sd[sd == 0] = 1.0
    Z = (X - X.mean(axis=0)) / sd
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    var = S ** 2
    explained = 100.0 * var / var.sum()
    scores = U * S
    # Correlation loadings: how strongly each parameter reads on each axis.
    loadings = (Vt.T * S) / np.sqrt(len(Z) - 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.6, 6.4))

    # Chrome, not a series colour: the group hues belong to the biplot beside
    # it, and a blue bar here would read as "petrol stations".
    n_show = min(len(explained), len(PARAMS))
    ax1.bar(range(1, n_show + 1), explained[:n_show], width=0.62, color=INK_2)
    ax1.plot(range(1, n_show + 1), np.cumsum(explained[:n_show]),
             color=MUTED, lw=2, marker="o", ms=5, label="Cumulative")
    for i, v in enumerate(explained[:n_show], start=1):
        ax1.text(i, v + 1.4, "%.0f%%" % v, ha="center", fontsize=10,
                 color=INK_2)
    ax1.set_xticks(range(1, n_show + 1))
    ax1.set_xticklabels(["PC%d" % i for i in range(1, n_show + 1)])
    ax1.set_ylabel("Variance explained (%)")
    ax1.set_ylim(0, 105)
    ax1.set_title("How much each component carries", fontsize=12.5)
    ax1.legend(frameon=False, fontsize=10, loc="upper left")
    for side in ("top", "right"):
        ax1.spines[side].set_visible(False)
    ax1.yaxis.grid(True, color=GRID, lw=1)
    ax1.set_axisbelow(True)

    plot_groups = [g for g in GROUPS] if GROUPED else [TITLE]
    biplot_cols = colors(len(plot_groups))
    for g, col in zip(plot_groups, biplot_cols):
        m = (pca_groups == g).to_numpy()
        ax2.scatter(scores[m, 0], scores[m, 1], s=52, color=col,
                    edgecolor=SURFACE, linewidth=1.4, alpha=0.9, label=str(g))
    reach = np.abs(scores[:, :2]).max() * 0.92
    for i, col in enumerate(PARAMS):
        x, y = loadings[i, 0] * reach, loadings[i, 1] * reach
        ax2.annotate("", xy=(x, y), xytext=(0, 0),
                     arrowprops=dict(arrowstyle="->", color=INK_2, lw=1.4,
                                     alpha=0.8))
        ax2.text(x * 1.1, y * 1.1, col, fontsize=10.5, color=INK,
                 ha="center", va="center", fontweight="bold")
    ax2.axhline(0, color=GRID, lw=1)
    ax2.axvline(0, color=GRID, lw=1)
    ax2.set_xlabel("PC1 (%.0f%%)" % explained[0])
    ax2.set_ylabel("PC2 (%.0f%%)" % explained[1])
    ax2.set_title("Samples and parameters on the first two components",
                  fontsize=12.5)
    for side in ("top", "right"):
        ax2.spines[side].set_visible(False)
    # The group legend sits in the panel the groups appear in. Put it above
    # both and it would seem to explain the scree bars as well.
    if GROUPED:
        ax2.legend(frameon=False, fontsize=10, loc="upper right",
                   handletextpad=0.4)

    finish(fig, "Principal component analysis",
           "Standardised, so no parameter dominates by having a bigger unit. "
           "Arrows point the way each parameter increases; two arrows close "
           "together move together. The first two components carry %.0f%% of "
           "the variation." % (explained[0] + explained[1]), source=SRC)
    keep(fig, "corr_pca.png")
    plt.show()

    loadings_table = pd.DataFrame(
        loadings[:, :min(3, loadings.shape[1])],
        index=PARAMS,
        columns=["PC%d" % i for i in
                 range(1, min(3, loadings.shape[1]) + 1)]).round(3)
else:
    explained = np.array([])
    loadings_table = pd.DataFrame()


# =======================================================================
#  4. The tables
# =======================================================================
def stats_frame(frame, label):
    d = frame[PARAMS]
    return pd.DataFrame({
        "Group": label,
        "Parameter": [full_name(c) for c in PARAMS],
        "Unit": [UNITS.get(c, "") for c in PARAMS],
        "N": d.notna().sum().values,
        "Mean": d.mean().values,
        "SD": d.std().values,
        "Min": d.min().values,
        "Median": d.median().values,
        "Max": d.max().values,
    })


stats = pd.concat(
    [stats_frame(data, "All samples")]
    + ([stats_frame(data[data["Group"] == g], str(g)) for g in GROUPS]
       if GROUPED else []),
    ignore_index=True)
for c in ("Mean", "SD", "Min", "Median", "Max"):
    stats[c] = pd.to_numeric(stats[c], errors="coerce").round(3)

stats.to_csv("Summary_Statistics.csv", index=False)
all_pairs.to_csv("Strongest_Correlations.csv", index=False)
with pd.ExcelWriter("Correlation_Matrices.xlsx") as writer:
    for name, matrix in CORR.items():
        matrix.round(3).to_excel(writer, sheet_name=str(name)[:31])
    stats.to_excel(writer, sheet_name="Summary", index=False)
    all_pairs.to_excel(writer, sheet_name="Pairs", index=False)
    if len(loadings_table):
        loadings_table.to_excel(writer, sheet_name="PCA loadings")


# =======================================================================
#  5. The report
# =======================================================================
CSS = """
@page { size: A4 landscape; margin: 12mm 11mm 12mm 11mm; }
body { font-family: 'Nimbus Sans', Helvetica, Arial, sans-serif;
       color: #0f172a; font-size: 10.5pt; }
.band { height: 4px; margin-bottom: 10px; background: linear-gradient(to right,
        #096EFF 0%, #096EFF 58%, #10B981 58%, #10B981 82%,
        #f59e0b 82%, #f59e0b 100%); }
h1 { font-size: 17pt; margin: 0 0 2px 0; }
h2 { font-size: 12.5pt; margin: 20px 0 6px 0; color: #096EFF;
     page-break-after: avoid; }
.sub { color: #475569; margin: 0 0 12px 0; font-size: 10.5pt; }
table { border-collapse: collapse; width: 100%; font-size: 9.2pt;
        margin-bottom: 6px; }
th { background: #0f172a; color: #fff; text-align: left; font-weight: 600;
     padding: 6px 7px; font-size: 8.8pt; }
td { padding: 4.5px 7px; border-top: 1px solid #e2e8f0; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tr:nth-child(even) td { background: #f8fafc; }
tr { page-break-inside: avoid; }
.note { color: #475569; font-size: 9.4pt; margin: 8px 0 0 0; }
.pos { color: #096EFF; font-weight: 700; }
.neg { color: #e11d48; font-weight: 700; }
/* Wide charts fill the page width; tall ones stop at the page height rather
   than running off the bottom edge. */
img { max-width: 100%; max-height: 168mm; display: block; margin: 10px auto;
      page-break-inside: avoid; }
.credit { color: #94a3b8; font-size: 8.6pt; margin-top: 14px; }
"""


def num_text(value):
    """A number written to a sensible number of places for its size.

    One fixed precision cannot serve conductivity in the thousands and
    cadmium in hundredths in the same column: 1353.840 is noise and 0.01 is
    a rounding error. Scale the places to the magnitude instead.
    """
    if value is None or pd.isna(value):
        return ""
    v = float(value)
    size = abs(v)
    places = 0 if size >= 1000 else 1 if size >= 100 else 2 if size >= 10 \
        else 3
    return "{:,.{p}f}".format(v, p=places)


def html_table(frame, numeric=()):
    head = "".join('<th class="num">%s</th>' % esc(c) if c in numeric
                   else "<th>%s</th>" % esc(c) for c in frame.columns)
    body, seen = [], None
    for _, row in frame.iterrows():
        cells = []
        for c in frame.columns:
            v = row[c]
            if c in ("r", "p") and not pd.isna(v):
                text = "%.3f" % v if c == "r" else ("%.4f" % v)
                if c == "r":
                    text = ('<span class="%s">%s</span>'
                            % ("pos" if v > 0 else "neg", text))
            elif c == "N" or c == "n":
                text = "" if pd.isna(v) else "%d" % int(v)
            elif isinstance(v, (float, np.floating)):
                text = num_text(v)
            else:
                text = esc(v)
            # A group name repeated down eight rows is eight times the ink
            # for one fact. Print it where it changes.
            if c == "Group":
                text = "" if v == seen else esc(v)
                seen = v
            cells.append('<td class="num">%s</td>' % text if c in numeric
                         else "<td>%s</td>" % text)
        body.append("<tr>%s</tr>" % "".join(cells))
    return ("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
            % (head, "".join(body)))


body = ['<div class="band"></div>',
        "<h1>%s</h1>" % esc(TITLE)]
if SUBJECT:
    body.append('<p class="sub">%s</p>' % esc(SUBJECT))
body.append('<p class="sub">%d samples, %d parameters%s. Prepared %s.</p>'
            % (len(data), len(PARAMS),
               ", %d groups" % len(GROUPS) if GROUPED else "",
               datetime.date.today().strftime("%d %B %Y")))

body.append("<h2>Summary statistics</h2>")
body.append(html_table(stats, numeric=("N", "Mean", "SD", "Min", "Median",
                                       "Max")))

body.append("<h2>Strongest correlations, over all samples</h2>")
if len(notable):
    body.append(html_table(notable.head(15)[["Parameter 1", "Parameter 2",
                                             "r", "p", "n"]],
                           numeric=("r", "p", "n")))
    body.append('<p class="note">%d of the %d pairs reach |r| of %.2f'
                '%s. Correlation is not causation, and with %d samples a '
                'coefficient this size is a lead to follow, not a '
                'finding.</p>'
                % (len(notable), len(pooled), MIN_R,
                   "" if not len(significant)
                   else ", and %d of those reach p of %.2f or less"
                   % (len(significant), ALPHA),
                   len(data)))
else:
    body.append('<p class="note">No pair reaches |r| of %.2f. The parameters '
                'in this table move independently of one another.</p>'
                % MIN_R)

if len(loadings_table):
    body.append("<h2>Principal component loadings</h2>")
    lt = loadings_table.reset_index()
    lt.columns = ["Parameter"] + list(loadings_table.columns)
    lt["Parameter"] = [full_name(c) for c in loadings_table.index]
    body.append(html_table(lt, numeric=tuple(loadings_table.columns)))
    body.append('<p class="note">A loading is the correlation between a '
                'parameter and a component. The first %d components carry '
                '%.0f%% of the variation between them.</p>'
                % (len(loadings_table.columns),
                   float(np.sum(explained[:len(loadings_table.columns)]))))

for name in charts:
    with open(name, "rb") as fh:
        body.append('<img src="data:image/png;base64,%s">'
                    % base64.b64encode(fh.read()).decode("ascii"))

body.append('<p class="credit">Generated by TSSFL Technology Stack '
            "&middot; www.tssfl.com</p>")

doc = ("<html><head><meta charset='utf-8'><title>%s</title><style>%s</style>"
       "</head><body>%s</body></html>" % (esc(TITLE), CSS, "".join(body)))
with open("Correlation_Report.html", "w", encoding="utf-8") as fh:
    fh.write(doc)
HTML(string=doc).write_pdf("Correlation_Report.pdf")

print("Wrote Correlation_Report.html / .pdf - %d charts, %d tables."
      % (len(charts), 3 if len(loadings_table) else 2))
print("Wrote Correlation_Matrices.xlsx - %d matrices, plus summary, pairs%s."
      % (len(CORR), " and PCA loadings" if len(loadings_table) else ""))
print("Wrote Summary_Statistics.csv and Strongest_Correlations.csv - %d rows."
      % len(all_pairs))

show_html(table(stats[stats["Group"] == "All samples"]
                .drop(columns=["Group"]),
                title="Summary statistics, all samples",
                fmt={c: "{:,.3f}" for c in ("Mean", "SD", "Min", "Median",
                                            "Max")},
                as_html=True))
if len(notable):
    show_html(table(notable.head(10)[["Parameter 1", "Parameter 2", "r", "p",
                                      "n"]],
                    title="Strongest correlations",
                    fmt={"r": "{:.3f}", "p": "{:.4f}"}, as_html=True))
