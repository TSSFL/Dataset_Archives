# -*- coding: utf-8 -*-
"""DUCE student information report - logic only. The data lives on Dropbox.

Run it from a SageMathCell by naming your data first, then loading this file:

    FILES_ZIP_URL = "https://www.dropbox.com/scl/fi/..../files.zip?...&dl=1"

    load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/duce_report.py")

The zip holds three exports - enrolment, registration, and students with IDs -
named so they sort in that order (enroled_1, Registered_2, IDs_3).

**No data URL appears in this file, and none ever should.** The code is public
on GitHub; the students' records are not.

The templates moved the other way. report_template.html, style.css and
replace_dict.json were in a second Dropbox zip, but a page layout, a
stylesheet and a name-normalising dictionary are logic, not data - they now
live beside this file in the repository and are fetched from there. Edit
them at duce_templates/ and every run picks the change up.

WHAT WAS WRONG WITH THE OLD REPORT
----------------------------------
The per-year M and F columns were swapped. pd.crosstab sorts SEX
alphabetically, so its columns arrive F then M, but the header row assigned
M then F. Against the source data, Master of Arts in Development Evaluation
is Year 1 F=2/M=9 and Year 2 F=9/M=6; the report printed Year 1 M=2/F=9 and
Year 2 M=9/F=6.

The Grand Total was not affected - it sums the real male column by name - so
the published table contradicted itself: that row showed Year 1 M=2 plus
Year 2 M=9, and a Grand Total M of 15. The labels now match the data.

Outputs
    Report.html / Report.pdf     the full report, TSSFL branded
    Report_Enrolled.csv          each table as data
    Report_Registered.csv
    Report_IDs.csv
    Report_Comparison.csv
    duce_charts.png              the figures, also embedded in the report
"""

_needed = ("FILES_ZIP_URL",)
_missing = [n for n in _needed if n not in globals()]
if _missing:
    raise NameError(
        "duce_report.py does not carry data locations - define them in the "
        "cell before loading it.\nMissing: " + ", ".join(_missing) + "\n\n"
        '    FILES_ZIP_URL = "https://www.dropbox.com/scl/fi/.../files.zip?dl=1"\n'
    )

import datetime
import glob
import io
import json
import os
import urllib.request
import zipfile

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytz
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# The subtitle rows carry '' in their numeric columns, and fillna(0) runs
# over object columns - both raise pandas deprecation notices about how a
# future version will treat them. Opting in to that future behaviour now is
# the supported way to settle it, rather than filtering the message away.
pd.set_option('future.no_silent_downcasting', True)

# --- TSSFL brand --------------------------------------------------------
BLUE, EMERALD, AMBER = "#096EFF", "#10B981", "#f59e0b"
ROSE, VIOLET = "#e11d48", "#7c3aed"
INK, INK_2, MUTED, GRID = "#0f172a", "#475569", "#94a3b8", "#e2e8f0"
BRAND = [BLUE, AMBER, EMERALD, ROSE, VIOLET]

# --- templates come from the repository, not from Dropbox ---------------
TEMPLATE_BASE = ("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/"
                 "main/duce_templates/")
os.makedirs("Templates", exist_ok=True)
for _name in ("report_template.html", "style.css", "replace_dict.json"):
    urllib.request.urlretrieve(TEMPLATE_BASE + _name,
                               os.path.join("Templates", _name))

# --- the data -----------------------------------------------------------
urllib.request.urlretrieve(FILES_ZIP_URL, "files.zip")
with zipfile.ZipFile("files.zip", "r") as zip_ref:
    zip_ref.extractall()
    for file_name in zip_ref.namelist():
        print(os.path.join(file_name))
os.remove("files.zip")


