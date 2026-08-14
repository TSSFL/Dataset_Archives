"""One-way and two-way ANOVA, worked through end to end.

Run it from a SageMathCell on www.tssfl.com with nothing but::

    [py]
    load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/anova.py")
    [/py]

The data is public, so it lives in this file alongside the logic - the two
teaching datasets are fetched straight from reneshbedre.github.io.

What it covers
--------------
One-way ANOVA
    F test, the ANOVA table from statsmodels and from bioinfokit, Tukey's HSD
    for the pairwise comparisons, then the assumption checks: QQ plot,
    residual histogram, Shapiro-Wilk for normality, Bartlett's and Levene's
    for homogeneity of variances.

Two-way ANOVA
    The same, plus an interaction plot and Tukey's HSD on each main effect and
    on the interaction.

Three fixes this file makes
---------------------------
bioinfokit 2.1.4 predates pandas 2 and breaks on it in one place; the patch is
at the top of the file with the reasoning. It also emits a handful of
SyntaxWarnings from its own source when imported, which have nothing to do
with your analysis and are silenced for the duration of the import only.

The third is scipy's, and it is the one worth knowing about: bartlett()
returns a different and incorrect statistic when handed integer arrays. The
one-way data file is whole numbers, so this is not hypothetical - it turns
p = 0.128 into p = 0.050 and reverses the verdict on the equal-variance
assumption. The data is cast to float before any test sees it.

Method and worked example after Renesh Bedre,
https://www.reneshbedre.com/blog/anova.html
"""

import warnings

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.graphics.factorplots import interaction_plot

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MaxNLocator

# bioinfokit's own source has a few unescaped backslashes in regexes, which
# Python 3.12 reports as SyntaxWarning while compiling the module. They are
# bioinfokit's to fix, not ours, and they say nothing about the analysis - so
# they are kept out of the way of the import and nowhere else.
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    from bioinfokit.analys import analys_general, stat


# ---------------------------------------------------------------------------
#  bioinfokit 2.1.4 vs pandas 2
#
#  get_list_from_df() averages a whole slice of the frame and then picks the
#  response column out of the result:
#
#      df[df[xfac_var] == ele].mean().loc[res_var]
#
#  Up to pandas 1.x, DataFrame.mean() quietly dropped the columns it could not
#  average. pandas 2 refuses instead, and the group-label column is what it
#  chokes on:
#
#      TypeError: Could not convert ['AAAAA'] to numeric
#
#  ...that being the five 'A' treatment labels glued together. Taking the
#  response column *before* averaging is the order that was always meant, and
#  gives identical numbers. Nothing else in bioinfokit is touched.
# ---------------------------------------------------------------------------
def _get_list_from_df(df=None, xfac_var=None, res_var=None, funct=None):
    group_list = []
    mult_group = dict()
    mult_group_count = dict()
    df_counts = 0
    sample_size_r = None

    if isinstance(xfac_var, list) and len(xfac_var) > 3:
        raise Exception("Only three factors supported")

    if isinstance(xfac_var, str):
        keys = [(ele,) for ele in df[xfac_var].unique()]
        cols = [xfac_var]
    elif isinstance(xfac_var, list) and 2 <= len(xfac_var) <= 3:
        cols = analys_general.keep_uniq(xfac_var)
        levels = [df[c].unique() for c in cols]
        keys = [(a, b) for a in levels[0] for b in levels[1]] if len(cols) == 2 \
            else [(a, b, c) for a in levels[0] for b in levels[1] for c in levels[2]]
    else:
        raise Exception("Only three factors supported")

    sample_size_r = len(keys)
    for key in keys:
        mask = np.ones(len(df), dtype=bool)
        for col, level in zip(cols, key):
            mask &= (df[col] == level).to_numpy()
        chunk = df[mask]
        name = key[0] if len(key) == 1 else key
        if funct == "get_list":
            group_list.append(list(chunk[res_var]))
            df_counts += 1
        elif funct == "get_dict":
            mult_group[name] = chunk[res_var].mean()      # column first, then mean
            mult_group_count[name] = chunk.shape[0]

    if funct == "get_list":
        return group_list, df_counts
    elif funct == "get_dict":
        return mult_group, mult_group_count, sample_size_r


