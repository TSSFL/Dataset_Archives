#https://docs.google.com/spreadsheets/d/1xjLTkLxr6-3cIGVbtMRHhXAkVgF7TCdis-eLWZQm6sI/edit#gid=874892587
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import requests
import io

textstr = 'Created at \nwww.tssfl.com'

"""
sheet_id = "1xjLTkLxr6-3cIGVbtMRHhXAkVgF7TCdis-eLWZQm6sI"
sheet_name = "Sheet1"
url_1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
"""
colors1 = ['tomato', 'gold', 'skyblue', '#ffcc99']
#colors2 = ['orange','blue','lime','red']
#colors2 = ['orange','blue','green','red'] #explsion
colors2 = ['#ff6666', '#ffcc99', '#99ff99', '#66b3ff']
def label_function(val):
    return f'{val / 100.0 * len(df):.0f}\n{val:.2f}%'

#"Growth form", "Part used", "Ailment cured", "Citation"
#df = pd.read_csv(url_1)
url = 'https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/students_survey_data.csv'
download = requests.get(url).content
#Reading the downloaded content and turning it into a pandas dataframe
df = pd.read_csv(io.StringIO(download.decode('utf-8')))

df = df.replace(r"_", " ", regex=True)

fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12, 6))

df.groupby('group_ow7qd27/Subject_for_assessment').size().plot(kind='pie', autopct=label_function, textprops={'fontsize': 14},
                                  colors=colors1, ax=ax1)
df.groupby('group_da25q48/What_are_your_percep_s_teaching_knowledge/Our_teacher_presents_y_and_systematically').size().plot(kind='pie', autopct=label_function, textprops={'fontsize': 14},
                                 colors=colors2, ax=ax2)
ax1.set_ylabel('')
ax2.set_ylabel('')
ax1.set_title('Subjects', size=18)
ax2.set_title('Question 1 Responses', size=18)
plt.tight_layout()
plt.gcf().text(0.02, 0.84, textstr, fontsize=14, color='green')
plt.show()
