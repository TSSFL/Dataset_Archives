# -*- coding: utf-8 -*-
"""RBF vs non-RBF regional assessment - one axis, the gap read directly.

This replaces a three-y-axis version of the same chart. The reason is not
tidiness: the two score series were drawn on scales offset by exactly five
points (`host.set_ylim(40, 75)` against `par2.set_ylim(35, 70)`), so the
rendered gap between the lines was always the true gap *minus five*. At
Clinical services the true difference is 5.1 points and the two lines met.
The chart contradicted the data.

Both series are average scores in the same unit, so they belong on one
scale. The band between the two dots is the difference, which is the
quantity the chart is actually about - no third axis needed.

Note on the source data: its own "Difference score" column does not equal
RBF minus non-RBF (they disagree by up to 2.3 points, far more than
rounding). The gap plotted here is computed from the two score columns and
labelled as such.
"""
import io

import matplotlib.pyplot as plt
import pandas as pd
import requests

load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tssfl_style.py")

use("tssfl")

URL = ("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/"
       "Raw%20data%20SRA_RBF_non_RBF.xls%20-%20Sheet1.csv")
# int() so this also works pasted straight into a Sage cell, where the
# preparser would turn 3 into a Sage Integer that pandas rejects.
df = pd.read_csv(io.StringIO(requests.get(URL).content.decode()),
                 skiprows=int(3))
df.columns = df.columns.str.strip()

AREA = "Assessed areas"
RBF = "Average Score by RBF regions assessment 2017/18"
NON = "Average Score by non-RBF regions assessment 2017/18"

ax, leg = dumbbell(df[AREA], df[NON], df[RBF],
                   left_name="non-RBF regions", right_name="RBF regions")
ax.set_xlabel("Average score, 2017/18 assessment")
finish(ax.figure,
       "RBF regions outscore non-RBF regions in every assessed area",
       "Average score out of 100. The band between the two dots is the gap, "
       "computed as RBF minus non-RBF.",
       legend=leg, source="Source: SRA RBF / non-RBF regional assessment "
                          "2017/18.")
plt.show()

# The same figures as a table, so every value is readable exactly.
t = df[[AREA, RBF, NON]].copy()
t.columns = ["Assessed area", "RBF regions", "non-RBF regions"]
t["Gap"] = (t["RBF regions"] - t["non-RBF regions"]).round(1)
table(t.sort_values("Gap", ascending=False),
      title="Average assessment scores and the RBF gap",
      fmt={"RBF regions": "{:.1f}", "non-RBF regions": "{:.1f}",
           "Gap": "{:+.1f}"},
      source="Source: SRA RBF / non-RBF regional assessment 2017/18.")
