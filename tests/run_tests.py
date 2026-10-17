#!/usr/bin/env python3
"""
run_tests.py -- regression tests for the converter and the build.

    python3 tests/run_tests.py            # convert every fixture, compare with tests/expected/; lint tests/lint/*.md
    python3 tests/run_tests.py --update   # accept the current output as the new expected output
    python3 tests/run_tests.py --build    # also compile every expected body and the example; each log must be clean,
                                          # and the PDF text must match a case's pdf_has / pdf_lacks lists;
                                          # the --print copies of the example and "print": true cases hold no colour

Corpus check, for real notes that live in another repo (run before and after a converter change):

    python3 tests/run_tests.py --snapshot DIR  notes.md other.md:--bangla ...
    python3 tests/run_tests.py --compare  DIR  notes.md other.md:--bangla ...

Each corpus entry is a Markdown path, optionally followed by ':' and md2tex flags separated by commas
(for example sheet.md:--fontsize,10pt,--margin-x,0.4in). Snapshots go to DIR, outside the skill.
"""
import argparse
import re
import difflib
import shutil
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TESTS = Path(__file__).resolve().parent
SKILL = TESTS.parent
FIXTURES = TESTS / "fixtures"
EXPECTED = TESTS / "expected"
MD2TEX = SKILL / "scripts" / "md2tex.py"
LINT = SKILL / "scripts" / "lint_md.py"
DOC = SKILL / "scripts" / "doc.py"
BUILD = SKILL / "scripts" / "build.py"


def convert(md, out, flags):
    r = subprocess.run([sys.executable, str(MD2TEX), str(md), "-o", str(out), *flags],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"md2tex failed on {md.name}:\n{r.stderr}")
    return out.read_text(encoding="utf-8")


def diff(expected, actual, name):
    return "".join(difflib.unified_diff(expected.splitlines(True), actual.splitlines(True),
                                        f"expected/{name}", f"actual/{name}", n=2))


def check_skill():
    """SKILL.md front matter must parse (a bad one stops the skill loading), and every type must be complete."""
    import yaml
    problems = []
    try:
        fm = yaml.safe_load((SKILL / "SKILL.md").read_text(encoding="utf-8").split("---")[1])
        if not fm.get("name") or not fm.get("description"):
            problems.append("SKILL.md front matter lacks name or description")
        elif len(fm["description"]) > 1024:
            problems.append(f"SKILL.md description is {len(fm['description'])} characters (limit 1024)")
    except Exception as e:
        problems.append(f"SKILL.md front matter is not valid YAML: {str(e).splitlines()[0]}")
    for reg in [SKILL / "template" / "commands.yaml", *sorted((SKILL / "types").glob("*/commands.yaml"))]:
        try:
            for name, e in (yaml.safe_load(reg.read_text(encoding="utf-8")) or {}).items():
                if e.get("kind") not in ("command", "environment") or e.get("markdown") not in ("span", "div", "auto", "none"):
                    problems.append(f"{reg.relative_to(SKILL)}: '{name}' needs kind command|environment and markdown span|div|auto|none")
        except Exception as ex:
            problems.append(f"{reg.relative_to(SKILL)} is not valid YAML: {str(ex).splitlines()[0]}")
    for t in sorted((SKILL / "types").iterdir()):
        for f in ("type.json", "guide.md"):
            if t.is_dir() and not (t / f).exists():
                problems.append(f"types/{t.name} has no {f}")
    sys.path.insert(0, str(SKILL / "scripts"))
    import frontmatter
    missing = [k for k in frontmatter.KEYS if k not in frontmatter.DOCS] + [k for k in frontmatter.DOCS if k not in frontmatter.KEYS]
    if missing:
        problems.append(f"front-matter keys without a DOCS entry (or the reverse): {', '.join(missing)}")
    ref = SKILL / "references" / "front-matter-keys.md"
    if not ref.exists() or ref.read_text(encoding="utf-8") != frontmatter.reference():
        problems.append("references/front-matter-keys.md is out of date: python3 scripts/doc.py keys --write")
    print(f"{'ok' if not problems else 'FAILED':8} skill files")
    for p in problems:
        print("  " + p)
    return len(problems)


def check_margins():
    """Margins: lengths parse, the text width follows the margin, and type or front matter override the default."""
    sys.path.insert(0, str(SKILL / "scripts"))
    import doctype
    import frontmatter
    problems = []
    for length, cm in (("0.5in", 1.27), ("1.27cm", 1.27), ("12.7mm", 1.27), ("36.135pt", 1.27)):
        if abs(doctype.length_cm(length) - cm) > 1e-6:
            problems.append(f"length_cm({length}) is {doctype.length_cm(length)}, not {cm}")
    if abs(doctype.text_width_cm("0.5in") - 18.46) > 1e-6:
        problems.append("A4 text width at 0.5in margins is not 18.46 cm")
    flags = frontmatter.md2tex_flags({"type": "formula-sheet", "margin_x": "0.6in"})
    if flags[-2:] != ["--margin-x", "0.6in"]:
        problems.append(f"front matter margin_x must come after --type so it wins: {flags}")
    expanded = doctype.expand(["x", "--type", "formula-sheet"], "build")
    if expanded[expanded.index("--margin-x") + 1] != "0.4in":
        problems.append("formula-sheet type no longer sets --margin-x 0.4in")
    print(f"{'ok' if not problems else 'FAILED':8} margins")
    for p in problems:
        print("  " + p)
    return len(problems)


