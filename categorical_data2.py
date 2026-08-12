# -*- coding: utf-8 -*-
"""Categorical data visualisation - an ethnobotany survey, many ways.

A deliberate tour of the categorical plots seaborn offers: box, violin,
boxen, bar, point, count, strip, swarm, faceted catplot and small
multiples, on one dataset so the forms can be compared directly.

What changed from the earlier version, and why:

* ``palette=`` was passed without ``hue=`` throughout. Seaborn 0.13 raises a
  FutureWarning for that on every call - eight of them in the cell output,
  above the figures, where the audience reads them. Each plot now assigns
  ``hue`` explicitly and hides the redundant legend.
* The counts-and-percentages block annotated *every* bar, including the
  zero-height ones a sparse ``hue`` leaves behind, writing the count and the
  percentage as two separate rotated annotations. They landed on each other.
  ``label_bars()`` now writes one string per non-empty bar and drops any
  label that would overlap one already placed.
* ``print(total)`` echoed a bare ``37.0`` above a figure.
* The swarm of scientific names was drawn on a default-sized canvas, so
  thirty-odd binomials overlapped into an illegible block, and
  ``plt.tight_layout()`` on a FacetGrid printed "Tight layout not applied".
  It is now sized from the number of rows, and sorted by citation count.
* ``sns.barplot(x=df['Growth form'].head(3), y=df['Citation'])`` passed three
  x values against thirty-odd y values. That is a length mismatch, not a
  plot; it is now an explicit top-three summary.
* The "Created at www.tssfl.com" credit was placed inside the axes and sat
  on the data. ``finish()`` reserves a margin for it.

Load the house style first; everything below uses it for layout and labels.
"""
import io

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns

load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tssfl_style.py")

use("vivid")                       # softer than the default, good in print
PAL = palette("vivid")
sns.set_theme(style="whitegrid", rc={
    "axes.facecolor": SURFACE, "figure.facecolor": SURFACE,
    "grid.color": GRID, "axes.edgecolor": GRID,
    "font.sans-serif": ["Nimbus Sans", "Helvetica", "DejaVu Sans"],
})

SRC = "Source: TSSFL ethnobotany survey."

# --- data -------------------------------------------------------------
url = ("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/"
       "Categorical_data.csv")
data = pd.read_csv(io.StringIO(requests.get(url).content.decode("utf-8")))

# HIV/AIDS dominates the counts; df is the view without it, used where the
# smaller categories would otherwise be flattened.
df = data[~data["Ailment cured"].isin(["HIV/AIDS"])].copy()
df["Ailment cured"] = df["Ailment cured"].replace(
    "Gonorrhoea, syphilis", "Gonorrhoea & Syphilis")



def fold_tail(series, keep=7, other="Other"):
    """Keep the commonest levels, gather the rest into one.

    "Part used" has ten levels, several of them single records ("Barks",
    "Bark, Roots", "Leaves, Roots"). Ten needs more colours than can be
    told apart, and the rare ones are invisible anyway - so the tail is
    named honestly rather than given a colour nobody can distinguish.
    """
    top = series.value_counts().nlargest(int(keep)).index
    return series.where(series.isin(top), other)


def cat_colors(series):
    """One colour per level of a categorical column, in a stable order.

    Ordered by frequency so the commonest level always takes slot 1, which
    keeps colours stable between charts of the same variable.
    """
    levels = list(series.value_counts().index)
    return dict(zip(levels, colors(len(levels), "vivid")))

# Ten levels of "Part used" cannot be told apart by colour; fold the rare
# ones so every legend entry is a colour the reader can actually match.
for frame in (data, df):
    frame["Part used"] = fold_tail(frame["Part used"], keep=7)


# =======================================================================
#  1. Box plots - the spread of citations within each category
# =======================================================================
fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.6))
sns.boxplot(data=data, x="Citation", y="Growth form", hue="Growth form",
            palette=cat_colors(data["Growth form"]), legend=False,
            width=0.6, ax=axes[0], fliersize=3)