class ReportGenerator:
    def __init__(self):
        self.gmt3 = pytz.timezone('Etc/GMT-3')
        self.current_datetime = datetime.datetime.now(self.gmt3).strftime(
            '%Y-%m-%d %H:%M:%S')

    def check_duplicates(self, df):
        duplicates = df[df.duplicated(['REG #'], keep=False)]
        if len(duplicates) > 0:
            print(f"  duplicate registration numbers: {len(duplicates)} "
                  f"rows, removed")
            return df.drop_duplicates(['REG #'], keep=False)
        print("  no duplicate registration numbers")
        return df

    def preprocess_data(self, df, reg_column, sex_column, year_column,
                        programme_column):
        wanted = [reg_column, sex_column, year_column, programme_column]
        if all(c in df.columns for c in wanted):
            # .copy(), or every later assignment on this frame warns that it
            # is writing to a slice of the file it came from.
            df = df[wanted].copy()
            return df.rename(columns={reg_column: 'REG #', sex_column: 'SEX',
                                      programme_column: 'PROGRAMME',
                                      year_column: 'YEAR'})
        missing = [c for c in wanted if c not in df.columns]
        print(f"  missing columns: {missing}")
        return None

    def generate_report(self, df):
        with open('./Templates/replace_dict.json', 'r') as file:
            replace_dict = json.load(file)
        df['PROGRAMME'] = df['PROGRAMME'].replace(replace_dict)

        unique_programmes = df['PROGRAMME'].unique().tolist()
        df_i = pd.DataFrame({'PROGRAMME': unique_programmes})

        group_order = {
            'Master': ['Master', 'MEELPS', 'MSc. in Industrial Chemistry',
                       'MSc. in Environmental Biology', 'MAED', 'MEDCS',
                       'MAPA', 'MADE', 'MScEB', 'MSc (IC)', 'MScEd'],
            'Postgraduate Diploma': ['Postgraduate Diploma', 'PGDE', 'PGD-GC'],
            'Bachelor': ['Bachelor', 'B.Ed. in Science',
                         'B.Sc. with Education', 'B.A. DRIM', 'B.Ed.in Arts',
                         'B.A. with Education', 'BSc. with Education',
                         'B.Sc.with Education', 'B.A. in DRM',
                         'B.A. with Education ', 'B.Ed. Arts',
                         'B. Ed. in Science', 'B.A. Ed.', 'B.Sc( Ed )',
                         'B.Ed. Science', 'B.A.Ed', 'B.A.Ed.',
                         'B.Ed. (Science)'],
            'Diploma': ['Diploma in Educational', 'DELS&T'],
            'Certificate': ['Basic Technician Certificate', 'T.C ELSc & Tch'],
        }

        group_programmes, group_indices, starting_index = {}, {}, 0
        for group, group_keywords in group_order.items():
            group_df = df_i[df_i['PROGRAMME'].apply(
                lambda x: any(k in x for k in group_keywords))]
            group_programmes[group] = group_df['PROGRAMME'].tolist()
            if group_programmes[group]:
                group_indices[group] = (starting_index,
                                        starting_index + len(group_df) - 1)
                starting_index += len(group_df)
            else:
                group_indices[group] = (None, None)

        ordered_programmes = []
        for group in group_order:
            ordered_programmes.extend(group_programmes.get(group, []))
        unique_ordered_programs = list(dict.fromkeys(ordered_programmes))

        mi = group_indices['Master']
        pi = group_indices['Postgraduate Diploma']
        bi = group_indices['Bachelor']
        di = group_indices['Diploma']
        ci = group_indices['Certificate']

        df['SEX'] = df['SEX'].str.upper()
        df2 = pd.crosstab(df.PROGRAMME, [df.YEAR, df.SEX], margins=False,
                          dropna=False).reset_index()
        df2.index += 1

        # pd.crosstab sorts SEX alphabetically, so the columns arrive F then
        # M. The header assigned later must follow that order - assuming M
        # first is what put every figure under the wrong sex.
        self.sex_order = [s for s in ('F', 'M')
                          if any(c[1] == s for c in df2.columns
                                 if isinstance(c, tuple))]

        df2['PROGRAMME'] = pd.CategoricalIndex(
            df2['PROGRAMME'], ordered=True, categories=unique_ordered_programs)
        df2 = df2.sort_values('PROGRAMME')
        df2 = df2.rename(columns={'YEAR': ' ', 'PROGRAMME': 'PROGRAMME',
                                  1.0: 'YEAR 1', 2.0: 'YEAR 2',
                                  3.0: 'YEAR 3'})

        column_totals = df2.dropna(axis=1, how='all').sum(numeric_only=True,
                                                          axis=0)
        df2.loc['Column Totals'] = column_totals
        df2.loc[:, 'GRAND TOTALS'] = df2.sum(numeric_only=True, axis=1)

        Total = df2["YEAR 1"].sum(numeric_only=True, axis=1)
        df2.insert(3, 'TOTAL YEAR 1', Total)
        Total = df2["YEAR 2"].sum(numeric_only=True, axis=1)
        df2.insert(6, 'TOTAL YEAR 2', Total)
        Total = df2["YEAR 3"].sum(numeric_only=True, axis=1)
        df2.insert(9, 'TOTAL YEAR 3', Total)

        total_m = df2[[c for c in df2.columns if c[1] == 'M']].sum(axis=1)
        df2.insert(10, 'M', total_m)
        total_f = df2[[c for c in df2.columns if c[1] == 'F']].sum(axis=1)
        df2.insert(11, 'F', total_f)

        df2['PROGRAMME'] = df2['PROGRAMME'].astype('category')
        blocks = []
        for idx, label, title in (
                (mi, 'Masters Sub-Total', 'Masters Programmes'),
                (pi, 'PGD Sub-Total', 'Postgraduate Diploma Programmes'),
                (bi, 'Undergraduate Sub-Total', 'Undergraduate Programmes'),
                (di, 'Diploma Sub-Total', 'Ordinary Diploma Programmes'),
                (ci, 'Certificate Sub-Total', 'Certificate Programmes')):
            if idx[0] is not None and idx[1] is not None:
                block = df2.iloc[idx[0]:idx[1] + 1].copy()
                block['PROGRAMME'] = block['PROGRAMME'].cat.add_categories(
                    f'<b>{label}</b>')
                block.loc[label, df2.columns[0]] = f'<b>{label}</b>'
                block.loc[label, df2.columns[1:]] = df2.iloc[
                    idx[0]:idx[1] + 1].sum(numeric_only=True)
                subtitle_row = pd.DataFrame(
                    [[f'<b>{title}</b>'] + [''] * (len(df2.columns) - 1)],
                    columns=df2.columns)
                block = pd.concat([subtitle_row, block])
            else:
                block = pd.DataFrame(columns=df2.columns)
                block.loc[0] = [f'<b>{label}</b>'] + [0] * (len(df2.columns) - 1)
            blocks.append(block)

        df2_0, df2_1, df2_2, df2_3, df2_4 = blocks
        df = pd.concat(blocks)
        df.reset_index(drop=True, inplace=True)

        df.loc['PGD + Masters Sub-Total', df.columns[0]] = \
            '<b>PGD + Masters Sub-Total</b>'
        df.loc['PGD + Masters Sub-Total', df.columns[1:]] = \
            df2_0.iloc[-1] + df2_1.iloc[-1]

        df.loc['Grand Total', df.columns[0]] = '<b>Grand Total</b>'
        df.loc['Grand Total', df.columns[1:]] = (
            df2_0.iloc[-1] + df2_1.iloc[-1] + df2_2.iloc[-1]
            + df2_3.iloc[-1] + df2_4.iloc[-1])

        # The sex labels follow the order the crosstab actually produced.
        a, b = self.sex_order if len(self.sex_order) == 2 else ('F', 'M')
        df.columns = [
            ['PROGRAMME', 'Year 1', ' ', ' ', 'Year 2', ' ', ' ', 'Year 3',
             ' ', ' ', 'Grand Total', ' ', ' '],
            ['PROGRAMME', a, b, 'T', a, b, 'T', a, b, 'T', 'M', 'F', 'T']]
        df.columns = df.columns.rename("Index", level=1)
        df = df.reset_index(drop=True)
        df.index += 1
        return df

    def generate_html_report(self, df1, df2, df3, df4, charts_uri=""):
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('./Templates/report_template.html')
        return template.render(df1=df1, df2=df2, df3=df3, df4=df4,
                               charts_uri=charts_uri,
                               current_datetime=self.current_datetime)

    def save_html_report(self, html_output, file_name):
        with open(file_name, 'w') as f:
            f.write(html_output)

    def generate_pdf_report(self, html_output, file_name):
        HTML(string=html_output).write_pdf(
            file_name, stylesheets=["./Templates/style.css"])

    def make_charts(self, df1, df2, df3, merged_df, file_name="duce_charts.png"):
        """Five views of the report, in the TSSFL brand.

        The tables answer "how many"; these answer "compared with what".
        """
        def totals(df):
            """Grand-total M, F and T for one report table."""
            row = df[df.iloc[:, 0].astype(str).str.contains("Grand Total")]
            if row.empty:
                return 0, 0, 0
            r = row.iloc[0]
            return int(r.iloc[-3]), int(r.iloc[-2]), int(r.iloc[-1])

        def group_rows(df):
            """Sub-total rows, one per programme group."""
            names, males, females = [], [], []
            for _, r in df.iterrows():
                label = str(r.iloc[0])
                if "Sub-Total" in label and "PGD + Masters" not in label:
                    names.append(label.replace("<b>", "").replace("</b>", "")
                                 .replace(" Sub-Total", ""))
                    males.append(int(r.iloc[-3]))
                    females.append(int(r.iloc[-2]))
            return names, males, females

        plt.rcParams.update({
            "font.family": "sans-serif",
            "font.sans-serif": ["Nimbus Sans", "Helvetica", "DejaVu Sans"],
            "figure.facecolor": "white", "axes.facecolor": "white",
            "axes.edgecolor": GRID, "text.color": INK,
            "axes.labelcolor": INK_2, "xtick.labelcolor": INK_2,
            "ytick.labelcolor": INK_2, "axes.titlesize": 13,
            "axes.titleweight": "bold", "axes.titlecolor": INK,
        })
        fig, axes = plt.subplots(3, 2, figsize=(15, 15.5))
        axes = axes.ravel()

        # 1. the three databases, side by side - the reconciliation the
        #    report exists to make
        labels = ["Enrolled", "Registered", "With IDs"]
        tot = [totals(d) for d in (df1, df2, df3)]
        ax = axes[0]
        x = np.arange(len(labels))
        b1 = ax.bar(x - 0.2, [t[0] for t in tot], 0.38, color=BLUE, label="Male")
        b2 = ax.bar(x + 0.2, [t[1] for t in tot], 0.38, color=AMBER,
                    label="Female")
        for bars in (b1, b2):
            ax.bar_label(bars, fmt="%d", padding=3, fontsize=10, color=INK_2)
        for i, t in enumerate(tot):
            ax.annotate(f"total {t[2]:,}", xy=(i, max(t[0], t[1])),
                        xytext=(0, 22), textcoords="offset points",
                        ha="center", fontweight="bold", color=INK)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylabel("Students")
        ax.set_title("The three databases do not agree")
        ax.legend(frameon=False)
        ax.margins(y=0.20)

        # 2. how far apart, as a share of the enrolment figure
        ax = axes[1]
        base = tot[0][2] or 1
        gaps = [tot[0][2] - t[2] for t in tot]
        cols = [EMERALD, AMBER, ROSE]
        bars = ax.bar(labels, gaps, 0.55, color=cols)
        ax.bar_label(bars, fmt="%d", padding=3, fontsize=11, color=INK_2)
        for i, g in enumerate(gaps):
            if i:
                ax.annotate(f"{100.0 * g / base:.1f}% of enrolment",
                            xy=(i, g), xytext=(0, 20),
                            textcoords="offset points", ha="center",
                            fontsize=10, color=MUTED)
        ax.set_ylabel("Students missing, against enrolment")
        ax.set_title("Students unaccounted for at each stage")
        ax.margins(y=0.22)

        # 3. enrolment by programme group
        ax = axes[2]
        names, males, females = group_rows(df1)
        if names:
            y = np.arange(len(names))
            ax.barh(y + 0.2, males, 0.38, color=BLUE, label="Male")
            ax.barh(y - 0.2, females, 0.38, color=AMBER, label="Female")
            ax.set_yticks(y)
            ax.set_yticklabels(names)
            ax.invert_yaxis()
            ax.set_xscale("symlog")
            ax.set_xlabel("Students (log scale)")
            ax.set_title("Enrolment by programme group")
            # A log axis cannot be read off accurately, so state each figure.
            for i, (m, f) in enumerate(zip(males, females)):
                ax.annotate(f"{m:,}", xy=(m, i + 0.2), xytext=(5, 0),
                            textcoords="offset points", va="center",
                            fontsize=9, color=INK_2)
                ax.annotate(f"{f:,}", xy=(f, i - 0.2), xytext=(5, 0),
                            textcoords="offset points", va="center",
                            fontsize=9, color=INK_2)
            ax.margins(x=0.16)
            ax.legend(frameon=False, loc="lower right",
                      bbox_to_anchor=(1.0, -0.02))

        # 4. the sex balance of each group, as shares
        ax = axes[3]
        if names:
            tot_g = [m + f for m, f in zip(males, females)]
            m_pct = [100.0 * m / t if t else 0 for m, t in zip(males, tot_g)]
            f_pct = [100.0 - p for p in m_pct]
            y = np.arange(len(names))
            ax.barh(y, m_pct, 0.55, color=BLUE, label="Male")
            ax.barh(y, f_pct, 0.55, left=m_pct, color=AMBER, label="Female")
            for i, (mp, fp, t) in enumerate(zip(m_pct, f_pct, tot_g)):
                if mp > 8:
                    ax.text(mp / 2, i, f"{mp:.0f}%", ha="center", va="center",
                            color="white", fontweight="bold", fontsize=10)
                if fp > 8:
                    ax.text(mp + fp / 2, i, f"{fp:.0f}%", ha="center",
                            va="center", color="white", fontweight="bold",
                            fontsize=10)
                ax.annotate(f"n = {t:,}", xy=(101, i), va="center",
                            fontsize=9.5, color=MUTED)
            ax.set_yticks(y)
            ax.set_yticklabels(names)
            ax.invert_yaxis()
            ax.set_xlim(0, 118)
            ax.set_xlabel("Share of the group (%)")
            ax.set_title("Sex balance within each group")
            # Above the plot, not on top of the last row.
            ax.legend(frameon=False, ncol=2, loc="lower left",
                      bbox_to_anchor=(0.0, 1.02))

        # 5. the shape of the cohort - how many in each year of study
        ax = axes[4]
        gt = df1[df1.iloc[:, 0].astype(str).str.contains("Grand Total")]
        if not gt.empty:
            r = gt.iloc[0]
            years = ["Year 1", "Year 2", "Year 3"]
            y_tot = [int(r.iloc[3]), int(r.iloc[6]), int(r.iloc[9])]
            bars = ax.bar(years, y_tot, 0.55, color=[BLUE, EMERALD, AMBER])
            ax.bar_label(bars, fmt="%d", padding=3, fontsize=11, color=INK_2)
            for i in range(1, len(y_tot)):
                if y_tot[i - 1]:
                    change = 100.0 * (y_tot[i] - y_tot[i - 1]) / y_tot[i - 1]
                    ax.annotate(f"{change:+.0f}%", xy=(i, y_tot[i]),
                                xytext=(0, 22), textcoords="offset points",
                                ha="center", fontsize=10,
                                color=ROSE if change < 0 else EMERALD)
            ax.set_ylabel("Students enrolled")
            ax.set_title("Cohort size by year of study")
            ax.margins(y=0.20)

        # 6. the largest programmes
        ax = axes[5]
        rows = []
        for _, r in df1.iterrows():
            label = str(r.iloc[0])
            if "<b>" in label or not label.strip():
                continue
            rows.append((label, int(r.iloc[-1])))
        rows = sorted(rows, key=lambda t: -t[1])[:8][::-1]
        if rows:
            import textwrap
            names2 = ["\n".join(textwrap.wrap(n.replace("[DUCE]", ""), 32)[:2])
                      for n, _ in rows]
            vals = [v for _, v in rows]
            y = np.arange(len(rows))
            bars = ax.barh(y, vals, 0.6, color=BLUE)
            ax.bar_label(bars, fmt="%d", padding=4, fontsize=10, color=INK_2)
            ax.set_yticks(y)
            ax.set_yticklabels(names2, fontsize=8.5)
            ax.set_xlabel("Students enrolled")
            ax.set_title("The eight largest programmes")
            ax.margins(x=0.14)

        for a in axes:
            for side in ("top", "right"):
                a.spines[side].set_visible(False)
            a.grid(True, axis="x" if a.get_yticklabels() else "y",
                   color=GRID, lw=1)
            a.set_axisbelow(True)

        fig.suptitle("DUCE Student Information, 2023/2024", fontsize=18,
                     fontweight="bold", color=INK, y=0.995)
        fig.text(0.5, 0.005, "Produced with the TSSFL Technology Stack  "
                 "www.tssfl.com", ha="center", fontsize=10, color=MUTED)
        fig.tight_layout(rect=(0, 0.014, 1, 0.982))
        fig.savefig(file_name, dpi=130, facecolor="white")
        plt.show()
        plt.close(fig)
        return file_name

    def generate_report_data(self, file_list):
        dfs = []
        file_mapping = {
            'REG #': ['REG #', 'REG # ', 'REGISTRATION_NO', 'RegNo'],
            'SEX': ['SEX', 'GENDER', 'Sex', 'Gender'],
            'YEAR': ['YEAR', 'STUDY_YEAR', 'StudyYear'],
            'PROGRAMME': ['PROGRAMME', 'Programme'],
        }

        file_list = sorted(
            file_list,
            key=lambda f: int(f.split('/')[-1].split('_')[-1].split('.')[0]))
        for file in file_list:
            print("reading:", file)
            extension = file.split('.')[-1]
            if extension in ('xlsx', 'xls'):
                df = pd.read_excel(file)
            elif extension == 'csv':
                df = pd.read_csv(file)
            else:
                print(f"  unsupported file format: {extension}")
                continue

            for target_column, possible_columns in file_mapping.items():
                column_found = False
                for possible_column in possible_columns:
                    if possible_column in df.columns:
                        df.rename(columns={possible_column: target_column},
                                  inplace=True)
                        column_found = True
                        break
                if not column_found:
                    print(f"  missing '{target_column}' column in {file}")
                    break
            else:
                dfs.append(self.preprocess_data(df, 'REG #', 'SEX', 'YEAR',
                                                'PROGRAMME'))

        if len(dfs) != 3:
            print("Insufficient data files. Three are required: enrolment, "
                  "registration, and students with IDs.")
            return None

        df1, df2, df3 = dfs
        print("\nChecking for duplicates")
        df1 = self.generate_report(self.check_duplicates(df1))
        df2 = self.generate_report(self.check_duplicates(df2))
        df3 = self.generate_report(self.check_duplicates(df3))

        df1_0, df2_1, df3_2 = (d.iloc[:, [0, -1]] for d in (df1, df2, df3))
        for d in (df1_0, df2_1, df3_2):
            d.columns = d.columns.get_level_values(0)
        dfs = [df1_0, df2_1, df3_2]

        stack_df = pd.concat(dfs, ignore_index=True)
        unique_programs_merged = stack_df['PROGRAMME'].unique()
        longest_df = max(dfs, key=len)
        unique_programs_long = longest_df['PROGRAMME'].unique()
        num_missing = len(set(unique_programs_merged)
                          - set(unique_programs_long))

        merged_1_df = dfs[0]
        merged_2_df = dfs[0]
        for df in dfs[1:]:
            merged_1_df = pd.merge(merged_1_df, df, on='PROGRAMME', how='left')
            merged_2_df = pd.merge(merged_2_df, df, on='PROGRAMME', how='outer')

        long_df = max(dfs, key=len)
        long_df = pd.concat(
            [long_df, pd.DataFrame([{} for _ in range(num_missing)])],
            ignore_index=True)
        merged_2_df = merged_2_df.reindex(long_df.index)

        part2 = merged_2_df.loc[
            ~merged_2_df['PROGRAMME'].isin(merged_1_df['PROGRAMME'])].copy()
        part2.reset_index(drop=True, inplace=True)
        part2.index += 1
        part2.rename(columns={part2.columns[1]: 'Enrolled Students',
                              part2.columns[2]: 'Registered Students',
                              part2.columns[3]: 'Students with IDs'},
                     inplace=True)
        part2.fillna(0, inplace=True)
        part2 = part2.map(lambda x: int(x) if isinstance(x, float) else x)

        merged_df = merged_1_df
        merged_df.fillna(0, inplace=True)
        merged_df = merged_df.map(lambda x: int(x) if isinstance(x, float)
                                  else x)
        df1 = df1.map(lambda x: int(x) if isinstance(x, float) else x)
        df2 = df2.map(lambda x: int(x) if isinstance(x, float) else x)
        df3 = df3.map(lambda x: int(x) if isinstance(x, float) else x)

        merged_df = merged_df.rename(columns={
            merged_df.columns[-3]: 'Enrolled Students',
            merged_df.columns[-2]: 'Registered Students',
            merged_df.columns[-1]: 'Students with IDs'})

        index = merged_df.index[
            merged_df['PROGRAMME'] == '<b>Grand Total</b>'].tolist()
        if index:
            index = index[0]
            new_row = pd.DataFrame({
                'PROGRAMME': ['<b>Programme Names Missing in an Enrolment '
                              'Database But Present in Either Registration '
                              'Database or Students with IDs Database</b>'],
                'Enrolled Students': [''],
                'Registered Students': [''],
                'Students with IDs': ['']})
            part1 = merged_df.iloc[:index + 1]
            merged_df = pd.concat([part1, new_row, part2], ignore_index=False)
        merged_df.index += 1

        # --- charts, embedded in the report -----------------------------
        charts_file = self.make_charts(df1, df2, df3, merged_df)
        import base64
        with open(charts_file, "rb") as fh:
            charts_uri = ("data:image/png;base64,"
                          + base64.b64encode(fh.read()).decode())

        html_output = self.generate_html_report(df1, df2, df3, merged_df,
                                                charts_uri)
        self.save_html_report(html_output, 'Report.html')
        self.generate_pdf_report(html_output, 'Report.pdf')

        # --- the tables as data ----------------------------------------
        for frame, name in ((df1, 'Report_Enrolled.csv'),
                            (df2, 'Report_Registered.csv'),
                            (df3, 'Report_IDs.csv'),
                            (merged_df, 'Report_Comparison.csv')):
            out = frame.copy()
            if isinstance(out.columns, pd.MultiIndex):
                lvl0, lvl1 = out.columns.get_level_values(0), \
                    out.columns.get_level_values(1)
                flat, year = [], ""
                for a, b in zip(lvl0, lvl1):
                    a, b = str(a).strip(), str(b).strip()
                    if a and a != "PROGRAMME":
                        year = a
                    flat.append(b if a == "PROGRAMME" else f"{year} {b}".strip())
                out.columns = flat
            out = out.map(lambda x: str(x).replace("<b>", "").replace("</b>", "")
                          if isinstance(x, str) else x)
            out.to_csv(name, index=False)

        print()
        print("Report.html   Report.pdf   duce_charts.png")
        print("Report_Enrolled.csv  Report_Registered.csv  Report_IDs.csv  "
              "Report_Comparison.csv")
        return df1, df2, df3, merged_df


# --- run ----------------------------------------------------------------
file_list = (glob.glob('files/*.xlsx') + glob.glob('files/*.xls')
             + glob.glob('files/*.csv'))
report_generator = ReportGenerator()
df1, df2, df3, df4 = report_generator.generate_report_data(file_list)
