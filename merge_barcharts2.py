# -*- coding: utf-8 -*-
"""Automated chart report - one merged PDF from a survey, in one pass.

Nine questions about the professional communities teachers take part in,
each broken down two ways (by gender, and by teaching subject), collected
into a single PDF ready to send.

What changed from the earlier version, and why:

* **It used to run out of kernel.** Eighteen figures at 17.5 x 7 inches,
  each written to its own PDF and reopened by PyPDF4 to be merged, took
  longer than SageCell allows and the cell died before finishing.
  ``PdfPages`` writes all pages to one file in one pass - no temporary
  files, no second library, and it finishes comfortably inside the limit.
* **Every bar was labelled twice and the empty ones as well.** A count in
  green, then a percentage rotated 90 degrees in red, on every patch
  including the zero-height ones a sparse ``hue`` leaves behind - which is
  where the ``0.00%`` labels came from. ``label_bars()`` writes one string
  per non-empty bar and drops any that would overlap.
* **The percentages did not add up.** The denominator was ``len(df)``, the
  number of rows in the whole survey, not the number who answered the
  question being charted. Every percentage was therefore too small, by a
  different amount on each page. It is now the answered count, stated on
  the page so the reader can see what the share is a share of.
* A summary page now leads the report: nine questions on one chart is the
  view that answers "which communities do teachers actually use", which no
  amount of paging through individual charts gives you.
"""
import io

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages

load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tssfl_style.py")

use("tssfl")
sns.set_theme(style="whitegrid", rc={
    "axes.facecolor": SURFACE, "figure.facecolor": SURFACE,
    "grid.color": GRID, "axes.edgecolor": GRID,
    "font.sans-serif": ["Nimbus Sans", "Helvetica", "DejaVu Sans"],
})

OUT = "Merged_Charts_XY.pdf"
SRC = "Source: TSSFL teachers survey, 116 respondents."

# --- data -------------------------------------------------------------
url = ("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/"
       "teachers_survey_data.csv")
df = pd.read_csv(io.StringIO(requests.get(url).content.decode("utf-8")))
df = df.replace(r"_", " ", regex=True)

# The nine "do you take part in ..." questions, and the two ways of
# splitting them. Selected by name rather than by position, so inserting a
# column upstream no longer silently charts the wrong thing.
GROUP = "group_ms4ff82/Indicate_whether_you_ommunities_or_groups/"
questions = [c for c in df.columns if c.startswith(GROUP)]
splits = ["group_fy3xs85/Gender_of_participant",
          "group_fy3xs85/Teaching_subjects"]

# Short readable names for the nine activities.
def short(col):
    return wrap(tidy(col).replace(" u", "").replace(" e", "").strip(), 30)


# =======================================================================
#  Summary page - all nine questions at once
# =======================================================================
rates = []
for q in questions:
    s = df[q].dropna().astype(str).str.strip().str.lower()
    if not len(s):
        continue
    rates.append((tidy(q), 100.0 * (s == "yes").sum() / len(s), len(s)))
summary_df = (pd.DataFrame(rates, columns=["Activity", "Percent", "Answered"])
                .sort_values("Percent"))

fig_summary, ax = plt.subplots(figsize=(11.5, 6.4))
ax.barh(range(len(summary_df)), summary_df["Percent"], height=0.62,
        color=palette()[0])
ax.set_yticks(range(len(summary_df)))
ax.set_yticklabels([wrap(a, 38) for a in summary_df["Activity"]],
                   fontsize=10)
ax.set_xlabel("Share answering yes (%)")
ax.set_xlim(0, 100)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.xaxis.grid(True, color=GRID, lw=1)
ax.set_axisbelow(True)
label_bars(ax, fmt="{:.0f}%", horizontal=True)
finish(fig_summary, "Which professional communities teachers take part in",
       "Percentage answering yes to each, out of those who answered that "
       "question.", source=SRC)

# =======================================================================
#  One page per question and split
# =======================================================================
pages = [fig_summary]
for q in questions:
    for split in splits:
        sub = df[[q, split]].dropna()
        if sub.empty or sub[q].nunique() < 1:
            continue                       # nothing to draw, so draw nothing
        answered = len(sub)
        levels = list(sub[split].value_counts().index)
        cols = dict(zip(levels, colors(min(len(levels), 8))))

        fig, ax = plt.subplots(figsize=(11.0, 5.6))
        sns.countplot(data=sub, x=q, hue=split, palette=cols,
                      order=scale_order(sub[q]), width=0.7, ax=ax)
        ax.set_xlabel("")
        ax.set_ylabel("Number of teachers")
        ax.set_xticklabels([wrap(t.get_text(), 18)
                            for t in ax.get_xticklabels()])
        if ax.legend_:
            ax.legend_.remove()
        # Share is out of those who answered *this* question, not the whole
        # survey - that was the bug that made the percentages meaningless.
        label_bars(ax, total=answered, pct=True)
        finish(fig, short(q),
               f"Split by {tidy(split).lower()}.  {answered} of {len(df)} "
               f"teachers answered this question.",
               legend=list(cols.items())[:6], source=SRC)
        pages.append(fig)

# =======================================================================
#  Write every page into one PDF, in a single pass
# =======================================================================
with PdfPages(OUT) as pdf:
    for fig in pages:
        pdf.savefig(fig)
        plt.close(fig)

print(f"Wrote {OUT} - {len(pages)} pages "
      f"({len(questions)} questions x {len(splits)} splits, plus a summary)")

# Show the summary on screen as well, so the cell is not silent.
table(summary_df.rename(columns={"Percent": "Percent yes"}),
      title="Participation in professional communities",
      fmt={"Percent yes": "{:.1f}%"}, source=SRC)
