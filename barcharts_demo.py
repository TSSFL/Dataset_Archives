#Various Barcharts Codes

#Code 1

#https://stackoverflow.com/questions/43554521/add-data-label-to-grouped-bar-chart-in-matplotlib
#Code adapted from:  
#https://chrisalbon.com/python/matplotlib_grouped_bar_plot.html
#matplotlib online
#Grouped bars
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import requests
import io

raw_data = {'plan_type': ['A1', 'A2', 'A3', 'A4', 'A5', 'A6'],
        'Group A':     [100, 0, 0, 0, 0, 0],
        'Group B':     [48, 16, 9, 22, 5, 0],
        'Group C':     [18, 28, 84, 34, 11, 0],
        'Group D': [49, 13, 7, 23, 6, 0],
        'Group E':          [57, 16, 9, 26, 3, 0]

    }
df = pd.DataFrame(raw_data, columns = ['plan_type', 'Group B', 'Group C', 'Group D', 'Group E'])


df2 =pd.DataFrame(raw_data, columns = ['plan_type', 'Group A'])



# Setting the positions and width for the bars
pos = list(range(len(df['Group B'])))
width = 0.3

# Plotting the bars
fig, ax = plt.subplots(figsize=(8, 5))

#This creates another y-axis that shares the same x-axis

# Create a bar with Group A data,
# in position pos + some width buffer,
plt.bar(pos,
    #using df['Group E'] data,
    df2['Group A'],
    # of width
    width*8,
    # with alpha 0.5
    alpha=1,
    # with color
    color='gray',
    # with label the fourth value in plan_type
    label=df2['plan_type'][0])


# Create a bar with Group B data,
# in position pos,
plt.bar(pos,
    #using df['Group B'] data,
    df['Group B'],
    # of width
    width,
    # with alpha 1  
    alpha=1,
    # with color
    color='#900C3F',
    # with label the first value in plan_type
    label=df['plan_type'][0])

# Create a bar with Group C data,
# in position pos + some width buffer,
plt.bar([p + width for p in pos],
    #using df['Group C'] data,
    df['Group C'],
    # of width
    width,
    # with alpha 1
    alpha=1.0,
    # with color
    color='#C70039',
    # with label the second value in plan_type
    label=df['plan_type'][1])

# Create a bar with Group D data,
# in position pos + some width buffer,
plt.bar([p + width*2 for p in pos],
    #using df['Group D'] data,
    df['Group D'],
    # of width
    width,
    # with alpha 1
    alpha=1,
    # with color
    color='#FF5733',
    # with label the third value in plan_type
    label=df['plan_type'][2])

# Create a bar with Group E data,
# in position pos + some width buffer,
plt.bar([p + width*3 for p in pos],
    #using df['Group E'] data,
    df['Group E'],
    # of width
    width,
    # with alpha 1
    alpha=1,
    # with color
    color='#FFC300',
    # with label the fourth value in plan_type
    label=df['plan_type'][3])


# Set the y axis label
ax.set_ylabel('Percent')

# Set the chart's title
ax.set_title('Grouped Data', fontweight = "bold")

# Set the position of the x ticks
ax.set_xticks([p + 1.5 * width for p in pos])

# Set the labels for the x ticks
ax.set_xticklabels(df['plan_type'])

# Setting the x-axis and y-axis limits

plt.xlim(min(pos)-width, max(pos)+width*5)
plt.ylim([0, 100] )
#plt.ylim([0, max(df['Group B'] + df['Group C'] + df['Group D'] + df['Group E'])] )

# Adding the legend and showing the plot.  Upper center location, 5 columns,
#Expanded to fit on one line.
plt.legend(['Group A','Group B', 'Group C', 'Group D', 'Group E'], loc='upper center', ncol=5, mode='expand', fontsize  ='x-small')

#plt.grid()  --> This would add a Grid, but I don't want that.

plt.show()

#Code 2

#https://stackoverflow.com/questions/43554521/add-data-label-to-grouped-bar-chart-in-matplotlib
#Code adapted from:  
#https://chrisalbon.com/python/matplotlib_grouped_bar_plot.html
#matplotlib online

