# -*- coding: utf-8 -*-
"""Teaching Practice assessment - logic only. The data lives in Google Drive.

Run it from a SageMathCell by naming your data first, then loading this file:

    SHEET_ID = "<the sheet id from its URL>"

    load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tp_assessment.py")

Any of these names will do, whichever suits where the data actually sits:

    SHEET_ID   a Google Sheets id; the sheet must be link-readable
    SHEET_NAME the tab, if not the first one           (optional)
    CSV_URL    a direct CSV link - Dropbox, KoBoToolbox, a web server
    XLSX_URL   a direct .xlsx link

**No data location appears in this file, and none ever should.** The code is
public on GitHub; the students' records are not.

WHAT IT PRODUCES
----------------
1. TP_Clean_Data.csv / .xlsx     one row per student, every visit on that row
2. TP_Student_Reports.html/.pdf  one assessment form per lesson observed,
                                 laid out exactly as the printed UDSM form,
                                 with the awarded rating circled
3. TP_Results.csv/.xlsx/.html/.pdf   the supervision results sheet, in the
                                 column order of the official workbook
4. TP_Data_Quality.csv           duplicate submissions, conflicting names and
                                 unrecognised ratings - what a clerk must look at

THE FORM IS THE SPECIFICATION
-----------------------------
Everything is driven by TEMPLATE below, which is the 2022 UDSM assessment form
transcribed: seven areas, twenty-five items, each scored 0-4, one hundred marks
in total. A collection form does not have to carry all twenty-five - MAPPING
binds whatever columns your data does have onto the template items, several
source columns to one item where the form merges them. Items with no data are
printed unassessed rather than silently scored zero, and the total is stated
out of what was actually assessed.

To use it with a different form, edit MAPPING and RUBRIC - or define either in
the cell before loading, and it wins. Nothing else needs to change.

RATINGS ARRIVE AS SENTENCES
---------------------------
The collection form records a phrase, not a number: "Somehow_clearly_formulated",
"Inaudible", "vg_intro_but_make_it_inspiring". Each phrase is worth two things -
a mark, through RUBRIC, and the supervisor's comment on that item, through
COMMENTS. Both go on the form, which is what the printed form asks for: a score
and a comment on every line.
"""

_needed = ("SHEET_ID", "CSV_URL", "XLSX_URL")
if not any(n in globals() for n in _needed):
    raise NameError(
        "tp_assessment.py does not carry data locations - define one in the "
        "cell before loading it.\n\n"
        '    SHEET_ID = "<the sheet id from its URL>"\n'
        "  or\n"
        '    CSV_URL  = "https://www.dropbox.com/scl/fi/.../tp.csv?dl=1"\n'
    )

import base64
import datetime
import io
import os
import re
import unicodedata
import urllib.parse
import urllib.request

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
from weasyprint import HTML

load("https://raw.githubusercontent.com/TSSFL/Dataset_Archives/main/tssfl_style.py")

use("tssfl")

# --- TSSFL brand --------------------------------------------------------
BLUE, EMERALD, AMBER = "#096EFF", "#10B981", "#f59e0b"
ROSE, VIOLET = "#e11d48", "#7c3aed"

# --- settings the cell may override -------------------------------------
TITLE = globals().get("TITLE", "Teaching Practice Assessment")
ACADEMIC_YEAR = globals().get("ACADEMIC_YEAR", "")
SUPERVISOR = globals().get("SUPERVISOR", "")
SUPERVISOR_CAMPUS = globals().get("SUPERVISOR_CAMPUS", "")
REGION_LABEL = globals().get("REGION_LABEL", "")
PASS_MARK = float(globals().get("PASS_MARK", 40.0))
MAX_PER_ITEM = 4                       # the printed form scores 0-4 per item
MAX_VISITS = 3                         # the results sheet has room for three

# Total = weighted mean of the components the workbook carries. IG (internal
# grade) and PTG (portfolio/teaching guide) are not collected by the lesson
# form, so by default only the visit average exists and the weights are
# renormalised over what is present - the total stays on a 0-100 scale
# instead of silently losing thirty marks to empty columns.
WEIGHTS = globals().get("WEIGHTS", {"AVR": 0.7, "IG": 0.1, "PTG": 0.2})

# UDSM classification. Edit in the cell if your programme differs.
GRADE_BANDS = globals().get("GRADE_BANDS", [
    (70.0, "A"), (60.0, "B+"), (50.0, "B"), (40.0, "C"), (35.0, "D"), (0.0, "E"),
])


# =======================================================================
#  The form, transcribed
# =======================================================================
TEMPLATE = [
    ("Lesson Plan and Scheme", 16, [
        ("1.i", "Clear statement of competencies"),
        ("1.ii", "Appropriate statements of teaching, learning and assessment "
                 "activities"),
        ("1.iii", "Appropriate teaching methods and relevant instructional "
                  "resources"),
        ("1.iv", "Concurrence of lesson plan with scheme of work"),
    ]),
    ("Teacher's Communication", 16, [
        ("2.i", "Motivating introduction of the lesson and clear linkage "
                "between previous and current lesson"),
        ("2.ii", "Language accuracy, adequate voice level, clarity of "
                 "explanation"),
        ("2.iii", "Questioning technique (relevance, clarity, frequency and "
                  "distribution, thought provoking, and answerability)"),
        ("2.iv", "Encourage students' participation and involvement in the "
                 "lesson"),
    ]),
    ("Mastery of Subject Matter", 16, [
        ("3.i", "Knowledge of subject content"),
        ("3.ii", "Presenting subject content using appropriate strategies"),
        ("3.iii", "Use of relevant examples and illustrations"),
        ("3.iv", "Sequencing and progression of activities associated with the "
                 "new skills"),
    ]),
    ("Use of Teaching/Learning Resources", 16, [
        ("4.i", "Safety and relevance/suitability of the resources to the topic "
                "and diverse needs of learners (clarity, attractiveness and "
                "readability)"),
        ("4.ii", "Creativity/use of environment/real objects/technology"),
        ("4.iii", "Correct time and use of teaching/learning resources"),
        ("4.iv", "Systematic use of chalkboard, legibility of letters, straight "
                 "lines and cleaning chalkboard after lesson"),
    ]),
    ("Classroom Organization and Management", 16, [
        ("5.i", "Sense of humor and awareness of class climate, addressing "
                "students by names"),
        ("5.ii", "Effective supervision of class work and mannerism"),
        ("5.iii", "Time management"),
        ("5.iv", "Accommodating diverse needs of learners (e.g. disabilities, "
                 "gender, ability and interest)"),
    ]),
    ("Assessment and Evaluation", 12, [
        ("6.i", "Evidence of whether learning has taken place as a result of "
                "instruction"),
        ("6.ii", "Relevant assignment given, marked and feedback given"),
        ("6.iii", "Evidence of meaningful self-evaluation"),
    ]),
    ("Ethical Conduct and Personality", 8, [
        ("7.i", "Composure, confidence and dressing/cleanliness"),
        ("7.ii", "Politeness and temperament"),
    ]),
]

