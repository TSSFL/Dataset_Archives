# -*- coding: utf-8 -*-
"""DUCE student enrolment by programme, year and sex.

Rewritten from the original sari_code.py. The figures are unchanged - they
are transcribed from that file - but the charts now say what the data says.

WHAT WAS WRONG, not just untidy
-------------------------------
1. A "Total" bar was drawn beside Male and Female. It is their sum, so it
   carried no information the chart did not already show, it was always
   labelled 100%, and being roughly twice the height of either real bar it
   set the y-scale and squashed the comparison that matters. The total is
   now written above each pair instead of competing with it.

2. "Grand Total" sat on the x-axis as though it were a fourth year. At 1,227
   against yearly figures near 400 it dominated every panel. A total is not
   a peer of the things it totals; it has moved to the panel subtitle.

3. The percentages were computed against the wrong programme. The first
   annotation loop divided every panel's bars by `df[0].iloc[l][3]` - the
   BSc. Ed totals - so the MSc panels were shown as a share of a programme
   they are not part of. Those labels were then overdrawn by a second,
   correct loop, and the wrong ones only escaped notice because the
   hardcoded `y-120` offset pushed them off the bottom of the small panels.

4. `plt.xlim(...)` and `plt.ylim(...)` were called inside a loop over
   subplots. Those act on the *current* axes, not on `ax[i][j]`, so the
   limits landed on whichever panel matplotlib considered current.

5. `plt.ylim([0, 68])` was hardcoded in the standalone charts. Any intake
   above 68 would be clipped without warning.

6. `df.iloc[i][3]` is chained indexing; pandas 2 emits a FutureWarning for
   every bar drawn, which filled the output above the figures.

7. Bars with height zero were labelled "0" and "0.00%".

A DATA CONFLICT YOU SHOULD RESOLVE
----------------------------------
MSc. Ed appears twice in the original with different numbers: 4M/3F and
3M/5F in the four-panel grid (15 students), but 12M/11F and 5M/5F in its own
chart (33 students). The faculty total of 1,260 is built from the first set -
232+0+8+4 = 244 male in Year 1 checks out against it - so the standalone
chart disagrees with both the grid and the faculty total. The first set is
used here because it is the one the totals are consistent with. Correct
PROGRAMMES below if that is the wrong choice.
"""
import matplotlib.pyplot as plt
import pandas as pd

load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tssfl_style.py")

use("tssfl")
MALE, FEMALE = palette()[0], palette()[1]
SRC = "Source: DUCE student enrolment records."

# programme -> (faculty, {year: (male, female)})
PROGRAMMES = {
    "BSc. Ed":        ("Science", {"Year 1": (232, 199), "Year 2": (250, 145),
                                   "Year 3": (240, 161)}),
    "MSc. Env Biol":  ("Science", {"Year 1": (0, 4), "Year 2": (2, 0)}),
    "MSc. Ind Chem":  ("Science", {"Year 1": (8, 4), "Year 2": (0, 0)}),
    "MSc. Ed":        ("Science", {"Year 1": (4, 3), "Year 2": (3, 5)}),
    "BA. Ed":         ("Humanities and Social Sciences",
                       {"Year 1": (630, 629), "Year 2": (631, 740),
                        "Year 3": (613, 514)}),
    "MA (PG). Ed":    ("Humanities and Social Sciences",
                       {"Year 1": (15, 12), "Year 2": (20, 11)}),
}


def frame(years):
    """Years as rows, with the totals derived rather than transcribed."""
    df = pd.DataFrame(
        [(y, m, f) for y, (m, f) in years.items()],
        columns=["Year", "Male", "Female"])
    df["Total"] = df["Male"] + df["Female"]
    return df


