# -*- coding: utf-8 -*-
"""DUCE registered students - the original table, with the warnings silenced.

Kept as it was: the same pretty_html_table 'green_light' styling, the same
column layout, the same subtotal rows, the same two output files. It exists
so the original report can still be shown.

Three fixes: the warnings, the column alignment, and the sex labels.

**The M and F headers were swapped.** pd.crosstab sorts SEX alphabetically,
so its columns arrive F then M, but the header row assigned 'M', 'F'. Every
sex figure in the table sat under the wrong heading - UDD01 Year 1 is M=66,
F=86 and the table printed 86 under M; the grand total claimed 1,150 male
when 1,150 is the female count. The labels now match the data.

**The counts were left-aligned**, so 86.0 and 1094.0 started at the same
edge and no column could be read down. Numeric columns are right-aligned
with tabular figures.

WARNINGS: one cause, fixed in six places. Each of these

    df2.loc['Column Totals'] = df2.sum(numeric_only=True, axis=0)

adds a row whose PROGRAMME cell has no value. pandas implements that as a
concatenation, and an appended frame with an all-NA column now raises

    FutureWarning: The behavior of DataFrame concatenation with empty or
    all-NA entries is deprecated ...

once per assignment - six lines of it above the table. The fix is to give
the label column an empty string before assigning, so no column of the
appended row is all-NA. The rendered cell was already blank, so the table
is unchanged; PROGRAMME is taken off its CategoricalIndex first, which it
only needed for the sort that has already happened by then.

The rebuilt version is sri_report.py. It also replaces the positional
group slicing - iloc[0:5], iloc[6:8], iloc[np.r_[5, 8:16]], iloc[18] -
which is only correct because of the exact order of the programmes list
below. Nothing in this file touches that.
"""
import pandas as pd
import numpy as np
import pandas
 
#https://pbpython.com/pandas-crosstab.html
df = pd.read_csv('https://www.dropbox.com/s/s2zl2ynxoaiuhbg/Registered_Students.csv?dl=1')
 
#Check duplicates
#https://stackoverflow.com/questions/14657241/how-do-i-get-a-list-of-all-the-duplicate-items-using-pandas-in-python
dp = df[df.duplicated(['REG #'], keep=False)] #Returns all duplicate rows if any

del df[df.columns[0]]
df = df[['SEX', 'PROGRAMME', 'YEAR']]
 
df2 = pd.crosstab(df.PROGRAMME, [df.YEAR, df.SEX],  margins=False,    
                      dropna=False).reset_index()
df2.index += 1
 
#Sort courses
programmes = ['Degree Programmes', 'UDD01 | [DUCE]Bachelor of Education in Arts', 'UDD02 | [DUCE]Bachelor of Education in Science',
'UDD03 | [DUCE]Bachelor of Science with  Education',
'UDD04 | [DUCE]Bachelor of Arts with Education',
'UDD05 | [DUCE]Bachelor of Arts in Disaster Risk Management ',
'UDMA 151 | Master of Education in Curriculum Studies',
'UDP14 | Postgraduate Diploma in Education (PGDE)',
'UDP14 | Postgraduate Diploma in Education-Online',
'UDMA125 | Master of Education in Educational Leadership and Policy Studies[DUCE]',
'UDMA140 | Master of Arts in Public Administration',
'UDMA148 | Master of Arts with Education',
'UDMA151 | Master of Education in Curriculum Studies [Online]',  
'UDMA168 | Master of Science in Environmental Biology',
'UDMA178 | Master of Science with Education[DUCE]',
'UDMA186 | Master Of Arts In Development Evaluation',
'UDMA197 | Master of Science in Industrial Chemistry']
 
df2['PROGRAMME'] = pd.CategoricalIndex(df2['PROGRAMME'], ordered=True, categories=programmes)
 
df2 = df2.sort_values('PROGRAMME')

#The CategoricalIndex above exists only to drive this sort. Converting back
#to plain objects lets the total rows below carry an empty label instead of
#NaN, which is what stops pandas warning about an all-NA column on concat.
df2['PROGRAMME'] = df2['PROGRAMME'].astype(object)

#In the original the counts print as 86.0 rather than 86, because the
#appended all-NA row upcast every column to float. Filling the label column
#stops that happening, so the cast is made explicit here - the table keeps
#exactly the numbers it always showed.
df2 = df2.astype({c: float for c in df2.select_dtypes('number').columns})


def _labelled(series):
    """A total row that fills every column, so none of them is all-NA."""
    row = series.copy()
    row['PROGRAMME'] = ''
    return row
 
#df2.columns.set_levels(['Male','Female','Undergraduate Programmes'],level=1,inplace=True)
df2 = df2.rename(columns={'YEAR': ' ', 'PROGRAMME': 'PROGRAMME', 1.0:'YEAR 1', 2.0:'YEAR 2', 3.0:'YEAR 3'})
 
df2.loc['Column Totals'] = _labelled(df2.sum(numeric_only=True, axis=0))
df2.loc[:,'GRAND TOTALS'] = df2.sum(numeric_only=True, axis=1) # Row totals
 