ITEM_KEYS = [k for _, _, items in TEMPLATE for k, _ in items]
ITEM_TEXT = {k: t for _, _, items in TEMPLATE for k, t in items}
SECTION_OF = {k: name for name, _, items in TEMPLATE for k, _ in items}
SECTION_NAMES = [name for name, _, _ in TEMPLATE]


# Which collected column feeds which item on the printed form. A list, because
# the 2022 form merges pairs that the collection form asks separately: teaching
# methods and instructional resources are one line, and so are language
# accuracy and voice level. Where two columns feed one item their marks are
# averaged and both comments are kept.
MAPPING = globals().get("MAPPING", {
    "1.i": ["Clear statement of competences"],
    "1.ii": ["Adequate content to be covered in a lesson"],
    "1.iii": ["Appropriate teaching methods", "Relevant instructional resources"],
    "1.iv": ["Concurrence with scheme of work"],
    "2.i": ["Motivating introduction of lesson and clear linkage between "
            "previous and current lesson"],
    "2.ii": ["Language accuracy", "Adequate voice level"],
})


# The rubric. Every phrase the collection form can record, worth 0-4:
#   4 excellent   3 good/very good   2 fair, needs improvement
#   1 poor        0 absent or unusable
RUBRIC = globals().get("RUBRIC", {
    # Clear statement of competences
    "Poor statements": 1,
    "Statements may be improved": 2,
    "Somehow clearly formulated": 2,
    "Clear formulation": 3,
    # Adequate content to be covered in a lesson
    "Poor content quality": 1,
    "Insuficient content covered": 1,
    "Inadequate content covered": 2,
    "Too much content covered": 2,
    "Satisfactory content adequacy": 3,
    "Adequate content": 4,
    # Appropriate teaching methods
    "Improve teaching methods": 1,
    "Moderate teaching methods": 2,
    "Very good teaching methods": 3,
    "Excellent teaching methods": 4,
    # Relevant instructional resources
    "Very poor resources": 0,
    "Irrelevant resources": 1,
    "Poor instructional resources": 1,
    "Less relevant Resources": 2,
    "Relevant instructional resources": 4,
    # Concurrence with scheme of work
    "Lesson and scheme somehow concur": 2,
    "Lesson plan concur with scheme": 4,
    # Motivating introduction
    "Link previous and current lesson": 1,
    "G but make intro arousing": 2,
    "vg intro but make it inspiring": 3,
    "Excellent introduction": 4,
    # Language accuracy
    "Write accurately": 1,
    "Improve pronunciation": 2,
    "Improve language accuracy": 2,
    "Improve instruction clarity": 2,
    # Adequate voice level
    "Inaudible": 0,
    "Increase voice level": 2,
    "improve voice clarity": 2,
    "Audible and clear": 4,
    # generic grades, used by several columns
    "Excellent": 4,
    "Very Good": 3,
    "Good": 3,
    "Fair": 2,
    "Poor": 1,
})

# The abbreviations the field form records, written out for the comment column.
COMMENTS = globals().get("COMMENTS", {
    "G but make intro arousing": "Good introduction, but make it arousing",
    "vg intro but make it inspiring": "Very good introduction, but make it "
                                      "inspiring",
    "Insuficient content covered": "Insufficient content covered",
    "Link previous and current lesson": "Link the previous and current lesson",
    "improve voice clarity": "Improve voice clarity",
    "Less relevant Resources": "Less relevant resources",
})

# Subjects written more than one way. Two visits to one student have to land in
# the same "Subj 1" column, and "Maths" and "Mathematics" are the same subject.
SUBJECT_ALIASES = globals().get("SUBJECT_ALIASES", {
    "maths": "Mathematics", "math": "Mathematics",
    "kiswahili": "Kiswahili", "eng": "English",
    "english language": "English", "phy": "Physics", "chem": "Chemistry",
    "bio": "Biology", "geo": "Geography",
})