def check_coverdata():
    """The facts the covers show are read from the body, not typed in: parts, formula rows, questions, paper times."""
    import argparse
    import coverdata
    problems = []
    theory = ("\\section{Part 1 --- Lectures 24, 25, 26: Frequency Modulation}\\label{sec:p1}\n"
              "\\subsection{Lecture 24 --- PM bandwidth}\\label{sec:l24}\n\\begin{examplebox}x\\end{examplebox}\n"
              "\\subsection{Lecture 25 --- FM methods}\n\\begin{selfcheckbox}x\\end{selfcheckbox}\n"
              "\\section{Part 2 --- Lecture 27: Sampling}\n\\subsection{Lecture 27 --- Sampling}\n")
    items, n = coverdata.parts(theory)
    if n != 2 or "Frequency Modulation" not in items[0] or "L24--26" not in items[0] or "2 lectures" not in items[0] \
            or "worked examples" not in items[0] or "self-check" not in items[0] or "L27" not in items[1]:
        problems.append(f"parts(): {items}")
    rows = coverdata.tracker(theory)
    if len(rows) != 3 or "sec:l24" not in rows[0] or "{L25}" not in rows[1] or not rows[2].endswith("{2}"):
        problems.append(f"tracker(): {rows}")
    sheet = ("\\section{Formula Sheet}\n\\subsection{Angle modulation (L24)}\n\\begin{tabularx}{\\textwidth}{|l|l|l|l|}\n"
             "\\hline\nT & E & N & R \\\\ \\hline\n\\endhead\nA & $x$ & n & r \\\\ \\hline\nB & \\tallcell{$y$} & n & r \\\\ \\hline\n"
             "\\rowcolor{white}\n\\caption{Angle}\n\\end{tabularx}\n")
    items, total, n = coverdata.topics(sheet)
    if (total, n) != (2, 1) or "2 formulas" not in items[0] or "CoverSoft}L24}" not in items[0]:
        problems.append(f"topics(): {items}, {total}, {n}")
    if coverdata.sample_row(sheet) != "\\coversamplerow{A}{$x$}{n}{r}":
        problems.append(f"sample_row(): {coverdata.sample_row(sheet)}")
    bank = ("\\subsection{A1 FM}\n\\phantomsection\\label{q:n1}\n\\begin{questionbox}{N1}{sol:n1}x\\end{questionbox}\n"
            "\\label{q:s1}\n\\begin{questionbox}{S1}{sol:s1}x\\end{questionbox}\n\\begin{solutionbox}{Solution N1}{q:n1}x\\end{solutionbox}\n")
    stats, groups, log = coverdata.bank(bank)
    if stats != ["\\coverstat{1}{Numericals}", "\\coverstat{1}{Short questions}", "\\coverstat{1}{Solutions}"] \
            or groups != ["\\covergroup{A1}{FM}{2}"] or "\\coverlog{N1}{q:n1}" not in log:
        problems.append(f"bank(): {stats} {groups} {log}")
    paper = ("\\begin{questionblock}[1(a) Entropy]{1.(a) Find it. Marks: 6}\n\\begin{questionblock}[1(b) Modes]{1.(b) Discuss. Marks: 4+5}\n"
             "\\begin{questionblock}[2(a) AM]{2.(a) AM. Marks: 10}\n")
    facts, prow, note = coverdata.paper(paper, ["Total Marks: 100", "Total Time: 3 Hours"],
                                       ["Part-A: 1-2 | [Answer any one of the following questions]"], True)
    if facts != ["\\paperfact{3 h}{Total time}", "\\paperfact{100}{Total marks}", "\\paperfact{1 of 2}{Questions to answer}",
                 "\\paperfact{180 min}{Per question}"] or "& 9 & 16 min &" not in "".join(prow) or "sol-1a" not in "".join(prow):
        problems.append(f"paper(): {facts} {prow}")
    import formulasheet
    sheet2 = ("\\begin{tabularx}{\\textwidth}{|l|l|l|l|}\n\\hline\nT & E & N & R \\\\ \\hline\n\\endhead\n"
              "\\keyterm{Carson} & $B_T$ & \\tallcell{$B_T$ = bandwidth\\newline $a(t) = \\int m$} & r \\\\ \\hline\n"
              "Plain & $x$ & $B_T$ = again\\newline k = constant & r \\\\ \\hline\n\\end{tabularx}\n")
    marked, rows = formulasheet.mark_rows(sheet2)
    syms = [(s, m) for s, m, _ in formulasheet.symbols(rows)]
    if [r["key"] for r in rows] != [True, False] or "\\hypertarget{fsrow-1}{}" not in marked or "$\\bigstar$" not in marked \
            or syms != [("$B_T$", "bandwidth"), ("k", "constant")]:
        problems.append(f"formulasheet: keys {[r['key'] for r in rows]}, symbols {syms}")
    if "Key formulas" not in formulasheet.pages(rows) or "Symbol index" not in formulasheet.pages(rows):
        problems.append("formulasheet.pages(): a section is missing")
    print(f"{'ok' if not problems else 'FAILED':8} cover data")
    for p in problems:
        print("  " + p)
    return len(problems)


