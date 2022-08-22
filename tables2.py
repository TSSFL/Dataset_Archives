from pretty_html_table import build_table
import pandas as pd
import seaborn as sns

from weasyprint import CSS
from weasyprint import HTML

import matplotlib.pyplot as plt

import requests
import io

url = 'https://raw.githubusercontent.com/fati8999-tech/Data-visualization-with-Python-Using-Seaborn-and-Plotly_-GDP-per-Capita-Life-Expectency-Dataset/master/2019.csv'
download = requests.get(url).content
df = pd.read_csv(io.StringIO(download.decode('utf-8')))
#Change colors as appropriate: blue_light, blue_dark, grey_light, grey_dark, orange_light, orange_dark, yellow_light, yellow_dark, green_light, green_dark, red_light, red_dark
output = build_table(df, 'green_light', font_size='medium', font_family='Open Sans, sans-serif', text_align='left', width='auto', index=False, even_color='black', even_bg_color='white')

#Let's create an image and attach it to HTML
plt.style.use('ggplot')
sns.pairplot(df)
plt.savefig("email_plots.png")

with open("email_report.html","w+") as file:
  file.write(output)
  file.write("<img src='email_plots.png'/>")

#HTML(string=output).write_pdf("email_report.pdf")
HTML(string=output).write_pdf("email_report.pdf", stylesheets=[CSS(string='@page { size: landscape }')])
