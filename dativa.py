# import libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rc
rc('mathtext', default='regular')

textstr = 'Created at www.tssfl.com'
sns.set_style('dark') # darkgrid, white grid, dark, white and ticks
#plt.style.use('ggplot')

df = pd.read_csv('https://github.com/TSSFL/Dataset_Archives/main/chem_data.csv', skiprows=1) #error_bad_lines=False
df.columns = df.columns.str.strip()

print(df.keys())
var1 = 'MPs/Kg DW'
var2 = 'depth (cm)'
var3 = 'Year'

#df = df.sort_values(by = [var2], ascending = False, na_position = 'first')

x = df[var1]
y1 = df[var2]
y2 = df[var3]

fig, ax = plt.subplots(figsize=(14, 8))

color1 = 'tab:red'
ax.plot(x, y1)

ax.set_xlabel('MPs/Kg DW', fontsize=16, color="darkblue")
ax.tick_params(axis ='x', labelcolor = "darkblue")

ax.set_ylabel('Depth (cm)', fontsize=16, color="navy")
ax.tick_params(axis ='y', labelcolor = "navy")

plt.xticks(x)
plt.yticks(y1)

ax2 = ax.twinx()
ax2.plot(x, y1, '-ok', color = "red")

ax2.set_yticks(ax.get_yticks())
ax2.set_ylim(ax.get_ylim())
fig.canvas.draw()

#Get the tick labels which are strings, convert them to integers
labels = [int(i.get_text().replace('−','-')) for i in ax2.get_yticklabels()]

new_ls = [y2[i] for i in range(len(labels))]
print(new_ls)

plt.gcf().text(0.12, 0.92, textstr, fontsize=14, color='green')

ax2.set_yticklabels(new_ls, color = "midnightblue")
ax2.set_ylabel('Year', fontsize=16, color = "midnightblue")

#Adding legend
#ax.legend(loc='center left')
#ax2.legend(loc='center right')

#Adding grid
ax.grid(color="blue", linestyle = '--')
ax2.grid(color="blue", linestyle= '--')

plt.title('Projecting 3D into 2D', fontweight ="bold", color="Black")
plt.show()