raw_data = {'plan_type': ['Type 1', 'Type 2', 'Type 3', 'Type 4', 'Type 5', 'Type 6'],
        'Group A':     [48, 16, 9, 22, 5, 12],
        'Group B':     [18, 28, 84, 34, 11, 36],
        'Group C': [49, 13, 7, 23, 6, 70],
        'Group D':          [57, 16, 9, 26, 3, 40]

    }
df = pd.DataFrame(raw_data, columns = ['plan_type', 'Group A', 'Group B', 'Group C', 'Group D'])


# Setting the positions and width for the bars
pos = list(range(len(df['Group A'])))

width = 0.22 #Change to 0.25

# Plotting the bars
fig, ax = plt.subplots(figsize=(10, 5))


#This creates another y-axis that shares the same x-axis


# Create a bar with Group A data,
# in position pos + some width buffer,

# Create a bar with Group B data,
# in position pos,
plt.bar(pos,
    #using df['Group A'] data,
    df['Group A'],
    # of width
    width,
    # with alpha 1  
    alpha=1,
    # with color
    color='#900C3F',
    # with label the first value in plan_type
    label=df['plan_type'][0])

# Create a bar with Group B data,
# in position pos + some width buffer,
plt.bar([p + width for p in pos],
    #using df['Group B'] data,
    df['Group B'],
    # of width
    width,
    # with alpha 1
    alpha=1.0,
    # with color
    color='#C70039',
    # with label the second value in plan_type
    label=df['plan_type'][1])

# Create a bar with Group D data,
# in position pos + some width buffer,
plt.bar([p + width*2 for p in pos],
    #using df['Group C'] data,
    df['Group C'],
    # of width
    width,
    # with alpha 1
    alpha=1,
    # with color
    color='#FF5733',
    # with label the third value in plan_type
    label=df['plan_type'][2])

# Create a bar with Group E data,
# in position pos + some width buffer,
plt.bar([p + width*3 for p in pos],
    #using df['Group D'] data,
    df['Group D'],
    # of width
    width,
    # with alpha 1
    alpha=1,
    # with color
    color='#FFC300',
    # with label the fourth value in plan_type
    label=df['plan_type'][3])


# Set the y axis label
ax.set_ylabel('Frequency')

# Set the chart's title
ax.set_title('Grouped Data', fontweight = "bold")

# Set the position of the x ticks
ax.set_xticks([p + 1.5 * width for p in pos])

# Set the labels for the x ticks
ax.set_xticklabels(df['plan_type'])

# Setting the x-axis and y-axis limits

plt.xlim(min(pos)-width, max(pos)+width*4)
plt.ylim([0, 100] )
#plt.ylim([0, max(df['Group A'] + df['Group B'] + df['Group C'] + df['Group D'])] )

# Adding the legend and showing the plot.  Upper center location, 5 columns,
#Expanded to fit on one line.
plt.legend(['Group A', 'Group B', 'Group C', 'Group D'], loc='upper center', ncol=5, mode='expand', fontsize  ='15')

#plt.grid()  --> This would add a Grid, but I don't want that.
textstr = 'Created at \nwww.tssfl.com'
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.02, 0.92, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right

plt.show()

#Code 3

raw_data = {'plan_type': ['Type 1', 'Type 2', 'Type 3', 'Type 4', 'Type 5', 'Type 6'],
        'Group A':     [48, 16, 9, 22, 5, 12],
        'Group B':     [18, 28, 84, 34, 11, 36],
        'Group C': [49, 13, 7, 23, 6, 70],
        'Group D':          [57, 16, 9, 26, 3, 40]
    }
#df2 =pd.DataFrame(raw_data, columns = ['plan_type', 'Group A'])
df = pd.DataFrame(raw_data,
                  columns = ['plan_type', 'Group A', 'Group B', 'Group C', 'Group D'])