axes[0].set_title("By growth form", fontsize=12.5)
sns.boxplot(data=data, x="Citation", y="Part used", hue="Part used",
            palette=cat_colors(data["Part used"]), legend=False,
            width=0.6, ax=axes[1], fliersize=3)
axes[1].set_title("By part used", fontsize=12.5)
finish(fig, "How often each kind of plant is cited",
       "Box spans the interquartile range; the line inside it is the median.",
       source=SRC)
plt.show()

# Ailments, with HIV/AIDS removed so the rest are visible.
fig, ax = plt.subplots(figsize=(11.5, 5.4))
sns.boxplot(data=df, x="Ailment cured", y="Citation", hue="Ailment cured",
            palette=cat_colors(df["Ailment cured"]), legend=False,
            width=0.55, ax=ax, fliersize=3)
ax.set_xlabel("Ailment cured", labelpad=12)
finish(fig, "Citations by ailment treated",
       "HIV/AIDS is excluded here - it dominates the counts and flattens "
       "everything else.", source=SRC)
plt.show()

# =======================================================================
#  2. Violin and boxen - the same comparison, more of the distribution
# =======================================================================
# Split by growth form only. Adding "Part used" as a hue divides 37 records
# across six forms and eight parts, leaving one or two points per cell - the
# violins then collapse to flat lines and the boxen boxes to single ticks.
# A density estimate needs points to estimate from; this is what having them
# looks like.
gf_cols = cat_colors(data["Growth form"])
fig, axes = plt.subplots(1, 2, figsize=(14.0, 5.8))
sns.violinplot(data=data, x="Citation", y="Growth form", hue="Growth form",
               palette=gf_cols, legend=False, ax=axes[0],
               density_norm="width", cut=0, linewidth=1, inner="quart")
axes[0].set_title("Violin: the shape of the distribution", fontsize=12.5)
sns.boxenplot(data=data, x="Citation", y="Growth form", hue="Growth form",
              palette=gf_cols, legend=False, ax=axes[1], linewidth=0.8)
axes[1].set_title("Boxen: the tails, in detail", fontsize=12.5)
finish(fig, "Two ways of showing the same distribution",
       "A violin shows the density; a boxen chart shows the quantiles a box "
       "plot hides. Bulb and Succulent hold a single record each, so neither "
       "form has anything to show for them.", source=SRC)
plt.show()

# =======================================================================
#  3. Counts - how many records fall in each category
# =======================================================================
fig, ax = plt.subplots(figsize=(11.0, 5.6))
sns.countplot(data=data, x="Growth form", hue="Growth form",
              palette=cat_colors(data["Growth form"]), legend=False,
              width=0.62, ax=ax)
ax.set_ylabel("Number of records")
label_bars(ax, pct=True)           # one label per bar, collisions dropped
finish(fig, "Shrubs and trees dominate the records",
       "Count of records per growth form, with each as a share of the total.",
       source=SRC)
plt.show()

# The same split by part used. This cross-tab is sparse, so it is a
# heatmap: as grouped bars most columns are empty and the bars become
# hairlines with unreadable labels stacked above them.
ct = pd.crosstab(data["Growth form"], data["Part used"])
ax = heatmap(ct, fmt="{:.0f}", order=False)
finish(ax.figure, "Which part is used, by growth form",
       "Number of records in each combination. Most combinations do not "
       "occur, which is why this is a table rather than a bar chart.",
       source=SRC)
plt.show()

# =======================================================================
#  4. Strip and swarm - every record as a point
# =======================================================================
fig, axes = plt.subplots(1, 2, figsize=(14.0, 5.8))
sns.stripplot(data=data, x="Citation", y="Growth form", hue="Part used",
              palette=cat_colors(data["Part used"]), dodge=True, jitter=True,
              size=5, alpha=0.85, ax=axes[0], linewidth=0)
