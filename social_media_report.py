"""Political-party social media accounts: reach, activity and a report.

Logic here, data in the cell. Nothing in this file says where the sheet is::

    [py]
    SHEET_ID = "<the sheet id from its URL>"
    PARTY    = "CCM"          # optional - omit for every party
    PLATFORM = "Facebook"     # optional - omit for every platform

    load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/social_media_report.py")
    [/py]

The sheet this reads
--------------------
A sheet written by hand, in sections, one section per platform::

    Instagram                                             <- a bare platform name
       SN | Name of Party | Name of  Account | Number of Followers | Number  of Posts
        1 | Chadema       | Bawacha_tz       |                 988 |               42
          |               | Chademapwani     |                1038 |              171
          | CCM           | ...                                                      <- new party
    FACEBOOK                                              <- next section
       SN | Party         | Name of facebook Account | Number of members | ...

Every section names its columns differently - "Number of Followers", "Number
of members", "subscribers" - and the party is written once, on the row where
it starts. Both are handled: sections are found by the bare name in the first
column, the party is carried down the rows, and the audience column is
whatever the section calls it.

That is the whole reason this module exists in the shape it does. Reading the
same sheet by position - ``df.loc[134:145]`` - works exactly until somebody
adds an account, and then it silently describes the wrong rows.
"""

_needed = ("SHEET_ID", "CSV_URL")
if not any(n in globals() for n in _needed):
    raise NameError(
        "social_media_report.py does not carry data locations - define one in "
        "the cell before loading it.\n\n"
        '    SHEET_ID = "<the sheet id from its URL>"\n'
        "  or\n"
        '    CSV_URL  = "https://www.dropbox.com/scl/fi/.../accounts.csv?dl=1"\n'
    )

import base64
import datetime
import re
import unicodedata

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import LogLocator, NullFormatter
from weasyprint import HTML

load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tssfl_style.py")

use("tssfl")

# --- what the cell may override -------------------------------------------
PARTY = globals().get("PARTY") or None            # None = every party
PLATFORM = globals().get("PLATFORM") or None      # None = every platform
TITLE = globals().get("TITLE") or "Political party accounts on social media"
TOP = int(globals().get("TOP") or 20)             # accounts per bar chart
SOURCE = globals().get("SOURCE") or "Compiled account census, one row per account"

# Party names are typed inconsistently down the sheet - "ccm", "CCM",
# "ACT Wazalendo", "act", "tlp". Fold them onto one spelling each so a party
# is one party and not four.
PARTY_ALIASES = {
    "CHADEMA": "CHADEMA", "CCM": "CCM", "NCCR": "NCCR", "NCCR MAGEUZI": "NCCR",
    "CUF": "CUF", "ACT": "ACT", "ACT WAZALENDO": "ACT", "TLP": "TLP",
}

PLATFORM_ALIASES = {
    "INSTAGRAM": "Instagram", "FACEBOOK": "Facebook", "TWITTER": "Twitter",
    "X": "Twitter", "YOUTUBE": "YouTube", "TIKTOK": "TikTok",
}

# The audience is called something different in every section. All of these
# mean "how many people follow this account".
AUDIENCE_WORDS = ("follower", "member", "subscriber", "like", "fan")
ACTIVITY_WORDS = ("post", "tweet", "video", "upload")


