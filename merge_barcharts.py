#Plot some graph
#Import required libraries
import gspread
import urllib.request
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from statsmodels.graphics.mosaicplot import mosaic
from textwrap import wrap
import requests
import io

#Merge files
from PyPDF4 import PdfFileMerger, PdfFileReader
mergedObject = PdfFileMerger()
#REDCap
textstr = 'Created at \nwww.tssfl.com'

#Let's visualize
#Graph styles and font size
sns.set_style('darkgrid') # darkgrid, white grid, dark, white and ticks
plt.rc('axes', titlesize=18)     # fontsize of the axes title
plt.rc('axes', labelsize=14)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=13)    # fontsize of the tick labels
plt.rc('ytick', labelsize=13)    # fontsize of the tick labels
plt.rc('legend', fontsize=13)    # legend fontsize
plt.rc('font', size=13)          # controls default text sizes

"""
sheet_id = "1_dkk7q41RfE4V3HBokcgqhrqOVDA26plu_MJKwE8OBY"
sheet_name = "Sheet1"
url_1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
df = pd.read_csv(url_1)
"""
url = "https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/teachers_survey_data.csv"
download = requests.get(url).content
df = pd.read_csv(io.StringIO(download.decode('utf-8'))
df = df.replace(r"_", " ", regex=True)
total = float(len(df))

#get column range
df1 = df.columns.get_loc("group_ms4ff82/Indicate_whether_you_ommunities_or_groups/School_wide_structur_unities_PLCs_groups")
df2 = df.columns.get_loc("group_ms4ff82/Indicate_whether_you_ommunities_or_groups/ZOOM_discussions_tha_hing_related_matters")
print(df1, df2)
df3 = df.iloc[:, np.r_[9, 13]] #[9, 13]
#df4 = df.iloc[:, np.r_[88:96]]
df4 = df.iloc[:, np.r_[58:67]]
colors1 = ['#ff6666', '#ffcc99', '#99ff99', '#66b3ff', 'tomato', 'gold', 'skyblue', '#ffcc99', 'orange','blue','green','red', 'orange','blue','lime','red']
#Loop over columns
for column1, i in zip(df4.columns, range(len(df4.columns))):
    for column2, j in zip(df3.columns, range(len(df3.columns))):

        #df[column1] = ['\n'.join(wrap(x, 10)) for x in  df[column1]]
        plt.figure(figsize=(17.5,7.))
        ax = plt.subplot(111)
        ax = sns.countplot(x=column1,data=df, hue=column2, palette=colors1)
        plt.xticks(rotation=90)
        for p in ax.patches[0:]:
            h = p.get_height()
            x = p.get_x()+p.get_width()/2.0
            if h != 0:
                ax.annotate("%g" % p.get_height(), xy=(x-0.01,h), xytext=(0,4), rotation=0, textcoords="offset points", ha="center",    va="bottom", color='green')

        for p in ax.patches:
            percentage = '{:.2f}%'.format(100 * p.get_height()/total)
            x = p.get_x() + p.get_width()
            y = p.get_height()
            ax.annotate(percentage, (x-0.01, y+0.45),ha='center', rotation=90, color='red')

        xlabel = "\n".join(wrap(column1.replace("/", " ").replace("_", " "), 120))
        #plt.xlabel(xlabel, labelpad=10)
        plt.ylabel("Frequency")
        plt.tight_layout()
        #ax.legend(bbox_to_anchor=(0.805, 1.0))
        #plt.legend(loc=1)
        plt.gcf().text(0.02, 0.93, textstr, fontsize=14, color='green')
        plt.savefig("./barchart_%s_%s.pdf" % (i, j), bbox_inches='tight')
        # Call the PdfFileMerger
        mergedObject.append(PdfFileReader('./barchart_%s_%s' % (i, j) + '.pdf', 'rb'))
        plt.show()
        plt.clf()      

#Write/merge all the files into a file which is named as shown below
mergedObject.write("./Merged_Charts_XY.pdf")
