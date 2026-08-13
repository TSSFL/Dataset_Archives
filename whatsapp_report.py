# -*- coding: utf-8 -*-
"""WhatsApp conversation analysis - logic only. The export lives on Dropbox.

Run it from a SageMathCell by naming your export first, then loading this:

    CHAT_URL = "https://www.dropbox.com/s/..../WhatsApp Chat with X.txt?dl=1"

    load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/whatsapp_report.py")

Optional switches, all with sensible defaults:

    ANONYMISE = True      names become "Member 1", "Member 2", ...
    TOP_N     = 10        how many members each ranking shows
    TITLE     = "..."     report heading; defaults to the file name

**No data URL appears in this file, and none ever should.** Point CHAT_URL at
any WhatsApp export and everything below works unchanged - that is the whole
idea. Android and iPhone exports are both handled, and the date format is
detected rather than assumed.

ANONYMISE DEFAULTS TO TRUE, ON PURPOSE
--------------------------------------
A WhatsApp export carries the real names and phone numbers of everyone in the
group, none of whom agreed to appear in a published report. With it on, the
analysis is identical and the charts name nobody. Set ANONYMISE = False only
for a group whose members are content to be named.

Outputs
    WhatsApp_Report.html / .pdf   the report, TSSFL branded
    WhatsApp_Charts.png           the figures
    WhatsApp_WordCloud.png        the words, by weight
    WhatsApp_Members.csv          per-member totals
    WhatsApp_Daily.csv            messages per day
"""

_missing = [n for n in ("CHAT_URL",) if n not in globals()]
if _missing:
    raise NameError(
        "whatsapp_report.py does not carry data locations - define them in "
        "the cell before loading it.\nMissing: " + ", ".join(_missing) + "\n\n"
        '    CHAT_URL = "https://www.dropbox.com/s/.../WhatsApp Chat.txt?dl=1"\n'
    )

import base64
import datetime
import os
import re
import textwrap
import urllib.request
from collections import Counter

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ANONYMISE = globals().get("ANONYMISE", True)
TOP_N = int(globals().get("TOP_N", 10))
TITLE = globals().get("TITLE", "")

# --- TSSFL brand --------------------------------------------------------
BLUE, EMERALD, AMBER = "#096EFF", "#10B981", "#f59e0b"
ROSE, VIOLET, TEAL = "#e11d48", "#7c3aed", "#0891b2"
INK, INK_2, MUTED, GRID = "#0f172a", "#475569", "#94a3b8", "#e2e8f0"
BRAND = [BLUE, AMBER, EMERALD, ROSE, VIOLET, TEAL]

# =======================================================================
#  Parsing
# =======================================================================
# Android:  12/01/2022, 08:24 - Author: message
# iPhone:   [12/01/2022, 08:24:11] Author: message
ANDROID = re.compile(
    r'^(\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}),?\s+'
    r'(\d{1,2}:\d{2}(?::\d{2})?)\s*([APap][Mm])?\s*-\s*(.*)$')
IPHONE = re.compile(
    r'^\[(\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}),?\s+'
    r'(\d{1,2}:\d{2}(?::\d{2})?)\s*([APap][Mm])?\]\s*(.*)$')

URLPATTERN = r'(https?://\S+)'

# Wordings WhatsApp uses for attachments and removals, on both platforms.
MEDIA_MARKERS = ('<media omitted>', 'image omitted', 'video omitted',
                 'sticker omitted', 'audio omitted', 'gif omitted',
                 'document omitted', 'contact card omitted')
DELETED_MARKERS = ('you deleted this message', 'this message was deleted',
                   'message deleted')


