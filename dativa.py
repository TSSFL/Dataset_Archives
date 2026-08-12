# -*- coding: utf-8 -*-
"""Casting 3-D into 2-D - microplastics down a dated sediment core.

Three variables (concentration, depth, year) on a two-dimensional plot.
Depth and year are not independent: each depth in the core was dated, so
year is a second *labelling* of the same axis rather than a second
measurement. That is what makes a right-hand axis legitimate here, unlike
a true dual-axis chart where two unrelated measures are forced onto one
picture and the alignment between them is arbitrary.

What changed from the earlier version, and why:

* ``print(df.keys())`` and ``print(new_ls)`` dumped an ``Index([...])`` and a
  list above the figure. The second printed as ``[np.int64(2016),
  np.int64(2015), ...]`` - not a warning and not an error: numpy 2 changed
  how a scalar reprs, so a list of numpy integers now shows its types.
  Under numpy 1 the same line printed ``[2016, 2015, ...]``. Neither line
  told the reader anything, so both are gone.
* ``plt.xticks(x)`` and ``plt.yticks(y1)`` put a tick at every one of the 30
  data values, which is where the wall of 90, 87, 84, 81, 78 came from.
* The year labels were built with ``[y2[i] for i in range(len(labels))]`` -
  the year of *row i*, matched to *tick i*. That is only correct while the
  frame happens to be sorted by depth; sort it any other way and the years
  silently stop matching the depths they sit beside. The mapping is now an
  explicit depth-to-year lookup.
* Depth now increases downwards, which is how a core is read: the surface
  is at the top and 1947 is at the bottom.
"""
import io

import matplotlib.pyplot as plt
import pandas as pd
import requests

load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tssfl_style.py")

use("tssfl")

URL = ("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/"
       "chem_data.csv")
df = pd.read_csv(io.StringIO(requests.get(URL).content.decode("utf-8")),
                 skiprows=int(1))
df.columns = df.columns.str.strip()

MPS, DEPTH, YEAR = "MPs/Kg DW", "depth (cm)", "Year"
df = df.sort_values(DEPTH).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(11.0, 7.0))
ax.plot(df[MPS], df[DEPTH], "-o", color=palette()[0], lw=2,
        ms=7, mec=SURFACE, mew=1.6, zorder=3)
ax.fill_betweenx(df[DEPTH], 0, df[MPS], color=palette()[0], alpha=0.10,
                 zorder=1)

ax.invert_yaxis()                       # surface at the top, as a core reads
ax.set_xlabel("Microplastics (particles per kg dry weight)")
ax.set_ylabel("Depth in core (cm)")
ax.set_xlim(0, df[MPS].max() * 1.12)
ax.xaxis.grid(True, color=GRID, lw=1)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
ax.spines["left"].set_color(GRID)
ax.spines["bottom"].set_color(GRID)

# Right-hand axis: the same depths, labelled with the year each was dated
# to. Built from an explicit lookup, so it stays correct whatever order
# the rows arrive in.
depth_to_year = dict(zip(df[DEPTH], df[YEAR]))
ticks = df[DEPTH][::4].tolist()          # every fourth level, not all thirty
if df[DEPTH].iloc[-1] not in ticks:
    ticks.append(df[DEPTH].iloc[-1])

ax.set_yticks(ticks)
ax2 = ax.twinx()
ax2.set_ylim(ax.get_ylim())              # identical scale, different labels
ax2.set_yticks(ticks)
ax2.set_yticklabels([depth_to_year[t] for t in ticks])
ax2.set_ylabel("Year the layer was dated to", labelpad=12)
for side in ("top", "left", "bottom"):
    ax2.spines[side].set_visible(False)
ax2.spines["right"].set_color(GRID)
ax2.tick_params(length=0)

first_year = depth_to_year[max(depth_to_year)]
finish(fig, "Microplastics appear in the core from the 1960s and rise sharply",
       f"Concentration by depth, with each level dated. Nothing is detected "
       f"below the layer dated {first_year}; the surface layer carries the "
       f"highest load of the whole core.",
       source="Source: TSSFL sediment core analysis.")
plt.show()

# The same figures as a table - three columns, so no axis has to be shared.
t = df[[DEPTH, YEAR, MPS]].copy()
t.columns = ["Depth (cm)", "Year", "Microplastics per kg"]
table(t, title="Microplastics by depth and year",
      fmt={"Depth (cm)": "{:.0f}", "Year": "{:.0f}",
           "Microplastics per kg": "{:.0f}"},
      source="Source: TSSFL sediment core analysis.")