fig, ax = plt.subplots(figsize=(10, 6))
#ax = df2.plot.bar(rot=0,color='#E6E9ED',width=1)
ax = df.plot.bar(rot=0, ax=ax, color=["#900C3F", '#C70039', '#FF5733', '#FFC300'],
                 width = 0.85)

for p in ax.patches[0:]:
    h = p.get_height()
    x = p.get_x()+p.get_width()/2.0
    if h != 0:
        ax.annotate("%g" % p.get_height(), xy=(x,h), xytext=(0,4), rotation=90,
                   textcoords="offset points", ha="center", va="bottom")


# Setting the positions and width for the bars
pos = list(range(len(df['Group A'])))
width = 0.22 #Change to 0.25

#ax.set_xlim(-0.5, None)
#ax.margins(y=0)
plt.xlim(min(pos)-width*2, max(pos)+width*2)
plt.ylim([0, 100] )
ax.legend(ncol=len(df.columns), loc="lower left", bbox_to_anchor=(0,1.02,1,0.08),
          borderaxespad=0, mode="expand", fontsize='15')
ax.set_xticklabels(df["plan_type"])

textstr = 'Created at \nwww.tssfl.com'
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.6, 0.75, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
plt.show()

#Code 4

# fig, is the whole thing; ax1 is a subplot in the figure,
# so we reference it to plot bars and lines there
fig, ax1 = plt.subplots()

ind = np.arange(3)
width = 0.15

# per dimension
colors = ['#00ff00', '#0000ff', '#ff00ff']
markers = ['x','o','v']
xticklabels = ['50/50', '60/40', '70/30']

#
group1 = [12,6,5]
group2 = [6,8,12]
group3 = [2,4,9]

#
all_groups = [ group1, group2, group3 ]

# plot each group of bars; loop-variable bar_values contains values for bars
for i, bar_values in enumerate( all_groups ):

  # compute position for each bar
  bar_position = width*i
  ax1.bar( ind + bar_position, bar_values, width, color=colors[i] )

# plot line for each group of bars; loop-variable y_values contains values for lines
for i, y_values in enumerate( all_groups ):

  # moves the beginning of a line to the middle of the bar
  additional_space = (width*i) + (width/2);
  # x_values contains list indices plus additional space
  x_values = [ x + additional_space for x,_ in enumerate( y_values ) ]

  # simply plot the values in y_values
  ax1.plot( x_values, y_values, marker=markers[i], color=colors[i] )

plt.setp([ax1], xticks=ind + width, xticklabels=xticklabels)

plt.tight_layout()
plt.show()

#Code 5

ind = np.arange(5)
avg_bar1 = (71191,2318,57965,40557,14793)
avg_bar2 = (26826,26615,31364,41088,50472)
avg_bar3 = (36232,38038,38615,39014,40812)
avg_bar4 = (26115,25879,55887,28326,27988)

plt.figure(figsize=(9.5, 6.5), tight_layout=True)
rects1 = plt.bar(ind, avg_bar1, 0.20, color='#900C3F',label='Group A')
rects2 = plt.bar(ind + 0.20, avg_bar2, 0.20, color='#C70039', label='Group B')
rects3 = plt.bar(ind + 0.40, avg_bar3, 0.20, color='#FF5733', label='Gropu C')
rects4 = plt.bar(ind + 0.60, avg_bar4, 0.20, color='#FFC300', label='Group D')

high_point_x = []
high_point_y = []    
for i in range(0,5):
    single_bar_group={rects1[i].get_height():rects1[i].get_x() + rects1[i].get_width()/2.0,
                      rects2[i].get_height():rects2[i].get_x() + rects2[i].get_width()/2.0,
                      rects3[i].get_height():rects3[i].get_x() + rects3[i].get_width()/2.0,
                      rects4[i].get_height():rects4[i].get_x() + rects4[i].get_width()/2.0}

    height_list = list(single_bar_group.keys())
    height_list.sort(reverse=True)
    for single_height in height_list:
        high_point_y.append(single_height)
        high_point_x.append(single_bar_group[single_height])
        break

