# -*- coding: utf-8 -*-
"""RBF vs non-RBF assessment - original version, warnings removed.

Kept exactly as it was: three y-axes, the same viridis/red/magenta lines,
the same 9 x 8 figure, the same dashed blue grids, the same axis limits,
the same watermark position, the same -45 degree tick labels. It exists so
the original look can still be shown.

Fixes, all of them console noise rather than appearance:

* `print(df.keys())` and `print(df[x])` dumped an Index and the full
  column above the figure.
* "color is redundantly defined by the 'color' keyword argument and the fmt
  string '-ok'" - the format string asks for black and `color=color1` then
  overrides it. Dropping the k leaves the line the same colour.
* `fig.set_tight_layout(True)` is deprecated since Matplotlib 3.6;
  `fig.set_layout_engine('tight')` is the same instruction, current.
* `skiprows=int(3)` so the script also works pasted straight into a Sage
  cell, where the preparser turns 3 into a Sage Integer pandas rejects.

READ THIS BEFORE PRESENTING FROM IT
-----------------------------------
The two score series are the same quantity in the same unit, but they are
drawn on scales offset by exactly five points:

    host.set_ylim(40, 75)   # RBF
    par2.set_ylim(35, 70)   # non-RBF

so the rendered distance between the black and magenta lines is always the
true gap MINUS FIVE:

    Staff Performance         true 14.0   shown  9.0
    Service provider charter  true 15.0   shown 10.0
    Infrastructure            true 10.6   shown  5.6
    Clinical services         true  5.1   shown  0.1  <- lines meet

At Clinical services the chart shows no difference where there is one of
5.1 points. Nothing here corrects that - it is preserved deliberately, so
the original can be shown as it was. some_data.py puts both series on one
axis, where the gap is what it is.
"""
import io

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
from matplotlib import rc
rc('mathtext', default='regular')

textstr = 'Created at www.tssfl.com'
sns.set_style('dark')  # darkgrid, white grid, dark, white and ticks

url = ('https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/'
       'Raw%20data%20SRA_RBF_non_RBF.xls%20-%20Sheet1.csv')
download = requests.get(url).content
df = pd.read_csv(io.StringIO(download.decode('utf-8')), skiprows=int(3))

df.columns = df.columns.str.strip()
x = 'Assessed areas'
yl1 = 'Average Score by RBF regions assessment 2017/18'
yl2 = 'Average Score by non-RBF regions assessment 2017/18'
yr = 'Difference score'

# More versatile wrapper
fig, host = plt.subplots(figsize=(9, 8))  # (width, height) in inches

par1 = host.twinx()
par2 = host.twinx()

host.set_ylim(40, 75)   # RBF
par2.set_ylim(35, 70)   # Non-RBF
par1.set_ylim(5, 20)    # Difference

host.set_xlabel('Assessed Areas')
host.set_ylabel('Average Score by RBF regions assessment 2017/18')
par2.set_ylabel('Average Score by non-RBF regions assessment 2017/18')
par1.set_ylabel('Difference score')

color1 = plt.cm.viridis(0)
color2 = 'tab:red'
color3 = 'magenta'

# '-ok' asks for black and color=color1 then overrides it; dropping the k
# silences the warning and leaves the line exactly the colour it was.
p1, = host.plot(df[x], df[yl1], '-o', color=color1, label="RBF Assessment")
p2, = par1.plot(df[x], df[yr], '-', color=color2, label="Difference")
p3, = par2.plot(df[x], df[yl2], '--', color=color3, label="Non-RBF Assessment")

lns = [p1, p2, p3]
host.legend(handles=lns, loc=2)

plt.gcf().text(0.4, 0.6, textstr, fontsize=14, color='green')

# Move the non-RBF axis to the left
par2.spines['left'].set_position(('outward', 60))
par2.spines['left'].set_visible(True)
par2.yaxis.set_label_position('left')
par2.yaxis.set_ticks_position('left')

host.yaxis.label.set_color(p1.get_color())
par1.yaxis.label.set_color(p2.get_color())
par2.yaxis.label.set_color(p3.get_color())

# Adjust spacings w.r.t. figsize
plt.subplots_adjust(bottom=0.75)
fig.tight_layout()

# Adding grid
host.grid(color="blue", linestyle='--')
par2.grid(color="blue", linestyle='--')
plt.setp(host.get_xticklabels(), rotation=-45, ha="left",
         rotation_mode="anchor")
plt.title("Average Score by RBF & Non-RBF Regions Assessment 2017/18 "
          "and Their Difference  (original version)")
plt.savefig("pyplot_multiple_y-axis.pdf", bbox_inches="tight")
# set_tight_layout(True) is deprecated since Matplotlib 3.6; this is the
# same instruction in current form.
fig.set_layout_engine('tight')
plt.show()
