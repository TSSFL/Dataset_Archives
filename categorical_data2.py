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
sheet_id = "1pm1mGdRgpitrYQiGqUNSHPdR43e-ZSXCavYr-TcqtwU"
sheet_name = "Sheet1"
url_1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
data = pd.read_csv(url_1)
"""
url = 'https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/Categorical_data.csv'
download = requests.get(url).content
data = pd.read_csv(io.StringIO(download.decode('utf-8')))

#print(data)
#Drop first row
#df = data.drop(labels=0, axis=0)
#df = data.drop(data.index[0])
df = data[~data['Ailment cured'].isin(['HIV/AIDS'])]
#df['Ailment cured'] = df['Ailment cured'].replace({'Gonorrhoea, syphilis':'Gonorrhoea & Syphilis'})
df["Ailment cured"] = df['Ailment cured'].replace('Gonorrhoea, syphilis', 'Gonorrhoea & Syphilis')
#print(df)

#Growth form vs Citation
plt.figure(figsize=(8,5))
sns.boxplot(x='Growth form',y='Citation',data=data, palette='rainbow')
plt.show()

#Citation vs Growth form
plt.figure(figsize=(8,5))
sns.boxplot(x='Citation',y='Growth form',data=data, palette='rainbow')
plt.show()

#Citation vs Growth form
plt.figure(figsize=(8,5))
sns.boxplot(x='Citation',y='Part used',data=data, palette='rainbow')
plt.tight_layout() #figure.savefig('myplot.png', bbox_inches='tight')
plt.show()

#Citation vs Ailment cured
plt.figure(figsize=(10,5))
sns.boxplot(x=df["Ailment cured"],y=df['Citation'],data=df, palette='rainbow')
plt.xlabel("Ailment cured", labelpad=15)
plt.tight_layout()
plt.show()

#Swarm plot
fig = plt.gcf()
fig.set_size_inches(30, 30)
sns.catplot(x="Citation", y="Scientific name", hue="Ailment cured", kind="swarm", data=df)
plt.tight_layout()
plt.show()


#Adding hue
#Citation vs Growth form
plt.figure(figsize=(8,5))
sns.boxplot(x='Citation',y='Growth form',data=data, hue ='Part used', palette='rainbow')
plt.tight_layout()
plt.show()

plt.figure(figsize=(8,5))
sns.boxplot(x='Citation',y='Growth form',data=data, hue ='Ailment cured', palette='rainbow')
plt.tight_layout()
plt.show()

#Violin plots
plt.figure(figsize=(8,6))
sns.violinplot(x='Citation',y='Growth form',data=data, hue ='Part used', palette='rainbow')
plt.show()

#Violin plots
plt.figure(figsize=(8,6))
sns.violinplot(x='Citation',y='Growth form',data=data, hue ='Ailment cured',palette='rainbow')
plt.show()

#Boxen plots
plt.figure(figsize=(8,6))
sns.boxenplot(x='Citation',y='Growth form',data=data, hue ='Part used', palette='rainbow')
plt.show()

plt.figure(figsize=(8,6))
sns.boxenplot(x='Citation',y='Part used',data=data, hue ='Ailment cured', palette='rainbow')
plt.tight_layout()
plt.show()

#Bar plots
plt.figure(figsize=(12,6))
sns.barplot(x='Growth form',y='Citation',data=data, palette='rainbow', hue='Part used')
plt.tight_layout()
plt.show()

plt.figure(figsize=(12,6))
ax = plt.subplot(111)
sns.barplot(x='Ailment cured',y='Citation',data=data, palette='rainbow', hue='Part used')
plt.tight_layout()
ax.legend(bbox_to_anchor=(0.8, 0.45))
#plt.legend(loc=1)
plt.show()

#Point plot
plt.figure(figsize=(10,6))
sns.pointplot(x='Citation',y='Growth form',data=data)
plt.show()

plt.figure(figsize=(10,6))
sns.pointplot(x='Citation',y='Growth form',data=data, hue='Part used')
plt.show()

plt.figure(figsize=(10,6))
sns.pointplot(x='Citation',y='Growth form',data=data, hue='Part used')
plt.show()

plt.figure(figsize=(10,6))
sns.pointplot(x='Citation',y='Growth form',data=data, hue='Ailment cured')
plt.show()

#Count plot
plt.figure(figsize=(10,6))
sns.countplot(x='Growth form',data=data, palette='rainbow')
plt.show()

plt.figure(figsize=(10,6))
sns.countplot(x='Growth form',data=data, hue='Part used', palette='rainbow')
plt.legend(loc=1)
plt.show()

plt.figure(figsize=(10,6))
sns.countplot(x='Growth form',data=data, hue='Ailment cured', palette='rainbow')
plt.legend(loc=2)
plt.show()


#Strip plot - Categorical Scatter Plots
plt.figure(figsize=(12,8))
sns.stripplot(x='Citation', y='Growth form', data=data, jitter=True, hue= 'Part used', dodge=True, palette='viridis')
plt.show()

#Swarm plots
plt.figure(figsize=(10,6))
sns.swarmplot(x='Citation', y='Ailment cured', data=data, hue='Growth form', dodge=True, palette='viridis')
plt.tight_layout()
plt.show()

"""
#Combining plots
plt.figure(figsize=(12,8))
sns.violinplot(x='Citation',y="Growth form", data=data, hue='Part used', dodge='True', palette='rainbow')
sns.swarmplot(x='Citation',y="Growth form", data=data, hue='Part used', dodge='True', color='grey', alpha=.8, s=4)
plt.show()

