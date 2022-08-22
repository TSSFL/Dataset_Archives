#Plot some graph
#Import required libraries
import gspread
import urllib.request
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from statsmodels.graphics.mosaicplot import mosaic
import requests
import io

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
sheet_id = "1xjLTkLxr6-3cIGVbtMRHhXAkVgF7TCdis-eLWZQm6sI"
sheet_name = "Sheet1"
url_1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
"""
var1 = "group_ow7qd27/Subject_for_assessment"
var2 = "group_da25q48/What_are_your_percep_s_teaching_knowledge/Our_teacher_presents_y_and_systematically"
var3 = "group_da25q48/What_are_your_percep_s_teaching_knowledge/The_teacher_usually_ives_before_teaching"
var4 = "group_da25q48/What_are_your_percep_s_teaching_knowledge/Our_teacher_collects_ow_we_want_to_learn"
title = ["Subjects", "Question 1 Responses", "Question 2 Responses", "Question 3 Responses"]
colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
colors = ["#900C3F", '#C70039', '#FF5733', '#FFC300']
#colors = ['orange','blue','green','red'] #explsion
#colors = ['#ff6666', '#ffcc99', '#99ff99', '#66b3ff']

#data = pd.read_csv(url_1)
url = 'https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/students_survey_data.csv'
download = requests.get(url).content
#Reading the downloaded content and turning it into a pandas dataframe
df = pd.read_csv(io.StringIO(download.decode('utf-8')))

#Replace underscores with white spaces
data = df.replace(r"_", " ", regex=True)

categorical_features = [var1, var2, var3, var4]
fig, ax = plt.subplots(1, len(categorical_features), figsize=(16,8))
for i, categorical_feature in enumerate(data[categorical_features]):
  data[categorical_feature].value_counts().plot(kind="bar", ax=ax[i], color=colors[i]).set_title(title[i], color=colors[i])

xlocs, xlabs = plt.xticks()
for i, v in enumerate(data[categorical_feature].value_counts()):
  plt.text(xlocs[i] - 0.14, v + 1.0, str(int(round(v))), color='red', va="center", rotation=0)    

"""    
for p in ax.patches[0:]:
h = p.get_height()
x = p.get_x()+p.get_width()/2.0
if h != 0:
    ax.annotate("%g" % p.get_height(), xy=(x,h), xytext=(0,4), rotation=90,
               textcoords="offset points", ha="center", va="bottom")
"""
plt.tight_layout()
plt.gcf().text(0.02, 0.02, textstr, fontsize=14, color='green')
plt.show()