def check_mindmap_fit():
    """Mind maps: the outline parses at any depth, and a column that is too tall is fitted in the agreed order
    (gaps, grey lines, then a split before title-only cards when a second column is free, a continuation last),
    with the split guard; parts are spread over main-map pages. Made-up card heights, so no LaTeX is needed."""
    import mindmap
    problems = []
    spec, errs = mindmap.parse("# Course | L1--9\n## One | L1\n- **A** ★: $x$\n  - def: what A is\n  - **B**\n    - **C**\n"
                               "  - → D\n- **D**\n  - plain detail\n## Two\n- **E**\n")
    a = spec["parts"][0]["kids"][0]
    if errs or spec["sub"] != "L1--9" or not a["star"] or a["defn"] != "what A is" or a["chips"] != ["D"] \
            or a["kids"][0]["kids"][0]["title"] != "C" or spec["parts"][0]["kids"][1]["kids"][0]["title"] != "plain detail":
        problems.append(f"parse: {errs} {a}")
    if not any("no card or item" in e for e in mindmap.parse("## P\n- **A**\n  - → Nowhere\n")[1]):
        problems.append("a → chip naming no card is not reported")
    if not mindmap.has_map(a) or mindmap.has_map(spec["parts"][0]["kids"][1]):
        problems.append("has_map: a card with grandchildren needs a sub-map, one with a single detail does not")

    def card(t, star=False, kids=0):
        return {"title": t, "key": t.lower(), "star": star, "formula": "f", "defn": "", "chips": [],
                "kids": [{"title": f"{t}{i}", "key": f"{t}{i}", "star": False, "formula": "", "defn": "", "chips": [], "kids": []}
                         for i in range(kids)]}
    z = dict(mindmap.SIZE["a4"])

    def fitter(parts, h_full, h_nogrey, h_title, width=27.16, head=1.0, narrow=False):
        mp = mindmap.Map({"title": "", "sub": "", "detail": None, "parts": parts}, 1)
        mp.paginate(z, width)
        H = {}
        for x in mindmap.walk(mp.parts):
            for w in set(mindmap.main_widths(mp.P, z, width).values()) | {mindmap.sub_width(z, width)}:
                r = 4.8 / w if narrow else 1.0   # narrower columns wrap more: taller cards
                H[(mp.p, x["id"], w, "full")] = (h_full + (0.4 if x["kids"] else 0)) * r
                H[(mp.p, x["id"], w, "nogrey")] = h_nogrey * r
                H[(mp.p, x["id"], w, "title")] = h_title * r
        for p in mp.parts:
            for slots in range(mp.P, 2 * mp.P + 1):
                for k in (1, 2):
                    H[(mp.p, f"head{p['n']}", round(k * mindmap.slot(z, width, slots) - z["sgap"], 3), "head")] = head
        return mp, mindmap.Fitter(mp, z, H)
    one = [card("A", kids=2), card("B", star=True), card("C", kids=2), card("D")]
    mp, fit = fitter([{"name": "P", "sub": "", "kids": one}], 1.0, 0.6, 0.4)
    w = list(mindmap.main_widths(mp.P, z, 27.16).values())[0]
    steps = []
    for avail in (10, 6.8, 6.0, 5.0, 4.5):   # card heights + padding 0.31: 1.71 1.31 1.71 1.31, as grey-less 0.91, as title 0.71
        f = fit.one_column(one, w, avail)
        steps.append((f.step, f.hidden, f.collapsed) if f else None)
    if steps != [(0, 0, 0), (1, 0, 0), (2, 1, 0), (2, 2, 0), (4, 2, 1)]:
        problems.append(f"steps gaps, grey lines, title-only in order, as little as needed: {steps}")
    f = fit.one_column(one, w, 4.0)   # three non-star cards could go, but a third of four cards is 2 (the minimum)
    if f is not None:
        problems.append("title-only cards: more than a third of the column (at least 2) were shortened")
    fit.titles = 1.0
    f = fit.one_column(one, w, 4.0)
    if not f or [f.variant[c["id"]] for c in one] != ["title", "full", "title", "title"]:
        problems.append("collapsing: the star card is kept while the others can go: "
                        f"{[f.variant[c['id']] for c in one] if f else None}")
    fit.titles = 0
    if fit.one_column(one, w, 4.5) is not None:
        problems.append("map_titles 0: a card was still shown as its title only")
    fit.titles = 1 / 3
    if [fit.limit([0] * n) for n in (4, 6, 12, 15)] != [2, 2, 4, 5]:
        problems.append(f"title-only limit: {[fit.limit([0] * n) for n in (4, 6, 12, 15)]}")
    f = fit.columns(one, w, 4.5, 2)   # two columns come before title-only cards
    if not f or len(f.columns) != 2 or f.collapsed or f.step != mindmap.SPLIT:
        problems.append(f"two-column sequence: a split before title-only cards ({f and (len(f.columns), f.collapsed, f.step)})")
    f = fit.sub_column(one * 1, w, 2.0, 4)   # sub-map pages: more columns, never title-only cards
    if not f or f.collapsed or len(f.columns) < 3:
        problems.append(f"sub-map page: up to the page's columns, no title-only cards ({f and (len(f.columns), f.collapsed)})")
    g = mindmap.Fit(one)
    g.gap = z["gap"]
    cols = fit.balance(one, g, w, 3)   # heights 1.71 1.31 1.71 1.31 (gap 0.36): the tallest column can be 3.38, no less (plus padding)
    if len(cols) != 3 or not all(cols) or max(fit.col_h(c, g, w) for c in cols) > 3.39:
        problems.append(f"balance into three columns: {[len(c) for c in cols]}")
    if mindmap.describe(fit.one_column(one, w, 4.5), z) != "step 3 (gaps tightened, grey lines hidden on 2 cards, 1 card shown as the title only)":
        problems.append("one-column sequence: title-only cards are step 3: " + mindmap.describe(fit.one_column(one, w, 4.5), z))
    if mindmap.page_sizes(7, 6) != [4, 3] or mindmap.page_sizes(20, 6) != [5, 5, 5, 5] or mindmap.page_sizes(5, 6) != [5]:
        problems.append(f"main-map pages: {mindmap.page_sizes(7, 6)} {mindmap.page_sizes(20, 6)}")
    if mindmap.per_page(z, 27.16) != 6 or mindmap.per_page(mindmap.SIZE["a3"], 39.46) != 6:
        problems.append("parts per main-map page: 6 on A4 and on A3")

    def five(first, h):   # four small parts and one that is too tall for one column
        parts = [{"name": f"P{i}", "sub": "", "kids": [card(f"Q{i}{j}") for j in range(3)]} for i in range(4)]
        parts[0]["kids"] = [card(f"R{j}", kids=2) for j in range(first)]
        parts.append({"name": "Big", "sub": "", "kids": [card(f"K{i}") for i in range(14)]})
        mp, fit = fitter(parts, h, h, 0.5, narrow=True)
        calm, _ = mindmap.layout_main(mp, mp.parts, fit, z, 27.16, 17.11 - mindmap.RESERVE_MAIN, split=False)
        main, _ = mindmap.fit_main(mp, mp.parts, fit, z, 27.16, 17.11 - mindmap.RESERVE_MAIN)
        return calm, main
    calm, main = five(6, 0.8)    # narrower columns cost part 1 nothing: Big splits
    if len(main[5].columns) != 2 or main[5].moved or main[1].step != calm[1].step:
        problems.append(f"guard: a harmless split was refused (Big: {len(main[5].columns)} columns)")
    calm, main = five(6, 1.0)    # a split would make part 1 hide grey lines: Big takes the one-column sequence
    if len(main[5].columns) != 1 or not main[5].moved or main[1].step != calm[1].step:
        problems.append(f"guard: a split that makes another part take a later step was kept (part 1 step {main[1].step})")
    for p in problems:
        print("FAILED   mind-map fit: " + p)
    if not problems:
        print("ok       mind-map parse and fitting")
    return len(problems)