axes[0].set_title("Strip: jittered", fontsize=12.5)
axes[0].legend_.remove()
sns.swarmplot(data=df, x="Citation", y="Ailment cured", hue="Growth form",
              palette=cat_colors(df["Growth form"]), dodge=True, size=4.5,
              ax=axes[1], linewidth=0, warn_thresh=1.0)
axes[1].set_title("Swarm: points nudged apart", fontsize=12.5)
axes[1].legend_.remove()
finish(fig, "Every record shown individually",
       "Jitter and nudging keep overlapping points visible; each dot is one "
       "record.", source=SRC)
plt.show()

# =======================================================================
#  5. The species themselves
#  Thirty-odd binomials need one row each. Sizing the canvas from the row
#  count is what stops the names overlapping, and sorting by citation
#  turns the axis into a ranking instead of an arbitrary list.
# =======================================================================
order = (df.groupby("Scientific name")["Citation"].max()
           .sort_values(ascending=False).index.tolist())
height = max(6.0, 0.30 * len(order) + 1.8)
# Marker size: use seaborn's `size` (diameter in points), NOT `s`. An `s`
# falls through to matplotlib's scatter, where it means *area* in points
# squared - so the original s=6 drew a 2.8pt dot, which is the speck you
# see on a figure this tall. aspect 1.05 also stops the 1-10 citation
# range being stretched so wide that each row reads as a lone dot adrift.
g = sns.catplot(data=df, x="Citation", y="Scientific name",
                hue="Ailment cured", kind="swarm", order=order,
                palette=cat_colors(df["Ailment cured"]),
                height=height, aspect=1.05, size=11, legend_out=True,
                linewidth=0.8, edgecolor=SURFACE)
g.set_axis_labels("Times cited", "")
# The longest binomial runs to ~45 characters, so the label column needs
# more than a third of the width or the first words are cut off.
g.figure.subplots_adjust(top=0.93, left=0.46, right=0.82, bottom=0.08)
g.figure.suptitle("Species by number of citations", x=0.02, ha="left",
                  fontsize=15.5, fontweight="bold", color=INK)
g.figure.text(0.02, 0.015, SRC + "   " + SITE, fontsize=9.5, color=MUTED)
for t in g.ax.get_yticklabels():
    t.set_fontstyle("italic")      # binomials are italicised by convention
plt.show()

# =======================================================================
#  6. Small multiples - all four variables at a glance
# =======================================================================
features = ["Growth form", "Part used", "Ailment cured"]
fig, axes = panels(len(features), ncols=3, width=14.0, height=4.6)
for ax_i, feat in zip(axes, features):
    vc = data[feat].value_counts()
    ax_i.barh(range(len(vc))[::-1], vc.values, height=0.62,
              color=PAL[features.index(feat)])
    ax_i.set_yticks(range(len(vc))[::-1])
    ax_i.set_yticklabels([wrap(tidy(i), 22) for i in vc.index], fontsize=9.5)
    ax_i.set_title(feat, fontsize=12)
    ax_i.set_xlabel("Records")
    for side in ("top", "right", "left"):
        ax_i.spines[side].set_visible(False)
    ax_i.xaxis.grid(True, color=GRID, lw=1)
    ax_i.set_axisbelow(True)
    label_bars(ax_i, horizontal=True)
finish(fig, "The three categorical variables, side by side",
       "Counts per level. Horizontal bars so the longer names stay readable.",
       source=SRC)
plt.show()

# =======================================================================
#  7. The most-cited growth forms, as a table
# =======================================================================
top = (data.groupby("Growth form")
           .agg(Records=("Citation", "size"),
                Median_citations=("Citation", "median"),
                Max_citations=("Citation", "max"))
           .sort_values("Records", ascending=False)
           .reset_index())
table(top, title="Growth forms, ranked by number of records",
      source=SRC, total=False,
      fmt={"Median_citations": "{:.1f}", "Max_citations": "{:.0f}"})
