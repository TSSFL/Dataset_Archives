# -*- coding: utf-8 -*-
"""DUCE registered students - enrolment table by programme, year and sex.

Rebuilt from the original sri_report.py. Same source, same figures, same two
outputs (an HTML file and a landscape PDF); a cleaner table and a silent run.

WARNINGS
--------
Six FutureWarnings, all the same cause:

    df2.loc['Column Totals'] = df2.sum(numeric_only=True, axis=0)

Assigning a new row with .loc on a frame that has non-numeric columns makes
pandas concatenate an all-NA row, which it now warns about on every call.
Totals here are computed into lists and the frame is built once, so there is
no row-by-row growth and nothing to warn about.

GROUPING
--------
The original sliced groups by position - iloc[0:5] for undergraduates,
iloc[6:8] for PGD, iloc[np.r_[5, 8:16]] for masters, and iloc[18] for a
sub-total. Those indices are only correct because of the exact order of a
hand-written `programmes` list, in which 'UDMA 151 | Master of Education in
Curriculum Studies' happens to sort sixth. Add a programme, rename one, or
let the registry return them in another order and the sub-totals silently
describe the wrong rows. Groups are now derived from the programme code:
UDD -> Bachelor, UDP -> Postgraduate Diploma, UDMA -> Masters.
"""
import re

import pandas as pd

# --- source -------------------------------------------------------------
URL = "https://www.dropbox.com/s/s2zl2ynxoaiuhbg/Registered_Students.csv?dl=1"
df = pd.read_csv(URL)

duplicates = int(df.duplicated(["REG #"], keep=False).sum())
df = df[["SEX", "PROGRAMME", "YEAR"]].dropna(subset=["PROGRAMME"])

YEARS = [1.0, 2.0, 3.0]
SEXES = ["M", "F"]

GROUPS = [("UDD", "Bachelor's degree programmes"),
          ("UDP", "Postgraduate diploma"),
          ("UDMA", "Masters programmes")]


def group_of(programme):
    code = str(programme).split("|")[0].strip().replace(" ", "")
    for prefix, _ in sorted(GROUPS, key=lambda g: -len(g[0])):
        if code.startswith(prefix):
            return prefix
    return "OTHER"


def pretty(programme):
    """'UDD03 | [DUCE]Bachelor of Science with  Education' -> code + title."""
    code, _, title = str(programme).partition("|")
    title = title.replace("[DUCE]", " ").replace("[Online]", " (online)")
    title = re.sub(r"\s+", " ", title).strip()
    return code.strip(), title


counts = (df.groupby(["PROGRAMME", "YEAR", "SEX"]).size()
            .unstack(["YEAR", "SEX"]).fillna(0).astype(int))

# --- assemble the rows once, rather than growing the frame --------------
rows = []          # (kind, code, title, cells...) ; kind drives the styling


def cells_for(frame):
    """Y1 M/F/T, Y2 M/F/T, Y3 M/F/T, grand total - for one row or a block."""
    out = []
    for y in YEARS:
        m = int(frame.get((y, "M"), 0).sum() if hasattr(frame.get((y, "M"), 0), "sum")
                else frame.get((y, "M"), 0))
        f = int(frame.get((y, "F"), 0).sum() if hasattr(frame.get((y, "F"), 0), "sum")
                else frame.get((y, "F"), 0))
        out += [m, f, m + f]
    out.append(out[2] + out[5] + out[8])
    return out


for prefix, label in GROUPS:
    members = [p for p in counts.index if group_of(p) == prefix]
    if not members:
        continue
    rows.append(("group", "", label, *([None] * 10)))
    for p in sorted(members):
        code, title = pretty(p)
        rows.append(("row", code, title, *cells_for(counts.loc[p])))
    rows.append(("subtotal", "", f"{label} - subtotal",
                 *cells_for(counts.loc[members])))

# The original reported a combined "PGD + Masters Sub-Total"; keep that
# figure available rather than leaving it as an addition for the reader.
postgrad = [p for p in counts.index if group_of(p) in ("UDP", "UDMA")]
if postgrad:
    rows.append(("subtotal", "", "All postgraduate (PGD + Masters)",
                 *cells_for(counts.loc[postgrad])))