def run_cases(cases, update):
    failed = 0
    EXPECTED.mkdir(exist_ok=True)
    for case in cases:
        name = case["name"]
        # Convert next to the fixture so relative figure paths come out exactly as in expected/
        out = FIXTURES / f".{name}.out.tex"
        side = out.with_suffix(".build.json")   # build settings md2tex writes from front matter, if any
        try:
            results = {".tex": convert(FIXTURES / f"{name}.md", out, case.get("md2tex", []))}
            if side.exists():
                results[".build.json"] = side.read_text(encoding="utf-8")
        finally:
            out.unlink(missing_ok=True)
            side.unlink(missing_ok=True)
        for ext in (".tex", ".build.json"):
            exp, actual = EXPECTED / f"{name}{ext}", results.get(ext)
            if actual is None:
                if exp.exists():
                    failed += 1
                    print(f"CHANGED  {name}{ext}: no longer produced")
                continue
            if update or not exp.exists():
                exp.write_text(actual, encoding="utf-8")
                print(f"updated  {name}{ext}")
            elif exp.read_text(encoding="utf-8") == actual:
                print(f"ok       {name}{ext}")
            else:
                failed += 1
                print(f"CHANGED  {name}{ext}\n{diff(exp.read_text(encoding='utf-8'), actual, name + ext)}")
    return failed


def run_lint(update):
    """lint_md.py on each tests/lint/*.md must print exactly tests/lint/NAME.expected."""
    failed = 0
    for md in sorted((TESTS / "lint").glob("*.md")):
        r = subprocess.run([sys.executable, str(LINT), md.name], cwd=md.parent, capture_output=True, text=True)
        actual = r.stdout + r.stderr
        exp = md.with_suffix(".expected")
        if update or not exp.exists():
            exp.write_text(actual, encoding="utf-8")
            print(f"updated  lint {md.name}")
        elif exp.read_text(encoding="utf-8") == actual:
            print(f"ok       lint {md.name}")
        else:
            failed += 1
            print(f"CHANGED  lint {md.name}\n{diff(exp.read_text(encoding='utf-8'), actual, md.stem + '.expected')}")
    return failed