def clean_text(value):
    """A cell as a person meant it: no soft hyphens, no doubled spaces.

    Account names in this sheet carry invisible characters - one of them holds
    a U+00AD soft hyphen - which make two spellings of the same name compare
    unequal and print with a stray dash.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = "".join(ch for ch in text
                   if unicodedata.category(ch)[0] != "C" and ch != "­")
    return re.sub(r"\s+", " ", text).strip()


def to_number(value):
    """A count, from whatever the cell holds: '1,038', '449000', 'Nil', ''."""
    text = clean_text(value).replace(",", "").replace("'", "")
    if not text or text.lower() in ("nil", "none", "n/a", "na", "-"):
        return np.nan
    match = re.match(r"^([0-9]*\.?[0-9]+)\s*([kKmM]?)$", text)
    if not match:
        return np.nan
    number = float(match.group(1))
    suffix = match.group(2).lower()
    if suffix == "k":
        number *= 1_000
    elif suffix == "m":
        number *= 1_000_000
    return number


def canonical(text, aliases):
    key = clean_text(text).upper()
    return aliases.get(key, clean_text(text).upper() if text else "")


# --- read the sheet exactly as it was typed --------------------------------
if "CSV_URL" in globals():
    raw = pd.read_csv(CSV_URL, header=None, dtype=object)
else:
    raw = pd.read_csv(
        "https://docs.google.com/spreadsheets/export?id=%s&exportFormat=csv"
        % SHEET_ID, header=None, dtype=object)

raw = raw.map(clean_text) if hasattr(raw, "map") else raw.applymap(clean_text)


def is_header_row(row):
    """The row that names the columns - it is the one that says SN."""
    return clean_text(row.iloc[1]).upper().startswith("SN")


def section_starts(frame):
    """Rows carrying a bare platform name and nothing else.

    Not "the first column": whoever typed this sheet put Instagram in column
    A and FACEBOOK, Twitter and Youtube in column B. What the four rows do
    have in common is that the platform name is the only thing on the row, so
    that is what is tested - one non-empty cell, no digits in it, and not the
    SN that starts a header row.
    """
    marks = []
    for i in frame.index:
        filled = [v for v in (frame.at[i, c] for c in frame.columns) if v]
        if len(filled) != 1:
            continue
        text = filled[0]
        if any(ch.isdigit() for ch in text):
            continue
        if text.upper().startswith("SN"):
            continue
        marks.append((i, text))
    return marks


records = []
skipped = 0
marks = section_starts(raw)
if not marks:
    raise ValueError(
        "No platform sections found. This module expects a bare platform "
        "name alone on a row (Instagram, Facebook, ...) above each block.")

for order, (start, name) in enumerate(marks):
    end = marks[order + 1][0] if order + 1 < len(marks) else raw.index[-1] + 1
    platform = PLATFORM_ALIASES.get(clean_text(name).upper(), clean_text(name))

    block = raw.loc[start + 1:end - 1]
    heads = [i for i in block.index if is_header_row(block.loc[i])]
    if not heads:
        continue
    head_at = heads[0]
    header = [clean_text(v) for v in block.loc[head_at]]

    # Which column holds the audience, and which the activity? Ask the header
    # rather than assuming a position, so a section with an extra column or a
    # renamed one still lands in the right place.
    audience_col = activity_col = None
    for pos, label in enumerate(header):
        low = label.lower()
        if audience_col is None and any(w in low for w in AUDIENCE_WORDS):
            audience_col = pos
        if activity_col is None and any(w in low for w in ACTIVITY_WORDS):
            activity_col = pos
    audience_name = header[audience_col] if audience_col is not None else "Followers"

    party = ""
    for i in block.loc[head_at + 1:].index:
        row = block.loc[i]
        if is_header_row(row):                       # a repeated header
            continue
        # The party is normally in column C, with the serial number in B. In
        # one place - the ACT block on Facebook - it was typed into B instead.
        # Column B otherwise only ever holds a number, so text there is a
        # party label that landed one cell to the left.
        label = clean_text(row.iloc[2])
        if not label:
            maybe = clean_text(row.iloc[1])
            if maybe and not maybe.replace(".", "").isdigit():
                label = maybe
        if label:
            party = canonical(label, PARTY_ALIASES)  # carried down the rows

        account = clean_text(row.iloc[3])
        # A bare number in the name column is a stray value, not an account.
        if (not account or account.lower() == "nil"
                or account.replace(",", "").replace(".", "").isdigit()):
            skipped += 1
            continue
        records.append({
            "Platform": platform,
            "Party": party or "UNSTATED",
            "Account": account,
            "Followers": (to_number(row.iloc[audience_col])
                          if audience_col is not None else np.nan),
            "Posts": (to_number(row.iloc[activity_col])
                      if activity_col is not None else np.nan),
            "Audience measure": audience_name,
        })

data = pd.DataFrame.from_records(records)
if data.empty:
    raise ValueError("No account rows were found in the sheet.")

PLATFORM_ORDER = [p for p in ("Instagram", "Facebook", "Twitter", "YouTube",
                              "TikTok")
                  if p in set(data["Platform"])]
PLATFORM_ORDER += [p for p in dict.fromkeys(data["Platform"])
                   if p not in PLATFORM_ORDER]
PARTY_ORDER = (data.groupby("Party")["Followers"].sum()
               .sort_values(ascending=False).index.tolist())

print("Read %d accounts: %d parties across %d platforms."
      % (len(data), data["Party"].nunique(), data["Platform"].nunique()))
print("Platforms: %s" % ", ".join(PLATFORM_ORDER))
print("Parties:   %s" % ", ".join(PARTY_ORDER))
if skipped:
    print("Skipped %d rows with no account name." % skipped)

# --- the slice the cell asked for ------------------------------------------
sel = data
if PARTY:
    want = canonical(PARTY, PARTY_ALIASES)
    sel = sel[sel["Party"] == want]
    if sel.empty:
        raise ValueError("No accounts for party %r. The sheet has: %s"
                         % (PARTY, ", ".join(PARTY_ORDER)))
if PLATFORM:
    want = PLATFORM_ALIASES.get(clean_text(PLATFORM).upper(),
                                clean_text(PLATFORM))
    sel = sel[sel["Platform"] == want]
    if sel.empty:
        raise ValueError("No accounts for platform %r. The sheet has: %s"
                         % (PLATFORM, ", ".join(PLATFORM_ORDER)))

SCOPE = " / ".join([x for x in (PARTY and canonical(PARTY, PARTY_ALIASES),
                                PLATFORM and PLATFORM_ALIASES.get(
                                    clean_text(PLATFORM).upper(),
                                    clean_text(PLATFORM))) if x]) or "All parties"
AUDIENCE = (sel["Audience measure"].mode().iloc[0]
            if len(sel["Audience measure"].mode()) else "Followers")
AUDIENCE = re.sub(r"^number\s+of\s+", "", AUDIENCE, flags=re.I).strip().title()
print("")
print("Selected: %s - %d accounts." % (SCOPE, len(sel)))

charts = []


def save(fig, name):
    fig.savefig(name, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    charts.append(name)


THOUSANDS = plt.FuncFormatter(lambda v, _: "{:,.0f}".format(v))


def thousands(value):
    if value is None or pd.isna(value):
        return ""
    return "{:,.0f}".format(float(value))


CREDIT = "%s  \u00b7  %s" % (SOURCE, datetime.date.today().strftime("%d %B %Y"))

# ===========================================================================
#  1. Reach: who has the audience
# ===========================================================================
reach = sel.dropna(subset=["Followers"]).sort_values("Followers",
                                                     ascending=False)
shown = reach.head(TOP)
if len(shown):
    fig, ax = figure(11.0, max(3.6, 0.42 * len(shown) + 2.2))
    bars(shown["Account"].tolist(), shown["Followers"].tolist(), ax=ax,
         horizontal=True, fmt="{:,.0f}", sort=True, clean=False)
    ax.set_xlabel(AUDIENCE)
    ax.xaxis.set_major_formatter(THOUSANDS)
    total = float(reach["Followers"].sum())
    lead = float(shown["Followers"].iloc[0]) / total * 100.0 if total else 0
    finish(fig, title="%s: %s by account" % (SCOPE, AUDIENCE.lower()),
           subtitle="%d accounts carry %s between them. The largest holds "
                    "%.0f%% of that."
                    % (len(reach), thousands(total), lead),
           source=CREDIT)
    save(fig, "reach_by_account.png")

# ===========================================================================
#  2. Activity: who is posting
# ===========================================================================
activity = sel.dropna(subset=["Posts"]).sort_values("Posts", ascending=False)
if len(activity):
    shown = activity.head(TOP)
    fig, ax = figure(11.0, max(3.6, 0.42 * len(shown) + 2.2))
    bars(shown["Account"].tolist(), shown["Posts"].tolist(), ax=ax,
         horizontal=True, fmt="{:,.0f}", sort=True, color=palette()[1],
         clean=False)
    ax.set_xlabel("Posts")
    ax.xaxis.set_major_formatter(THOUSANDS)
    finish(fig, title="%s: posts by account" % SCOPE,
           subtitle="Reach and activity are different things - the order here "
                    "is not the order above.",
           source=CREDIT)
    save(fig, "activity_by_account.png")

# ===========================================================================
#  3. Reach against activity - the two measures on one pair of axes
# ===========================================================================
paired = sel.dropna(subset=["Followers", "Posts"])
both = paired[(paired["Followers"] > 0) & (paired["Posts"] > 0)]
# A log axis has no room for zero, and "posted nothing" is a real and common
# state in this sheet. Say how many were set aside rather than quietly
# dropping them.
silent = int((paired["Posts"] == 0).sum())
if len(both) >= 4:
    fig, ax = figure(10.6, 6.2)
    ax.scatter(both["Posts"], both["Followers"], s=70,
               color=palette()[0], edgecolor=SURFACE, linewidth=1.4, zorder=3)
    # Both measures span orders of magnitude, so a linear axis would pile
    # every small account into one corner.
    for name, axis, series in (("x", ax.xaxis, both["Posts"]),
                               ("y", ax.yaxis, both["Followers"])):
        if float(series.max()) / float(series.min()) < 20:
            continue
        (ax.set_xscale if name == "x" else ax.set_yscale)("log")
        # The default log locator labels decades only, which on a range of
        # 20 to 600 leaves a single number on the axis.
        axis.set_major_locator(
            LogLocator(base=10.0, subs=(1.0, 2.0, 5.0), numticks=12))
        axis.set_minor_formatter(NullFormatter())
        axis.set_major_formatter(THOUSANDS)
    top_few = both.nlargest(min(6, len(both)), "Followers")
    for _, r in top_few.iterrows():
        ax.annotate(r["Account"], (r["Posts"], r["Followers"]),
                    textcoords="offset points", xytext=(7, 5),
                    fontsize=9.5, color=INK_2,
                    annotation_clip=False)
    ax.margins(x=0.16, y=0.12)
    ax.set_xlabel("Posts")
    ax.set_ylabel(AUDIENCE)
    finish(fig, title="%s: audience against activity" % SCOPE,
           subtitle="Each point is one account. Posting more does not by "
                    "itself buy an audience - the accounts at the top are not "
                    "the accounts on the right.",
           note=("%d of the %d accounts here record no posts at all and "
                 "cannot be placed on a logarithmic axis." % (silent, len(sel))
                 if silent else None),
           source=CREDIT)
    save(fig, "reach_vs_activity.png")

# ===========================================================================
#  4. Parties compared, platform by platform
# ===========================================================================
totals = (data.pivot_table(index="Party", columns="Platform",
                           values="Followers", aggfunc="sum")
          .reindex(index=PARTY_ORDER, columns=PLATFORM_ORDER))
if totals.notna().any().any():
    # Bars cannot carry this. TLP's 124 followers and CHADEMA's 2.2 million
    # are five orders of magnitude apart, and on a linear axis half the
    # parties draw as nothing at all. A dot on a logarithmic axis encodes the
    # value by position rather than by length, so every party is legible and
    # nothing is exaggerated.
    fig, ax = figure(11.2, max(3.8, 0.62 * len(PARTY_ORDER) + 2.4))
    cols = colors(len(PLATFORM_ORDER))
    ypos = np.arange(len(PARTY_ORDER))[::-1]

    for y, party_name in zip(ypos, PARTY_ORDER):
        row = totals.loc[party_name].dropna()
        row = row[row > 0]
        if len(row) > 1:                      # a spine joining the platforms
            ax.plot([row.min(), row.max()], [y, y], color=GRID, lw=2.4,
                    zorder=1, solid_capstyle="round")
    for k, plat in enumerate(PLATFORM_ORDER):
        vals = totals[plat].reindex(PARTY_ORDER).to_numpy(dtype=float)
        keep = np.isfinite(vals) & (vals > 0)
        ax.scatter(vals[keep], ypos[keep], s=118, color=cols[k], label=plat,
                   edgecolor=SURFACE, linewidth=1.6, zorder=3)

    ax.set_yticks(ypos)
    ax.set_yticklabels(PARTY_ORDER)
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(
        LogLocator(base=10.0, subs=(1.0,), numticks=12))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.xaxis.set_major_formatter(THOUSANDS)
    # This chart crosses platforms, and each one counts its audience under
    # a different name. "Audience" is the only honest word for the total.
    ax.set_xlabel("Total audience (logarithmic)")
    ax.set_ylim(-0.7, len(PARTY_ORDER) - 0.3)
    _grid(ax, "x")

    grand = float(np.nansum(totals.to_numpy(dtype=float)))
    finish(fig, title="Total audience by party and platform",
           subtitle="Summed across every account a party runs on that "
                    "platform - %s in all. Each step along the axis is a "
                    "tenfold difference." % thousands(grand),
           note="Audience means followers on Instagram and Twitter, members "
                "on Facebook and subscribers on YouTube - the sheet counts "
                "each platform in its own terms.",
           legend=list(zip(PLATFORM_ORDER, cols)), source=CREDIT)
    save(fig, "party_by_platform.png")

# ===========================================================================
#  5. How many accounts each party runs
# ===========================================================================
counts_tab = (data.pivot_table(index="Party", columns="Platform",
                               values="Account", aggfunc="count")
              .reindex(index=PARTY_ORDER, columns=PLATFORM_ORDER)
              .fillna(0))
if counts_tab.to_numpy().sum():
    fig, ax = figure(9.4, max(3.4, 0.52 * len(PARTY_ORDER) + 2.4))
    heatmap(counts_tab, ax=ax, ramp="blue", fmt="{:.0f}", order=False,
            clean=False)   # CHADEMA and NCCR are acronyms, not headings
    finish(fig, title="Accounts run, by party and platform",
           subtitle="A count of separate accounts, not their size. Several "
                    "small accounts and one large one are very different "
                    "things.",
           source=CREDIT)
    save(fig, "accounts_grid.png")


# ===========================================================================
#  The report
# ===========================================================================
def esc(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


CSS = """
@page { size: A4 landscape; margin: 12mm 11mm 12mm 11mm; }
body { font-family: 'Nimbus Sans', Helvetica, Arial, sans-serif;
       color: #0f172a; font-size: 10.5pt; }
.band { height: 4px; margin-bottom: 10px; background: linear-gradient(to right,
        #096EFF 0%, #096EFF 58%, #10B981 58%, #10B981 82%,
        #f59e0b 82%, #f59e0b 100%); }
h1 { font-size: 17pt; margin: 0 0 2px 0; }
h2 { font-size: 12.5pt; margin: 20px 0 6px 0; color: #096EFF;
     page-break-after: avoid; }
.sub { color: #475569; margin: 0 0 12px 0; font-size: 10.5pt; }
table { border-collapse: collapse; width: 100%; font-size: 9.2pt;
        margin-bottom: 6px; }
th { background: #0f172a; color: #fff; text-align: left; font-weight: 600;
     padding: 6px 7px; font-size: 8.8pt; }
td { padding: 4.5px 7px; border-top: 1px solid #e2e8f0; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tr:nth-child(even) td { background: #f8fafc; }
tr { page-break-inside: avoid; }
.note { color: #475569; font-size: 9.4pt; margin: 8px 0 0 0; }
img { max-width: 100%; max-height: 168mm; display: block; margin: 10px auto;
      page-break-inside: avoid; }
.credit { color: #94a3b8; font-size: 8.6pt; margin-top: 14px; }
"""


def html_table(frame, numeric=()):
    head = "".join('<th class="num">%s</th>' % esc(c) if c in numeric
                   else "<th>%s</th>" % esc(c) for c in frame.columns)
    rows = []
    for _, r in frame.iterrows():
        cells = []
        for c in frame.columns:
            v = r[c]
            if c in numeric:
                cells.append('<td class="num">%s</td>' % thousands(v))
            else:
                cells.append("<td>%s</td>" % esc("" if pd.isna(v) else v))
        rows.append("<tr>%s</tr>" % "".join(cells))
    return ("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
            % (head, "".join(rows)))


party_summary = pd.DataFrame({
    "Party": PARTY_ORDER,
    "Accounts": [int((data["Party"] == p).sum()) for p in PARTY_ORDER],
    "Platforms": [int(data[data["Party"] == p]["Platform"].nunique())
                  for p in PARTY_ORDER],
    "Total audience": [data[data["Party"] == p]["Followers"].sum()
                       for p in PARTY_ORDER],
    "Largest account": [
        (data[data["Party"] == p].dropna(subset=["Followers"])
         .sort_values("Followers", ascending=False)["Account"].iloc[0]
         if data[data["Party"] == p]["Followers"].notna().any() else "")
        for p in PARTY_ORDER],
})

listing = sel.sort_values("Followers", ascending=False)[
    ["Platform", "Party", "Account", "Followers", "Posts"]]

body = ['<div class="band"></div>',
        "<h1>%s</h1>" % esc(TITLE),
        '<p class="sub">%s &middot; %d accounts &middot; %s</p>'
        % (esc(SCOPE), len(sel), esc(CREDIT.replace("&middot;", "-")))]

body.append("<h2>By party</h2>")
body.append(html_table(party_summary,
                       numeric=("Accounts", "Platforms", "Total audience")))
body.append('<p class="note">Audience is summed over every account a party '
            'runs. An account census counts presence, not people: the same '
            'person may follow several accounts, and a follower is not a '
            'voter.</p>')

body.append("<h2>Accounts in this selection</h2>")
body.append(html_table(listing.head(60), numeric=("Followers", "Posts")))
if len(listing) > 60:
    body.append('<p class="note">First 60 of %d rows; the full list is in '
                'Social_Media_Accounts.csv.</p>' % len(listing))

for name in charts:
    with open(name, "rb") as fh:
        body.append('<img src="data:image/png;base64,%s">'
                    % base64.b64encode(fh.read()).decode("ascii"))

body.append('<p class="credit">Generated by TSSFL Technology Stack '
            "&middot; www.tssfl.com</p>")

doc = ("<html><head><meta charset='utf-8'><title>%s</title><style>%s</style>"
       "</head><body>%s</body></html>" % (esc(TITLE), CSS, "".join(body)))
with open("Social_Media_Report.html", "w", encoding="utf-8") as fh:
    fh.write(doc)
HTML(string=doc).write_pdf("Social_Media_Report.pdf")

data.to_csv("Social_Media_Accounts.csv", index=False)
party_summary.to_csv("Party_Summary.csv", index=False)

print("")
print("Wrote Social_Media_Report.html / .pdf - %d charts, 2 tables."
      % len(charts))
print("Wrote Social_Media_Accounts.csv - %d rows, every platform and party."
      % len(data))
print("Wrote Party_Summary.csv - %d parties." % len(party_summary))