def parse_chat(path):
    """Return a tidy frame of one row per message, from either platform."""
    rows, buffer, current = [], [], None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n").replace(" ", " ").replace("\xa0", " ")
            line = line.lstrip("‎‏")          # WhatsApp marks
            m = IPHONE.match(line) or ANDROID.match(line)
            if m:
                if current:
                    current[-1] = " ".join([current[-1]] + buffer).strip()
                    rows.append(current)
                buffer = []
                date, time, meridiem, body = m.groups()
                if meridiem:
                    time = f"{time} {meridiem.upper()}"
                # "Author: text" - but a system notice has no author, and a
                # colon inside the text must not be mistaken for one.
                author, _, text = body.partition(": ")
                if not _ or len(author) > 60 or "\n" in author:
                    author, text = None, body
                current = [date, time, author, text]
            elif current:
                buffer.append(line.strip())
    if current:
        current[-1] = " ".join([current[-1]] + buffer).strip()
        rows.append(current)

    df = pd.DataFrame(rows, columns=["Date", "Time", "Author", "Message"])
    df = df[df["Author"].notna()].copy()         # drop system notices

    # Let pandas decide the order rather than assuming a locale. If the first
    # field ever exceeds 12 it cannot be a month, which settles day-first.
    first = pd.to_numeric(df["Date"].str.split(r"[/.-]").str[0],
                          errors="coerce")
    dayfirst = bool((first > 12).any()) and not bool(
        (pd.to_numeric(df["Date"].str.split(r"[/.-]").str[0],
                       errors="coerce") > 31).any())
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=dayfirst,
                                format="mixed", errors="coerce")
    df = df[df["Date"].notna()].copy()

    stamp = pd.to_datetime(df["Time"].str.strip(), format="mixed",
                           errors="coerce")
    df["Hour"] = stamp.dt.hour
    df["Weekday"] = df["Date"].dt.day_name()
    df["Message"] = df["Message"].fillna("").str.strip()

    low = df["Message"].str.lower()
    df["IsMedia"] = low.str.contains("|".join(re.escape(m)
                                              for m in MEDIA_MARKERS))
    df["IsDeleted"] = low.str.contains("|".join(re.escape(m)
                                               for m in DELETED_MARKERS))
    df["Links"] = df["Message"].apply(lambda s: len(re.findall(URLPATTERN, s)))
    df["IsText"] = ~df["IsMedia"] & ~df["IsDeleted"]
    df["Words"] = np.where(df["IsText"],
                           df["Message"].str.split().str.len(), 0)
    df["Letters"] = np.where(df["IsText"], df["Message"].str.len(), 0)
    return df.reset_index(drop=True)


def emoji_name(ch):
    """A readable label for an emoji.

    Neither Nimbus Sans nor DejaVu carries emoji glyphs, and SageCell has no
    emoji font installed, so drawing the character itself produces an empty
    box and a "Glyph missing from font" warning per emoji. The name renders
    everywhere and says more than the picture does at chart size.
    """
    try:
        import emoji as _emoji
        name = _emoji.demojize(ch, delimiters=("", ""))
    except Exception:
        name = ""
    if not name or name == ch:
        return "emoji"
    name = name.replace("_", " ").strip()
    name = re.sub(r"\s*(light|medium|dark|medium light|medium dark)?"
                  r"\s*skin tone$", "", name).strip()
    return name[:1].upper() + name[1:]


def count_emojis(series):
    """Emoji tally, counting sequences as one.

    The original analysis was commented out because it used
    emoji.UNICODE_EMOJI, which the package renamed to EMOJI_DATA.

    emoji_list() is used rather than testing character by character:
    a thumbs-up with a skin tone is U+1F44D followed by U+1F3FE, and a
    per-character count reports the modifier as an emoji in its own right.
    This export contains 48 such modifiers and 40 variation selectors.
    """
    try:
        import emoji as _emoji
    except ImportError:
        return Counter()
    tally = Counter()
    if hasattr(_emoji, "emoji_list"):
        for text in series:
            for found in _emoji.emoji_list(str(text)):
                tally[found["emoji"]] += 1
        return tally
    table = getattr(_emoji, "EMOJI_DATA", None) or getattr(
        _emoji, "UNICODE_EMOJI", {})
    for text in series:
        for ch in str(text):
            if ch in table:
                tally[ch] += 1
    return tally