def run_templates(build):
    """Every types/*/template.md must lint with no findings and, with --build, go through doc.py to a clean PDF."""
    failed = 0
    for tpl in sorted((SKILL / "types").glob("*/template.md")):
        name = tpl.parent.name
        r = subprocess.run([sys.executable, str(LINT), str(tpl)], capture_output=True, text=True)
        ok = r.returncode == 0 and r.stdout.strip().endswith("0 error(s), 0 warning(s)")
        if ok and build:
            with tempfile.TemporaryDirectory() as tmp:
                md = Path(tmp) / f"{name}.md"
                md.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")
                b = subprocess.run([sys.executable, str(DOC), "build", str(md)], capture_output=True, text=True)
                ok = b.returncode == 0 and "Log clean" in b.stdout
                r = b
        print(f"{'ok' if ok else 'FAILED':8} template {name}{' (built)' if build and ok else ''}")
        if not ok:
            print("  " + (r.stdout + r.stderr).strip().replace("\n", "\n  "))
        failed += not ok
    return failed


def run_commands_add():
    """commands.py add, on a scratch copy of the skill: adds, refuses a taken name, rolls back a broken definition."""
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        skill = Path(tmp) / "skill"
        shutil.copytree(SKILL, skill, ignore=shutil.ignore_patterns(".git", "__pycache__", "tests"))
        tool = [sys.executable, str(skill / "scripts" / "commands.py")]
        pre = skill / "types" / "past-paper" / "preamble.tex"

        def add(name, latex):
            return subprocess.run(tool + ["add", name, "--kind", "command", "--level", "type", "--type", "past-paper",
                                          "--latex", latex, "--args", "text", "--markdown", "span", "--use", "test"],
                                  capture_output=True, text=True)
        checks = []
        r = add("marksnote", r"\newcommand{\marksnote}[1]{\hfill\textit{#1}}")
        checks.append(("adds a new command", r.returncode == 0 and "\\marksnote" in pre.read_text()
                       and "marksnote:" in (skill / "types" / "past-paper" / "commands.yaml").read_text()))
        r = add("marksnote", r"\newcommand{\marksnote}[1]{#1}")
        checks.append(("refuses a registered name", r.returncode != 0 and "taken" in r.stdout + r.stderr))
        r = add("section", r"\newcommand{\section}[1]{#1}")
        checks.append(("refuses a LaTeX name", r.returncode != 0 and "LaTeX or a loaded package" in r.stdout + r.stderr))
        before = pre.read_text()
        r = add("brokencmd", r"\newcommand{\brokencmd}[1]{\undefinedmacro{#1}}")
        checks.append(("rolls back a definition that does not compile", r.returncode != 0 and pre.read_text() == before))
        for what, ok in checks:
            print(f"{'ok' if ok else 'FAILED':8} commands.py add: {what}")
            failed += not ok
    return failed


def build_one(body, flags, label, has=(), lacks=(), grey=False):
    """Compile body; the log must be clean, and the PDF text must contain every `has` and no `lacks` string.
    grey: no rendered page may hold colour (the --print copy)."""
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(BUILD), str(body), "--out", f"{tmp}/t.pdf",
                            "--build-dir", f"{tmp}/b", *flags], capture_output=True, text=True)
        problems = [] if r.returncode == 0 and "Log clean" in r.stdout else [(r.stdout + r.stderr).strip()]
        if not problems and (has or lacks):
            text = subprocess.run(["pdftotext", f"{tmp}/t.pdf", "-"], capture_output=True, text=True).stdout
            problems += [f"PDF text lacks {s!r}" for s in has if s not in text]
            problems += [f"PDF text has {s!r}" for s in lacks if s in text]
        if not problems and grey:
            problems += colour_pages(f"{tmp}/t.pdf", tmp)
        print(f"{'ok' if not problems else 'FAILED':8} build {label}")
        for p in problems:
            print("  " + p.replace("\n", "\n  "))
        return 1 if problems else 0


def colour_pages(pdf, tmp):
    import numpy as np
    from PIL import Image
    subprocess.run(["pdftoppm", "-r", "40", "-png", pdf, f"{tmp}/pg"], check=True)
    bad = []
    for png in sorted(Path(tmp).glob("pg-*.png")):
        px = np.asarray(Image.open(png).convert("RGB")).astype(int)
        if ((px.max(2) - px.min(2)) > 12).sum() > 5:
            bad.append(png.stem)
    return [f"colour left on {', '.join(bad)}"] if bad else []


def share_problems(pdf, pages):
    """What is wrong with a share copy: printing must be locked, every page must carry the print-only stamp on one
    layer that is off on screen and on in print, and the footer line must be on the pages with a footer."""
    from pypdf import PdfReader
    from pypdf.constants import UserAccessPermissions as P
    r = PdfReader(pdf)
    if not r.is_encrypted:
        return ["not locked"]
    r.decrypt("")
    problems = [] if not r.user_access_permissions & P.PRINT else ["printing is allowed"]
    oc = r.trailer["/Root"].get("/OCProperties")
    ocgs = [g.get_object() for g in oc["/OCGs"].get_object()] if oc else []
    if [str(g["/Name"]) for g in ocgs] != ["Print stamp"]:
        return problems + [f"expected one layer 'Print stamp', found {[str(g['/Name']) for g in ocgs]}"]
    usage = ocgs[0].get("/Usage", {})
    if str(usage.get("/Print", {}).get("/PrintState")) != "/ON" or str(usage.get("/View", {}).get("/ViewState")) != "/OFF":
        problems.append("the stamp layer is not view: off, print: on")
    if oc["/OCGs"].get_object()[0].idnum not in [g.idnum for g in oc["/D"].get_object().get("/OFF", [])]:
        problems.append("the stamp layer starts visible on screen")
    stamped = sum(c is not None and b"/OC" in c.get_data() for c in (pg.get_contents() for pg in r.pages))
    if stamped != len(r.pages):
        problems.append(f"the stamp is on {stamped} of {len(r.pages)} pages")
    footer = sum("Free shared copy" in (pg.extract_text() or "") for pg in r.pages)
    if footer < pages:
        problems.append(f"the footer line is on {footer} pages, expected at least {pages}")
    return problems