def enrolment_panel(ax, title, years, show_legend=False, label_size=10):
    """Male and Female side by side, with each year's total above the pair."""
    df = frame(years)
    x = range(len(df))
    w = 0.38
    bars_m = ax.bar([i - w / 2 for i in x], df["Male"], w, color=MALE,
                    label="Male")
    bars_f = ax.bar([i + w / 2 for i in x], df["Female"], w, color=FEMALE,
                    label="Female")

    top = max(df["Total"].max(), 1)
    ax.set_ylim(0, top * 1.30)          # derived, never a magic number

    for i, row in df.iterrows():
        for bar, value in ((bars_m[i], row["Male"]), (bars_f[i], row["Female"])):
            if not value:
                continue                # no label on a bar that is not there
            share = 100.0 * value / row["Total"] if row["Total"] else 0
            ax.text(bar.get_x() + bar.get_width() / 2, value + top * 0.02,
                    f"{value:,}\n{share:.0f}%", ha="center", va="bottom",
                    fontsize=label_size, color=INK_2, linespacing=1.25)
        # the total, stated once, above the pair it belongs to
        ax.text(i, top * 1.19, f"{row['Total']:,}", ha="center", va="center",
                fontsize=label_size + 0.5, fontweight="bold", color=INK)

    ax.set_xticks(list(x))              # set ticks before labels: no warning
    ax.set_xticklabels(df["Year"])
    ax.set_ylabel("Students")
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)

    grand = int(df["Total"].sum())
    male = int(df["Male"].sum())
    pct = 100.0 * male / grand if grand else 0
    ax.set_title(f"{title}\n{grand:,} students, {pct:.0f}% male",
                 fontsize=12, color=INK)
    if show_legend:
        ax.legend(loc="upper left", frameon=False, fontsize=10)
    return df


# =======================================================================
#  1. The four Faculty of Science programmes
# =======================================================================
science = [p for p, (fac, _) in PROGRAMMES.items() if fac == "Science"]
fig, axes = plt.subplots(2, 2, figsize=(13.0, 9.0))
for ax, name in zip(axes.ravel(), science):
    enrolment_panel(ax, name, PROGRAMMES[name][1])
finish(fig, "Enrolment in Faculty of Science programmes",
       "Male and female students by year of study. The figure above each "
       "pair is that year's total; each bar carries its count and its share "
       "of the year. Panels have their own scales - BSc. Ed is two orders of "
       "magnitude larger than the MSc programmes.",
       legend=[("Male", MALE), ("Female", FEMALE)], source=SRC)
plt.show()

# =======================================================================
#  2. Every programme, side by side
# =======================================================================
rows = []
for name, (fac, years) in PROGRAMMES.items():
    df = frame(years)
    rows.append({"Programme": name, "Faculty": fac,
                 "Male": int(df["Male"].sum()),
                 "Female": int(df["Female"].sum()),
                 "Total": int(df["Total"].sum())})
summary = pd.DataFrame(rows).sort_values("Total", ascending=False)

fig, ax = plt.subplots(figsize=(11.5, 6.2))
y = range(len(summary))
ax.barh([i + 0.19 for i in y], summary["Male"], 0.38, color=MALE, label="Male")
ax.barh([i - 0.19 for i in y], summary["Female"], 0.38, color=FEMALE,
        label="Female")
ax.set_yticks(list(y))
ax.set_yticklabels(summary["Programme"])
ax.invert_yaxis()
ax.set_xlabel("Students enrolled")
ax.set_xscale("log")     # BA. Ed is ~250x MSc. Env Biol; linear hides the rest
ax.xaxis.grid(True, color=GRID, lw=1)
ax.set_axisbelow(True)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
label_bars(ax, fmt="{:,.0f}", horizontal=True)
finish(fig, "BA. Ed and BSc. Ed carry almost all enrolment",
       "Total students per programme across all years. A log scale, because "
       "the largest programme is around 250 times the smallest - on a linear "
       "axis every postgraduate programme collapses to a hairline.",
       legend=[("Male", MALE), ("Female", FEMALE)], source=SRC)
plt.show()

# =======================================================================
#  3. One chart per programme
# =======================================================================
for name, (fac, years) in PROGRAMMES.items():
    fig, ax = plt.subplots(figsize=(9.5, 6.0))
    enrolment_panel(ax, name, years, show_legend=True, label_size=11)
    finish(fig, f"{name} - {fac}",
           "Students by year of study and sex.", source=SRC)
    plt.show()

# =======================================================================
#  4. The same figures as a table
# =======================================================================
summary["% male"] = (100.0 * summary["Male"] / summary["Total"]).round(1)
table(summary[["Programme", "Faculty", "Male", "Female", "Total", "% male"]],
      title="Enrolment by programme", total=False,
      fmt={"% male": "{:.1f}%"}, source=SRC)