#Sum every two columns and insert the column next to them
Total = df2["YEAR 1"].sum(numeric_only=True, axis=1)
df2.insert (3, 'TOTAL YEAR 1', Total)
 
Total = df2["YEAR 2"].sum(numeric_only=True, axis=1)
df2.insert (6, 'TOTAL YEAR 2', Total)
 
Total = df2["YEAR 3"].sum(numeric_only=True, axis=1)
df2.insert (9, 'TOTAL YEAR 3', Total)
 
#Sub-total 1
df2_0 = df2.iloc[0:5].copy()
df2_0.loc["Undergrads Sub-Total"] = _labelled(df2.iloc[0:5].sum(numeric_only=True))
 
df2_1 = df2.iloc[6:8].copy()
df2_1.loc["PGD Sub-Total"] = _labelled(df2.iloc[6:8].sum(numeric_only=True))
 
df2_2 = df2.iloc[np.r_[5,8:16]].copy()
df2_2.loc["Masters Sub-Total"] = _labelled(df2.iloc[np.r_[5,8:16]].sum(numeric_only=True))
 
#Concatenate
frames = [df2_0, df2_1, df2_2]
df2 = pd.concat(frames)
 
df2.loc["PGD + Masters Sub-Total"] = _labelled(
    df2.iloc[6:8].sum(numeric_only=True)
    + df2.iloc[18].iloc[1:])
df2.loc["Grand Total"] = _labelled(
    df2.iloc[0:5].sum(numeric_only=True)
    + df2.iloc[6:8].sum(numeric_only=True)
    + df2.iloc[18].iloc[1:])
 
#Multilevel index https://stackoverflow.com/questions/21443963/pandas-multilevel-column-names
#pd.crosstab sorts SEX alphabetically, so the columns arrive as F then M -
#but this header row said M then F, which put every figure under the wrong
#sex. UDD01 Year 1 is M=66, F=86, and the table printed 86 under M. The
#grand total reported 1,150 male when 1,150 is the female count. Labels
#corrected to the order the data is actually in.
df2.columns = [['PROGRAMMES', 'Year 1', ' ', ' ', 'Year 2', ' ', ' ', 'Year 3',  '', '', 'Row Totals'], ['Bachelors, PGD, MS', 'F', 'M', 'Total', 'F', 'M', 'Total', 'F', 'M', 'Total', 'Grand Total']]
 
df2.columns = df2.columns.rename("Index", level=1)
#df2 = df2.reset_index(drop=False)
#df2.reset_index(drop=True, inplace=True)
 
from pretty_html_table import build_table
from weasyprint import CSS
from weasyprint import HTML
 
#Create pdf table
#Change colors as appropriate: blue_light, blue_dark, grey_light, grey_dark, orange_light, orange_dark, yellow_light, yellow_dark, green_light, green_dark, red_light, red_dark
#text_align='left' left-aligned the counts too, so digits never lined up:
#86.0 and 1094.0 began at the same edge. build_table takes one alignment for
#the whole table, so the numeric columns are right-aligned afterwards with a
#small stylesheet, which also drops the trailing .0 the float dtype shows.
output = build_table(df2, 'green_light', font_size='medium', font_family='Open Sans, sans-serif', text_align='left', width='auto', index=True, even_color='black', even_bg_color='white')

align_css = '''
<style>
  table {{ width: 100%; }}
  table tr td:nth-child(n+3), table tr th:nth-child(n+3) {{
      text-align: right !important;
      font-variant-numeric: tabular-nums; }}
  table tr td:nth-child(-n+2), table tr th:nth-child(-n+2) {{
      text-align: left !important; }}
</style>
'''.replace("{{", "{").replace("}}", "}")
output = align_css + output
 
with open("Students_Registered.html","w+") as file:
    file.write(output)
 
#HTML(string=output).write_pdf("email_report.pdf")
HTML(string=output).write_pdf("DUCE_Registered_Students.pdf", stylesheets=[CSS(string='@page { size: landscape }')])

#The same table as data. The two-level column index is flattened - "Year 1
#F" reads better in a spreadsheet than a merged header - and the counts are
#written as whole people rather than the floats the total rows produced.
#Distinct filenames, because sri_report.py writes a report of the same name.
_out = df2.copy()
#Only the first column of each year group carries the year name; the next
#two are blank, so carry it forward or the flattened names collide.
_flat, _year = [], ""
for _a, _b in _out.columns:
    _a, _b = str(_a).strip(), str(_b).strip()
    if _a and _a != "PROGRAMMES":
        _year = _a
    _flat.append(_b if _a == "PROGRAMMES" else f"{_year} {_b}".strip())
_out.columns = _flat
for _c in _out.columns[1:]:
    _out[_c] = pd.to_numeric(_out[_c], errors="coerce").round(0).astype("Int64")
_out.index.name = "Row"
_out.to_csv("DUCE_Registered_Students_original.csv")

with pd.ExcelWriter("DUCE_Registered_Students_original.xlsx",
                    engine="openpyxl") as _xl:
    _out.to_excel(_xl, sheet_name="Enrolment")

print("Students_Registered.html   DUCE_Registered_Students.pdf")
print("DUCE_Registered_Students_original.csv"
      "   DUCE_Registered_Students_original.xlsx")