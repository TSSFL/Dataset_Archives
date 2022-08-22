#https://medium.com/@kvnamipara/a-better-visualisation-of-pie-charts-by-matplotlib-935b7667d77f
import matplotlib.pyplot as plt

textstr = 'Created at \nwww.tssfl.com'
# Pie chart
labels = ['Cows', 'Goats', 'Sheep', 'Other']
sizes = [45, 15, 30, 10]# only "explode" the 2nd slice (i.e. 'Hogs')
explode = (0, 0., 0, 0)  
fig1, ax1 = plt.subplots(figsize=(5, 5))
ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
        shadow=True, startangle=90)# Equal aspect ratio ensures that pie is drawn as a circle
ax1.axis('equal')  
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Plot 2
fig1, ax2 = plt.subplots(figsize=(5, 5))
explode = (0.1, 0., 0, 0)  
ax2.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
        shadow=True, startangle=90)# Equal aspect ratio ensures that pie is drawn as a circle
ax2.axis('equal')  
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Plot 3
fig1, ax3 = plt.subplots(figsize=(5, 5))
explode = (0., 0., 0, 0.1)  
ax3.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
        shadow=True, startangle=90)# Equal aspect ratio ensures that pie is drawn as a circle
ax3.axis('equal')  
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Add colors#################################
colors = ["#900C3F", '#C70039', '#FF5733', '#FFC300']
fig1, ax1 = plt.subplots(figsize=(5, 5))
explode = (0., 0.1, 0, 0)  
ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
        shadow=True, startangle=90)# Equal aspect ratio ensures that pie is drawn as a circle
ax1.axis('equal')
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()

#Another plot
colors = ["#900C3F", '#C70039', '#FF5733', '#FFC300']
fig1, ax1 = plt.subplots(figsize=(5, 5))
explode = (0., 0., 0.1, 0)  
ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
        shadow=True, startangle=90)# Equal aspect ratio ensures that pie is drawn as a circle
ax1.axis('equal')
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()

#Another one
colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
fig1, ax1 = plt.subplots(figsize=(5, 5))
explode = (0., 0., 0.1, 0.)  
ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
        shadow=True, startangle=90)# Equal aspect ratio ensures that pie is drawn as a circle
ax1.axis('equal')
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#We can change the color of labels and percent labels
#by set_color() property of matplotlib.text.Text
#object which are return type of function plot.pie()
#colors
colors = ["#900C3F", '#C70039', '#FF5733', '#FFC300']

fig1, ax1 = plt.subplots(figsize=(5, 5))
explode = (0.1, 0.1, 0.1, 0.1)  
patches, texts, autotexts = ax1.pie(sizes, explode=explode, colors = colors, labels=labels, autopct='%1.1f%%', startangle=90)
for text in texts:
    text.set_color('mediumblue')
for autotext in autotexts:
    autotext.set_color('mediumblue')# Equal aspect ratio ensures that pie is drawn as a circle
ax1.axis('equal')  
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()
#Changing the pie chart to donut chart ####################
#Making donut graph from pie chart in Matplotlib
#is not easy, let's change the pie chart to donut chart
#by drawing a circle with white color at origin(Source: here).

#Modify code as below to draw a circle centered at (0,0)

#colors
colors = ["#900C3F", '#C70039', '#FF5733', '#FFC300']

fig1, ax1 = plt.subplots(figsize=(5, 5))
ax1.pie(sizes, colors = colors, labels=labels, autopct='%1.1f%%', startangle=90)#draw circle
centre_circle = plt.Circle((0,0),0.75,fc='white')
fig = plt.gcf()
fig.gca().add_artist(centre_circle)# Equal aspect ratio ensures that pie is drawn as a circle
ax1.axis('equal')  
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()
#Changing label positions
#We can change the position of labels (both outer and percent labels)
#by modifying labeldistance(defaul:1) and pctdistance(default:0.6)
#Let’s modify code by adding pctdistance=0.85 and use explosion
#property to make it looks better

