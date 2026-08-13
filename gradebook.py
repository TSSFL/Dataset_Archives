# -*- coding: utf-8 -*-
"""Student grade book - logic only. The data lives on Dropbox.

Run it from a SageMathCell by naming your data first, then loading this file:

    ROSTER_URL   = "https://www.dropbox.com/s/..../roster.csv?dl=1"
    HWK_EXAM_URL = "https://www.dropbox.com/s/..../hwk_and_exam_grades.csv?dl=1"
    QUIZ_ZIP_URL = "https://www.dropbox.com/s/..../Quiz_Folder.zip?dl=1"

    load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/gradebook.py")

Sage's load() executes this file in the caller's namespace, so the three
names above are already in scope by the time anything here runs.

**No data URL appears in this file, and none ever should.** The code is
public on GitHub; the links to the students' records are not. Keeping them in
the cell means the same logic serves any class - point it at a different
roster and it runs unchanged - and a fork of this repository carries no route
to anybody's data.

Outputs
    Exams_Results.html / .pdf   the full grade book
    Exams_Results.csv           the same table, as data
    Final_Grades.csv            the summary: who got what, and did they pass
    Section N Grades.csv        one per section, sorted by name

Adapted from a Real Python article; the sample data is theirs.
"""

# --- the data, named by the caller --------------------------------------
_needed = ("ROSTER_URL", "HWK_EXAM_URL", "QUIZ_ZIP_URL")
_missing = [n for n in _needed if n not in globals()]
if _missing:
    raise NameError(
        "gradebook.py does not carry data locations - define them in the cell "
        "before loading it.\nMissing: " + ", ".join(_missing) + "\n\n"
        '    ROSTER_URL   = "https://www.dropbox.com/s/.../roster.csv?dl=1"\n'
        '    HWK_EXAM_URL = "https://www.dropbox.com/s/.../hwk_and_exam_grades.csv?dl=1"\n'
        '    QUIZ_ZIP_URL = "https://www.dropbox.com/s/.../Quiz_Folder.zip?dl=1"\n'
    )

import os
import urllib.request
import zipfile

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats            # `import scipy` alone does not bring in .stats
import seaborn as sns

textstr = 'Created at \nwww.tssfl.com'

# --- load the roster ----------------------------------------------------
# An index is set with index_col to help process the data later, and only the
# useful columns are kept with usecols. converters lowercases the join keys so
# strings compare cleanly later on.
roster_df = pd.read_csv(
    ROSTER_URL,
    converters={"NetID": str.lower, "Email Address": str.lower},
    usecols=["Section", "Email Address", "NetID"],
    index_col="NetID",
)

# --- homework and examination grades ------------------------------------
# The submission-time columns are dropped by the lambda passed to usecols.
# SID is the index, to match the roster.
hwk_exam_grades_df = pd.read_csv(
    HWK_EXAM_URL,
    converters={"SID": str.lower},
    usecols=lambda x: "Submission" not in x,
    index_col="SID",
)

# --- quiz grades --------------------------------------------------------
# The quizzes arrive zipped, one CSV each. They are concatenated along axis=1
# so each quiz becomes a column, aligned on the student's email address.
urllib.request.urlretrieve(QUIZ_ZIP_URL, "Quiz_Folder.zip")
with zipfile.ZipFile("Quiz_Folder.zip", "r") as zip_ref:
    zip_ref.extractall()

quiz_grades_df = pd.DataFrame()
for j in range(1, 6):
    file_path = "./Quiz_Folder/quiz_%s_grades.csv" % (j)
    quiz = pd.read_csv(
        file_path,
        converters={"Email": str.lower},
        index_col=["Email"],
        usecols=["Email", "Grade"],
    ).rename(columns={"Grade": "Quiz %s" % j})
    quiz_grades_df = pd.concat([quiz_grades_df, quiz], axis=1)
    os.remove(file_path)