def run_share():
    """--share: the example and a pack of two share copies are locked, stamped on one layer, and carry the footer line."""
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for name in ("a", "b"):
            subprocess.run([sys.executable, str(BUILD), str(SKILL / "examples" / "example-body.tex"),
                            "--out", str(tmp / f"{name}_share.pdf"), "--share"], capture_output=True, text=True)
        (tmp / "pack.yaml").write_text('title: "Test Pack"\ncourse_code: "VLSI"\nparts:\n  - pdf: a.pdf\n  - pdf: b.pdf\n',
                                       encoding="utf-8")
        r = subprocess.run([sys.executable, str(DOC), "bundle", str(tmp / "pack.yaml"), "--share"], capture_output=True, text=True)
        for label, pdf, pages in (("build example-body --share", tmp / "a_share.pdf", 1),
                                  ("bundle --share", tmp / "pack_share.pdf", 2)):
            problems = share_problems(pdf, pages) if pdf.exists() else [f"not built\n{r.stdout[-600:]}{r.stderr[-600:]}"]
            print(f"{'ok' if not problems else 'FAILED':8} {label}")
            for p in problems:
                print("  " + p)
            failed += bool(problems)
    return failed


def run_figures_bw():
    """figures_bw.to_bw: two coloured curves get different dashes, legend samples follow, nothing stays coloured."""
    sys.path.insert(0, str(SKILL / "scripts"))
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.colors import to_rgb
    import figures_bw
    fig, ax = plt.subplots()
    x = [i / 10 for i in range(20)]
    a, = ax.plot(x, x, color="#1f5fa8", label="blue")
    b, = ax.plot(x, [1 - v for v in x], color="#d9730d", label="orange")
    ax.annotate("", xy=(1, 1), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color="red"))
    band = ax.fill_between([0, 1], 0, 0.5, color="#9fbfe6", ec="#1f5fa8", hatch="++")   # a hatch keeps its edge colour
    ax.legend()
    figures_bw.to_bw(fig)
    legend = ax.get_legend().get_lines()
    grey = all(max(to_rgb(c)) - min(to_rgb(c)) < 1e-6 for c in (a.get_color(), b.get_color()))
    arrow = ax.texts[0].arrow_patch.get_edgecolor()
    checks = [("curves get different dashes", a.get_linestyle() != b.get_linestyle()),
              ("legend samples match their curves", [l.get_linestyle() for l in legend] == [a.get_linestyle(), b.get_linestyle()]),
              ("curves and arrows are grey", grey and max(arrow[:3]) - min(arrow[:3]) < 1e-6)]
    if hasattr(band, "get_hatchcolor"):
        import numpy as np
        h = np.atleast_2d(band.get_hatchcolor())[0]
        checks.append(("hatching is grey", max(h[:3]) - min(h[:3]) < 1e-6))
    plt.close(fig)
    for what, ok in checks:
        print(f"{'ok' if ok else 'FAILED':8} figures_bw: {what}")
    return sum(not ok for _, ok in checks)


def run_builds(cases):
    failed = build_one(SKILL / "examples" / "example-body.tex", [], "example-body")
    failed += build_one(SKILL / "examples" / "example-body.tex", ["--print"], "example-body --print", grey=True)
    failed += run_share()
    failed += run_figures_bw()
    for case in cases:
        if case.get("build", True):
            body = FIXTURES / f".{case['name']}.tex"   # beside the fixture, so figures/ resolves
            side = body.with_suffix(".build.json")
            body.write_text((EXPECTED / f"{case['name']}.tex").read_text(encoding="utf-8"), encoding="utf-8")
            if (EXPECTED / f"{case['name']}.build.json").exists():
                side.write_text((EXPECTED / f"{case['name']}.build.json").read_text(encoding="utf-8"), encoding="utf-8")
            try:
                failed += build_one(body, case.get("build_flags", []), case["name"],
                                    case.get("pdf_has", []), case.get("pdf_lacks", []))
                if case.get("print"):   # the black-and-white copy must hold no colour
                    failed += build_one(body, [*case.get("build_flags", []), "--print"], case["name"] + " --print",
                                        grey=True)
            finally:
                body.unlink(missing_ok=True)
                side.unlink(missing_ok=True)
    return failed