# =======================================================================
#  Small helpers
# =======================================================================
def _norm(text):
    """Lower-case, unpunctuated, single-spaced - for matching names."""
    text = unicodedata.normalize("NFKD", str(text))
    text = re.sub(r"^data[-_ ]+", "", text, flags=re.I)
    text = re.sub(r"[^0-9a-zA-Z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


RUBRIC_N = {_norm(k): v for k, v in RUBRIC.items()}
COMMENTS_N = {_norm(k): v for k, v in COMMENTS.items()}

# Phrases the rubric has never seen still have to be scored, and a sentence
# written by a supervisor carries its own grade in words. Longest key first, so
# "very good" is tested before "good".
KEYWORDS = [
    ("excellent", 4), ("very good", 3), ("very poor", 0), ("outstanding", 4),
    ("adequate", 4), ("audible and clear", 4), ("satisfactory", 3),
    ("good", 3), ("moderate", 2), ("somehow", 2), ("fair", 2),
    ("may be improved", 2), ("improve", 2), ("increase", 2), ("less ", 2),
    ("inadequate", 2), ("too much", 2), ("poor", 1), ("insuficient", 1),
    ("insufficient", 1), ("irrelevant", 1), ("write ", 1), ("link ", 1),
    ("inaudible", 0), ("not done", 0), ("none", 0), ("absent", 0),
]
KEYWORDS.sort(key=lambda kv: -len(kv[0]))

UNKNOWN_PHRASES = {}


def score_of(phrase):
    """The mark a recorded phrase is worth, 0-4, or None if it is blank."""
    if phrase is None or (isinstance(phrase, float) and np.isnan(phrase)):
        return None
    text = str(phrase).strip()
    if not text or text.lower() in ("nan", "na", "n/a", "-"):
        return None
    key = _norm(text)
    if key in RUBRIC_N:
        return RUBRIC_N[key]
    if re.fullmatch(r"[0-4](\.0)?", text):          # already a number
        return int(float(text))
    for word, mark in KEYWORDS:
        if word in key:
            UNKNOWN_PHRASES[text] = mark
            return mark
    UNKNOWN_PHRASES[text] = 2
    return 2                                        # neutral rather than zero


def comment_of(phrase):
    """The recorded phrase as a sentence a student can read."""
    if phrase is None or (isinstance(phrase, float) and np.isnan(phrase)):
        return ""
    text = str(phrase).strip()
    if not text or text.lower() in ("nan", "na", "n/a", "-"):
        return ""
    key = _norm(text)
    if key in COMMENTS_N:
        return COMMENTS_N[key]
    words = text.replace("_", " ").split()
    if not words:
        return ""
    out = " ".join(words)
    return out[0].upper() + out[1:]


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def find_col(frame, *candidates):
    """The first column matching any candidate, ignoring case and punctuation."""
    lookup = {_norm(c): c for c in frame.columns}
    for want in candidates:
        if _norm(want) in lookup:
            return lookup[_norm(want)]
    return None


def get(row, frame, *candidates):
    col = find_col(frame, *candidates)
    if col is None:
        return ""
    value = row.get(col, "")
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return str(value).strip()


def prettify(value):
    """Underscored form values as written English: B.Ed._Sc._ -> B.Ed. Sc."""
    text = str(value).replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def titled(value):
    """A field typed in by hand, capitalised: "english" -> "English".

    Only the first letter, and only when the value is all lower case -
    "B.Ed. Sc." and "Dar Es Salaam" are already right and must be left alone.
    """
    text = prettify(value)
    if not text or not text.islower():
        return text
    return " ".join(w[0].upper() + w[1:] if w else w for w in text.split(" "))


def short_item(key):
    """An item's name in a few words, for a sentence rather than a table."""
    text = ITEM_TEXT[key].split("(")[0].split(",")[0].strip()
    # Cut at a clause boundary rather than a word count, so nothing ends on a
    # dangling "and clear" or "relevant instructional".
    if len(text.split()) > 6 and " and " in text:
        text = text.split(" and ")[0]
    words = text.split()[:7]
    while words and words[-1].lower() in ("and", "or", "of", "the", "a", "to",
                                          "in", "for", "with", "between"):
        words.pop()
    text = " ".join(words)
    return text[0].lower() + text[1:] if text else key


def series(items):
    """a, b and c - so a list reads as a sentence, not a semicolon dump."""
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


# =======================================================================
#  1. Read the data
# =======================================================================
def _read():
    if "CSV_URL" in globals():
        return pd.read_csv(io.BytesIO(urllib.request.urlopen(CSV_URL).read())), \
            "CSV"
    if "XLSX_URL" in globals():
        return pd.read_excel(io.BytesIO(urllib.request.urlopen(XLSX_URL).read())), \
            "Excel workbook"
    query = {"tqx": "out:csv"}
    if "SHEET_NAME" in globals() and SHEET_NAME:
        query["sheet"] = SHEET_NAME
    url = ("https://docs.google.com/spreadsheets/d/" + SHEET_ID +
           "/gviz/tq?" + urllib.parse.urlencode(query))
    return pd.read_csv(io.BytesIO(urllib.request.urlopen(url).read())), \
        "Google Sheet"


raw, source_kind = _read()
n_raw = len(raw)

# Column names arrive as ODK/KoBo field paths: "data-Reg_No",
# "data-Leson_End_Time" (the typo is in the form, not here). Strip the prefix,
# unfold the underscores, and leave everything else alone.
raw.columns = [re.sub(r"^data[-_]", "", str(c)).replace("_", " ").strip()
               for c in raw.columns]

# --- data quality -------------------------------------------------------
issues = []

id_col = find_col(raw, "meta-instanceID", "instanceID", "_uuid", "uuid")
if id_col is not None:
    repeats = raw[raw.duplicated(id_col, keep=False)]
    for uid, group in repeats.groupby(id_col):
        issues.append({
            "Issue": "Duplicate submission",
            "Key": uid,
            "Detail": "%d identical submissions of the same form; kept the "
                      "first" % len(group)})
    raw = raw.drop_duplicates(id_col, keep="first").reset_index(drop=True)
else:
    raw = raw.drop_duplicates().reset_index(drop=True)

reg_col = find_col(raw, "Reg No", "Registration Number", "Reg. No", "RegNo")
if reg_col is None:
    raise KeyError("No registration-number column found. Columns read: "
                   + ", ".join(map(str, raw.columns)))
raw = raw.rename(columns={reg_col: "Registration Number"})

sur_col = find_col(raw, "Surname")
oth_col = find_col(raw, "Other Names", "Other Name(s)", "First Name")

# One registration number, two different names, is a clerical error worth
# seeing rather than a merge to do quietly.
if sur_col and oth_col:
    for reg, group in raw.groupby("Registration Number"):
        names = {(str(a).strip() + " " + str(b).strip()).strip()
                 for a, b in zip(group[sur_col], group[oth_col])}
        if len(names) > 1:
            issues.append({
                "Issue": "Conflicting names on one registration number",
                "Key": reg,
                "Detail": " / ".join(sorted(names))})

subj_col = find_col(raw, "Subject", "Subjects")
if subj_col:
    def _subject(value):
        text = prettify(value).strip()
        return SUBJECT_ALIASES.get(text.lower(), titled(text))
    before = raw[subj_col].astype(str).map(prettify)
    raw["Subject"] = raw[subj_col].map(_subject)
    for old, new in sorted(set(zip(before, raw["Subject"]))):
        if old != new:
            issues.append({"Issue": "Subject name normalised", "Key": old,
                           "Detail": "recorded as %r, read as %r" % (old, new)})

def parse_dates(series):
    """Dates, without asking pandas to guess.

    Left to itself pandas warns "Could not infer format, so each element will
    be parsed individually" and the warning prints above the report. Try the
    forms a collection tool actually emits, take the first that reads every
    value, and only then fall back - through format="mixed", which does the
    same element-wise parse without the complaint.
    """
    text = series.astype(str).str.strip()
    for fmt in ("%d/%m/%y %H:%M", "%d/%m/%Y %H:%M", "%d/%m/%y", "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M",
                "%d-%b-%Y", "%d %B %Y"):
        parsed = pd.to_datetime(text, format=fmt, errors="coerce")
        if parsed.notna().all():
            return parsed
    return pd.to_datetime(text, format="mixed", dayfirst=True, errors="coerce")


date_col = find_col(raw, "Date", "Lesson Date", "today")
raw["Assessed on"] = (parse_dates(raw[date_col]) if date_col
                      else pd.Series(pd.NaT, index=raw.index))


# =======================================================================
#  2. Score every visit against the template
# =======================================================================
# Bind the collected columns onto the printed form's items. Anything MAPPING
# does not claim is offered to the template by name, so a fuller collection
# form works without editing this file.
bound = {}
claimed = set()
for key, sources in MAPPING.items():
    if key not in ITEM_TEXT:
        continue
    cols = [c for c in (find_col(raw, s) for s in sources) if c is not None]
    if cols:
        bound[key] = cols
        claimed.update(cols)

identity_like = {_norm(c) for c in (
    "meta-instanceID", "Registration Number", "Surname", "Other Names",
    "Campus", "Year of Study", "Programme", "TP Institution", "District",
    "Region", "Class", "Subject", "Subjects", "Sub Topic", "Date",
    "Lesson Start Time", "Lesson End Time", "Leson End Time", "Assessed on",
    "Sex", "Student Phone", "Supervisor")}

for col in raw.columns:
    if col in claimed or _norm(col) in identity_like:
        continue
    match, best = None, 0.0
    words = set(_norm(col).split())
    for key, text in ITEM_TEXT.items():
        if key in bound:
            continue
        other = set(_norm(text).split())
        overlap = len(words & other) / max(len(words | other), 1)
        if overlap > best:
            match, best = key, overlap
    if match and best >= 0.5:
        bound[match] = [col]
        claimed.add(col)

assessed_keys = [k for k in ITEM_KEYS if k in bound]
if not assessed_keys:
    raise ValueError(
        "None of the columns read could be matched to an item on the "
        "assessment form. Set MAPPING in the cell.\nColumns read: "
        + ", ".join(map(str, raw.columns)))

MAX_ASSESSED = MAX_PER_ITEM * len(assessed_keys)

visits = []
for _, row in raw.iterrows():
    marks, notes = {}, {}
    for key in assessed_keys:
        got = [(score_of(row[c]), comment_of(row[c])) for c in bound[key]]
        got = [(m, c) for m, c in got if m is not None]
        if got:
            marks[key] = float(np.mean([m for m, _ in got]))
            notes[key] = "; ".join(c for _, c in got if c)
    if not marks:
        continue
    total = sum(marks.values())
    visits.append({
        "row": row,
        "marks": marks,
        "notes": notes,
        "total": total,
        "percent": 100.0 * total / MAX_ASSESSED,
        "reg": str(row["Registration Number"]).strip(),
        "subject": str(row.get("Subject", "")).strip(),
        "date": row["Assessed on"],
    })

visits.sort(key=lambda v: (v["reg"], pd.Timestamp.min if pd.isna(v["date"])
                           else v["date"]))
print("Read %d submissions from the %s; %d after removing duplicates, "
      "scored on %d of the form's %d items (%d marks)."
      % (n_raw, source_kind, len(visits), len(assessed_keys), len(ITEM_KEYS),
         MAX_ASSESSED))


# =======================================================================
#  3. One row per student
# =======================================================================
students = []
for reg in sorted({v["reg"] for v in visits}):
    mine = [v for v in visits if v["reg"] == reg]
    last = mine[-1]["row"]                        # most recent identity wins
    record = {
        "Registration Number": reg,
        "Surname": prettify(get(last, raw, "Surname")).upper(),
        "Other Names": prettify(get(last, raw, "Other Names", "Other Name(s)")),
        "Sex": get(last, raw, "Sex", "Gender"),
        "Year of Study": prettify(get(last, raw, "Year of Study", "YOS")),
        "Programme": prettify(get(last, raw, "Programme")),
        "Campus": prettify(get(last, raw, "Campus")),
        "Student Phone": get(last, raw, "Student Phone", "Phone"),
        "TP Institution": prettify(get(last, raw, "TP Institution",
                                       "TP Station")),
        "Region": prettify(get(last, raw, "Region", "TP Region")),
        "District": prettify(get(last, raw, "District")),
        "Supervisor": get(last, raw, "Supervisor", "Supervisors Name") \
            or SUPERVISOR,
        "Visits": len(mine),
    }
    # Visits grouped by subject, because the results sheet has room for two
    # subjects with up to three assessments each.
    by_subject = {}
    for v in mine:
        by_subject.setdefault(v["subject"] or "Not stated", []).append(v)
    for s_i, (subject, group) in enumerate(list(by_subject.items())[:2], start=1):
        record["Subj %d" % s_i] = subject
        for a_i, v in enumerate(group[:MAX_VISITS], start=1):
            record["Subj %d Ass %d" % (s_i, a_i)] = round(v["percent"], 1)
            record["Subj %d Ass %d date" % (s_i, a_i)] = (
                "" if pd.isna(v["date"]) else v["date"].strftime("%d/%m/%Y"))
    # Every item's mark, averaged over the student's visits, so the clean
    # sheet carries the detail and not only the totals.
    for key in assessed_keys:
        got = [v["marks"][key] for v in mine if key in v["marks"]]
        record["Score %s %s" % (key, ITEM_TEXT[key][:40])] = (
            round(float(np.mean(got)), 2) if got else np.nan)
    for name, _, items in TEMPLATE:
        got = [v["marks"][k] for v in mine for k, _ in items if k in v["marks"]]
        record[name] = round(float(np.mean(got)), 2) if got else np.nan
    marks = [v["percent"] for v in mine]
    record["AVR(P&T)"] = round(float(np.mean(marks)), 2)
    students.append(record)

clean = pd.DataFrame(students)

# --- the totals ---------------------------------------------------------
components = {"AVR": clean["AVR(P&T)"]}
for name in ("IG", "PTG"):
    col = find_col(raw, name)
    components[name] = (pd.to_numeric(raw[col], errors="coerce")
                        if col else pd.Series(np.nan, index=clean.index))
    clean[name] = components[name].values

present = [k for k, s in components.items() if s.notna().any()]
scale = sum(WEIGHTS[k] for k in present) or 1.0
clean["Total"] = sum(WEIGHTS[k] * components[k].fillna(0).values
                     for k in present) / scale
clean["Total"] = clean["Total"].round(2)


def grade_of(mark):
    for floor, letter in GRADE_BANDS:
        if mark >= floor:
            return letter
    return GRADE_BANDS[-1][1]


clean["Grade"] = clean["Total"].map(grade_of)
clean["Remarks"] = np.where(clean["Total"] >= PASS_MARK, "PASS", "FAIL")

WEIGHT_NOTE = ("Total = " + " + ".join(
    "%.0f%% %s" % (100.0 * WEIGHTS[k] / scale, k) for k in present) +
    ("." if len(present) > 1 else
     ". IG and PTG are not collected by the lesson form, so the visit "
     "average carries the whole mark."))


# =======================================================================
#  Output 1 - the clean sheet
# =======================================================================
clean.to_csv("TP_Clean_Data.csv", index=False)
with pd.ExcelWriter("TP_Clean_Data.xlsx", engine="openpyxl") as writer:
    clean.to_excel(writer, sheet_name="Students", index=False)
    pd.DataFrame([
        {"Item": ITEM_TEXT[k], "Area": SECTION_OF[k],
         "Collected as": ", ".join(bound[k]), "Maximum": MAX_PER_ITEM}
        for k in assessed_keys
    ]).to_excel(writer, sheet_name="Items assessed", index=False)

for phrase, mark in sorted(UNKNOWN_PHRASES.items()):
    issues.append({"Issue": "Rating not in the rubric", "Key": phrase,
                   "Detail": "read as %d out of %d by keyword"
                             % (mark, MAX_PER_ITEM)})
quality = pd.DataFrame(issues, columns=["Issue", "Key", "Detail"])
quality.to_csv("TP_Data_Quality.csv", index=False)


# =======================================================================
#  Output 2 - the assessment form, one per lesson observed
# =======================================================================
FORM_CSS = """
@page { size: A4 portrait; margin: 1.1cm 1.2cm 1.3cm 1.2cm; }
body { font-family: "Nimbus Sans", Helvetica, Arial, sans-serif;
       font-size: 8.1pt; color: #0f172a; margin: 0; }
.form { page-break-after: always; }
.form:last-child { page-break-after: auto; }
.band { height: 4px; margin-bottom: 7px; background: linear-gradient(to right,
        #096EFF 0%, #096EFF 58%, #10B981 58%, #10B981 82%,
        #f59e0b 82%, #f59e0b 100%); }
h1 { font-size: 11.5pt; text-align: center; margin: 0; letter-spacing: .04em; }
h2 { font-size: 9.6pt; text-align: center; margin: 2px 0 8px 0;
     font-weight: 600; color: #475569; letter-spacing: .02em; }
.meta { width: 100%; border-collapse: collapse; margin-bottom: 7px; }
.meta td { padding: 2.4px 4px; vertical-align: bottom; }
.lab { color: #475569; white-space: nowrap; }
.val { border-bottom: .6px dotted #94a3b8; font-weight: 600;
       padding-right: 10px !important; }
.opt { padding: 0 5px; }
.tick { font-weight: 700; color: #096EFF;
        border: 1.1px solid #096EFF; border-radius: 3px; padding: 0 3px; }
table.items { width: 100%; border-collapse: collapse; }
table.items th { background: #0f172a; color: #fff; font-size: 8pt;
                 padding: 4px 6px; text-align: left; font-weight: 600; }
table.items td { border-bottom: .5px solid #e2e8f0; padding: 3.4px 6px;
                 vertical-align: top; }
tr.sec td { background: #eff6ff; font-weight: 700; color: #096EFF;
            border-top: 1px solid #096EFF; border-bottom: none;
            padding: 4px 6px; }
tr { page-break-inside: avoid; }
td.no { width: 4%; color: #475569; }
td.txt { width: 56%; }
td.sc { width: 15%; white-space: nowrap; text-align: center;
        font-variant-numeric: tabular-nums; }
td.cm { width: 25%; color: #475569; font-size: 7.6pt; }
.digit { display: inline-block; width: 12px; height: 12px; line-height: 12px;
         text-align: center; color: #94a3b8; }
.circled { color: #096EFF; font-weight: 700; border: 1.3px solid #096EFF;
           border-radius: 50%; }
.na { color: #94a3b8; font-style: italic; font-size: 7.4pt; }
.gen { margin-top: 8px; border: .6px solid #e2e8f0; border-radius: 4px;
       padding: 6px 8px; }
.gen h3 { margin: 0 0 3px 0; font-size: 8.4pt; color: #475569; }
.gen p { margin: 0; line-height: 1.45; }
.total { margin-top: 8px; background: #096EFF; color: #fff; border-radius: 4px;
         padding: 6px 10px; font-size: 10pt; font-weight: 700;
         display: flex; justify-content: space-between; }
.total .out { font-weight: 500; font-size: 8.4pt; opacity: .9; }
.sign { margin-top: 9px; font-size: 8pt; color: #475569;
        width: 100%; border-collapse: collapse; }
.sign td { padding: 3px 4px; }
.credit { margin-top: 7px; font-size: 7pt; color: #94a3b8; text-align: right; }
"""


def scale_html(mark):
    """0 1 2 3 4 with the awarded one circled, as the printed form asks."""
    out = []
    for digit in range(MAX_PER_ITEM + 1):
        hit = mark is not None and int(round(mark)) == digit
        out.append('<span class="digit%s">%d</span>'
                   % (" circled" if hit else "", digit))
    return "".join(out)


def options_html(value, options):
    """Main Campus DUCE MUCE, with the one that matches ticked."""
    out = []
    matched = False
    for opt in options:
        hit = _norm(value) == _norm(opt) or _norm(value).startswith(_norm(opt))
        matched = matched or hit
        out.append('<span class="opt%s">%s</span>'
                   % (' tick" ' if hit else '"', esc(opt)))
    if value and not matched:
        out.append('<span class="opt tick">%s</span>' % esc(prettify(value)))
    return "".join(out)


def year_options(value):
    text = _norm(value)
    for word, label in (("first", "1st"), ("second", "2nd"), ("third", "3rd")):
        if text.startswith(word) or text.startswith(label):
            return options_html(label, ["1st", "2nd", "3rd"])
    return options_html(value, ["1st", "2nd", "3rd"])


def form_html(visit, index, of):
    row, marks, notes = visit["row"], visit["marks"], visit["notes"]
    got = ['<div class="form"><div class="band"></div>',
           "<h1>UNIVERSITY OF DAR ES SALAAM</h1>",
           "<h2>Teaching Practice Assessment Report Form</h2>",
           '<table class="meta">']

    def line(*cells):
        got.append("<tr>" + "".join(cells) + "</tr>")

    def lab(text):
        return '<td class="lab">%s</td>' % esc(text)

    def val(text, span=1):
        return ('<td class="val" colspan="%d">%s</td>'
                % (span, esc(text) if text else "&nbsp;"))

    line(lab("Surname:"), val(get(row, raw, "Surname").upper()),
         lab("Other Name(s):"), val(prettify(get(row, raw, "Other Names",
                                                 "Other Name(s)")), 3))
    line(lab("Reg. No:"), val(get(row, raw, "Registration Number")),
         lab("Campus:"),
         '<td colspan="3">%s</td>' % options_html(
             get(row, raw, "Campus"), ["Main Campus", "DUCE", "MUCE"]))
    line(lab("Year of Study:"),
         '<td>%s</td>' % year_options(get(row, raw, "Year of Study", "YOS")),
         lab("Programme:"),
         val(prettify(get(row, raw, "Programme")), 3))
    line(lab("TP Institution:"),
         val(titled(get(row, raw, "TP Institution", "TP Station"))),
         lab("Class:"), val(prettify(get(row, raw, "Class"))),
         lab("Time of Lesson:"),
         val("%s - %s" % (get(row, raw, "Lesson Start Time") or "...",
                          get(row, raw, "Lesson End Time", "Leson End Time")
                          or "...")))
    when = visit["date"]
    line(lab("Subject:"), val(titled(get(row, raw, "Subject"))),
         lab("Sub-Topic:"), val(titled(get(row, raw, "Sub Topic",
                                          "Sub-Topic")), 2),
         val("" if pd.isna(when) else when.strftime("%d %B %Y")))
    got.append("</table>")

    if of > 1:
        got.append('<p class="na" style="margin:0 0 5px 0">Assessment visit '
                   '%d of %d for this student.</p>' % (index, of))

    got.append('<table class="items"><tr><th>Areas of assessment</th>'
               '<th style="text-align:center">Score (circle)</th>'
               '<th>Comment(s)</th></tr>')
    for name, marks_total, items in TEMPLATE:
        section_got = [marks[k] for k, _ in items if k in marks]
        # Out of what was assessed, not out of the section's full marks - a
        # section where two of four items were observed is scored out of 8.
        badge = ("&nbsp;&nbsp;%g / %d"
                 % (sum(section_got), MAX_PER_ITEM * len(section_got))
                 if section_got else "")
        got.append('<tr class="sec"><td colspan="3">%s (%d marks)%s</td></tr>'
                   % (esc(name), marks_total, badge))
        for key, text in items:
            mark = marks.get(key)
            got.append(
                '<tr><td class="txt" colspan="1" style="width:56%%">'
                '<span class="no">%s.</span> %s</td>'
                '<td class="sc">%s</td><td class="cm">%s</td></tr>'
                % (key.split(".")[1], esc(text),
                   scale_html(mark) if key in bound
                   else '<span class="na">not assessed</span>',
                   esc(notes.get(key, "")) if key in bound else ""))
    got.append("</table>")

    # Not a repeat of the comment column - the comments are already on every
    # line. This is what a supervisor writes at the bottom: what went well,
    # what to work on, and the remarks that matter most.
    best = sorted([k for k, m in marks.items() if m >= 3], key=marks.get,
                  reverse=True)
    worst = sorted([k for k, m in marks.items() if m <= 2], key=marks.get)
    parts = []
    if best:
        parts.append("Strongest on %s."
                     % series(short_item(k) for k in best[:3]))
    if worst:
        parts.append("Needs most attention on %s."
                     % series(short_item(k) for k in worst[:3]))
    raised = [notes[k].rstrip(" .;") for k in worst if notes.get(k)]
    if raised:
        parts.append("Points raised: %s." % "; ".join(raised))
    if not parts:
        parts.append("&nbsp;")
    got.append('<div class="gen"><h3>General comments / points for '
               'discussion</h3><p>%s</p></div>'
               % " ".join(esc(p) if p != "&nbsp;" else p for p in parts))

    got.append('<div class="total"><span>Total score: %g / %d</span>'
               '<span class="out">%.1f%% &nbsp;&middot;&nbsp; %d of the '
               "form's %d items assessed</span></div>"
               % (visit["total"], MAX_ASSESSED, visit["percent"],
                  len(marks), len(ITEM_KEYS)))

    got.append('<table class="sign"><tr>'
               '<td class="lab">Name of Supervisor:</td>%s'
               '<td class="lab">Campus:</td>%s'
               '<td class="lab">Signature:</td>%s'
               '<td class="lab">Date:</td>%s</tr></table>'
               % (val(get(row, raw, "Supervisor", "Supervisors Name")
                      or SUPERVISOR),
                  val(SUPERVISOR_CAMPUS), val(""), val("")))
    got.append('<div class="credit">Generated by TSSFL Technology Stack '
               '&middot; www.tssfl.com</div></div>')
    return "".join(got)


forms = []
for reg in sorted({v["reg"] for v in visits}):
    mine = [v for v in visits if v["reg"] == reg]
    for i, visit in enumerate(mine, start=1):
        forms.append(form_html(visit, i, len(mine)))

forms_doc = ("<html><head><meta charset='utf-8'><title>%s - assessment forms"
             "</title><style>%s</style></head><body>%s</body></html>"
             % (esc(TITLE), FORM_CSS, "".join(forms)))
with open("TP_Student_Reports.html", "w", encoding="utf-8") as fh:
    fh.write(forms_doc)
HTML(string=forms_doc).write_pdf("TP_Student_Reports.pdf")
print("Wrote TP_Student_Reports.pdf - %d assessment forms for %d students."
      % (len(forms), len(clean)))


# =======================================================================
#  4. Charts
# =======================================================================
SRC = "Source: TSSFL teaching practice assessment records."
charts = []


def keep(fig, name):
    fig.savefig(name, dpi=150, facecolor=SURFACE)
    charts.append(name)
    return fig


# --- how the marks fell -------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.4, 6.4))
lo = min(clean["Total"].min(), PASS_MARK)
edges = np.arange(np.floor(lo / 5) * 5,
                  np.ceil(clean["Total"].max() / 5) * 5 + 5, 5)
ax1.hist(clean["Total"], bins=edges, color=BLUE, edgecolor=SURFACE, lw=1.4)
ax1.axvline(clean["Total"].mean(), color=AMBER, lw=2.4,
            label="Mean %.1f%%" % clean["Total"].mean())
ax1.axvline(PASS_MARK, color=ROSE, lw=1.8, ls="--",
            label="Pass mark %.0f%%" % PASS_MARK)
# The pass-mark rule sits on the first bin edge; widen the view a little so
# it is a line on the chart rather than a mark on the frame.
ax1.set_xlim(edges[0] - 2.5, edges[-1] + 1.0)
ax1.set_xlabel("Total score (%)")
ax1.set_ylabel("Students")
# A count of students is a whole number, so the axis must not offer halves,
# and the two rules are named below the plot where no bar can reach them.
ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
ax1.set_ylim(0, max(np.histogram(clean["Total"], bins=edges)[0]) * 1.12)
ax1.legend(frameon=False, fontsize=10, loc="upper center",
           bbox_to_anchor=(0.5, -0.13), ncol=2, handlelength=1.8)
ax1.set_title("Distribution of totals", fontsize=12.5)

grades = clean["Grade"].value_counts()
order = [g for _, g in GRADE_BANDS if g in grades.index]
grades = grades.reindex(order)
grade_cols = colors(len(grades))
donut(list(grades.index), list(grades.values), ax=ax2,
      cols=grade_cols, centre_note="Students",
      fmt="{value:.0f}\n{pct:.0f}%")
ax2.set_title("Classification", fontsize=12.5)
finish(fig, "How the teaching practice marks fell",
       "%d students, %d lessons observed. %s"
       % (len(clean), len(visits), WEIGHT_NOTE),
       legend=list(zip(["Grade " + g for g in grades.index], grade_cols)),
       source=SRC, gap=0.5)
keep(fig, "tp_chart_totals.png")
plt.show()

# --- which areas are strong, which are weak -----------------------------
means = pd.Series(
    {ITEM_TEXT[k]: np.mean([v["marks"][k] for v in visits if k in v["marks"]])
     for k in assessed_keys}).sort_values()
fig, ax = plt.subplots(figsize=(11.6, 0.62 * len(means) + 3.1))
ax.barh(range(len(means)), means.values, height=0.6,
        color=[EMERALD if m >= 3 else AMBER if m >= 2 else ROSE
               for m in means.values])
ax.set_yticks(range(len(means)))
ax.set_yticklabels([wrap(t, 46) for t in means.index], fontsize=10)
ax.set_xlim(0, MAX_PER_ITEM)
ax.set_xlabel("Mean mark out of %d" % MAX_PER_ITEM)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.xaxis.grid(True, color=GRID, lw=1)
ax.set_axisbelow(True)
label_bars(ax, fmt="{:.2f}", horizontal=True)
finish(fig, "Where the students are strong, and where they are not",
       "Mean mark on each item of the assessment form, over all %d lessons "
       "observed. Green is 3 and above, amber 2 to 3, red below 2."
       % len(visits), source=SRC)
keep(fig, "tp_chart_items.png")
plt.show()

# --- who, and where -----------------------------------------------------
splits = [(c, t) for c, t in (("Campus", "By campus"),
                              ("Programme", "By programme"),
                              ("Region", "By region"))
          if c in clean and clean[c].replace("", np.nan).notna().any()]
if splits:
    fig, axes = panels(len(splits), ncols=len(splits), width=13.6, height=6.2)
    for ax_i, (col, title), tint in zip(axes, splits, (BLUE, EMERALD, AMBER)):
        means_ = (clean.groupby(col)["Total"].agg(["mean", "size"])
                  .sort_values("mean"))
        # One hue per panel. The bars carry a magnitude, not an identity -
        # a colour per programme would be twelve hues saying nothing, and
        # more than the palette has that stay distinguishable.
        ax_i.barh(range(len(means_)), means_["mean"], height=0.6, color=tint)
        ax_i.set_yticks(range(len(means_)))
        ax_i.set_yticklabels(["%s (%d)" % (wrap(str(i), 20), n)
                              for i, n in zip(means_.index, means_["size"])],
                             fontsize=9.5)
        ax_i.set_xlabel("Mean total (%)")
        ax_i.set_title(title, fontsize=12)
        ax_i.set_xlim(0, 100)
        for side in ("top", "right", "left"):
            ax_i.spines[side].set_visible(False)
        ax_i.xaxis.grid(True, color=GRID, lw=1)
        ax_i.set_axisbelow(True)
        label_bars(ax_i, fmt="{:.1f}", horizontal=True)
    finish(fig, "Mean total by campus, programme and placement region",
           "Number of students in brackets. Groups of one or two students "
           "are a description, not a comparison.", source=SRC)
    keep(fig, "tp_chart_groups.png")
    plt.show()

# --- did the second visit go better than the first? ---------------------
pairs = [(reg, [v for v in visits if v["reg"] == reg])
         for reg in sorted({v["reg"] for v in visits})]
# Three is the fewest that makes a chart rather than a sentence; below that
# the dumbbell is one bar in an empty frame.
pairs = [(reg, vs) for reg, vs in pairs if len(vs) >= 2]
if len(pairs) >= 3:
    names = []
    for reg, vs in pairs:
        who = clean.loc[clean["Registration Number"] == reg]
        names.append(who["Surname"].iloc[0].title() if len(who) else reg)
    fig, ax = plt.subplots(figsize=(11.6, 0.7 * len(pairs) + 3.6))
    first, latest = palette()[0], palette()[1]
    dumbbell(names, [vs[0]["percent"] for _, vs in pairs],
             [vs[-1]["percent"] for _, vs in pairs], ax=ax,
             cols=[first, latest],
             left_name="First visit", right_name="Latest visit")
    ax.set_xlabel("Score for the lesson observed (%)")
    finish(fig, "Change between the first and the latest visit",
           "The %d students observed more than once. The number at the end of "
           "each line is the change in percentage points." % len(pairs),
           legend=[("First visit", first), ("Latest visit", latest)],
           source=SRC)
    keep(fig, "tp_chart_progress.png")
    plt.show()
elif pairs:
    print("%d student(s) were observed more than once - too few for a chart; "
          "the visits are in TP_Clean_Data.csv." % len(pairs))


# =======================================================================
#  Output 3 - the results sheet
# =======================================================================
RESULT_COLS = ["S/N", "STUDENT NAME", "STUDENT REG NO.", "SEX", "YOS",
               "PROGRAMME", "CAMPUS", "STUDENT PHONE", "SUBJECTS",
               "TP STATION", "TP REGION", "DISTRICT", "SUPERVISORS NAME",
               "Subj 1", "1st Ass", "2nd Ass", "3rd Ass",
               "Subj 2", "1st Ass ", "2nd Ass ", "3rd Ass ",
               "AVR(P&T)", "IG", "PTG", "Total", "Grade", "Remarks"]

rows = []
for n, (_, r) in enumerate(clean.iterrows(), start=1):
    row = {c: "" for c in RESULT_COLS}
    row["S/N"] = n
    row["STUDENT NAME"] = ("%s, %s" % (r["Surname"], r["Other Names"].upper())
                           ).strip(", ")
    row["STUDENT REG NO."] = r["Registration Number"]
    row["SEX"] = r["Sex"]
    row["YOS"] = r["Year of Study"]
    row["PROGRAMME"] = r["Programme"]
    row["CAMPUS"] = r["Campus"]
    row["STUDENT PHONE"] = r["Student Phone"]
    row["SUBJECTS"] = ", ".join(
        str(r[c]) for c in ("Subj 1", "Subj 2") if c in r and pd.notna(r.get(c)))
    row["TP STATION"] = r["TP Institution"]
    row["TP REGION"] = r["Region"] or REGION_LABEL
    row["DISTRICT"] = r["District"]
    row["SUPERVISORS NAME"] = r["Supervisor"]
    for s_i, suffix in ((1, ""), (2, " ")):
        row["Subj %d" % s_i] = r.get("Subj %d" % s_i, "") if pd.notna(
            r.get("Subj %d" % s_i, np.nan)) else ""
        for a_i, label in enumerate(("1st Ass", "2nd Ass", "3rd Ass"), start=1):
            value = r.get("Subj %d Ass %d" % (s_i, a_i), np.nan)
            row[label + suffix] = "" if pd.isna(value) else value
    for c in ("AVR(P&T)", "IG", "PTG", "Total", "Grade", "Remarks"):
        value = r.get(c, "")
        row[c] = "" if (isinstance(value, float) and np.isnan(value)) else value
    rows.append(row)

results = pd.DataFrame(rows, columns=RESULT_COLS)

# The trailing spaces on the second subject's columns exist only to keep the
# frame's labels unique. The workbook they copy has "1st Ass" twice, and a
# file is allowed to as well - strip them on the way out.
exported = results.copy()
exported.columns = [c.strip() for c in RESULT_COLS]
exported.to_csv("TP_Results.csv", index=False)
with pd.ExcelWriter("TP_Results.xlsx", engine="openpyxl") as writer:
    exported.to_excel(writer, sheet_name="Results", index=False)
    quality.to_excel(writer, sheet_name="Data quality", index=False)

RESULT_CSS = """
@page { size: A4 landscape; margin: 1.0cm 1.0cm 1.2cm 1.0cm;
        @bottom-right { content: "Page " counter(page) " of " counter(pages);
                        font-size: 7pt; color: #94a3b8; } }
body { font-family: "Nimbus Sans", Helvetica, Arial, sans-serif;
       font-size: 6.6pt; color: #0f172a; margin: 0; hyphens: none; }
.band { height: 4px; margin-bottom: 8px; background: linear-gradient(to right,
        #096EFF 0%, #096EFF 58%, #10B981 58%, #10B981 82%,
        #f59e0b 82%, #f59e0b 100%); }
h1 { font-size: 12pt; text-align: center; margin: 0; letter-spacing: .04em; }
h2 { font-size: 9.5pt; text-align: center; margin: 3px 0 2px 0;
     font-weight: 600; color: #475569; }
.sub { text-align: center; color: #94a3b8; font-size: 7.6pt;
       margin: 0 0 9px 0; }
/* table-layout: fixed, with a colgroup, because the automatic algorithm
   gives the long text columns whatever they ask for and pushes Grade and
   Remarks off the right-hand edge of the page. */
table.res { width: 100%; border-collapse: collapse; table-layout: fixed; }
table.res td { word-wrap: break-word; overflow-wrap: break-word; }
table { width: 100%; border-collapse: collapse; }
th { background: #0f172a; color: #fff; padding: 4px 2px; font-size: 5.8pt;
     font-weight: 600; text-align: left; vertical-align: bottom;
     word-wrap: break-word; letter-spacing: -.01em; }
th.n { text-align: right; }
td { padding: 2.6px 2px; border-bottom: .5px solid #e2e8f0;
     vertical-align: top; }
td.n { text-align: right; font-variant-numeric: tabular-nums; }
tr:nth-child(even) td { background: #f8fafc; }
tr { page-break-inside: avoid; }
thead { display: table-header-group; }
.grp { background: #eff6ff !important; color: #096EFF; font-weight: 700;
       text-align: center; font-size: 6.9pt; }
.tot { font-weight: 700; }
.pass { color: #15803d; font-weight: 700; }
.fail { color: #e11d48; font-weight: 700; }
.note { margin-top: 9px; font-size: 7pt; color: #475569; line-height: 1.5; }
.credit { margin-top: 4px; font-size: 7pt; color: #94a3b8; }
.stats { width: 100%; margin: 0 0 10px 0; border-collapse: separate;
         border-spacing: 6px 0; }
.stats td { background: #f8fafc; border: none; border-radius: 5px;
            padding: 7px 9px; text-align: center; }
.stats .k { display: block; font-size: 15pt; font-weight: 700; color: #096EFF;
            font-variant-numeric: tabular-nums; }
.stats .l { display: block; font-size: 7pt; color: #475569; }
img { width: 100%; margin-top: 9px; page-break-inside: avoid; }
"""

NUMERIC = {"S/N", "1st Ass", "2nd Ass", "3rd Ass", "1st Ass ", "2nd Ass ",
           "3rd Ass ", "AVR(P&T)", "IG", "PTG", "Total"}
GROUPS = [("", 13), ("Subject 1", 4), ("Subject 2", 4), ("Result", 6)]

# Column widths, in characters, normalised to percentages below. Each is the
# longest thing the column has to hold without breaking - a registration
# number is thirteen unbreakable characters, "Mathematics" is eleven, and
# "PROGRAMME" nine. Given less, the fixed layout breaks words in half.
WIDTHS = {"S/N": 3, "STUDENT NAME": 13, "STUDENT REG NO.": 14, "SEX": 4,
          "YOS": 8, "PROGRAMME": 9, "CAMPUS": 7, "STUDENT PHONE": 6,
          "SUBJECTS": 11, "TP STATION": 10, "TP REGION": 9, "DISTRICT": 11,
          "SUPERVISORS NAME": 11, "Subj 1": 11, "Subj 2": 9,
          "AVR(P&T)": 8, "IG": 3, "PTG": 4, "Total": 6, "Grade": 6,
          "Remarks": 8}
for _c in ("1st Ass", "2nd Ass", "3rd Ass"):
    WIDTHS[_c] = 5
for _c in ("1st Ass ", "2nd Ass ", "3rd Ass "):
    WIDTHS[_c] = 4
_span = sum(WIDTHS[c] for c in RESULT_COLS)
COLGROUP = "<colgroup>" + "".join(
    '<col style="width:%.2f%%">' % (100.0 * WIDTHS[c] / _span)
    for c in RESULT_COLS) + "</colgroup>"

# Two headers are longer than any value beneath them, and paying for their
# width would cost the columns that carry real text. The exported CSV and
# workbook keep the official wording; only the printed table abbreviates.
PRINT_HEADER = {"STUDENT REG NO.": "REG NO.", "SUPERVISORS NAME": "SUPERVISOR",
                "STUDENT PHONE": "PHONE", "PROGRAMME": "PROGR.", "S/N": "#"}

body = ['<div class="band"></div>',
        "<h1>UNIVERSITY OF DAR ES SALAAM</h1>",
        "<h2>%s%s</h2>" % (esc(TITLE),
                           " &middot; " + esc(ACADEMIC_YEAR)
                           if ACADEMIC_YEAR else ""),
        '<p class="sub">Supervision results for %d students over %d lessons '
        "observed%s. Prepared %s.</p>"
        % (len(clean), len(visits),
           ", " + esc(REGION_LABEL) if REGION_LABEL else "",
           datetime.date.today().strftime("%d %B %Y"))]

passed = int((clean["Total"] >= PASS_MARK).sum())
body.append('<table class="stats"><tr>' + "".join(
    '<td><span class="k">%s</span><span class="l">%s</span></td>' % (k, l)
    for k, l in (
        (len(clean), "Students"), (len(visits), "Lessons observed"),
        ("%.1f%%" % clean["Total"].mean(), "Mean total"),
        ("%.1f%%" % clean["Total"].max(), "Highest"),
        ("%.1f%%" % clean["Total"].min(), "Lowest"),
        ("%d of %d" % (passed, len(clean)), "At or above the pass mark"))
) + "</tr></table>")

body.append('<table class="res">' + COLGROUP + "<thead><tr>" + "".join(
    '<th class="grp" colspan="%d">%s</th>' % (n, esc(g) or "&nbsp;")
    for g, n in GROUPS) + "</tr><tr>" + "".join(
    '<th%s>%s</th>' % (' class="n"' if c in NUMERIC else "",
                       esc(PRINT_HEADER.get(c.strip(), c.strip())))
    for c in RESULT_COLS) + "</tr></thead><tbody>")
for _, r in results.iterrows():
    cells = []
    for c in RESULT_COLS:
        value = r[c]
        css = "n" if c in NUMERIC else ""
        if c == "Total":
            css += " tot"
        if c == "Remarks" and value:
            css += " pass" if value == "PASS" else " fail"
        if isinstance(value, float):
            value = "%.1f" % value if c != "Total" else "%.2f" % value
        cells.append('<td class="%s">%s</td>' % (css.strip(), esc(value)))
    body.append("<tr>" + "".join(cells) + "</tr>")
body.append("</tbody></table>")

body.append('<p class="note"><b>How the total is formed.</b> Each lesson '
            "observed is marked out of %d on the %d items of the assessment "
            "form the collection instrument covers, and expressed as a "
            "percentage. AVR(P&amp;T) is the mean of a student's lessons. %s "
            "Classification: %s. The pass mark is %.0f%%.</p>"
            % (MAX_ASSESSED, len(assessed_keys), esc(WEIGHT_NOTE),
               esc(", ".join("%s from %.0f" % (g, f) for f, g in GRADE_BANDS
                             if f > 0)), PASS_MARK))
if len(issues):
    body.append('<p class="note"><b>Data quality.</b> %d item%s needed '
                "attention before these figures could be produced; they are "
                "listed in TP_Data_Quality.csv.</p>"
                % (len(issues), "" if len(issues) == 1 else "s"))

for name in charts:
    with open(name, "rb") as fh:
        body.append('<img src="data:image/png;base64,%s">'
                    % base64.b64encode(fh.read()).decode("ascii"))

body.append('<p class="credit">Generated by TSSFL Technology Stack '
            "&middot; www.tssfl.com</p>")

results_doc = ("<html><head><meta charset='utf-8'><title>%s - results</title>"
               "<style>%s</style></head><body>%s</body></html>"
               % (esc(TITLE), RESULT_CSS, "".join(body)))
with open("TP_Results.html", "w", encoding="utf-8") as fh:
    fh.write(results_doc)
HTML(string=results_doc).write_pdf("TP_Results.pdf")

print("Wrote TP_Results.pdf / .html / .csv / .xlsx - %d students, mean %.1f%%, "
      "%d at or above the pass mark."
      % (len(clean), clean["Total"].mean(), passed))
print("Wrote TP_Clean_Data.csv / .xlsx - one row per student, %d columns."
      % clean.shape[1])
if len(issues):
    print("Wrote TP_Data_Quality.csv - %d item(s) for a clerk to look at."
          % len(issues))


# =======================================================================
#  On screen
# =======================================================================
show = results[["S/N", "STUDENT NAME", "STUDENT REG NO.", "PROGRAMME",
                "CAMPUS", "Subj 1", "1st Ass", "2nd Ass", "AVR(P&T)",
                "Total", "Grade", "Remarks"]].copy()
table(show, title="Teaching practice supervision results",
      source=SRC, total=False,
      fmt={"1st Ass": "{:g}", "2nd Ass": "{:g}", "AVR(P&T)": "{:.1f}",
           "Total": "{:.2f}"})

if len(issues):
    table(quality, title="Data quality - what needed attention",
          source=SRC, total=False)