trend_line = plt.plot(high_point_x,high_point_y,marker='o', color='mediumblue', label='Trend Line')

plt.xlabel('Categories')
plt.ylabel('Quantities')
plt.title("Grouped Data")
plt.xticks(ind+0.30, ('Type 1', 'Type 2', 'Type 3', 'Type 4', 'Type 5'))
plt.legend(fontsize='15', loc=1)
textstr = 'Created at \nwww.tssfl.com'
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.3, 0.85, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
plt.show()

#Code 6

myDict = {'Type 1':[3,13,18,16,19,9,13,15,0,2],\
      'Type 2':[23,14,18,24,19,9,14,13,21,22],\
      'Type 3':[38,17,12,15,39,38,23,19,16,16]}

df = pd.DataFrame(myDict)
df_melted = df.melt(value_vars=['Type 1','Type 2','Type 3'])
#Use a lineplot but first, you need to keep the same order because lineplot does not have the order argument as barplot. The steps are:
#1. Create a copy of the dataframe
#2. Set variable to be categorical with the order of ['b','a','c']
#3. lineplot in the same ax

order = ['Type 2', 'Type 1', 'Type 3'] #Try ['a','b','c']
df_2 = df_melted.copy()
df_2['Variable'] = pd.Categorical(df_2['variable'], order)
df_2.sort_values('Variable', inplace=True)

#plot
fig, ax1 = plt.subplots()
sns.barplot(x='variable', y='value', data=df_melted, capsize=0.1, ax=ax1,
            order=order)
sns.lineplot(x='variable', y='value', data=df_2,
             ax=ax1, color='#FF5733', marker='o', linewidth=5, ci=None)
plt.title("Categorical Data")
plt.xlabel("Categories")
plt.ylabel("Quantities")
#plt.grid()  --> This would add a Grid, but I don't want that.
textstr = 'Created at \nwww.tssfl.com'
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.2, 0.75, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
plt.show()

#Code 7

#Creating dataframe
dataFrame = pd.DataFrame({"Car": ['Land Rover', 'Range Rover', 'BMW', 'Hammer', 'Mercedes', 'Jaguar'],"Cubic Capacity": [2800, 3800, 2800, 4500, 2200, 3400],"Price": [5000, 10000, 6000, 12000, 4000, 6500],
})

plt.figure(figsize=(10,6), tight_layout=True)
#Plotting grouped Horizontal Bar Chart with all the columns
dataFrame.plot.barh(x = "Car", title='Car CC and Price', color=("blue", "orange"))

#Display the plotted Horizontal Bar Chart
textstr = 'Created at \nwww.tssfl.com'
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.65, 0.15, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
plt.subplots_adjust(left=0.20)
plt.legend(loc=1)
plt.show()
plt.clf()

#Code 8

# importing package #Ref https://www.geeksforgeeks.org/create-a-grouped-bar-plot-in-matplotlib/
# https://matplotlib.org/stable/gallery/lines_bars_and_markers/barchart.html
#Code 1
# create data
x = np.arange(5)
y1 = [45, 35, 28, 72, 56]
y2 = [20, 65, 50, 45, 78]
width = 0.40

# plot data in grouped manner of bar type
plt.bar(x-0.2, y1, width)
plt.bar(x+0.2, y2, width)
plt.title("Grouped Data")
textstr = 'Created at \nwww.tssfl.com'
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.22, 0.76, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
plt.show()
plt.clf()

#Code 2
# create data
x = np.arange(5)
y1 = [45, 35, 28, 72, 56]
y2 = [20, 65, 50, 45, 78]
y3 = [25, 32, 60, 40, 80]
width = 0.2