# =======================================================================
#  Load
# =======================================================================
local = "whatsapp_chat.txt"
urllib.request.urlretrieve(CHAT_URL, local)
df = parse_chat(local)

if df.empty:
    raise ValueError(
        "No messages were parsed. The file does not look like a WhatsApp "
        "export - open it and check the first line begins with a date.")

group = TITLE or os.path.basename(
    urllib.request.url2pathname(CHAT_URL.split("?")[0])).replace(".txt", "")

if ANONYMISE:
    names = {a: f"Member {i}" for i, a in
             enumerate(df["Author"].value_counts().index, start=1)}
    df["Author"] = df["Author"].map(names)

# --- headline figures ---------------------------------------------------
members = df["Author"].nunique()
total = len(df)
media = int(df["IsMedia"].sum())
deleted = int(df["IsDeleted"].sum())
links = int(df["Links"].sum())
words = int(df["Words"].sum())
letters = int(df["Letters"].sum())
span = (df["Date"].max() - df["Date"].min()).days + 1
emojis = count_emojis(df.loc[df["IsText"], "Message"])

print(f"{group}")
print(f"  {total:,} messages from {members} members over {span:,} days "
      f"({df['Date'].min():%d %b %Y} to {df['Date'].max():%d %b %Y})")
print(f"  {words:,} words, {letters:,} letters, {media:,} attachments, "
      f"{links:,} links, {deleted:,} deleted, {sum(emojis.values()):,} emojis")
print(f"  names {'hidden' if ANONYMISE else 'shown'}")

per_member = (df.groupby("Author")
                .agg(Messages=("Message", "size"),
                     Words=("Words", "sum"),
                     Letters=("Letters", "sum"),
                     Attachments=("IsMedia", "sum"),
                     Links=("Links", "sum"))
                .sort_values("Messages", ascending=False))
per_member["Words per message"] = (
    per_member["Words"] / per_member["Messages"]).round(1)
per_member["Share of messages %"] = (
    100.0 * per_member["Messages"] / total).round(1)

daily = (df.groupby(df["Date"].dt.date)
           .size().rename("Messages").reset_index())
daily.columns = ["Date", "Messages"]

per_member.to_csv("WhatsApp_Members.csv")
daily.to_csv("WhatsApp_Daily.csv", index=False)

# =======================================================================
#  Charts
# =======================================================================
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Nimbus Sans", "Helvetica", "DejaVu Sans"],
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": GRID, "text.color": INK, "axes.labelcolor": INK_2,
    "xtick.labelcolor": INK_2, "ytick.labelcolor": INK_2,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlecolor": INK,
})


def dress(ax, axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(True, axis=axis, color=GRID, lw=1)
    ax.set_axisbelow(True)


fig, axes = plt.subplots(3, 2, figsize=(15, 15))
ax = axes[0][0]
ax.fill_between(daily["Date"], daily["Messages"], color=BLUE, alpha=0.22)
ax.plot(daily["Date"], daily["Messages"], color=BLUE, lw=1.6)
peak = daily.loc[daily["Messages"].idxmax()]
ax.annotate(f"busiest day\n{peak['Messages']:,} messages\n"
            f"{pd.to_datetime(peak['Date']):%d %b %Y}",
            xy=(peak["Date"], peak["Messages"]), xytext=(-12, -46),
            textcoords="offset points", fontsize=10, color=INK_2,
            ha="right", arrowprops=dict(arrowstyle="-", color=MUTED))
ax.set_ylabel("Messages")
ax.set_title("Conversation over time")
# Full ISO dates at every tick ran into each other. Let matplotlib choose
# how many ticks the axis can hold, label them "15 Jan" rather than
# "2022-01-15", and rotate so they never collide however long the chat is.
ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=9))
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(
    ax.xaxis.get_major_locator()))
for label in ax.get_xticklabels():
    label.set_rotation(45)
    label.set_horizontalalignment("right")
