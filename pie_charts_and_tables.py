#Generate pie charts and tables, merge charts in one pdf, similarly for tables:
import warnings
warnings.filterwarnings('ignore')
import requests
import io
from textwrap import wrap
import pandas as pd
import numpy as np
import random
from matplotlib import pyplot as plt
# Enable tight layout globally for all figures
plt.rcParams['figure.autolayout'] = True

from PyPDF4 import PdfFileMerger, PdfFileReader

#https://www.geeksforgeeks.org/how-to-calculate-the-percentage-of-a-column-in-pandas/
#https://www.geeksforgeeks.org/plot-a-pie-chart-in-python-using-matplotlib/

textstr = 'Created at \nwww.tssfl.com'

"""
sheet_id = "1xjLTkLxr6-3cIGVbtMRHhXAkVgF7TCdis-eLWZQm6sI" #Rehema_Japhet1
sheet_name = "Sheet1"
url_1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
"""
colors1 = ['tomato', 'gold', 'skyblue', '#ffcc99']
#colors2 = ['orange','blue','lime','red']
#colors2 = ['orange','blue','green','red'] #explsion
colors1 = ['#ff6666', '#ffcc99', '#99ff99', '#66b3ff', 'tomato', 'gold', 'skyblue', '#ffcc99', 'orange','blue','green','red', 'orange','blue','lime','red']

def label_function(val, total):
  # total is the number of answers in THIS chart. The old version divided
  # by len(df), the whole survey, but groupby drops the blanks - so the
  # count printed on each slice did not match the slice it sat on.
  return f'{val / 100.0 * total:.0f}\n{val:.2f}%'

#Select multiple ranges of columns in Pandas DataFrame
#df = df.iloc[:, np.r_[4:9, 12:13, 14, 16]]

#df = pd.read_csv(url_1)

url = 'https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/students_survey_data.csv' # Make sure the url is the raw version of the file on GitHub
download = requests.get(url).content

#Reading the downloaded content and turning it into a pandas dataframe

df = pd.read_csv(io.StringIO(download.decode('utf-8')))  #error_bad_lines=False

#[df.columns.get_loc(c) for c in cols if c in df]
#Check indices -- Rehema_Japhet1: F --> BO
df1 = df.columns.get_loc("group_ow7qd27/Name_of_school")
df2 = df.columns.get_loc("group_qn2ae21/In_your_opinion_wha_learning_competences")
df3 = df.iloc[:, np.r_[5,66]].columns
df4 = df.iloc[:, np.r_[5,66]]
col_list = [chr(i+65) for i in range(len(df4.columns))]
df = df.replace(r"_", " ", regex=True)
i = 5
j = 67

# Every pie is displayed. The cost of doing that is not the drawing - all
# 58 build and save in about 19 seconds - it is pushing 58 PNGs down the
# websocket, which is what used to run the cell out of time.
#
# DISPLAY_DPI is the lever. The chart PDFs are vector, so this does not
# touch them or their quality at all; it only sets how many pixels the
# browser copy has. The figures stay 11 x 8.5 inches either way.
SHOW_ALL = True
SHOW = []
DISPLAY_DPI = 70
# Free-text columns - 26, 32, 95 and 158 distinct answers. A pie needs
# categories, not sentences, so these are charted by nobody. They still get
# a frequency table further down, which is the right form for them.
SKIP = {0, 50, 60, 61}