rows.append(("total", "", "All programmes", *cells_for(counts)))

COLS = ["kind", "code", "programme",
        "y1m", "y1f", "y1t", "y2m", "y2f", "y2t", "y3m", "y3f", "y3t", "all"]
table_df = pd.DataFrame(rows, columns=COLS)

grand = int(table_df.loc[table_df["kind"] == "total", "all"].iloc[0])

# --- the table ----------------------------------------------------------
BLUE, INK, INK2 = "#096EFF", "#0f172a", "#475569"
MUTED, GRID, BAND = "#94a3b8", "#e2e8f0", "#f8fafc"

css = f"""
<style>
  @page {{ size: A4 landscape; margin: 10mm 12mm; }}
  body {{ font-family: 'Nimbus Sans', Helvetica, Arial, sans-serif;
         color: {INK}; margin: 0; }}
  /* Full width, and scrollable rather than squashed: inside a SageCell
     output pane the table would otherwise wrap every programme name onto
     three lines. min-width keeps the columns legible and the pane scrolls. */
  .wrap {{ width: 100%; overflow-x: auto; }}
  h1 {{ font-size: 24px; margin: 0 0 4px 0; }}
  p.sub {{ font-size: 14.5px; color: {INK2}; margin: 0 0 14px 0; }}
  table {{ border-collapse: collapse; width: 100%; min-width: 940px;
           font-size: 16px; }}
  thead th {{ background: {BLUE}; color: #fff; font-weight: 600;
              padding: 9px 12px; font-size: 14.5px; text-align: right; white-space: nowrap; }}
  thead th.left {{ text-align: left; }}
  thead tr.top th {{ border-bottom: 1px solid rgba(255,255,255,.35);
                     text-align: center; font-size: 12px; }}
  tbody td {{ padding: 7px 12px; text-align: right;
              font-variant-numeric: tabular-nums;
              border-bottom: 1px solid {GRID}; }}
  tbody td.left {{ text-align: left; }}
  tbody td .code {{ color: {MUTED}; font-size: 13.5px; white-space: nowrap; }}
  tbody tr.alt td {{ background: {BAND}; }}
  tbody tr.group td {{ background: #eaf2ff; color: {BLUE}; font-weight: 700;
                       font-size: 16px; letter-spacing: .02em;
                       padding-top: 7px; padding-bottom: 7px; }}
  tbody tr.subtotal td {{ font-weight: 700; background: #f1f5f9;
                          border-top: 1.5px solid {GRID}; }}
  tbody tr.total td {{ font-weight: 700; background: {BLUE}; color: #fff;
                       border-top: 2px solid {BLUE}; font-size: 17px; }}
  td.tot {{ font-weight: 600; }}
  td.zero {{ color: #cbd5e1; }}
  .bar {{ display: inline-block; height: 7px; background: {BLUE};
          opacity: .28; border-radius: 2px; margin-right: 6px;
          vertical-align: middle; }}
  p.foot {{ font-size: 12.5px; color: {MUTED}; margin-top: 12px; }}

  /* The PDF has a fixed sheet to fit, so it keeps the compact sizes. */
  @media print {{
    .wrap {{ overflow-x: visible; }}
    table {{ min-width: 0; }}
    h1 {{ font-size: 18px; }}
    p.sub {{ font-size: 11.5px; margin-bottom: 10px; }}
    table {{ font-size: 11px; }}
    thead th {{ padding: 6px 9px; font-size: 11px; }}
    tbody td {{ padding: 3.5px 9px; }}
    tbody td .code {{ font-size: 10.5px; }}
    tbody tr.group td {{ font-size: 11.5px;
                         padding-top: 6px; padding-bottom: 6px; }}
    tbody tr.total td {{ font-size: 12.5px; }}
    p.foot {{ font-size: 10px; margin-top: 9px; }}
  }}
</style>
"""