# --- merge the three sources -------------------------------------------
# Each source identifies a student differently: NetID, SID, email address.
# Merge the roster to the homework on their shared index, then bring in the
# quizzes on the email address.
final_data_df = pd.merge(
    roster_df, hwk_exam_grades_df, left_index=True, right_index=True)
final_data_df = pd.merge(
    final_data_df, quiz_grades_df, left_on="Email Address", right_index=True)
final_data_df = final_data_df.fillna(0)

# --- exam scores --------------------------------------------------------
n_exams = 3
for n in range(1, n_exams + 1):
    final_data_df[f"Exam {n} Score"] = (
        final_data_df[f"Exam {n}"] / final_data_df[f"Exam {n} - Max Points"]
    )

# --- homework scores ----------------------------------------------------
# Two ways of scoring homework, and the student keeps the better of the two:
# total points earned over total available, or the mean of the per-assignment
# fractions (which weights every assignment equally regardless of its size).
homework_scores = final_data_df.filter(regex=r"^Homework \d\d?$", axis=1)
homework_max_points = final_data_df.filter(regex=r"^Homework \d\d? -", axis=1)

sum_of_hwk_scores = homework_scores.sum(axis=1)
sum_of_hwk_max = homework_max_points.sum(axis=1)
final_data_df["Total Homework"] = sum_of_hwk_scores / sum_of_hwk_max

hw_max_renamed = homework_max_points.set_axis(homework_scores.columns, axis=1)
average_hw_scores = (homework_scores / hw_max_renamed).sum(axis=1)
final_data_df["Average Homework"] = average_hw_scores / homework_scores.shape[1]

final_data_df["Homework Score"] = final_data_df[
    ["Total Homework", "Average Homework"]].max(axis=1)

# --- quiz scores --------------------------------------------------------
quiz_scores = final_data_df.filter(regex=r"^Quiz \d$", axis=1)
quiz_max_points = pd.Series(
    {"Quiz 1": 11, "Quiz 2": 15, "Quiz 3": 17, "Quiz 4": 14, "Quiz 5": 12})

sum_of_quiz_scores = quiz_scores.sum(axis=1)
sum_of_quiz_max = quiz_max_points.sum()
final_data_df["Total Quizzes"] = sum_of_quiz_scores / sum_of_quiz_max

average_quiz_scores = (quiz_scores / quiz_max_points).sum(axis=1)
final_data_df["Average Quizzes"] = average_quiz_scores / quiz_scores.shape[1]

final_data_df["Quiz Score"] = final_data_df[
    ["Total Quizzes", "Average Quizzes"]].max(axis=1)

# --- the final grade ----------------------------------------------------
weightings = pd.Series({
    "Exam 1 Score": 0.05,
    "Exam 2 Score": 0.1,
    "Exam 3 Score": 0.15,
    "Quiz Score": 0.30,
    "Homework Score": 0.4,
})

final_data_df["Final Score"] = (
    final_data_df[weightings.index] * weightings).sum(axis=1)
final_data_df["Ceiling Score"] = np.ceil(final_data_df["Final Score"] * 100)

grades = {
    90: "A+",
    70: "A",
    60: "B+",
    50: "B",
    40: "C",
    35: "D",
    25: "E",
    0: "F",
}


def grade_mapping(value):
    for key, letter in grades.items():
        if value >= key:
            return letter


letter_grades = final_data_df["Ceiling Score"].map(grade_mapping)
final_data_df["Final Grade"] = pd.Categorical(
    letter_grades, categories=grades.values(), ordered=True)

print(final_data_df)

# --- one file per section ----------------------------------------------
for section, table in final_data_df.groupby("Section"):
    section_file = f"Section {section} Grades.csv"
    num_students = table.shape[0]
    print(f"In Section {section} there are {num_students} students saved to "
          f"file {section_file}.")
    table.sort_values(by=["Last Name", "First Name"]).to_csv(section_file)

# =======================================================================
#  Plots
# =======================================================================
sns.set_style('darkgrid')        # darkgrid, white grid, dark, white and ticks
plt.rc('axes', titlesize=18)
plt.rc('axes', labelsize=14)
plt.rc('xtick', labelsize=13)
plt.rc('ytick', labelsize=13)
plt.rc('legend', fontsize=13)
plt.rc('font', size=13)