for column, k in zip(df.columns[i:j], range(len(df.columns[i:j]))): #5:65
  if k in SKIP:
      # These four are free text: 26, 32, 95 and 158 distinct answers. They
      # were already excluded from the merged PDF, but the figure was built
      # and written to disk first and only then discarded - and drawing a
      # 158-slice pie, measuring 158 labels for bbox_inches='tight', is
      # what used up the cell's time budget. Skip before building.
      continue
  # 11 x 8.5 rather than 8 x 6. The old size was also why "Tight layout not
  # applied - the left and right margins cannot be made large enough" kept
  # appearing: a long slice label simply had nowhere to go.
  fig, ax1 = plt.subplots(figsize=(11, 8.5))
  title = "\n".join(wrap(column.replace("/", " ").replace("_", " "), 40))

  counts = df.groupby(column).size()
  total = int(counts.sum())
  # Wrap the slice labels too, so a long answer stacks instead of pushing
  # the pie off its own canvas.
  counts.index = ["\n".join(wrap(str(ix), 20)) for ix in counts.index]

  counts.plot(kind='pie', autopct=lambda v: label_function(v, total),
              textprops={'fontsize': 13}, colors=colors1, ax=ax1,
              startangle=90, counterclock=False, labeldistance=1.06,
              pctdistance=0.62,
              wedgeprops=dict(edgecolor='white', linewidth=2))
  ax1.set_ylabel('')
  ax1.set_title(title, size=19, pad=18)
  ax1.set_position([0.08, 0.06, 0.84, 0.78])   # room for title and labels
  plt.gcf().text(0.02, 0.94, textstr, fontsize=14, color='green')
  # Saved before the dpi is lowered - and a PDF is vector regardless.
  plt.savefig("./chart_%s.pdf" % (k), bbox_inches='tight')
  if SHOW_ALL or k in SHOW:
      fig.set_dpi(DISPLAY_DPI)     # affects the PNG only, never the PDF
      plt.show()
  plt.close(fig)      # see note above: releases the figure straight away


mergedCharts = PdfFileMerger()
merged = 0
for fileNumber in range(0, k+1):

  if fileNumber in SKIP:
      continue
  else:
      mergedCharts.append(PdfFileReader('chart_' + str(fileNumber)+ '.pdf', 'rb'))
      merged += 1

#Write all the files into a file which is named as shown below
mergedCharts.write("./Merged_ChartsXX.pdf")
print("Merged_ChartsXX.pdf  - %d pie charts "
      "(%d shown above)" % (merged, len([n for n in SHOW if n not in SKIP])))


#Write/merge all the files into a file which is named as shown below
#mergedCharts.write("/home/elimboto/KoBo_Data_Processing/Charts_R_Japhet1/Charts_XY.pdf")

#Create and Merge Tables

#https://caendkoelsch.wordpress.com/2019/05/10/merging-multiple-pdfs-into-a-single-pdf/
from pretty_html_table import build_table
import pandas as pd
import seaborn as sns

from weasyprint import CSS
from weasyprint import HTML


# All 62 tables are collected into one HTML document and rendered once.
# weasyprint costs roughly 0.4 s to start up per call regardless of how
# small the table is, so 62 separate write_pdf() calls spent about 25 s
# doing nothing but starting - enough, on top of the charts, to run the
# cell out of time before it could write this file. One call, same output.
parts = []
for column, i in zip(df.columns[i:j], range(len(df.columns[i:j]))): #5:65
  title = "\n".join(wrap(column.replace("/", " ").replace("_", " "), 40))
  series = df[column].value_counts()

  df2 = series.to_frame().reset_index()
  df2.columns.values[0] = title
  df2.columns.values[1] = "Frequency"

  df2['Percentage (%)'] = np.round(((df2['Frequency'] /
                df2['Frequency'].sum()) * 100.0), 2)
  table = "Table %s" % (i+1)
  if i == 0:
      textstr = 'Created at TSSFL ODF: www.tssfl.com'
      df2.columns=pd.MultiIndex.from_product([[textstr],df2.columns])
  else:
      df2.columns=pd.MultiIndex.from_product([[table],df2.columns])
  output = build_table(df2, 'green_light', font_size='medium', font_family='Open Sans, sans-serif', text_align='left', width='auto',        index=False, even_color='black', even_bg_color='white')
  parts.append(output)

with open("Table.html", "w+") as file:
    file.write("\n".join(parts))

# One page per table, as before.
page_break = '<div style="page-break-after: always;"></div>'
HTML(string=page_break.join(parts)).write_pdf("./Merged_TablesXY.pdf")
print("Merged_TablesXY.pdf  - %d frequency tables" % len(parts))


#Delete images and pdfs
#import os
#os.remove("chart_*.pdf")
#os.remove("Table_*.pdf")
#Multiple headers https://pretagteam.com/question/pandas-dataframe-making-multiple-rows-of-headers
#Concatenate pd dataframes https://www.geeksforgeeks.org/how-to-concatenate-two-or-more-pandas-dataframes/