analys_general.get_list_from_df = staticmethod(_get_list_from_df)


def rule(text):
    """A heading, so a long run of output stays readable."""
    print("")
    print("=" * 78)
    print(text)
    print("=" * 78)


def note(text):
    """An interpretation, wrapped, set apart from the numbers above it."""
    import textwrap
    print("")
    for line in textwrap.wrap(text, 76):
        print(line)


# The plotting look of the original: seaborn's darkgrid, larger type.
sns.set_style("darkgrid")          # darkgrid, whitegrid, dark, white, ticks
plt.rc("axes", titlesize=18)       # fontsize of the axes title
plt.rc("axes", labelsize=14)       # fontsize of the x and y labels
plt.rc("xtick", labelsize=13)      # fontsize of the tick labels
plt.rc("ytick", labelsize=13)      # fontsize of the tick labels
plt.rc("legend", fontsize=13)      # legend fontsize
plt.rc("font", size=13)


# ===========================================================================
#  ONE-WAY (ONE FACTOR) ANOVA
# ===========================================================================
rule("ONE-WAY ANOVA  -  four treatments, five plants each")

ONEWAY_URL = "https://reneshbedre.github.io/assets/posts/anova/onewayanova.txt"
df = pd.read_csv(ONEWAY_URL, sep="\t")
print("")
print("Here is the data - one column per treatment:")
print(df)

# The file is whole numbers, so pandas reads it as int64 - and scipy 1.15's
# bartlett() gives a different, wrong answer for integer input: T = 7.8307,
# p = 0.0496 instead of T = 5.6878, p = 0.1278. That flips the conclusion of
# the homogeneity-of-variance check from "assumption holds" to "assumption
# fails". Working out the statistic by hand confirms 5.6878 is the right one.
# Levene and the F test are unaffected, but one wrong answer is enough:
# measurements are real numbers, so store them as real numbers.
df = df.astype(float)

# statsmodels wants the data stacked: one row per observation, with the group
# it belongs to named in its own column.
df_melt = pd.melt(df.reset_index(), id_vars=["index"],
                  value_vars=["A", "B", "C", "D"])
df_melt.columns = ["index", "treatments", "value"]

# A boxplot shows the spread; the swarm on top of it shows every observation,
# which matters when each group holds only five.
ax = sns.boxplot(x="treatments", y="value", data=df_melt, color="#40E0D0")
ax = sns.swarmplot(x="treatments", y="value", data=df_melt, color="#8601AF")
plt.xlabel("Treatments")
plt.ylabel("Value")
plt.title("Distribution of the response by treatment")
plt.tight_layout()
plt.show()
plt.close()

# --- The F test ------------------------------------------------------------
# f_oneway takes the groups themselves and returns the F statistic and p value.
fvalue, pvalue = stats.f_oneway(df["A"], df["B"], df["C"], df["D"])
print("")
print("F value = %.6f,  p value = %.3e" % (fvalue, pvalue))

# --- The ANOVA table, R-style ----------------------------------------------
model = ols("value ~ C(treatments)", data=df_melt).fit()
anova_table = sm.stats.anova_lm(model, typ=2)
print("")
print("ANOVA table (statsmodels):")
print(anova_table)

# The same table through bioinfokit, which wraps anova_lm. With a balanced
# design - equal sample size in every group - Type 1, 2 and 3 sums of squares
# all agree, so it does not matter which you ask for.
res = stat()
res.anova_stat(df=df_melt, res_var="value", anova_model="value ~ C(treatments)")
print("")
print("ANOVA table (bioinfokit):")
print(res.anova_summary)

note("The p value is below 0.05, so the treatments do not all have the same "
     "mean. F and p move in opposite directions: a large F, above the "
     "critical value, is what produces a small p.")