ax.set_xlim(daily["Date"].min(), daily["Date"].max())
dress(ax)

ax = axes[0][1]
top = per_member.head(TOP_N).iloc[::-1]
bars = ax.barh(range(len(top)), top["Messages"], 0.62, color=BLUE)
ax.bar_label(bars, fmt="%d", padding=4, fontsize=10, color=INK_2)
ax.set_yticks(range(len(top)))
ax.set_yticklabels(top.index, fontsize=10)
ax.set_xlabel("Messages sent")
ax.set_title(f"The {len(top)} most active members")
ax.margins(x=0.18)   # room for the longest bar's value label
dress(ax, "x")

ax = axes[1][0]
by_hour = df.groupby("Hour").size().reindex(range(24), fill_value=0)
cols = [AMBER if h == by_hour.idxmax() else BLUE for h in by_hour.index]
ax.bar(by_hour.index, by_hour.values, 0.74, color=cols)
ax.annotate(f"peak hour: {by_hour.idxmax():02d}:00",
            xy=(by_hour.idxmax(), by_hour.max()), xytext=(0, 8),
            textcoords="offset points", ha="center", fontsize=10, color=AMBER,
            fontweight="bold")
ax.set_xticks(range(0, 24, 2))
ax.set_xlabel("Hour of day")
ax.set_ylabel("Messages")
ax.set_title("When the group talks")
ax.margins(y=0.16)
dress(ax)

ax = axes[1][1]
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
         "Saturday", "Sunday"]
by_day = df.groupby("Weekday").size().reindex(order, fill_value=0)
cols = [AMBER if d in ("Saturday", "Sunday") else BLUE for d in order]
bars = ax.bar(range(7), by_day.values, 0.66, color=cols)
ax.bar_label(bars, fmt="%d", padding=3, fontsize=10, color=INK_2)
ax.set_xticks(range(7))
ax.set_xticklabels([d[:3] for d in order])
ax.set_ylabel("Messages")
ax.set_title("Weekdays against weekends")
ax.margins(y=0.16)
dress(ax)

ax = axes[2][0]
parts = {"Text": int(df["IsText"].sum()) - int((df["Links"] > 0).sum()),
         "With a link": int((df["Links"] > 0).sum()),
         "Attachments": media, "Deleted": deleted}
parts = {k: v for k, v in parts.items() if v > 0}
wedges, _ = ax.pie(list(parts.values()), colors=BRAND[:len(parts)],
                   startangle=90, counterclock=False,
                   wedgeprops=dict(width=0.44, edgecolor="white",
                                   linewidth=2.5))
for w, (label, value) in zip(wedges, parts.items()):
    angle = np.deg2rad((w.theta1 + w.theta2) / 2)
    share = 100.0 * value / total
    if share >= 4:
        ax.text(0.78 * np.cos(angle), 0.78 * np.sin(angle),
                f"{share:.0f}%", ha="center", va="center", color="white",
                fontweight="bold", fontsize=11)
ax.text(0, 0.06, f"{total:,}", ha="center", va="center", fontsize=21,
        fontweight="bold", color=INK)
ax.text(0, -0.13, "messages", ha="center", va="center", fontsize=10.5,
        color=MUTED)
ax.set(aspect="equal")
ax.set_title("What gets sent")
ax.legend(wedges, [f"{k}  ({v:,})" for k, v in parts.items()],
          loc="upper center", bbox_to_anchor=(0.5, 0.04), ncol=2,
          frameon=False, fontsize=10)

ax = axes[2][1]
if emojis:
    top_e = emojis.most_common(10)[::-1]
    bars = ax.barh(range(len(top_e)), [c for _, c in top_e], 0.62,
                   color=AMBER)
    ax.bar_label(bars, fmt="%d", padding=4, fontsize=10, color=INK_2)
    ax.set_yticks(range(len(top_e)))
    ax.set_yticklabels(["\n".join(textwrap.wrap(emoji_name(e), 22))
                        for e, _ in top_e], fontsize=9.5)
    ax.set_xlabel("Times used")
    ax.set_title(f"Most used emojis  ({sum(emojis.values()):,} in total)")
    ax.margins(x=0.14)
    dress(ax, "x")