head = f"""
<div class="wrap">
<h1>DUCE registered students, by programme, year and sex</h1>
<p class="sub">{grand:,} registered students across
{len(counts.index):,} programmes. Every figure is a headcount;
subtotals are the sum of the programmes above them.</p>
<table>
  <colgroup>
    <col style="width:24%">
    <col span="9" style="width:7%">
    <col style="width:13%">
  </colgroup>
  <thead>
    <tr class="top">
      <th class="left" rowspan="2">Programme</th>
      <th colspan="3">Year 1</th><th colspan="3">Year 2</th>
      <th colspan="3">Year 3</th><th rowspan="2">All years</th>
    </tr>
    <tr>
      <th>M</th><th>F</th><th>Total</th>
      <th>M</th><th>F</th><th>Total</th>
      <th>M</th><th>F</th><th>Total</th>
    </tr>
  </thead>
  <tbody>
"""

body, alt = [], False
for _, r in table_df.iterrows():
    kind = r["kind"]
    if kind == "group":
        body.append(f'<tr class="group"><td class="left" colspan="11">'
                    f'{r["programme"]}</td></tr>')
        alt = False
        continue
    cls = {"row": "alt" if alt else "", "subtotal": "subtotal",
           "total": "total"}[kind]
    if kind == "row":
        alt = not alt
    # Code first: it is how the registry identifies a programme, and it
    # gives every row the same left edge to scan down.
    name = (f'<span class="code">{r["code"]}</span>&nbsp;&middot;&nbsp;'
            f'{r["programme"]}' if r["code"] else r["programme"])
    tds = [f'<td class="left">{name}</td>']
    for key in COLS[3:12]:
        v = int(r[key])
        z = " zero" if v == 0 else ""
        t = " tot" if key.endswith("t") else ""
        tds.append(f'<td class="{t.strip()}{z}">{v:,}</td>')
    # a quiet bar in the last column, so scale is visible without reading
    width = 0 if not grand else round(58.0 * int(r["all"]) / grand)
    bar = (f'<span class="bar" style="width:{width}px"></span>'
           if kind == "row" and width else "")
    tds.append(f'<td class="tot">{bar}{int(r["all"]):,}</td>')
    body.append(f'<tr class="{cls}">' + "".join(tds) + "</tr>")

foot = f"""
  </tbody>
</table>
<p class="foot">Source: DUCE student registry.
{duplicates} duplicate registration numbers found.
Generated by TSSFL Technology Stack &middot; www.tssfl.com</p>
</div>
"""

html = css + head + "\n".join(body) + foot

with open("Students_Registered.html", "w+") as file:
    file.write(html)

from weasyprint import HTML
HTML(string=html).write_pdf("DUCE_Registered_Students.pdf")

# --- the same table as data, not just as a picture ----------------------
export = table_df.drop(columns=["kind"]).copy()
export.insert(0, "Section", "")
section = ""
for i, r in table_df.iterrows():
    if r["kind"] == "group":
        section = r["programme"]
    export.loc[i, "Section"] = section
export = export[table_df["kind"] != "group"]      # headers are not data rows
export.columns = ["Section", "Code", "Programme",
                  "Y1 Male", "Y1 Female", "Y1 Total",
                  "Y2 Male", "Y2 Female", "Y2 Total",
                  "Y3 Male", "Y3 Female", "Y3 Total", "All years"]
export.to_csv("DUCE_Registered_Students.csv", index=False)

with pd.ExcelWriter("DUCE_Registered_Students.xlsx", engine="openpyxl") as xl:
    export.to_excel(xl, sheet_name="Enrolment", index=False)
    # the underlying counts too, so the workbook can be re-pivoted
    counts.to_excel(xl, sheet_name="By programme")

print("Students_Registered.html   DUCE_Registered_Students.pdf")
print("DUCE_Registered_Students.csv   DUCE_Registered_Students.xlsx")
print(f"{grand:,} students, {len(counts.index)} programmes, "
      f"{duplicates} duplicate registration numbers")

try:
    from IPython.display import HTML as _show, display
    display(_show(html))
except Exception:
    pass
