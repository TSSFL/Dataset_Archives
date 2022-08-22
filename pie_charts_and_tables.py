#Generate pie charts and tables, merge charts in one pdf, similarly for tables:
import requests
import io
from textwrap import wrap
import pandas as pd
import numpy as np
import random
from matplotlib import pyplot as plt

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

def label_function(val):
  return f'{val / 100.0 * len(df):.0f}\n{val:.2f}%'

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
print(df1, df2)
df3 = df.iloc[:, np.r_[5,66]].columns
df4 = df.iloc[:, np.r_[5,66]]
col_list = [chr(i+65) for i in range(len(df4.columns))]
df = df.replace(r"_", " ", regex=True)
i = 5
j = 67

for column, k in zip(df.columns[i:j], range(len(df.columns[i:j]))): #5:65
  fig, ax1 = plt.subplots(figsize=(8, 6))
  title = "\n".join(wrap(column.replace("/", " ").replace("_", " "), 40))
  df.groupby(column).size().plot(kind='pie', autopct=label_function, textprops={'fontsize': 14},
                                colors=colors1, ax=ax1)
  ax1.set_ylabel('')
  ax1.set_title(title, size=18)
  plt.tight_layout()
  plt.gcf().text(0.02, 0.80, textstr, fontsize=14, color='green')
  plt.savefig("./chart_%s.pdf" % (k), bbox_inches='tight')
  if k == 0 or k == 50 or k == 60 or k == 61:
      continue
  else:
      print(k)
      plt.show()


mergedCharts = PdfFileMerger()
for fileNumber in range(0, k+1):

  if fileNumber == 0 or fileNumber == 50 or fileNumber == 60 or fileNumber == 61:
      continue
  else:
      #print(fileNumber)
      mergedCharts.append(PdfFileReader('chart_' + str(fileNumber)+ '.pdf', 'rb'))

#Write all the files into a file which is named as shown below
mergedCharts.write("./Merged_ChartsXX.pdf")


#Write/merge all the files into a file which is named as shown below
#mergedCharts.write("/home/elimboto/KoBo_Data_Processing/Charts_R_Japhet1/Charts_XY.pdf")

#Create and Merge Tables

#Call the PdfFileMerger
mergedTables = PdfFileMerger()

#https://caendkoelsch.wordpress.com/2019/05/10/merging-multiple-pdfs-into-a-single-pdf/
from pretty_html_table import build_table
import pandas as pd
import seaborn as sns

from weasyprint import CSS
from weasyprint import HTML


for column, i in zip(df.columns[i:j], range(len(df.columns[i:j]))): #5:65
  title = "\n".join(wrap(column.replace("/", " ").replace("_", " "), 40))
  series = df[column].value_counts()

  df2 = series.to_frame().reset_index()
  df2.columns.values[0] = title
  df2.columns.values[1] = "Frequency"

  #df2['B'].value_counts(normalize=True) * 100
  #(df2['B'].value_counts()/df2['B'].count())*100
  df2['Percentage (%)'] = np.round(((df2['Frequency'] /
                df2['Frequency'].sum()) * 100.0), 2)
  #print(df2['Percentage (%)'].sum())
  table = "Table %s" % (i+1)
  #https://stackoverflow.com/questions/48274259/is-there-a-way-to-add-a-title-to-a-dataframe-spanning-across-multiple-columns
  if i == 0:
      textstr = 'Created at TSSFL ODF: www.tssfl.com'
      df2.columns=pd.MultiIndex.from_product([[textstr],df2.columns])
  else:
      df2.columns=pd.MultiIndex.from_product([[table],df2.columns])
  output = build_table(df2, 'green_light', font_size='medium', font_family='Open Sans, sans-serif', text_align='left', width='auto',        index=False, even_color='black', even_bg_color='white')

  with open("Table.html","w+") as file:
      file.write(output)

  HTML(string=output).write_pdf("./Table_%s.pdf" % i)

#Write all the files into a file which is named as shown below
for fileNumber in range(0, i+1):
  mergedTables.append(PdfFileReader('Table_' + str(fileNumber) + '.pdf', 'rb'))

mergedTables.write("./Merged_TablesXY.pdf")

#Delete images and pdfs
#import os
#os.remove("chart_*.pdf")
#os.remove("Table_*.pdf")
#Multiple headers https://pretagteam.com/question/pandas-dataframe-making-multiple-rows-of-headers
#Concatenate pd dataframes https://www.geeksforgeeks.org/how-to-concatenate-two-or-more-pandas-dataframes/