colors = ['orange','blue','green','red'] #explsion
explode = (0.05,0.05,0.05,0.05)
fig1, ax1 = plt.subplots(figsize=(5, 5))
ax1.pie(sizes, colors = colors, labels=labels, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode)#draw circle
centre_circle = plt.Circle((0,0),0.75,fc='white')
fig = plt.gcf()
fig.gca().add_artist(centre_circle)# Equal aspect ratio ensures that pie is drawn as a circle
ax1.axis('equal')  
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Multiple-pie charts to make data more visualizable
#Multiple chart 1
labels1 = ['Cows', 'Goats', 'Sheep', 'Other']
sizes1 = [4500, 1500, 3000, 1000]
labels2 = ['Male', 'Female']
sizes2 = [2000, 2500]

colors1 = ['orange','blue','green','red']
colors2 = ['cyan','yellow']

explode1 = (0.05,0.05,0.05,0.05)
explode2 = (0.05,0.05)

fig = plt.figure(figsize = (8,4))

ax1 = fig.add_subplot(1,2,1)
ax1.pie(sizes1, colors = colors1, labels=labels1, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode1)
centre_circle = plt.Circle((0,0),0.65,fc='white')
ax1.axis('equal')
ax1.set_title("Population")

ax2 = fig.add_subplot(1,2,2)
ax2.pie(sizes2, colors = colors2, labels=labels2, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode2)#draw circle
centre_circle = plt.Circle((0,0),0.65,fc='white')
ax2.axis('equal')
ax2.set_title("Gender")

fig = plt.gcf()
fig.gca().add_artist(centre_circle)# Equal aspect ratio ensures that pie is drawn as a circle
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Multiple chart 2
explode1 = (0.0,0.0,0.0,0.0)
explode2 = (0.0,0.0)

fig = plt.figure(figsize = (8,4))

ax1 = fig.add_subplot(1,2,1)
ax1.pie(sizes1, colors = colors1, labels=labels1, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode1)
centre_circle = plt.Circle((0,0),0.65,fc='white')
ax1.axis('equal')
ax1.set_title("Population")

ax2 = fig.add_subplot(1,2,2)
ax2.pie(sizes2, colors = colors2, labels=labels2, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode2)#draw circle
centre_circle = plt.Circle((0,0),0.65,fc='white')
ax2.axis('equal')
ax2.set_title("Gender")

fig = plt.gcf()
fig.gca().add_artist(centre_circle)# Equal aspect ratio ensures that pie is drawn as a circle
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Multiple chart 3
explode1 = (0.0,0.0,0.0,0.0)
explode2 = (0.0,0.0)

fig = plt.figure(figsize = (5,8))

ax1 = fig.add_subplot(2,1,1)
ax1.pie(sizes1, colors = colors1, labels=labels1, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode1)
centre_circle = plt.Circle((0,0),0.65,fc='white')
ax1.axis('equal')
ax1.set_title("Population")

ax2 = fig.add_subplot(2,1,2)
ax2.pie(sizes2, colors = colors2, labels=labels2, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode2)#draw circle
centre_circle = plt.Circle((0,0),0.65,fc='white')
ax2.axis('equal')
ax2.set_title("Gender")