else:
    ax.text(0.5, 0.5, "no emojis found", ha="center", va="center",
            color=MUTED, transform=ax.transAxes)
    ax.set_axis_off()

fig.suptitle(group, fontsize=19, fontweight="bold", color=INK, y=0.997)
fig.text(0.5, 0.005, "Produced with the TSSFL Technology Stack  "
         "www.tssfl.com", ha="center", fontsize=10, color=MUTED)
fig.tight_layout(rect=(0, 0.014, 1, 0.984))
fig.savefig("WhatsApp_Charts.png", dpi=130, facecolor="white")
plt.show()
plt.close(fig)

# --- word cloud ---------------------------------------------------------
cloud_uri = ""
try:
    from wordcloud import WordCloud, STOPWORDS
    text = " ".join(df.loc[df["IsText"], "Message"])
    text = re.sub(URLPATTERN, " ", text)
    stop = set(STOPWORDS) | {
        "media", "omitted", "https", "http", "www", "com", "ok", "okay",
        "yes", "no", "will", "one", "us", "na", "ya", "kwa", "ni", "la",
        "wa", "za", "hii", "sasa", "tu", "pia", "kama", "au", "ila", "ndio",
        "sana", "asante", "karibu", "nini", "vizuri", "message", "deleted"}
    if text.strip():
        wc = WordCloud(width=1500, height=760, background_color="white",
                       stopwords=stop, colormap="viridis",
                       collocations=False, max_words=170).generate(text)
        fig, ax = plt.subplots(figsize=(13, 6.6))
        ax.imshow(wc, interpolation="bilinear")
        ax.set_axis_off()
        ax.set_title(f"What the group talks about  -  {group}",
                     fontsize=15, pad=14)
        fig.text(0.5, 0.015, "Produced with the TSSFL Technology Stack  "
                 "www.tssfl.com", ha="center", fontsize=9.5, color=MUTED)
        fig.tight_layout(rect=(0, 0.03, 1, 1))
        fig.savefig("WhatsApp_WordCloud.png", dpi=130, facecolor="white")
        plt.show()
        plt.close(fig)
except ImportError:
    print("  wordcloud is not installed - skipping the word cloud")