# plot data in grouped manner of bar type
plt.bar(x-0.2, y1, width, color='green')
plt.bar(x, y2, width, color='cyan')
plt.bar(x+0.2, y3, width, color='orange')
plt.xticks(x, ['Player 1', 'Player 2', 'Player 3', 'Player 4', 'Player 5'])
plt.xlabel("Players")
plt.ylabel("Scores")
plt.legend(["UEFA", "La Liga", "World Cup"])
plt.gcf().text(0.42, 0.79, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
plt.show()
plt.clf()


#Code 3
# create data
df = pd.DataFrame([['A', 10, 20, 10, 30], ['B', 18, 25, 15, 16], ['C', 12, 15, 19, 6],
                   ['D', 10, 29, 13, 19]],
                  columns=['Streams', 'Group A', 'Group B', 'Group C', 'Group D'])

plt.figure(figsize=(8,5), tight_layout=True)
# plot grouped bar chart
df.plot(x='Streams',
        kind='bar',
        stacked=False,
        title='Grouped Bar Charts')
plt.legend(loc="upper center")
plt.gcf().text(0.15, 0.90, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
plt.show()

#Code 9: Per Capita GDP 2020

#We use the dataset called "2019.csv" found at https://github.com/fati8999-tech/Data-visualization-with-Python-Using-Seaborn-and-Plotly_-GDP-per-Capita-Life-Expectency-Dataset/blob/master/2019.csv
#Pull the "raw" GitHub content
url = 'https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/GDP_per_capita_World_Data.csv'
download = requests.get(url).content
#Reading the downloaded content and turning it into a pandas dataframe
df = pd.read_csv(io.StringIO(download.decode('utf-8')), error_bad_lines=False, skiprows=4)
print(df.head(5))

#Configure plotting parameters
import seaborn as sns
#plt.style.use('ggplot')
sns.set_style('darkgrid') # darkgrid, white grid, dark, white and ticks
plt.rc('axes', titlesize=18)     # fontsize of the axes title
plt.rc('axes', labelsize=14)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=13)    # fontsize of the tick labels
plt.rc('ytick', labelsize=13)    # fontsize of the tick labels
plt.rc('legend', fontsize=13)    # legend fontsize
plt.rc('font', size=13)

colors1 = sns.color_palette('pastel')
colors2 = sns.color_palette('deep')
#colors = sns.color_palette("Set2")


df_sorted = df.sort_values('2020',ascending=False)
#Let's plot categorical GDP per capita for top ten countries
plt.figure(figsize=(9.5, 6), tight_layout=True)
sns.barplot(x=df_sorted['2020'],y=df_sorted['Country Name'].head(10),data=df_sorted, color="yellowgreen")
plt.xticks(rotation=90)
plt.title("Countries with Highest GDP per Capita in 2020")
for i, v in enumerate(df_sorted['2020'].head(10)):
    plt.text(v+1000, i, str(round(v, 4)), color='steelblue', va="center")
    plt.text(v+30000, i, str(i+1), color='black', va="center")

print(df_sorted['Country Name'].head(10))
print(df_sorted['2020'].head(10))
#plt.subplots_adjust(right=0.3)    
textstr = 'Created at \nwww.tssfl.com'
#plt.text(0.02, 0.5, textstr, fontsize=14, transform=plt.gcf().transFigure)
plt.gcf().text(0.02, 0.92, textstr, fontsize=14, color='green') # (0,0) is bottom left, (1,1) is top right
plt.xlabel("GDP per Capita (US$)")
plt.ylabel("Country Name")
plt.show()
plt.clf()

df_sorted = df.sort_values('2020',ascending=False)
#Let's plot categorical GDP per capital for top ten countries
plt.figure(figsize=(8,6), tight_layout=True)
sns.barplot(x=df_sorted['Country Name'].head(10), y=df_sorted['2020'],data=df_sorted, color="yellowgreen")
plt.xticks(rotation=90)
plt.title("Countries with Highest GDP per Capita in 2020", y = 1.08)
xlocs, xlabs = plt.xticks()
for i, v in enumerate(df_sorted['2020'].head(10)):
    plt.text(xlocs[i] - 0.25, v + 0.05, str(round(v, 4)), color='red', va="center", rotation=45)
plt.gcf().text(0.02, 0.03, textstr, fontsize=14, color='green')
plt.xlabel("Country Name")
plt.ylabel("GDP per Capita (US$)")
plt.show()
plt.clf()

#Let's plot categorical GDP per capital for top ten countries
df_sorted = df.sort_values('2020',ascending=True)
plt.figure(figsize=(8,6), tight_layout=True)
sns.barplot(x=df_sorted['2020'],y=df_sorted['Country Name'].head(10),data=df_sorted, color="cadetblue")
plt.xticks(rotation=90)
plt.title("Countries with Lowest GDP per Capita in 2020")
for i, v in enumerate(df_sorted['2020'].head(10)):
    plt.text(v+10, i, str(round(v, 4)), color='teal', va="center")
plt.gcf().text(0.8, 0.85, textstr, fontsize=14, color='green')
plt.xlabel("GDP per Capita (US$)")
plt.ylabel("Country Name")
plt.show()
plt.clf()

df_sorted = df.sort_values('2020',ascending=True)
#Let's plot categorical GDP per capital for top ten countries
plt.figure(figsize=(8,6), tight_layout=True)
sns.barplot(x=df_sorted['Country Name'].head(10), y=df_sorted['2020'],data=df_sorted, color="cadetblue")
plt.xticks(rotation=90)
plt.title("Countries with Lowest GDP per Capita in 2020", y = 1.08)
xlocs, xlabs = plt.xticks()
for i, v in enumerate(df_sorted['2020'].head(10)):
    plt.text(xlocs[i] - 0.25, v + 0.5, str(round(v, 4)), color='crimson', va="center", rotation=90)
plt.gcf().text(0.1, 0.1, textstr, fontsize=14, color='green')
plt.xlabel("Country Name")
plt.ylabel("GDP per Capita (US$)")
plt.show()
plt.clf()

df_sorted = df.sort_values('2020',ascending=True)
#Let's plot categorical GDP per capital for top ten countries
plt.figure(figsize=(15,70), tight_layout=True)
sns.barplot(x=df_sorted['2020'],y=df_sorted['Country Name'],data=df_sorted, color="deepskyblue")
plt.xticks(rotation=90)
plt.title("Global GDP per Capita in 2020")
for i, v in enumerate(df_sorted['2020']):
    plt.text(v+1000, i, str(round(v, 4)), color='teal', va="center")
    plt.text(v+22000, i, str(226-(i+1)), color='black', va="center")
plt.gcf().text(0.55, 0.98, textstr, fontsize=14, color='green')
plt.xlabel("GDP per Capita (US$)")
plt.ylabel("Country Name")
plt.show()
plt.clf()

df_sorted = df.sort_values('2020',ascending=False)
#Let's plot categorical GDP per capital for top ten countries
plt.figure(figsize=(15,70), tight_layout=True)
sns.barplot(x=df_sorted['2020'],y=df_sorted['Country Name'],data=df_sorted, color="deepskyblue")
plt.xticks(rotation=90)
plt.title("Global GDP per Capita in 2020")
for i, v in enumerate(df_sorted['2020']):
    plt.text(v+1000, i, str(round(v, 4)), color='teal', va="center")
    plt.text(v+22000, i, str(i+1), color='black', va="center")
plt.gcf().text(0.1, 0.99, textstr, fontsize=14, color='green')
plt.xlabel("GDP per Capita (US$)")
plt.ylabel("Country Name")
plt.show()
plt.clf()

df_sorted = df.sort_values('2020',ascending=False)[:225]
#Let's plot categorical GDP per capital for top ten countries
plt.figure(figsize=(15,70), tight_layout=True)
sns.barplot(x=df_sorted['2020'],y=df_sorted['Country Name'],data=df_sorted, color="deepskyblue")
plt.xticks(rotation=90)
plt.title("Global GDP per Capita in 2020")
for i, v in enumerate(df_sorted['2020']):
    plt.text(v+1000, i, str(round(v, 4)), color='teal', va="center")
    plt.text(v+22000, i, str(i+1), color='black', va="center")
plt.gcf().text(0.1, 0.99, textstr, fontsize=14, color='green')
plt.xlabel("GDP per Capita (US$)")
plt.ylabel("Country Name")
plt.show()
plt.clf()
