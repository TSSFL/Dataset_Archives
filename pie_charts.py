# -*- coding: utf-8 -*-
"""Pie charts from the students survey, merged into one PDF.

Split out of pie_charts_and_tables.py. The charts and the frequency tables
were competing for a single cell's execution budget and neither finished;
each half now has its own. The tables live in frequency_tables.py.

Every column gets a pie and every pie goes into Merged_ChartsXX.pdf. A
handful are then shown on screen at the end, as a preview of the file.

That order matters. Drawing and saving all 58 takes about 19 seconds;
displaying one costs far more than drawing it, so showing all 58 inside
the loop is what used to exhaust the cell before it could write the PDF.
Change PREVIEW to see different ones - it does not affect the PDF.

Fixes carried over from the combined script:

* "More than 20 figures have been opened" - the loop never released a
  figure. plt.close(fig) each pass.
* "Tight layout not applied. The left and right margins cannot be made
  large enough to accommodate all Axes decorations" - a long slice label on
  an 8 x 6 canvas had nowhere to go. Now 11 x 8.5, slice labels wrap, and
  the axes are placed explicitly rather than asking tight_layout to solve
  something unsolvable.
* print(df1, df2) and print(k) wrote "5 66" and a column of loop counters
  through the output.
* label_function divided by len(df) - the whole survey - while groupby
  drops blank answers, so the count printed on a slice disagreed with the
  slice. It now divides by the answers in that chart.
* The four free-text columns (26, 32, 95 and 158 distinct answers) were
  already excluded from the merged PDF, but the figure was drawn and saved
  first and only then discarded. Drawing a 158-slice pie is not free.
"""
import requests
import io
from textwrap import wrap
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

from PyPDF4 import PdfFileMerger, PdfFileReader

textstr = 'Created at \nwww.tssfl.com'

colors1 = ['#ff6666', '#ffcc99', '#99ff99', '#66b3ff', 'tomato', 'gold',
           'skyblue', '#ffcc99', 'orange', 'blue', 'green', 'red', 'orange',
           'blue', 'lime', 'red']


def label_function(val, total):
  # total is the number of answers in THIS chart, not len(df).
  return f'{val / 100.0 * total:.0f}\n{val:.2f}%'


url = 'https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/students_survey_data.csv'
download = requests.get(url).content
df = pd.read_csv(io.StringIO(download.decode('utf-8')))
df = df.replace(r"_", " ", regex=True)

i = 5
j = 67

# Free-text columns: a pie needs categories, not sentences. These get a
# frequency table in frequency_tables.py, which is the right form for them.
SKIP = {0, 50, 60, 61}

# Which pies to show on screen once everything is written. The PDF always
# holds the full set regardless of what is listed here.
PREVIEW = [1, 2, 3, 10, 25, 40]

for column, k in zip(df.columns[i:j], range(len(df.columns[i:j]))):
  if k in SKIP:
      continue

  fig, ax1 = plt.subplots(figsize=(11, 8.5))
  title = "\n".join(wrap(column.replace("/", " ").replace("_", " "), 40))

  counts = df.groupby(column).size()
  total = int(counts.sum())
  counts.index = ["\n".join(wrap(str(ix), 20)) for ix in counts.index]

  counts.plot(kind='pie', autopct=lambda v: label_function(v, total),
              textprops={'fontsize': 13}, colors=colors1, ax=ax1,
              startangle=90, counterclock=False, labeldistance=1.06,
              pctdistance=0.62,
              wedgeprops=dict(edgecolor='white', linewidth=2))
  ax1.set_ylabel('')
  ax1.set_title(title, size=19, pad=18)
  ax1.set_position([0.08, 0.06, 0.84, 0.78])
  plt.gcf().text(0.02, 0.94, textstr, fontsize=14, color='green')
  plt.savefig("./chart_%s.pdf" % (k), bbox_inches='tight')
  if k not in PREVIEW:
      plt.close(fig)      # released now; the preview ones are kept open

mergedCharts = PdfFileMerger()
merged = 0
for fileNumber in range(0, k + 1):
  if fileNumber in SKIP:
      continue
  mergedCharts.append(PdfFileReader('chart_' + str(fileNumber) + '.pdf', 'rb'))
  merged += 1

mergedCharts.write("./Merged_ChartsXX.pdf")
print("Merged_ChartsXX.pdf  -  %d pie charts" % merged)
print("Showing %d of them below." % len([n for n in PREVIEW if n not in SKIP]))

# The preview figures are the only ones still open, so this renders exactly
# those - after the PDF is safely written.
plt.show()