# =======================================================================
#  Report
# =======================================================================
def embed(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode()


busiest_day = daily.loc[daily["Messages"].idxmax()]
quiet = int((daily["Messages"] == 0).sum())
top_row = per_member.iloc[0]

stats = [
    ("Messages", f"{total:,}"),
    ("Members", f"{members:,}"),
    ("Days covered", f"{span:,}"),
    ("Messages per day", f"{total / span:,.1f}"),
    ("Words", f"{words:,}"),
    ("Letters", f"{letters:,}"),
    ("Attachments", f"{media:,}"),
    ("Links shared", f"{links:,}"),
    ("Deleted", f"{deleted:,}"),
    ("Emojis", f"{sum(emojis.values()):,}"),
]

rows_html = "".join(
    f"<tr><td class='rank'>{i}</td><td class='who'>{name}</td>"
    f"<td>{r.Messages:,}</td><td>{r['Share of messages %']:.1f}%</td>"
    f"<td>{r.Words:,}</td><td>{r['Words per message']:.1f}</td>"
    f"<td>{int(r.Attachments):,}</td><td>{int(r.Links):,}</td></tr>"
    for i, (name, r) in enumerate(per_member.head(TOP_N).iterrows(), 1))

stat_html = "".join(
    f"<div class='stat'><div class='v'>{v}</div><div class='k'>{k}</div></div>"
    for k, v in stats)

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{group}</title><style>
@page {{ size: A4; margin: 16mm 14mm; }}
body {{ font-family: 'Nimbus Sans', Helvetica, Arial, sans-serif;
       color: {INK}; margin: 0; }}
.band {{ height: 5px; background: linear-gradient(to right,
        {BLUE} 0%, {BLUE} 58%, {EMERALD} 58%, {EMERALD} 82%,
        {AMBER} 82%, {AMBER} 100%); margin-bottom: 18px; }}
h1 {{ font-size: 23px; margin: 0 0 4px 0; }}
p.sub {{ font-size: 13px; color: {INK_2}; margin: 0 0 18px 0; }}
.stats {{ display: flex; flex-wrap: wrap; gap: 9px; margin-bottom: 20px; }}
.stat {{ flex: 1 1 17%; background: #f8fafc; border-radius: 9px;
        padding: 11px 13px; }}
.stat .v {{ font-size: 20px; font-weight: 700; color: {BLUE}; }}
.stat .k {{ font-size: 11px; color: {MUTED}; margin-top: 2px; }}
h2 {{ font-size: 16px; color: {BLUE}; margin: 22px 0 9px 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: 12.5px; }}
thead th {{ background: {BLUE}; color: #fff; text-align: right;
           padding: 8px 10px; font-weight: 600; }}
thead th:nth-child(-n+2) {{ text-align: left; }}
tbody td {{ padding: 6px 10px; text-align: right;
           font-variant-numeric: tabular-nums;
           border-bottom: 1px solid {GRID}; }}
tbody td.rank, tbody td.who {{ text-align: left; }}
tbody td.rank {{ color: {MUTED}; }}
tbody tr:nth-child(even) {{ background: #f8fafc; }}
img {{ width: 100%; margin-top: 6px; }}
p.foot {{ font-size: 10.5px; color: {MUTED}; margin-top: 16px; }}
p.emoji {{ font-size: 21px; margin: 0 0 6px 0; }}
p.emoji span {{ margin-right: 20px; }}
p.emoji b {{ font-size: 13px; color: {INK_2}; }}
</style></head><body>
<div class="band"></div>
<h1>{group}</h1>
<p class="sub">{total:,} messages from {members} members between
{df['Date'].min():%d %B %Y} and {df['Date'].max():%d %B %Y}
&mdash; {span:,} days, averaging {total / span:.1f} messages a day.
The busiest day was {pd.to_datetime(busiest_day['Date']):%d %B %Y} with
{busiest_day['Messages']:,}. {'Members are anonymised.' if ANONYMISE
 else 'Members are named.'}</p>
<div class="stats">{stat_html}</div>
<h2>Most used emojis</h2>
<p class="emoji">{"".join(f"<span>{e} <b>{c}</b></span>" for e, c in emojis.most_common(8))}</p>
<h2>The {TOP_N} most active members</h2>
<table><thead><tr><th>#</th><th>Member</th><th>Messages</th><th>Share</th>
<th>Words</th><th>Words each</th><th>Attachments</th><th>Links</th>
</tr></thead><tbody>{rows_html}</tbody></table>
<div style="page-break-before: always;"></div>
<h2>At a glance</h2>
<img src="{embed('WhatsApp_Charts.png')}" alt="Summary charts"/>
{'<div style="page-break-before: always;"></div><h2>What the group talks about</h2><img src="' + embed('WhatsApp_WordCloud.png') + '" alt="Word cloud"/>' if os.path.exists('WhatsApp_WordCloud.png') else ''}
<p class="foot">Generated {datetime.datetime.now():%d %B %Y at %H:%M}
&middot; Produced with the TSSFL Technology Stack &middot; www.tssfl.com</p>
</body></html>"""

with open("WhatsApp_Report.html", "w") as fh:
    fh.write(html)

from weasyprint import HTML
HTML(string=html).write_pdf("WhatsApp_Report.pdf")

print()
print("WhatsApp_Report.html   WhatsApp_Report.pdf")
print("WhatsApp_Charts.png    WhatsApp_WordCloud.png")
print("WhatsApp_Members.csv   WhatsApp_Daily.csv")