#Plot 2
plt.figure(figsize=(12,8))
sns.boxplot(x='Citation',y='Part used',hue='Growth form',data=data, palette='rainbow')
sns.swarmplot(x='Citation',y='Part used',hue='Growth form', dodge=True,data=data, alpha=.8,color='grey',s=4)

#Plot 3
plt.figure(figsize=(12,7))
sns.barplot(x='Growth form',y='Citation',data=data, palette='rainbow', hue='Part used')
sns.stripplot(x='Growth form',y="Citation",data=data, hue='Citation', dodge='True', color='grey', alpha=.8, s=2)
plt.show()

#Faceting Data with Catplot
#https://towardsdatascience.com/a-complete-guide-to-plotting-categorical-variables-with-seaborn-bfe54db66bec
g = sns.catplot(x='Citation',y='Growth form', col = 'Local name', data=data,
          kind='bar', aspect=.6, palette='Set2')
(g.set_axis_labels("Class", "Survival Rate")
.set_titles("{col_name}")
.set(ylim=(0,1)))
plt.tight_layout()
plt.savefig('seaborn_catplot.png', dpi=1000)
"""

categorical_features = ["Growth form", "Part used", "Ailment cured", "Citation"]
fig, ax = plt.subplots(1, len(categorical_features), figsize=(16,8))
for i, categorical_feature in enumerate(data[categorical_features]):
  data[categorical_feature].value_counts().plot(kind="bar", ax=ax[i]).set_title(categorical_feature)
plt.tight_layout()
plt.show()

"""
#print(data)
#print(data['Local Name'])
data['Growth form'].value_counts().plot(kind='bar')
plt.show()
#data['Growth form'].value_counts().plot(kind='hist')

