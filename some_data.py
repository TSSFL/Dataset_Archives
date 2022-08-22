#import libraries
import requests
import io
#https://stackoverflow.com/questions/9103166/multiple-axis-in-matplotlib-with-different-scales
#https://matplotlib.org/2.0.2/examples/axes_grid/demo_parasite_axes2.html
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rc
rc('mathtext', default='regular')

textstr = 'Created at www.tssfl.com'
sns.set_style('dark') # darkgrid, white grid, dark, white and ticks
#plt.style.use('ggplot')

#sheet_id = "1Z0_bdrIub3qESAaVIpzo42XGiukt-4-8"
#sheet_name = "Sheet"
#url_1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

url = 'https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/Raw%20data%20SRA_RBF_non_RBF.xls%20-%20Sheet1.csv'
download = requests.get(url).content
df = pd.read_csv(io.StringIO(download.decode('utf-8')), skiprows=3)

#df = pd.read_csv(data, skiprows=0) #error_bad_lines=False
df.columns = df.columns.str.strip()
print(df.keys())
x = 'Assessed areas'
yl1 = 'Average Score by RBF regions assessment 2017/18'
yl2 = 'Average Score by non-RBF regions assessment 2017/18'
yr = 'Difference score'
print(df[x])
# Create figure and subplot manually
# fig = plt.figure()
# host = fig.add_subplot(111)

# More versatile wrapper
fig, host = plt.subplots(figsize=(9,8)) # (width, height) in inches
# (see https://matplotlib.org/3.3.3/api/_as_gen/matplotlib.pyplot.subplots.html)

par1 = host.twinx()
par2 = host.twinx()

#host.set_xlim(0, 2)
host.set_ylim(40, 75) #RBF
par2.set_ylim(35, 70) #Non-RBF
par1.set_ylim(5, 20) #Difference


host.set_xlabel('Assessed Areas')
host.set_ylabel('Average Score by RBF regions assessment 2017/18')
par2.set_ylabel('Average Score by non-RBF regions assessment 2017/18')
par1.set_ylabel('Difference score')


color1 = plt.cm.viridis(0)
color2 = 'tab:red' #plt.cm.viridis(0.5)
color3 = 'magenta' #plt.cm.viridis(.9)

p1, = host.plot(df[x], df[yl1], '-ok',   color=color1, label="RBF Assessment")
p2, = par1.plot(df[x], df[yr], '-',  color=color2, label="Difference")
p3, = par2.plot(df[x], df[yl2], '--', color=color3,  label="Non-RBF Assessment")

lns = [p1, p2, p3]
host.legend(handles=lns, loc=2)

plt.gcf().text(0.4, 0.6, textstr, fontsize=14, color='green')
# right, left, top, bottom
#par2.spines['right'].set_position(('outward', 60)) #move axis to the right

# no x-ticks                
#par2.xaxis.set_ticks([])
#plt.show()
# Sometimes handy, same for xaxis
#par2.yaxis.set_ticks_position('right')

#Move "Velocity"-axis to the left
par2.spines['left'].set_position(('outward', 60))
par2.spines['left'].set_visible(True)
par2.yaxis.set_label_position('left')
par2.yaxis.set_ticks_position('left')
#End move axis to the left

host.yaxis.label.set_color(p1.get_color())
par1.yaxis.label.set_color(p2.get_color())
par2.yaxis.label.set_color(p3.get_color())

# Adjust spacings w.r.t. figsize
plt.subplots_adjust(bottom=0.75)
fig.tight_layout()
# Alternatively: bbox_inches='tight' within the plt.savefig function
#                (overwrites figsize)
#Adding grid
host.grid(color="blue", linestyle = '--')
par2.grid(color="blue", linestyle= '--')
#host.tick_params(axis='x', rotation=45) #pad=-30
#https://stackoverflow.com/questions/14852821/aligning-rotated-xticklabels-with-their-respective-xticks
plt.setp(host.get_xticklabels(), rotation=-45, ha="left", rotation_mode="anchor")
plt.title("Average Score by RBF & Non-RBF Regions Assessment 2017/18 and Their Difference")
# Best for professional typesetting, e.g. LaTeX
plt.savefig("pyplot_multiple_y-axis.pdf", bbox_inches="tight")
# For raster graphics use the dpi argument. E.g. '[...].png", dpi=200)'
#https://stackoverflow.com/questions/6774086/how-to-adjust-padding-with-cutoff-or-overlapping-labels
fig.set_tight_layout(True)
plt.show()
