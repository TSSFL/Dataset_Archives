# -*- coding: utf-8 -*-
"""Frequency tables from the students survey, merged into one PDF.

Split out of pie_charts_and_tables.py, where the charts and the tables were
competing for one cell's execution budget and neither finished. The pie
charts live in pie_charts.py.

The tables are not displayed - they are rendered straight into
Merged_TablesXY.pdf, which is what they are for. All 62 columns get a
table, including the four free-text ones that cannot be pie charts.

One change of substance: the 62 tables are rendered in a single weasyprint
call rather than 62. weasyprint costs roughly 0.4 s to start up per call
regardless of size, so a four-row table cost as much in overhead as it did
in work - about 25 s of the budget spent starting up. One document with a
page break between tables produces the same PDF, one page per table, and
removes the need for PyPDF4 here.
"""
import requests
import io
from textwrap import wrap
import pandas as pd
import numpy as np

from pretty_html_table import build_table
from weasyprint import HTML

url = 'https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/students_survey_data.csv'
download = requests.get(url).content
df = pd.read_csv(io.StringIO(download.decode('utf-8')))
df = df.replace(r"_", " ", regex=True)

i = 5
j = 67

parts = []
for column, n in zip(df.columns[i:j], range(len(df.columns[i:j]))):
  title = "\n".join(wrap(column.replace("/", " ").replace("_", " "), 40))
  series = df[column].value_counts()

  df2 = series.to_frame().reset_index()
  df2.columns.values[0] = title
  df2.columns.values[1] = "Frequency"

  df2['Percentage (%)'] = np.round(((df2['Frequency'] /
                df2['Frequency'].sum()) * 100.0), 2)

  if n == 0:
      heading = 'Created at TSSFL ODF: www.tssfl.com'
  else:
      heading = "Table %s" % (n + 1)
  df2.columns = pd.MultiIndex.from_product([[heading], df2.columns])

  parts.append(build_table(df2, 'green_light', font_size='medium',
                           font_family='Open Sans, sans-serif',
                           text_align='left', width='auto', index=False,
                           even_color='black', even_bg_color='white'))

with open("Table.html", "w+") as file:
    file.write("\n".join(parts))

# One page per table, as before.
page_break = '<div style="page-break-after: always;"></div>'
HTML(string=page_break.join(parts)).write_pdf("./Merged_TablesXY.pdf")
print("Merged_TablesXY.pdf  -  %d frequency tables" % len(parts))
