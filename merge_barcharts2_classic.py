# -*- coding: utf-8 -*-
"""Generate and merge bar charts - original version, 0.00% and warnings fixed.

Kept exactly as it was: the same rainbow palette, the same 17.5 x 7 inch
pages, the same darkgrid theme, the same green counts and red rotated
percentages, the same watermark position, the same PyPDF4 merge. It exists
so the original look can still be shown.

Two fixes, nothing else:

1. **The 0.00% labels.** The percentage loop annotated every patch in
   ax.patches. A grouped countplot creates a patch for every category-by-hue
   combination, including ones with no records, so each empty slot still got
   a "0.00%" written above it - which is where the drifting labels across
   the merged PDF came from. The count loop directly above already guarded
   with `if h != 0`; the percentage loop never did. It does now.

2. **The palette warning.** "The palette list has more values (16) than
   needed (2)" was printed above the figures. colors1 holds sixteen colours
   while the hue column has two levels (gender) or eleven (subjects), so
   seaborn was handed more than it could use. Passing only as many as the
   hue needs silences it and changes no colour - the same entries are still
   taken, in the same order, from the front of the same list.

For the redesigned version, load merge_barcharts2.py instead.
"""
import io

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from textwrap import wrap

# Merge files
from PyPDF4 import PdfFileMerger, PdfFileReader
mergedObject = PdfFileMerger()

textstr = 'Created at \nwww.tssfl.com'

# Let's visualize - graph styles and font size (unchanged)
sns.set_style('darkgrid')        # darkgrid, white grid, dark, white, ticks
plt.rc('axes', titlesize=18)     # fontsize of the axes title
plt.rc('axes', labelsize=14)     # fontsize of the x and y labels
plt.rc('xtick', labelsize=13)    # fontsize of the tick labels
plt.rc('ytick', labelsize=13)    # fontsize of the tick labels
plt.rc('legend', fontsize=13)    # legend fontsize
plt.rc('font', size=13)          # controls default text sizes

url = ("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/"
       "teachers_survey_data.csv")
download = requests.get(url).content
df = pd.read_csv(io.StringIO(download.decode('utf-8')))
df = df.replace(r"_", " ", regex=True)
total = float(len(df))

# get column range
df3 = df.iloc[:, np.r_[9, 13]]
df4 = df.iloc[:, np.r_[58:67]]

colors1 = ['#ff6666', '#ffcc99', '#99ff99', '#66b3ff', 'tomato', 'gold',
           'skyblue', '#ffcc99', 'orange', 'blue', 'green', 'red', 'orange',
           'blue', 'lime', 'red']

# Loop over columns
for column1, i in zip(df4.columns, range(len(df4.columns))):
    for column2, j in zip(df3.columns, range(len(df3.columns))):

        plt.figure(figsize=(17.5, 7.))
        ax = plt.subplot(111)
        # Hand seaborn only as many colours as the hue has levels - same
        # colours, same order, just no unused tail to warn about.
        n_hue = df[column2].nunique(dropna=True)
        ax = sns.countplot(x=column1, data=df, hue=column2,
                           palette=colors1[:n_hue])
        plt.xticks(rotation=90)

        for p in ax.patches[0:]:
            h = p.get_height()
            x = p.get_x() + p.get_width() / 2.0
            if h != 0:
                ax.annotate("%g" % p.get_height(), xy=(x - 0.01, h),
                            xytext=(0, 4), rotation=0,
                            textcoords="offset points", ha="center",
                            va="bottom", color='green')

        for p in ax.patches:
            # THE FIX: an empty category still has a patch, and labelling it
            # printed 0.00% over a bar that is not there. Skip those.
            if p.get_height() == 0:
                continue
            percentage = '{:.2f}%'.format(100 * p.get_height() / total)
            x = p.get_x() + p.get_width()
            y = p.get_height()
            ax.annotate(percentage, (x - 0.01, y + 0.45), ha='center',
                        rotation=90, color='red')

        xlabel = "\n".join(wrap(column1.replace("/", " ").replace("_", " "),
                                120))
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.gcf().text(0.02, 0.93, textstr, fontsize=14, color='green')
        plt.savefig("./barchart_%s_%s.pdf" % (i, j), bbox_inches='tight')
        # Call the PdfFileMerger
        mergedObject.append(PdfFileReader('./barchart_%s_%s' % (i, j)
                                          + '.pdf', 'rb'))
        plt.show()
        plt.clf()

# Write/merge all the files into a file which is named as shown below
mergedObject.write("./Merged_Charts_XY.pdf")
