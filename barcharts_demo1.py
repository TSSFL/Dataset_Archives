# -*- coding: utf-8 -*-
"""Bar charts from a students survey - four questions, side by side.

What changed from the earlier version, and why:

* The raw KoBo field names were used as axis labels, so four of them ran
  along the bottom of the figure overlapping into an illegible band, and
  the credit line landed on top of them. ``tidy()`` reduces each name to
  its last path segment and the titles carry it instead.
* The value labels were drawn from ``categorical_feature`` *after* the loop
  had ended, so every panel was annotated with the last panel's counts -
  the numbers on the first three charts belonged to the fourth.
* Panel titles were coloured to match their bars. Colour that carries no
  information competes with colour that does, so titles are now ink and
  the bars keep the palette.
* Responses were ordered by frequency, which put "Strongly agree" between
  "Disagree" and "Strongly disagree". ``scale_order()`` restores the scale.
"""
import matplotlib.pyplot as plt
import pandas as pd

load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tssfl_style.py")

use("tssfl")

URL = ("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/"
       "students_survey_data.csv")
df = pd.read_csv(URL).replace(r"_", " ", regex=True)

VARS = [
    ("group_ow7qd27/Subject_for_assessment", "Subject"),
    ("group_da25q48/What_are_your_percep_s_teaching_knowledge/"
     "Our_teacher_presents_y_and_systematically", "Presents systematically"),
    ("group_da25q48/What_are_your_percep_s_teaching_knowledge/"
     "The_teacher_usually_ives_before_teaching", "States objectives first"),
    ("group_da25q48/What_are_your_percep_s_teaching_knowledge/"
     "Our_teacher_collects_ow_we_want_to_learn", "Collects our views"),
]

fig, axes = panels(len(VARS), ncols=4, width=15.0, height=5.2)
for ax, (col, title), tint in zip(axes, VARS, palette()):
    vc = df[col].value_counts()
    vc = vc.reindex(scale_order(vc.index)).dropna()
    ax.bar(range(len(vc)), vc.values, width=0.62, color=tint)
    ax.set_xticks(range(len(vc)))
    ax.set_xticklabels([wrap(str(i), 12) for i in vc.index], fontsize=9.5)
    ax.set_title(title, fontsize=12)          # ink, not the bar colour
    ax.set_ylabel("Students" if ax is axes[0] else "")
    ax.set_ylim(0, vc.max() * 1.18)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    label_bars(ax, horizontal=False)          # this panel's own counts

finish(fig, "Students report strong agreement across all three statements",
       "Number of students giving each response. Each panel has its own "
       "scale, so compare shapes rather than heights across panels.",
       source="Source: TSSFL students survey.")
plt.show()