fig = plt.gcf()
fig.gca().add_artist(centre_circle)# Equal aspect ratio ensures that pie is drawn as a circle
plt.tight_layout()
plt.gcf().text(0.02, 0.92, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Multiple chart 4

explode1 = (0.05,0.05,0.05,0.05)
explode2 = (0.05,0.05)

fig = plt.figure(figsize = (8,4))

ax1 = fig.add_subplot(1,2,1)
ax1.pie(sizes1, colors = colors1, labels=labels1, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode1)
centre_circle = plt.Circle((0,0),0.65,fc='white')
ax1.axis('equal')
ax1.set_title("Population")
fig = plt.gcf()
fig.gca().add_artist(centre_circle)# Equal aspect ratio ensures that pie is drawn as a circle
plt.tight_layout()

ax2 = fig.add_subplot(1,2,2)
ax2.pie(sizes2, colors = colors2, labels=labels2, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode2)#draw circle
centre_circle = plt.Circle((0,0),0.65,fc='white')
ax2.axis('equal')
ax2.set_title("Gender")

fig = plt.gcf()
fig.gca().add_artist(centre_circle)# Equal aspect ratio ensures that pie is drawn as a circle
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Multiple chart 5

explode1 = (0.0,0.0,0.0,0.0)
explode2 = (0.0,0.0)

fig = plt.figure(figsize = (8,4))

ax1 = fig.add_subplot(1,2,1)
ax1.pie(sizes1, colors = colors1, labels=labels1, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode1)
centre_circle = plt.Circle((0,0),0.65,fc='white')
ax1.axis('equal')
ax1.set_title("Population")
fig = plt.gcf()
fig.gca().add_artist(centre_circle)# Equal aspect ratio ensures that pie is drawn as a circle
plt.tight_layout()

ax2 = fig.add_subplot(1,2,2)
ax2.pie(sizes2, colors = colors2, labels=labels2, autopct='%1.1f%%', startangle=90, pctdistance=0.85, explode = explode2)#draw circle
centre_circle = plt.Circle((0,0),0.65,fc='white')
ax2.axis('equal')
ax2.set_title("Gender")

fig = plt.gcf()
fig.gca().add_artist(centre_circle)# Equal aspect ratio ensures that pie is drawn as a circle
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Multiple chart 6
labels = ['C++', 'Java', 'Python', 'JavaScript']
sizes = [504, 337, 415, 280]
labels_gender = ['Man','Woman','Man','Woman','Man','Woman','Man','Woman']
sizes_gender = [315,189,125,212,270,145,190,90]
colors = ['orange', 'green', 'darkblue', 'red']
colors_gender = ['cyan','magenta', 'cyan','magenta', 'cyan','magenta', 'cyan','magenta']

labelsx = ["Male", "Female"] #Inner circle

plt.pie(sizes, labels=labels, colors=colors, startangle=90,frame=True)
pie = plt.pie(sizes_gender,colors=colors_gender,radius=0.75,startangle=90)
plt.legend(pie[0],labelsx, loc="upper right", fontsize=10,
           bbox_transform=plt.gcf().transFigure)
centre_circle = plt.Circle((0,0),0.5,color='black', fc='white',linewidth=0)
fig = plt.gcf()
#fig.gca().add_artist(centre_circle)

plt.axis('equal')
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Multiple chart 7
plt.pie(sizes, labels=labels, colors=colors, startangle=90,frame=True)
pie = plt.pie(sizes_gender,colors=colors_gender,radius=0.75,startangle=90)
#plt.legend(pie[0],labels, bbox_to_anchor=(1,0.5), loc="center right", fontsize=10,
          # bbox_transform=plt.gcf().transFigure)
plt.legend(pie[0],labelsx, loc="upper right", fontsize=10,
           bbox_transform=plt.gcf().transFigure)
#plt.legend(['_', '_', '', '', '', 'Male'])
centre_circle = plt.Circle((0,0),0.5,color='black', fc='white',linewidth=0)
fig = plt.gcf()
fig.gca().add_artist(centre_circle)
plt.axis('equal')
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

#Multiple chart 8

# Data to plot
labels = ['Python', 'C++', 'Java', 'PHP']
sizes = [504, 337, 415, 280]
labels_gender = ['Man','Woman','Man','Woman','Man','Woman','Man','Woman']
sizes_gender = [315,189,125,212,270,145,190,90]
colors = ['#ff6666', '#ffcc99', '#99ff99', '#66b3ff']
colors_gender = ['cyan','magenta', '#c2c2f0','#ffb3e6', '#c2c2f0','#ffb3e6', '#c2c2f0','#ffb3e6']
colors_gender = ['cyan','magenta', 'cyan','magenta', 'cyan','magenta', 'cyan','magenta']
explode = (0.2,0.2,0.2,0.2)
explode_gender = (0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1)
#Plot
plt.pie(sizes, labels=labels, colors=colors, startangle=90,frame=True, explode=explode,radius=3)
pie= plt.pie(sizes_gender,colors=colors_gender,startangle=90, explode=explode_gender,radius=2.0 )
plt.legend(pie[0],labelsx, loc="upper right", fontsize=10,
           bbox_transform=plt.gcf().transFigure)
#Draw circle
centre_circle = plt.Circle((0,0),1.5,color='black', fc='white',linewidth=0)
fig = plt.gcf()
fig.gca().add_artist(centre_circle)

plt.axis('equal')
plt.tight_layout()
plt.gcf().text(0.02, 0.85, textstr, fontsize=14, color='green')
plt.show()