plt.figure()
from statsmodels.graphics.mosaicplot import mosaic
plt.rcParams['font.size'] = 16.0
mosaic(data, ['Growth form', 'Part used']);
plt.show()
"""
plt.figure()
sns.barplot(x=df['Growth form'].head(3),y=df['Citation'],data=df)
plt.show()

#Add frequencies/counts and percentages on bar tops
total = float(len(data))
print(total)
plt.figure(figsize=(10,6))
ax = sns.countplot(x='Growth form',data=data, hue='Part used', palette='rainbow')

for p in ax.patches[0:]:
  h = p.get_height()
  x = p.get_x()+p.get_width()/2.0
  if h != 0:
      ax.annotate("%g" % p.get_height(), xy=(x,h-0.19), xytext=(0,4), rotation=0,
                 textcoords="offset points", ha="center", va="bottom", color='green')

for p in ax.patches:
  percentage = '{:.2f}%'.format(100 * p.get_height()/total)
  x = p.get_x() + p.get_width()
  y = p.get_height()
  ax.annotate(percentage, (x-0.02, y+0.45),ha='center', rotation=90, color='red')

plt.tight_layout()
plt.ylabel("Counts")
plt.legend(loc=1)
plt.gcf().text(0.1, 0.77, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

plt.figure(figsize=(10,6))
ax = sns.countplot(x='Growth form',data=data, hue='Ailment cured', palette='rainbow')
for p in ax.patches[0:]:
  h = p.get_height()
  x = p.get_x()+p.get_width()/2.0
  if h != 0:
      ax.annotate("%g" % p.get_height(), xy=(x,h-0.19), xytext=(0,4), rotation=0,
              textcoords="offset points", ha="center", va="bottom", color='green')

for p in ax.patches:
  percentage = '{:.2f}%'.format(100 * p.get_height()/total)
  x = p.get_x() + p.get_width()
  y = p.get_height()
  ax.annotate(percentage, (x-0.06, y+0.30),ha='center', rotation=90, color='red')

plt.tight_layout()
plt.ylabel("Counts")
plt.legend(loc=1)
plt.gcf().text(0.1, 0.77, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Add frequencies only
plt.figure(figsize=(10,6))
ax = sns.countplot(x='Growth form',data=data, hue='Part used', palette='rainbow')

for p in ax.patches[0:]:
  h = p.get_height()
  x = p.get_x()+p.get_width()/2.0
  if h != 0:
      ax.annotate("%g" % p.get_height(), xy=(x,h), xytext=(0,4), rotation=0,
                 textcoords="offset points", ha="center", va="bottom", color='green')
plt.tight_layout()
plt.ylabel("Counts")
plt.legend(loc=1)
plt.gcf().text(0.1, 0.77, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Add percentages only
plt.figure(figsize=(10,6))
ax = sns.countplot(x='Growth form',data=data, hue='Part used', palette='rainbow')

for p in ax.patches:
  percentage = '{:.2f}%'.format(100 * p.get_height()/total)
  x = p.get_x() + p.get_width()/2.0
  h = p.get_height()
  if h !=0:
      ax.annotate(percentage, xy=(x,h+0.1), ha="center", va="bottom", rotation=90, color='red') #textcoords="offset points",

plt.tight_layout()
plt.ylabel("Counts")
plt.legend(loc=1)
plt.gcf().text(0.1, 0.77, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Add frequencies only
plt.figure(figsize=(10,6))
ax = sns.countplot(x='Growth form',data=data, hue='Ailment cured', palette='rainbow')
for p in ax.patches[0:]:
  h = p.get_height()
  x = p.get_x()+p.get_width()/2.0
  if h != 0:
      ax.annotate("%g" % p.get_height(), xy=(x,h), xytext=(0,4), rotation=0,
              textcoords="offset points", ha="center", va="bottom", color='green')

plt.tight_layout()
plt.ylabel("Counts")
plt.legend(loc=1)
plt.gcf().text(0.1, 0.77, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Add percentages only
plt.figure(figsize=(10,6))
ax = sns.countplot(x='Growth form',data=data, hue='Ailment cured', palette='rainbow')

for p in ax.patches:
  percentage = '{:.2f}%'.format(100 * p.get_height()/total)
  x = p.get_x() + p.get_width()/2.0
  h = p.get_height()
  if h !=0:
      ax.annotate(percentage, xy=(x,h+0.1), ha="center", va="bottom", rotation=90, color='red') #textcoords="offset points",

plt.tight_layout()
plt.ylabel("Counts")
plt.legend(loc=1)
plt.gcf().text(0.1, 0.77, textstr, fontsize=14, color='green')
plt.show()
plt.clf()    
