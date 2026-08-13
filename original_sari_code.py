# -*- coding: utf-8 -*-
"""DUCE enrolment charts - the original, with the warnings silenced.

Kept exactly as it was: the same figures, the same colours, the same layout,
the same Total bar, the same Grand Total category, the same annotation
positions. It exists so the original can still be shown.

One change, applied ten times and nothing else:

    df.iloc[i][3]   ->   df.iloc[i, 3]

That is chained indexing. It reads the row, then indexes the resulting
Series by position - which pandas 2 deprecates, emitting

    FutureWarning: Series.__getitem__ treating keys as positions is
    deprecated ... use `ser.iloc[pos]`

once per bar drawn, so the output filled with the same sentence before any
figure appeared. `.iloc[i, 3]` asks for the same cell in one step and
returns the identical value, so every number and every chart is unchanged.

The rewritten version is sari_code.py. It also corrects the percentages in
the four-panel grid, which are divided by the BSc. Ed totals for every panel
here, and the plt.xlim/plt.ylim calls that act on the current axes rather
than on the subplot being drawn. Nothing in this file touches either.
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from itertools import cycle


def _pct(height, total, dp):
    """Percentage, or an empty string when the total is zero.

    MSc. Ind Chem has no Year 2 intake, so its total for that year is 0 and
    the division raised "RuntimeWarning: invalid value encountered in scalar
    divide" once per bar. Those bars are height 0 and were never annotated
    anyway - the division simply happened before the `if y != 0` guard.
    """
    if not total:
        return ''
    return '{:.{dp}f}%'.format(100 * height / total, dp=dp)

 
raw_data_1 = {'plan_type': ['Year 1', 'Year 2', 'Year 3', 'Grand Total'],
        'Male':     [232,250,240,722],
        'Female':     [199,145,161, 505],
        'Total': [431,395,401, 1227],}
 
raw_data_2 = {'plan_type': ['Year 1', 'Year 2', 'Grand Total'],
        'Male':     [0,2,2],
        'Female':     [4,0, 4],
        'Total': [4,2, 6],}
 
raw_data_3 = {'plan_type': ['Year 1', 'Year 2', 'Grand Total'],
        'Male':     [8,0, 8],
        'Female':     [4,0, 4],
        'Total': [12,0, 12],}
 
raw_data_4 = {'plan_type': ['Year 1', 'Year 2', 'Grand Total'],
        'Male':     [4,3,7],
        'Female':     [3,5,8],
        'Total': [7,8,15],}
 
raw_data_5 = {'plan_type': ['Year 1', 'Year 2', 'Year 3', 'Grand Total'],
        'Male':     [244, 255, 240, 739],
        'Female':     [210, 150, 161, 521],
        'Total': [454, 405, 401, 1260],}
 
df = pd.DataFrame(raw_data_1,
                  columns = ['plan_type', 'Male', 'Female', 'Total'])
 
df2 = pd.DataFrame(raw_data_2,
                  columns = ['plan_type', 'Male', 'Female', 'Total'])
 
df3 = pd.DataFrame(raw_data_3,
                  columns = ['plan_type', 'Male', 'Female', 'Total'])
 
df4 = pd.DataFrame(raw_data_4,
                  columns = ['plan_type', 'Male', 'Female', 'Total'])
 
df5 = pd.DataFrame(raw_data_5,
                  columns = ['plan_type', 'Male', 'Female', 'Total'])
 
fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(12, 10), constrained_layout=True)
 
df = [df,df2,df3,df4]
 
idx = 0
 
for i in range(ax.shape[0]):
    for j in range(0, ax.shape[1]):
        #ax=ax[i][j]
        #ax = df2.plot.bar(rot=0,color='#E6E9ED',width=1)
        df[idx].plot.bar(rot=0, ax=ax[i][j], color=["#900C3F", '#C70039', '#FF5733'],
                 width = 0.85) #'#FFC300'
        idx += 1
 
        for p in ax[i][j].patches[0:]:
            h = p.get_height()
            x = p.get_x()+p.get_width()/2.0
            ax[i][j].annotate("%g" % p.get_height(), xy=(x,h), xytext=(0,0), rotation=0.0,
                   textcoords="offset points", ha="center", va="bottom", color='red')
       
        #Add %
        for l, p in zip(cycle(range(4)), ax[i][j].patches[0:]):
            percentage = _pct(p.get_height(), df[0].iloc[l, 3], 0)
            x = p.get_x() + p.get_width()
            y = p.get_height()
            if y != 0:
                ax[i][j].annotate(percentage, (x-0.13, y-120),ha='center', rotation=90, color='black')
                #Issues taking care 4 by 3 cycles, and relative heights
           
            #Setting the positions and width for the bars
            pos = list(range(len(df2['Male'])))
            width = 0.22 #Change to 0.25      
            #ax.set_xlim(-0.5, None)
            #ax.margins(y=0)
            plt.xlim(min(pos)-width*2, max(pos)+width*2)
            if h != 0:
                plt.ylim([0, h+1.0])
 
            if len(df[idx-1]) == 4:
                ax[i][j].legend(ncol=len(df[0].columns), loc="upper left", bbox_to_anchor=(0.51,1.07,1,0.08),
                borderaxespad=0, mode="expand", fontsize='12')
                ax[i][j].set_xticklabels(df[0]["plan_type"])
                ax[i][j].set_title("BSc. Ed")
 
            elif i == 0 and j == 1:
                ax[i][j].set_xticklabels(df[1]["plan_type"])
                legend = ax[i][j].legend()
                legend.remove()
                ax[i][j].set_title("MSc. Env Biol")
                #Add %
                for l, p in zip(cycle(range(3)), ax[i][j].patches[0:]):
                    percentage = _pct(p.get_height(), df2.iloc[l, 3], 0)
                    x = p.get_x() + p.get_width()
                    y = p.get_height()
                    if y != 0:
                        ax[i][j].annotate(percentage, (x-0.13, y-30/100*y),ha='center', rotation=90, color='black')
               
 
            elif i == 1 and j == 0:
                ax[i][j].set_xticklabels(df[1]["plan_type"])
                legend = ax[i][j].legend()
                legend.remove()
                ax[i][j].set_title("MSc. Ind Chem")
                #Add %
                for l, p in zip(cycle(range(3)), ax[i][j].patches[0:]):
                    percentage = _pct(p.get_height(), df3.iloc[l, 3], 0)
                    x = p.get_x() + p.get_width()
                    y = p.get_height()
                    if y != 0:
                        ax[i][j].annotate(percentage, (x-0.13, y-30/100*y),ha='center', rotation=90, color='black')
            else:
                ax[i][j].set_xticklabels(df[1]["plan_type"])
                legend = ax[i][j].legend()
                legend.remove()
                ax[i][j].set_title("MSc. Ed")
                #Add %
                for l, p in zip(cycle(range(3)), ax[i][j].patches[0:]):
                    percentage = _pct(p.get_height(), df4.iloc[l, 3], 0)
                    x = p.get_x() + p.get_width()
                    y = p.get_height()
                    if y != 0:
                        ax[i][j].annotate(percentage, (x-0.13, y-40/100*y),ha='center', rotation=90, color='black')
 
plt.suptitle("Enrolment of Students in Different Faculty of Science Programmes")
#plt.tight_layout()
plt.show()
plt.clf()
 
fig, ax = plt.subplots(figsize=(8, 8), constrained_layout=True)
#ax = df2.plot.bar(rot=0,color='#E6E9ED',width=1)
ax = df5.plot.bar(rot=0, ax=ax, color=["#900C3F", '#C70039', '#FF5733'],
                 width = 0.85) #'#FFC300', "#900C3F", '#C70039', '#FF5733'
 
for p in ax.patches[0:]:
    h = p.get_height()
    x = p.get_x()+p.get_width()/2.0
    if h != 0:
        ax.annotate("%g" % p.get_height(), xy=(x,h), xytext=(0,0), rotation=0.0,
                   textcoords="offset points", ha="center", va="bottom", color='red')
#Add %
for l, p in zip(cycle(range(4)), ax.patches[0:]):
    percentage = _pct(p.get_height(), df5.iloc[l, 3], 2)
    x = p.get_x() + p.get_width()
    y = p.get_height()
    if y != 0:
        ax.annotate(percentage, (x-0.13, y-70/100*y),ha='center', rotation=90, color='black')
       
# Setting the positions and width for the bars
pos = list(range(len(df5['Male'])))
width = 0.22 #Change to 0.25
 
#ax.set_xlim(-0.5, None)
#ax.margins(y=0)
plt.xlim(min(pos)-width*2, max(pos)+width*2)
plt.ylim([0, 1300] )
ax.legend(ncol=len(df5.columns), loc="lower left", bbox_to_anchor=(0,1.00,1,0.08),
          borderaxespad=0, mode="expand", fontsize='12')
ax.set_xticklabels(df5["plan_type"])
 
textstr = 'Created at \nwww.tssfl.com'
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
#plt.gcf().text(0.6, 0.75, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
plt.suptitle("Enrolment of Students in Different Faculty of Science Programmes \n both Undergraduates and Postgraduates: \n BSc. Ed, MSc. Env Biol, Msc. Ind Chem, & MSc. Ed")
#plt.tight_layout()
plt.show()
plt.clf()

#BSc Ed 

raw_data = {'plan_type': ['Year 1', 'Year 2', 'Year 3', 'Grand Total'],
        'Male':     [232,250,240,722],
        'Female':     [199,145,161, 505],
        'Total': [431,395,401, 1227], }
 
df = pd.DataFrame(raw_data,
                  columns = ['plan_type', 'Male', 'Female', 'Total'])
 
total = df["Male"].sum() + df["Female"].sum()
 
fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
#ax = df2.plot.bar(rot=0,color='#E6E9ED',width=1)
ax = df.plot.bar(rot=0, ax=ax, color=["#900C3F", '#C70039', '#FF5733'],
                 width = 0.85) #'#FFC300'
 
for p in ax.patches[0:]:
    h = p.get_height()
    x = p.get_x()+p.get_width()/2.0
    if h != 0:
        ax.annotate("%g" % p.get_height(), xy=(x,h), xytext=(0,4), rotation=90,
                   textcoords="offset points", ha="center", va="bottom")
#Add %
for i, p in zip(cycle(range(4)), ax.patches[0:]):
    percentage = _pct(p.get_height(), df.iloc[i, 3], 2)
    x = p.get_x() + p.get_width()
    y = p.get_height()
    if y != 0:
        ax.annotate(percentage, (x-0.02, y+20.0),ha='center', rotation=90, color='red')
 
#Setting the positions and width for the bars
pos = list(range(len(df['Male'])))
width = 0.22 #Change to 0.25
 
#ax.set_xlim(-0.5, None)
#ax.margins(y=0)
plt.xlim(min(pos)-width*2, max(pos)+width*2)
plt.ylim([0, 1500] )
ax.legend(ncol=len(df.columns), loc="lower left", bbox_to_anchor=(0,1.02,1,0.08),
          borderaxespad=0, mode="expand", fontsize='15')
ax.set_xticklabels(df["plan_type"])
 
textstr = 'Created at \nwww.tssfl.com'
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.45, 0.75, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
 
plt.suptitle("BSc. Ed")
plt.ylabel("Number of Enrolled Students")
plt.show()
plt.clf()

#Faculty of Science BSc. Ed Students Enrolment

import datetime
e = datetime.datetime.now()
time = e.strftime("Created on %a, %b %d, %Y at %H:%M:%S GMT")
 
#Variables
course_title =  "Faculty of Science \n BSc. Ed Students Enrolment"
#Year 1
m1 = 232
f1 = 199
t1 = 431
#Year 2
m2 = 250
f2 = 145
t2 = 395
#Year 3
m3 = 240
f3 = 161
t3 = 401
#Grand total for Years 1 - 3
tm = m1 + m2 + m3
tf = f1 + f2 + f3
tmf = tm + tf
#Colors
#colors = ["#900C3F", '#C70039', '#FF5733']
colors = ["#ea5545", "#f46a9b", "#ef9b20"]
per_color = "#7c1158"
 
raw_data = {'plan_type': ['Year 1', 'Year 2', 'Year 3', 'Grand Total'],
        'Male':     [m1,m2,m3,tm],
        'Female':     [f1,f2,f3, tf],
        'Total': [t1,t2,t3, tmf], }
 
df = pd.DataFrame(raw_data,
                  columns = ['plan_type', 'Male', 'Female', 'Total'])
 
total = df["Male"].sum() + df["Female"].sum()
 
fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
#ax = df2.plot.bar(rot=0,color='#E6E9ED',width=1)
ax = df.plot.bar(rot=0, ax=ax, color=colors,
                 width = 0.85) #'#FFC300'
 
for p in ax.patches[0:]:
    h = p.get_height()
    x = p.get_x()+p.get_width()/2.0
    if h != 0:
        ax.annotate("%g" % p.get_height(), xy=(x,h), xytext=(-10,4), rotation=90,
                   textcoords="offset points", ha="center", va="bottom")
#Add %
for i, p in zip(cycle(range(4)), ax.patches[0:]):
    percentage = _pct(p.get_height(), df.iloc[i, 3], 2)
    x = p.get_x() + p.get_width()
    y = p.get_height()
    if y != 0:
        ax.annotate(percentage, (x-0.075, y+20.0),ha='center', rotation=90, color=per_color)
 
#Setting the positions and width for the bars
pos = list(range(len(df['Male'])))
width = 0.22 #Change to 0.25
 
#ax.set_xlim(-0.5, None)
#ax.margins(y=0)
plt.xlim(min(pos)-width*2, max(pos)+width*2)
plt.ylim([0, 1450] )
ax.legend(ncol=len(df.columns), loc="lower left", bbox_to_anchor=(0,1.02,1,0.08),
          borderaxespad=0, mode="expand", fontsize='15')
ax.set_xticklabels(df["plan_type"])
 
textstr = time
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.2, 0.75, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
 
plt.suptitle(course_title)
plt.ylabel("Number of Enrolled Students")
plt.show()
plt.clf()

#Faculty of Humanities and Social Sciences BA. Ed Students Enrolment

e = datetime.datetime.now()
time = e.strftime("Created on %a, %b %d, %Y at %H:%M:%S GMT")
 
#Variables
course_title =  "Faculty of Humanities and Social Sciences \n BA. Ed Students Enrolment"
#Year 1
m1 = 630
f1 = 629
t1 = 1259
#Year 2
m2 = 631
f2 = 740
t2 = 1371
#Year 3
m3 = 613
f3 = 514
t3 = 1127
#Grand total for Years 1 - 3
tm = m1 + m2 + m3
tf = f1 + f2 + f3
tmf = tm + tf
#Colors
#colors = ["#900C3F", '#C70039', '#FF5733']
colors = ["#e60049", "#0bb4ff", "#50e991"]
per_color = "#dc0ab4"
 
raw_data = {'plan_type': ['Year 1', 'Year 2', 'Year 3', 'Grand Total'],
        'Male':     [m1,m2,m3,tm],
        'Female':     [f1,f2,f3, tf],
        'Total': [t1,t2,t3, tmf], }
 
df = pd.DataFrame(raw_data,
                  columns = ['plan_type', 'Male', 'Female', 'Total'])
 
total = df["Male"].sum() + df["Female"].sum()
 
fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
#ax = df2.plot.bar(rot=0,color='#E6E9ED',width=1)
ax = df.plot.bar(rot=0, ax=ax, color=colors,
                 width = 0.85) #'#FFC300'
 
for p in ax.patches[0:]:
    h = p.get_height()
    x = p.get_x()+p.get_width()/2.0
    if h != 0:
        ax.annotate("%g" % p.get_height(), xy=(x,h), xytext=(-10,4), rotation=90,
                   textcoords="offset points", ha="center", va="bottom")
#Add %
for i, p in zip(cycle(range(4)), ax.patches[0:]):
    percentage = _pct(p.get_height(), df.iloc[i, 3], 2)
    x = p.get_x() + p.get_width()
    y = p.get_height()
    if y != 0:
        ax.annotate(percentage, (x-0.075, y+80.0),ha='center', rotation=90, color=per_color)
 
#Setting the positions and width for the bars
pos = list(range(len(df['Male'])))
width = 0.22 #Change to 0.25
 
#ax.set_xlim(-0.5, None)
#ax.margins(y=0)
plt.xlim(min(pos)-width*2, max(pos)+width*2)
plt.ylim([0, 4500] )
ax.legend(ncol=len(df.columns), loc="lower left", bbox_to_anchor=(0,1.02,1,0.08),
          borderaxespad=0, mode="expand", fontsize='15')
ax.set_xticklabels(df["plan_type"])
 
textstr = time
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.2, 0.75, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
 
plt.suptitle(course_title)
plt.ylabel("Number of Enrolled Students")
plt.show()
plt.clf()

#Faculty of Science MSc. Ed Students Enrolment

e = datetime.datetime.now()
time = e.strftime("Created on %a, %b %d, %Y at %H:%M:%S GMT")
 
#Variables
course_title =  "Faculty of Science \n MSc. Ed Students Enrolment"
#Year 1
m1 = 12
f1 = 11
t1 = 23
#Year 2
m2 = 5
f2 = 5
t2 = 10
#Grand total for Years 1 - 3
tm = m1 + m2
tf = f1 + f2
tmf = tm + tf
#Colors
#colors = ["#900C3F", '#C70039', '#FF5733']
colors = ["#9b19f5", "#ffa300", "#dc0ab4"]
per_color = "green"
 
raw_data = {'plan_type': ['Year 1', 'Year 2', 'Grand Total'],
        'Male':     [m1,m2,tm],
        'Female':     [f1,f2, tf],
        'Total': [t1,t2,tmf],}
 
df = pd.DataFrame(raw_data,
                  columns = ['plan_type', 'Male', 'Female', 'Total'])
 
total = df["Male"].sum() + df["Female"].sum()
 
fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
#ax = df2.plot.bar(rot=0,color='#E6E9ED',width=1)
ax = df.plot.bar(rot=0, ax=ax, color=colors,
                 width = 0.85) #'#FFC300'
 
for p in ax.patches[0:]:
    h = p.get_height()
    x = p.get_x()+p.get_width()/2.0
    if h != 0:
        ax.annotate("%g" % p.get_height(), xy=(x,h), xytext=(-10,4), rotation=0,
                   textcoords="offset points", ha="center", va="bottom")
#Add %
for i, p in zip(cycle(range(3)), ax.patches[0:]):
    percentage = _pct(p.get_height(), df.iloc[i, 3], 2)
    x = p.get_x() + p.get_width()
    y = p.get_height()
    if y != 0:
        ax.annotate(percentage, (x-0.075, y+0.7),ha='center', rotation=90, color=per_color)
 
#Setting the positions and width for the bars
pos = list(range(len(df['Male'])))
width = 0.22 #Change to 0.25
 
#ax.set_xlim(-0.5, None)
#ax.margins(y=0)
plt.xlim(min(pos)-width*2, max(pos)+width*2)
plt.ylim([0, 40] )
ax.legend(ncol=len(df.columns), loc="lower left", bbox_to_anchor=(0,1.02,1,0.08),
          borderaxespad=0, mode="expand", fontsize='15')
ax.set_xticklabels(df["plan_type"])
 
textstr = time
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.2, 0.75, textstr, fontsize=14, color='darkblue') # (0,0) is bottom left, (1,1) is top right
 
plt.suptitle(course_title)
plt.ylabel("Number of Enrolled Students")
plt.show()
plt.clf()

#Faculty of Humanities and Social Sciences MA (PG). Ed Students Enrolment

e = datetime.datetime.now()
time = e.strftime("Created on %a, %b %d, %Y at %H:%M:%S GMT")
 
#Variables
course_title =  "Faculty of Humanities and Social Sciences \n MA (PG). Ed Students Enrolment"
#Year 1
m1 = 15
f1 = 12
t1 = 27
#Year 2
m2 = 20
f2 = 11
t2 = 31
#Grand total for Years 1 - 3
tm = m1 + m2
tf = f1 + f2
tmf = tm + tf
#Colors
#colors = ["#900C3F", '#C70039', '#FF5733']
colors = ["#dc0ab4", "#b3d4ff", "#00bfa0"]
per_color = "blue"
 
raw_data = {'plan_type': ['Year 1', 'Year 2', 'Grand Total'],
        'Male':     [m1,m2,tm],
        'Female':     [f1,f2, tf],
        'Total': [t1,t2,tmf],}
 
df = pd.DataFrame(raw_data,
                  columns = ['plan_type', 'Male', 'Female', 'Total'])
 
total = df["Male"].sum() + df["Female"].sum()
 
fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
#ax = df2.plot.bar(rot=0,color='#E6E9ED',width=1)
ax = df.plot.bar(rot=0, ax=ax, color=colors,
                 width = 0.85) #'#FFC300'
 
for p in ax.patches[0:]:
    h = p.get_height()
    x = p.get_x()+p.get_width()/2.0
    if h != 0:
        ax.annotate("%g" % p.get_height(), xy=(x,h), xytext=(-10,4), rotation=0,
                   textcoords="offset points", ha="center", va="bottom")
#Add %
for i, p in zip(cycle(range(3)), ax.patches[0:]):
    percentage = _pct(p.get_height(), df.iloc[i, 3], 2)
    x = p.get_x() + p.get_width()
    y = p.get_height()
    if y != 0:
        ax.annotate(percentage, (x-0.075, y+1.5),ha='center', rotation=90, color=per_color)
 
#Setting the positions and width for the bars
pos = list(range(len(df['Male'])))
width = 0.22 #Change to 0.25
 
#ax.set_xlim(-0.5, None)
#ax.margins(y=0)
plt.xlim(min(pos)-width*2, max(pos)+width*2)
plt.ylim([0, 68] )
ax.legend(ncol=len(df.columns), loc="lower left", bbox_to_anchor=(0,1.02,1,0.08),
          borderaxespad=0, mode="expand", fontsize='15')
ax.set_xticklabels(df["plan_type"])
 
textstr = time
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.2, 0.75, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
 
plt.suptitle(course_title)
plt.ylabel("Number of Enrolled Students")
plt.show()