# --- Which pairs differ? ---------------------------------------------------
# The F test is an omnibus test. It says the group means are not all equal; it
# does not say which ones differ. Tukey's HSD compares every pair while
# holding the family-wise error rate at 0.05. With unequal group sizes this is
# the Tukey-Kramer test, which bioinfokit selects for you.
res = stat()
res.tukey_hsd(df=df_melt, res_var="value", xfac_var="treatments",
              anova_model="value ~ C(treatments)")
print("")
print("Tukey's HSD, every pair of treatments:")
print(res.tukey_summary)

note("A p-value printed as 0.001 means <= 0.001. Every pair except A-C "
     "rejects the null hypothesis at 0.05, so A and C are the only two "
     "treatments this experiment cannot tell apart.")

# --- Do the assumptions hold? ---------------------------------------------
rule("ONE-WAY ANOVA  -  checking the assumptions")

# Standardized residuals show outliers more clearly than raw ones. On a QQ
# plot, points lying along the 45-degree line mean approximately normal
# residuals.
sm.qqplot(res.anova_std_residuals, line="45")
plt.xlabel("Theoretical quantiles")
plt.ylabel("Standardized residuals")
plt.title("QQ plot of the standardized residuals")
plt.tight_layout()
plt.show()
plt.close()

plt.hist(res.anova_model_out.resid, bins="auto", histtype="bar",
         ec="k", color="green")
plt.xlabel("Residuals")
plt.ylabel("Frequency")
plt.title("Residuals of the one-way model")
# A frequency is a count of observations, so the axis has no half-steps.
plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
plt.tight_layout()
plt.show()
plt.close()

# Shapiro-Wilk. Null hypothesis: the data is drawn from a normal distribution.
w, pvalue = stats.shapiro(model.resid)
print("")
print("Shapiro-Wilk on the residuals:  W = %.6f,  p = %.6f" % (w, pvalue))
note("p is not significant, so we fail to reject the null hypothesis and "
     "treat the residuals as normally distributed.")

# Bartlett's test. Null hypothesis: the populations have equal variances. It
# assumes normality, which the Shapiro-Wilk result above supports.
w, pvalue = stats.bartlett(df["A"], df["B"], df["C"], df["D"])
print("")
print("Bartlett's test:  T = %.6f,  p = %.6f" % (w, pvalue))

# The same test from a stacked table, which is the shape real data arrives in.
res = stat()
res.bartlett(df=df_melt, res_var="value", xfac_var="treatments")
print("")
print("Bartlett's test (bioinfokit, from the stacked table):")
print(res.bartlett_summary)

note("p is not significant, so the treatments have equal variances and the "
     "ANOVA's second assumption holds.")

# Levene's test does the same job without assuming normality, so it is the one
# to reach for when Shapiro-Wilk has already failed.
res = stat()
res.levene(df=df_melt, res_var="value", xfac_var="treatments")
print("")
print("Levene's test (no normality assumed):")
print(res.levene_summary)


# ===========================================================================
#  TWO-WAY (TWO FACTOR) ANOVA  -  a factorial design
# ===========================================================================
rule("TWO-WAY ANOVA  -  genotype and time, and their interaction")

# Two factors act at once here: the genotype of the plant and the year. A
# two-way ANOVA evaluates both together, and tests three hypotheses: the
# effect of genotype on yield, the effect of time on yield, and the effect of
# the two interacting. One-way ANOVA could only look at one factor at a time.
TWOWAY_URL = "https://reneshbedre.github.io/assets/posts/anova/twowayanova.txt"
d = pd.read_csv(TWOWAY_URL, sep="\t")
d_melt = pd.melt(d, id_vars=["Genotype"],
                 value_vars=["1_year", "2_year", "3_year"])
d_melt.columns = ["Genotype", "years", "value"]
d_melt["value"] = d_melt["value"].astype(float)   # see the note above
print("")
print("Stacked, one row per observation - compare with the file as it came:")
print(d_melt.head())

