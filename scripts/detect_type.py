"""
detect_type.py -- guess the document type of Markdown that has no `type:` in its front matter.

Only a suggestion: the linter and md2tex.py report it, and nothing is applied until the user (or Claude, after
asking) adds `type: NAME` to the front matter. Returns (type, reason) pairs, best first.
"""
import re

FENCE = re.compile(r"^(```|~~~).*?^\1", re.M | re.S)


def detect(meta, body):
    text = FENCE.sub("", body)
    title = " ".join(str(meta.get(k, "")) for k in ("title", "subtitle")).lower()
    h = lambda pattern: re.findall(pattern, text, re.M)
    found = []

    papers, parts = h(r"^# Question \d+"), h(r"^## \d*\s*\.?\s*\(\w+\)")
    if papers and parts:
        found.append(("past-paper", f"{len(papers)} '# Question N' blocks and {len(parts)} '## 1(a)' solutions"))
    days = h(r"^# Day \d+")
    if days:
        found.append(("project-report", f"{len(days)} '# Day NN' chapters"))
    qs, sols = h(r"^#### [NSL]\d+[a-z]?\s*$"), h(r"^#### Solution [NSL]\d+")
    if len(qs) >= 3 and sols:
        found.append(("question-bank", f"{len(qs)} numbered questions with solutions"))
    if h(r"^\|\s*Title\s*\|\s*Equation\s*\|") or "formula sheet" in title:
        found.append(("formula-sheet", "a Title | Equation table" if h(r"^\|\s*Title\s*\|") else "the title says formula sheet"))
    explained = h(r"^\*Explained in ")
    if explained or "exam notes" in title or h(r"^# .*Exam Notes"):
        found.append(("exam-notes", f"{len(explained)} '*Explained in' links" if explained else "the title says exam notes"))
    lectures, checks = h(r"^## Lecture \d+"), h(r"^###.*self-check")
    if lectures or checks or "theory" in title:
        found.append(("theory-notes", f"{len(lectures)} '## Lecture NN' headings, {len(checks)} self-checks"
                      if lectures or checks else "the title says theory"))
    return found