def run_print_layout():
    """Print copies of a document with a cover: page 2 is the back of the cover (or blank), the back cover is the
    last page and gives the PDF's whole page count, and the page count is even (a multiple of 4 for a booklet); without a back cover, still even."""
    failed = 0
    body = FIXTURES / ".print-layout.tex"
    side = body.with_suffix(".build.json")
    body.write_text((EXPECTED / "front-matter.tex").read_text(encoding="utf-8"), encoding="utf-8")
    side.write_text((EXPECTED / "front-matter.build.json").read_text(encoding="utf-8"), encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for flags, group, back in (([], 2, True), (["--print-layout", "booklet"], 4, True), (["--no-back-cover"], 2, False)):
                out = Path(tmp) / "p.pdf"
                r = subprocess.run([sys.executable, str(BUILD), str(body), "--out", str(out), "--print", *flags],
                                   capture_output=True, text=True)
                name = "print layout " + (" ".join(flags) or "duplex")
                if r.returncode or not out.exists():
                    failed += 1
                    print(f"FAILED   {name}: build failed\n{r.stdout[-800:]}")
                    continue
                info = subprocess.run(["pdfinfo", str(out)], capture_output=True, text=True).stdout
                pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
                last = subprocess.run(["pdftotext", "-f", str(pages), "-l", str(pages), str(out), "-"],
                                      capture_output=True, text=True).stdout
                problems = []
                if pages % group:
                    problems.append(f"{pages} pages, not a multiple of {group}")
                if back != ("ABOUT THIS DOCUMENT" in last):
                    problems.append("the back cover is not the last page" if back else "a back cover was added")
                said = [int(n) for n in re.findall(r"(\d+)\s+pages", last)]
                if back and said != [pages]:
                    problems.append(f"the back cover says {said} pages, the PDF has {pages}")
                print(f"{'ok' if not problems else 'FAILED':8} {name} ({pages} pages)")
                for p in problems:
                    print("  " + p)
                failed += bool(problems)
    finally:
        body.unlink(missing_ok=True)
        side.unlink(missing_ok=True)
    return failed


def run_edge_tabs():
    """Edge tabs: every chip is a link over its whole area (not only its number) to a destination that exists."""
    import logging
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    body = FIXTURES / ".edge-tabs.tex"
    side = body.with_suffix(".build.json")
    body.write_text((EXPECTED / "front-matter.tex").read_text(encoding="utf-8"), encoding="utf-8")
    side.write_text((EXPECTED / "front-matter.build.json").read_text(encoding="utf-8"), encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "t.pdf"
            r = subprocess.run([sys.executable, str(BUILD), str(body), "--out", str(out), "--edge-tabs"],
                               capture_output=True, text=True)
            if r.returncode or not out.exists():
                print(f"FAILED   edge tabs: build failed\n{r.stdout[-800:]}")
                return 1
            pdf = PdfReader(out)
            names, problems, chips = pdf.named_destinations, [], 0
            width = float(pdf.pages[0].mediabox.width)
            for page in pdf.pages:
                for annot in page.get("/Annots", []) or []:
                    annot = annot.get_object()
                    x0, y0, x1, y1 = (float(v) for v in annot["/Rect"])
                    if x1 < width - 1:
                        continue
                    chips += 1
                    target = str(annot["/A"].get_object().get("/D"))
                    if x1 - x0 < 10 or y1 - y0 < 25:
                        problems.append(f"a chip link of {x1 - x0:.0f}x{y1 - y0:.0f}pt covers only part of the chip")
                    if target not in names:
                        problems.append(f"a chip links to a missing destination {target}")
            if not chips:
                problems.append("no edge-tab links found")
            print(f"{'ok' if not problems else 'FAILED':8} edge tabs ({chips} chip links)")
            for p in sorted(set(problems))[:5]:
                print("  " + p)
            return bool(problems)
    finally:
        body.unlink(missing_ok=True)
        side.unlink(missing_ok=True)


def run_bundle():
    """doc.py bundle: two built PDFs become one pack with its own cover and "In this pack" page (both linking to
    each part), and in print one
    back cover; the parts' own back covers are left out, every link still resolves, and the print pack starts each part on an
    odd page and has an even page count."""
    import logging
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for case in ("front-matter", "core-elements"):
            body = FIXTURES / f".bundle-{case}.tex"
            side = body.with_suffix(".build.json")
            body.write_text((EXPECTED / f"{case}.tex").read_text(encoding="utf-8"), encoding="utf-8")
            if (EXPECTED / f"{case}.build.json").exists():
                side.write_text((EXPECTED / f"{case}.build.json").read_text(encoding="utf-8"), encoding="utf-8")
            try:
                for extra, name in (([], f"{case}.pdf"), (["--print"], f"{case}_print.pdf")):
                    subprocess.run([sys.executable, str(BUILD), str(body), "--out", str(tmp / name), *extra],
                                   capture_output=True, text=True)
            finally:
                body.unlink(missing_ok=True)
                side.unlink(missing_ok=True)
        (tmp / "pack.yaml").write_text('title: "Test Pack"\ncourse_code: "VLSI"\nparts:\n'
                                       '  - pdf: front-matter.pdf\n    title: "Report"\n'
                                       '  - pdf: core-elements.pdf\n    title: "Core"\n', encoding="utf-8")
        for extra in ([], ["--print"]):
            name = "bundle" + (" --print" if extra else "")
            r = subprocess.run([sys.executable, str(DOC), "bundle", str(tmp / "pack.yaml"), *extra], capture_output=True, text=True)
            out = tmp / ("pack_print.pdf" if extra else "pack.pdf")
            if r.returncode or not out.exists():
                failed += 1
                print(f"FAILED   {name}\n{r.stdout[-600:]}{r.stderr[-600:]}")
                continue
            pdf = PdfReader(out)
            names, problems = pdf.named_destinations, []
            pages = {pg.indirect_reference.idnum for pg in pdf.pages}
            links = 0
            for k, page in enumerate(pdf.pages):
                for annot in page.get("/Annots", []) or []:
                    act = annot.get_object().get("/A")
                    act = act.get_object() if act else {}
                    if act.get("/S") != "/GoTo":
                        continue
                    links += k >= 2   # the parts' links (pages 1-2 are the pack's own)
                    d = act.get("/D")
                    if isinstance(d, list) and d[0].idnum not in pages or not isinstance(d, list) and str(d) not in names:
                        problems.append(f"broken link to {d}")
            # every link of the parts is in the pack (a part's own back cover is left out, with its links)
            own = 0
            for part in ("front-matter", "core-elements"):
                src = PdfReader(tmp / (f"{part}_print.pdf" if extra else f"{part}.pdf"))
                for pg in src.pages[:-1] if extra else src.pages:
                    own += sum(1 for x in pg.get("/Annots", []) or [] if (x.get_object().get("/A") or {}).get("/S") == "/GoTo")
            if links < own:
                problems.append(f"the pack has {links} links in its parts, the parts have {own}")
            text = [re.sub(r"\s", "", p.extract_text() or "").upper() for p in pdf.pages]   # labels are letter-spaced
            backs = sum("ABOUTTHISDOCUMENT" in t or "ABOUTTHISPACK" in t for t in text)
            if extra and (backs != 1 or "ABOUTTHISPACK" not in text[-1]):
                problems.append("expected exactly one back cover, the pack's own, as the last page")
            if not extra and backs:
                problems.append("the screen pack has a back cover (it belongs to the print pack only)")
            said = [int(n) for n in re.findall(r"(\d+)PAGES", text[-1])] if extra else []
            if extra and (not said or max(said) != len(pdf.pages)):   # the largest number is the whole pack's
                problems.append(f"the back cover says {said} pages, the pack has {len(pdf.pages)}")
            if "INTHISPACK" not in text[1]:
                problems.append("page 2 is not the In this pack page")
            for k, what in ((0, "cover"), (1, "In this pack page")):   # each part's card or heading is a link
                annots = pdf.pages[k].get("/Annots")
                targets = {str(a.get_object()["/A"].get_object().get("/D")) for a in (annots.get_object() if annots else [])
                           if a.get_object().get("/A")}
                if not {"p0-bundle-part-1", "p0-bundle-part-2"} <= targets:
                    problems.append(f"the {what} does not link to both parts")
            if [o.title for o in pdf.outline if not isinstance(o, list)] != ["Report", "Core"]:
                problems.append("bookmarks are not one per part")
            starts = [pdf.get_destination_page_number(names[f"p0-bundle-part-{i}"]) + 1 for i in (1, 2)]
            if extra and (len(pdf.pages) % 2 or any(s % 2 == 0 for s in starts)):
                problems.append(f"print pack: {len(pdf.pages)} pages, parts start at {starts}")
            print(f"{'ok' if not problems else 'FAILED':8} {name} ({len(pdf.pages)} pages, parts at {starts})")
            for p in problems[:5]:
                print("  " + p)
            failed += bool(problems)
    return failed


def corpus(entries, folder, mode):
    folder.mkdir(parents=True, exist_ok=True)
    failed = 0
    for entry in entries:
        path, _, flags = entry.partition(":")
        md = Path(path).resolve()
        flags = [f for f in flags.split(",") if f]
        key = md.stem + ".tex"
        with tempfile.TemporaryDirectory(dir=md.parent) as tmp:
            actual = convert(md, Path(tmp) / key, flags)
        snap = folder / key
        if mode == "snapshot":
            snap.write_text(actual, encoding="utf-8")
            print(f"saved    {key}")
        elif not snap.exists():
            failed += 1
            print(f"MISSING  {key} (no snapshot)")
        elif snap.read_text(encoding="utf-8") == actual:
            print(f"ok       {key}")
        else:
            failed += 1
            print(f"CHANGED  {key}\n{diff(snap.read_text(encoding='utf-8'), actual, key)}")
    return failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--snapshot", type=Path)
    ap.add_argument("--compare", type=Path)
    ap.add_argument("corpus", nargs="*")
    a = ap.parse_args()

    if a.snapshot or a.compare:
        failed = corpus(a.corpus, a.snapshot or a.compare, "snapshot" if a.snapshot else "compare")
    else:
        cases = json.loads((TESTS / "cases.json").read_text())
        failed = check_skill() + check_margins() + check_coverdata() + check_mindmap_fit() + run_cases(cases, a.update) + run_lint(a.update) + run_templates(a.build)
        if a.build:
            failed += run_builds(cases) + run_print_layout() + run_edge_tabs() + run_bundle() + run_commands_add()
    print("\nAll passed." if not failed else f"\n{failed} failed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
