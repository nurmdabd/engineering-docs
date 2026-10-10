#!/usr/bin/env python3
"""
lint_md.py -- check Markdown against references/authoring.md before converting it.

Usage:
    python3 lint_md.py NOTES.md [MORE.md ...] [--strict]

Prints `file:line: error|warning: message`. Errors break the build or lose content (an unclosed code fence,
a question without its solution, bad front matter); warnings change the output in a way the writer probably
didn't mean (a heading ending in a colon, a link the PDF can't follow, a glyph the font doesn't have).
Exit code 1 if there are errors (or any warnings with --strict), else 0.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import doctype
import frontmatter
import slugs

Q_ID = re.compile(r"^[A-Z]{1,2}\d+[a-z]?$")            # N1, S12, L3, Q4a (same as house.lua)
SOL = re.compile(r"^Solution\s+([A-Z]{1,2}\d+[a-z]?)$")
MARKERS = "⚠🎯📌"
# glyphs the listing font (Latin Modern Mono) doesn't have; references/latex-rules.md, Section 5
NO_MONO = re.compile(r"[│┃└┘┌┐├┤┬┴┼─━═║╚╝╔╗▼▲►◄→←↑↓⇒✔✘✓✗]")
PICTO = re.compile("[\U0001F300-\U0001FAFF☀-⛿✀-➿]")
KEEP_PICTO = set("⚠✅✔✓❌✘🎯📌★⭐➕①②③④\uFE0F")      # the converter turns these into markers (house.lua TEXTCH)


def pandoc_ids(body):
    """Heading identifiers exactly as pandoc (and so the converter) makes them."""
    r = subprocess.run(["pandoc", "-f", "markdown+lists_without_preceding_blankline-fancy_lists-implicit_figures",
                        "-t", "json"], input=body, capture_output=True, text=True)
    if r.returncode:
        return None
    ids = set()

    def walk(x):
        if isinstance(x, dict):
            if x.get("t") == "Header":
                ids.add(x["c"][1][0])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(json.loads(r.stdout))
    return ids


def lint(path):
    text = path.read_text(encoding="utf-8")
    out = []

    def say(line, level, msg):
        out.append((line, level, msg))

    meta, body, problems = frontmatter.split(text)
    offset = text[:len(text) - len(body)].count("\n")      # body line numbers -> file line numbers
    for p in problems:
        say(1, "error", p)
    if meta.get("type") and meta["type"] not in doctype.available():
        say(1, "error", f"unknown type '{meta['type']}' (available: {', '.join(doctype.available())})")

    lines = body.split("\n")
    fence, fence_line = None, 0
    headings, questions, solutions, anchors = [], {}, {}, []
    open_display = None                                    # line of an unclosed $$
    for n, line in enumerate(lines, start=offset + 1):
        m = re.match(r"^(```+|~~~+)", line)
        if m:
            if fence is None:
                fence, fence_line = m.group(1), n
            elif line.strip().startswith(fence):
                fence = None
            continue
        if fence is not None:
            bad = sorted(set(NO_MONO.findall(line)))
            if bad:
                say(n, "warning", f"code block uses {' '.join(bad)}, which the listing font lacks; use ASCII (| +-- -> v)")
            continue
        h = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if h:
            level, title = len(h.group(1)), h.group(2)
            if title.endswith(":"):
                say(n, "warning", "heading ends with ':'; drop it, the colon is added automatically")
            if level >= 5:
                say(n, "warning", f"level-{level} heading; the deepest supported is ####")
            is_q = level == 4 and (Q_ID.match(title) or SOL.match(title))   # #### N1 sits under ## by convention
            if headings and level > headings[-1][1] + 1 and not is_q:
                say(n, "warning", f"heading jumps from level {headings[-1][1]} to {level}")
            headings.append((n, level, title))
            if level == 4 and Q_ID.match(title):
                if title in questions:
                    say(n, "error", f"question {title} appears twice (first at line {questions[title]})")
                questions.setdefault(title, n)
            s = SOL.match(title) if level == 4 else None
            if s:
                if s.group(1) in solutions:
                    say(n, "error", f"solution {s.group(1)} appears twice")
                solutions.setdefault(s.group(1), n)
            continue
        for _ in re.findall(r"(?<!\\)\$\$", line):
            open_display = None if open_display else n
        for a in re.finditer(r"\]\(#([^)\s]+)\)", line):
            anchors.append((n, a.group(1)))
        for img in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)", line):
            src = img.group(1)
            if not re.match(r"^https?:", src) and not (path.parent / src).exists():
                say(n, "warning", f"image {src} not found; it will be left as a TODO in the LaTeX")
        q = re.match(r"^>\s*(\S)", line)
        if q and PICTO.match(q.group(1)) and q.group(1) not in KEEP_PICTO:
            say(n, "warning", f"callout starts with {q.group(1)}; only ⚠ 🎯 📌 choose a box, this one becomes a note")
        text_part = re.sub(r"`[^`]*`", "", line[q.end():] if q else line)    # the callout opener is reported above
        stray = sorted({c for c in PICTO.findall(text_part) if c not in KEEP_PICTO})
        if stray:
            say(n, "warning", f"emoji {' '.join(stray)} will be dropped; say it in words")
        if re.search(r"\bTODO\b", line):
            say(n, "warning", "TODO left in the text")
    if fence is not None:
        say(fence_line, "error", "code fence is never closed")
    if open_display:
        say(open_display, "error", "display equation opened with $$ is never closed")

    for qid, n in questions.items():
        if qid not in solutions:
            say(n, "error", f"question {qid} has no '#### Solution {qid}'")
    for sid, n in solutions.items():
        if sid not in questions:
            say(n, "error", f"'Solution {sid}' has no question '#### {sid}'")

    ids = (pandoc_ids(body) or set()) | set(slugs.heading_slugs(body)) if anchors else set()
    for n, a in anchors:
        if a not in ids:
            say(n, "warning", f"link to #{a} matches no heading in this file, so the PDF will show plain text")

    if meta.get("type") == "project-report" and not any(l == 1 for _, l, _ in headings):
        say(offset + 1, "warning", "project-report expects one '# Day NN: ...' chapter per day")
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md", nargs="+", type=Path)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    a = ap.parse_args()
    errors = warnings = 0
    for md in a.md:
        for line, level, msg in lint(md):
            print(f"{md}:{line}: {level}: {msg}")
            errors += level == "error"
            warnings += level == "warning"
    print(f"{errors} error(s), {warnings} warning(s)")
    sys.exit(1 if errors or (a.strict and warnings) else 0)


if __name__ == "__main__":
    main()
