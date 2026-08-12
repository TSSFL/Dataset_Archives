# -*- coding: utf-8 -*-
"""Casting 3-D into 2-D - original version, console output removed.

Kept exactly as it was: the same dark seaborn theme, the same 14 x 8 inch
figure, the same red line with black markers, the same dashed blue grids,
the same axis colours, the same watermark position, a tick at every data
value. It exists so the original look can still be shown.

One fix, nothing else: the two `print()` calls are gone.

    print(df.keys())   ->  Index(['MPs/Kg DW', 'depth (cm)', 'Year'], ...)
    print(new_ls)      ->  [np.int64(2016), np.int64(2015), ...]

Neither was a warning or an error. The second looked alarming only because
numpy 2 changed how a scalar reprs: under numpy 1 that same line printed
[2016, 2015, ...], and SageCell now runs numpy 2. Both were debug output
that told the reader nothing, so both are removed.

The year labels themselves were correct. They are built by matching tick k
to row k, which is right for as long as the file stays sorted by depth -
it is, and every year sits beside its true depth. It is fragile rather
than wrong: re-sort the CSV and the years would quietly stop matching.
dativa.py replaces that with an explicit depth-to-year lookup, thins the
ticks, and turns the core the right way up.
"""
import requests
import io
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rc
rc('mathtext', default='regular')

textstr = 'Created at www.tssfl.com'
sns.set_style('dark')  # darkgrid, white grid, dark, white and ticks

url = 'https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/chem_data.csv'
download = requests.get(url).content

# Reading the downloaded content and turning it into a pandas dataframe
df = pd.read_csv(io.StringIO(download.decode('utf-8')), skiprows=int(1))

df.columns = df.columns.str.strip()

var1 = 'MPs/Kg DW'
var2 = 'depth (cm)'
var3 = 'Year'

x = df[var1]
y1 = df[var2]
y2 = df[var3]

fig, ax = plt.subplots(figsize=(14, 8))

color1 = 'tab:red'
ax.plot(x, y1)

ax.set_xlabel('MPs/Kg DW', fontsize=16, color="darkblue")
ax.tick_params(axis='x', labelcolor="darkblue")

ax.set_ylabel('Depth (cm)', fontsize=16, color="navy")
ax.tick_params(axis='y', labelcolor="navy")

plt.xticks(x)
plt.yticks(y1)

ax2 = ax.twinx()
# '-ok' asks for black and color="red" then overrides it, which is what
# the "color is redundantly defined" warning was reporting. Dropping the k
# leaves the line exactly as red as it always was, and says nothing.
ax2.plot(x, y1, '-o', color="red")

ax2.set_yticks(ax.get_yticks())
ax2.set_ylim(ax.get_ylim())
fig.canvas.draw()

# Get the tick labels which are strings, convert them to integers
labels = [int(i.get_text().replace('−', '-'))
          for i in ax2.get_yticklabels()]

new_ls = [y2[i] for i in range(len(labels))]

plt.gcf().text(0.12, 0.92, textstr, fontsize=14, color='green')

ax2.set_yticklabels(new_ls, color="midnightblue")
ax2.set_ylabel('Year', fontsize=16, color="midnightblue")

# Adding grid
ax.grid(color="blue", linestyle='--')
ax2.grid(color="blue", linestyle='--')

plt.title('Projecting 3D into 2D  (original version)',
          fontweight="bold", color="Black")
plt.show()