sns.boxplot(x="Genotype", y="value", hue="years", data=d_melt, palette="Set2")
plt.xlabel("Genotype")
plt.ylabel("Yield")
plt.title("Yield by genotype and year")
plt.legend(title="Years")
plt.tight_layout()
plt.show()
plt.close()

TWOWAY_MODEL = "value ~ C(Genotype) + C(years) + C(Genotype):C(years)"
model = ols(TWOWAY_MODEL, data=d_melt).fit()
anova_table = sm.stats.anova_lm(model, typ=2)
print("")
print("Two-way ANOVA table (statsmodels):")
print(anova_table)

res = stat()
res.anova_stat(df=d_melt, res_var="value",
               anova_model="value~C(Genotype)+C(years)+C(Genotype):C(years)")
print("")
print("Two-way ANOVA table (bioinfokit):")
print(res.anova_summary)

note("All three p values are below 0.05. Genotype affects yield, time affects "
     "yield, and the two interact - the effect of one depends on the level of "
     "the other. With an unbalanced design, ask for typ=3 instead; Type 3 "
     "sums of squares is the right choice for unequal group sizes in a "
     "multifactorial ANOVA.")

# An interaction plot, also called a profile plot. Parallel traces would mean
# no interaction; traces that cross or diverge are the interaction made
# visible.
interaction_plot(x=d_melt["Genotype"], trace=d_melt["years"],
                 response=d_melt["value"],
                 colors=["#4c061d", "#d17a22", "#b4c292"])
plt.xlabel("Genotype")
plt.ylabel("Mean yield")
plt.title("Interaction between genotype and year")
plt.tight_layout()
plt.show()
plt.close()

# --- Post-hoc, one effect at a time ---------------------------------------
rule("TWO-WAY ANOVA  -  which levels differ (Tukey's HSD)")

res = stat()
res.tukey_hsd(df=d_melt, res_var="value", xfac_var="Genotype",
              anova_model=TWOWAY_MODEL)
print("")
print("Main effect: genotype")
print(res.tukey_summary)

res.tukey_hsd(df=d_melt, res_var="value", xfac_var="years",
              anova_model=TWOWAY_MODEL)
print("")
print("Main effect: years")
print(res.tukey_summary)

res.tukey_hsd(df=d_melt, res_var="value", xfac_var=["Genotype", "years"],
              anova_model=TWOWAY_MODEL)
print("")
print("Interaction, genotype by year (first rows of %d):"
      % len(res.tukey_summary))
print(res.tukey_summary.head())

# --- Assumptions again -----------------------------------------------------
rule("TWO-WAY ANOVA  -  checking the assumptions")

sm.qqplot(res.anova_std_residuals, line="45")
plt.xlabel("Theoretical quantiles")
plt.ylabel("Standardized residuals")
plt.title("QQ plot of the standardized residuals")
plt.tight_layout()
plt.show()
plt.close()

plt.hist(res.anova_model_out.resid, bins="auto", histtype="bar",
         ec="k", color="seagreen")
plt.xlabel("Residuals")
plt.ylabel("Frequency")
plt.title("Residuals of the two-way model")
plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
plt.tight_layout()
plt.show()
plt.close()

w, pvalue = stats.shapiro(res.anova_model_out.resid)
print("")
print("Shapiro-Wilk on the residuals:  W = %.6f,  p = %.6f" % (w, pvalue))

note("This one is significant, but do not stop at the number. The QQ plot has "
     "its points along the 45-degree line and the histogram is roughly "
     "symmetric, both of which say the residuals are near enough normal. "
     "ANOVA is robust to this assumption: as long as there are no outliers, "
     "the Type I error rate and the p values hold up.")

res = stat()
res.levene(df=d_melt, res_var="value", xfac_var=["Genotype", "years"])
print("")
print("Levene's test across genotype and year:")
print(res.levene_summary)

note("p is not significant, so the groups have equal variances.")

rule("Done")
print("")
print("Method and worked example after Renesh Bedre,")
print("https://www.reneshbedre.com/blog/anova.html")