colors1 = sns.color_palette('pastel')
colors2 = sns.color_palette('deep')

total = float(len(final_data_df))
p1 = mpatches.Patch(label='A+: 90 - 100')
p2 = mpatches.Patch(label='A: 70 - 89')
p3 = mpatches.Patch(label='B+: 60 - 69')
p4 = mpatches.Patch(label='B: 50 - 59')
p5 = mpatches.Patch(label='C: 40 - 49')
p6 = mpatches.Patch(label='D: 35 - 39')
p7 = mpatches.Patch(label='E: 25 - 34')
# The grade below 25 is F, not a second E - the key in `grades` says so.
p8 = mpatches.Patch(label='F: 0 - 24')

# Plot 1 - counts
grade_counts = final_data_df["Final Grade"].value_counts().sort_index()
ax = grade_counts.plot.bar(color=colors2[:5])
ax.bar_label(ax.containers[0], label_type='edge')
ax.margins(y=0.1)
plt.title("Letter Grade Distribution")
plt.legend(handles=[p1, p2, p3, p4, p5, p6, p7, p8], title="Grade Summary",
           loc=1, fontsize='medium', fancybox=True)
plt.gcf().text(0.60, 0.25, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

# Plot 2 - percentages
grade_counts = final_data_df["Final Grade"].value_counts().sort_index()
ax = grade_counts.plot.bar(color=colors1[:5])
for p in ax.patches:
    percentage = '{:.2f}%'.format(100 * p.get_height() / total)
    x = p.get_x() + p.get_width() / 2.0
    h = p.get_height()
    if h != 0:
        ax.annotate(percentage, xy=(x, h + 0.1), ha="center", va="bottom",
                    rotation=0, color='red')
plt.title("Letter Grade Distribution")
plt.legend(handles=[p1, p2, p3, p4, p5, p6, p7, p8], title="Grade Summary",
           loc=1, fontsize='medium', fancybox=True)
plt.gcf().text(0.60, 0.25, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

# Plot 3 - histogram of the ceiling score
final_data_df["Ceiling Score"].plot.hist(bins=20, label="Hist", color="magenta")
plt.title("Student Scores Distribution")
plt.gcf().text(0.2, 0.75, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

# Plot 4 - kernel density against a normal of the same mean and spread
final_data_df["Ceiling Score"].plot.density(linewidth=4, label="KDE")
final_mean = final_data_df["Ceiling Score"].mean()
final_std = final_data_df["Ceiling Score"].std()
x = np.linspace(final_mean - 5 * final_std, final_mean + 5 * final_std, 200)
normal_dist = scipy.stats.norm.pdf(x, loc=final_mean, scale=final_std)
plt.plot(x, normal_dist, label="Normal Distr", linewidth=4)
plt.title("Student Scores Distribution")
plt.legend()
plt.gcf().text(0.2, 0.75, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

# Plot 5 - the same for the unrounded final score
final_data_df["Final Score"].plot.hist(bins=20, label="Hist", color="magenta")
final_data_df["Final Score"].plot.density(linewidth=4, label="KDE")
final_mean = final_data_df["Final Score"].mean()
final_std = final_data_df["Final Score"].std()
x = np.linspace(final_mean - 5 * final_std, final_mean + 5 * final_std, 200)
normal_dist = scipy.stats.norm.pdf(x, loc=final_mean, scale=final_std)
plt.plot(x, normal_dist, label="Normal Distr", linewidth=4)
plt.title("Normalized Student Scores Distribution")
plt.legend()
plt.gcf().text(0.2, 0.75, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

# --- additional views ---------------------------------------------------

# Plot 6 - is any section doing better than the others?
# Drawn with matplotlib rather than seaborn: seaborn changed the boxplot
# signature between 0.12 and 0.13 (hue/legend handling), and this has to run
# on whichever version the kernel happens to have.
sections = sorted(final_data_df["Section"].unique())
data = [final_data_df.loc[final_data_df["Section"] == s, "Ceiling Score"].values
        for s in sections]
fig, ax = plt.subplots(figsize=(9, 6))
bp = ax.boxplot(data, patch_artist=True, widths=0.55,
                medianprops=dict(color="white", linewidth=2))
for patch, colour in zip(bp["boxes"], colors1):
    patch.set_facecolor(colour)
for i, values in enumerate(data, start=1):
    jitter = np.random.default_rng(int(7)).normal(0, 0.045, len(values))
    ax.plot(np.full(len(values), i) + jitter, values, ".", color=".25",
            markersize=5, alpha=0.55)
    # Above the whisker, not on the median line it was landing on.
    ax.annotate(f"mean {values.mean():.1f}", xy=(i, values.max()),
                xytext=(0, 10), textcoords="offset points", ha="center",
                color="red")
ax.set_xticks(range(1, len(sections) + 1))
ax.set_xticklabels([f"Section {s}" for s in sections])
plt.title("Score Distribution by Section")
plt.ylabel("Ceiling Score")
ax.margins(y=0.12)
plt.gcf().text(0.01, 0.01, textstr, fontsize=12, color='green')
plt.show()
plt.clf()

# Plot 7 - which component actually decides the grade?
fig, ax = plt.subplots(figsize=(9, 6.5))
scatter = ax.scatter(final_data_df["Homework Score"] * 100,
                     final_data_df["Quiz Score"] * 100,
                     c=final_data_df["Ceiling Score"], cmap="viridis",
                     s=55, edgecolor="white", linewidth=0.7)
cbar = fig.colorbar(scatter, ax=ax)
cbar.set_label("Ceiling Score")
ax.set_xlabel("Homework Score (%)")
ax.set_ylabel("Quiz Score (%)")
plt.title("Homework against Quiz Performance")
plt.gcf().text(0.02, 0.02, textstr, fontsize=14, color='green')
plt.show()
plt.clf()

# Plot 8 - what each component contributes to the final mark. Homework is
# weighted 0.4 and the three exams only 0.3 between them, so the picture is
# not the one the exam timetable suggests.
contrib = pd.DataFrame({
    name.replace(" Score", ""): final_data_df[name] * w * 100
    for name, w in weightings.items()
})
means = contrib.mean().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(9, 6))
bars = ax.barh(range(len(means)), means.values, color=colors2[:len(means)],
               height=0.6)
ax.set_yticks(range(len(means)))
ax.set_yticklabels(means.index)
ax.invert_yaxis()
ax.bar_label(bars, fmt="%.1f", padding=4)
ax.set_xlabel("Mean contribution to the final mark (points out of 100)")
plt.title("Where the Final Mark Comes From")
ax.text(0.98, 0.06, textstr, transform=ax.transAxes, ha="right",
        fontsize=12, color='green')
plt.show()
plt.clf()

# Plot 9 - the grade profile of each section, as shares
by_section = pd.crosstab(final_data_df["Section"],
                         final_data_df["Final Grade"])
by_section = by_section.loc[:, by_section.sum() > 0]
shares = by_section.div(by_section.sum(axis=1), axis=0) * 100
ax = shares.plot.barh(stacked=True, color=colors1[:shares.shape[1]],
                      figsize=(10, 5), width=0.6)
for container in ax.containers:
    labels = [f"{v:.0f}%" if v >= 5 else "" for v in container.datavalues]
    ax.bar_label(container, labels=labels, label_type="center", fontsize=11)
ax.set_xlabel("Share of the section (%)")
ax.set_xlim(0, 100)
plt.title("Grade Profile by Section")
plt.legend(title="Final Grade", bbox_to_anchor=(1.01, 1), loc="upper left")
plt.subplots_adjust(bottom=0.24)
plt.gcf().text(0.01, 0.02, textstr, fontsize=12, color='green')
plt.show()
plt.clf()

# Plot 10 - the ranked curve, which shows where the grade boundaries actually
# fall and how many students sit within a point or two of one.
ranked = final_data_df["Ceiling Score"].sort_values(ascending=False).values
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(range(1, len(ranked) + 1), ranked, linewidth=3, color=colors2[0])
ax.fill_between(range(1, len(ranked) + 1), ranked, color=colors1[0], alpha=0.6)
for cut, letter in sorted(grades.items()):
    if cut and (ranked.min() - 6) <= cut <= ranked.max():
        ax.axhline(cut, color="red", linewidth=1, linestyle="--", alpha=0.6)
        ax.annotate(letter, xy=(len(ranked), cut), xytext=(6, -4),
                    textcoords="offset points", color="red")
# Start the axis near the data. From zero, every score sat in the top third
# of the chart and the shape of the curve was invisible.
low = max(0, ranked.min() - 6)
ax.set_ylim(low, ranked.max() + 4)
ax.set_xlim(1, len(ranked))
ax.set_xlabel("Student rank")
ax.set_ylabel("Ceiling Score")
plt.title("Scores in Rank Order, with Grade Boundaries")
ax.text(0.98, 0.94, textstr, transform=ax.transAxes, ha="right", va="top",
        fontsize=12, color='green')
plt.show()
plt.clf()

# =======================================================================
#  Reports
# =======================================================================
from pretty_html_table import build_table
from weasyprint import CSS
from weasyprint import HTML


def remarks(row):
    if row['Final Grade'] in ('A+', 'A', 'B+', 'B', 'C'):
        return 'Pass'
    if row['Final Grade'] in ('D', 'E'):
        return 'Fail'
    return 'Other'


final_data_df['Remarks'] = final_data_df.apply(lambda row: remarks(row), axis=1)

final_data_df.insert(0, 'Registration_Number',
                     range(25341, 25341 + len(final_data_df)))
final_data_df['Registration_Number'] = final_data_df['Registration_Number'].apply(
    lambda x: "{}{}".format('2023-04-', x))

df_sorted = final_data_df.sort_values('Final Score', ascending=False)
summary = df_sorted['Ceiling Score'].describe()
print(summary)
df_sorted.insert(0, 'S/No', range(1, 1 + len(df_sorted)))

# The CSVs are written before the MultiIndex title is added, so they carry
# plain single-row headers that a spreadsheet can sort and filter.
df_sorted.to_csv("Exams_Results.csv", index=False)

summary_cols = ['S/No', 'Registration_Number', 'First Name', 'Last Name',
                'Section', 'Homework Score', 'Quiz Score', 'Final Score',
                'Ceiling Score', 'Final Grade', 'Remarks']
final_grades = df_sorted[[c for c in summary_cols if c in df_sorted.columns]].copy()
for col in ('Homework Score', 'Quiz Score', 'Final Score'):
    if col in final_grades:
        final_grades[col] = (final_grades[col] * 100).round(1)
final_grades.to_csv("Final_Grades.csv", index=False)

textstr = "Mock Student Results Computed at TSSFL Stack: www.tssfl.com"
df_sorted.columns = pd.MultiIndex.from_product([[textstr], df_sorted.columns])

output = build_table(df_sorted, 'blue_light', font_size='medium',
                     font_family='Open Sans, sans-serif', text_align='left',
                     index=False, even_color='black', even_bg_color='white')

with open("Exams_Results.html", "w+") as file:
    file.write(output)

HTML(string=output).write_pdf("Exams_Results.pdf",
                              stylesheets=[CSS(string='@page { size: landscape }')])

print()
print("Exams_Results.html   Exams_Results.pdf")
print("Exams_Results.csv    - the full grade book, %d rows x %d columns"
      % df_sorted.shape)
print("Final_Grades.csv     - the summary, %d rows x %d columns"
      % final_grades.shape)
print("Pass: %d   Fail: %d"
      % ((final_data_df['Remarks'] == 'Pass').sum(),
         (final_data_df['Remarks'] == 'Fail').sum()))
