#!/usr/bin/env python3
"""
bundle.py -- combine finished PDFs into one pack: one cover, an "In this pack" page, the parts, one back cover.

    python3 bundle.py pack.yaml [--print] [--out pdf/pack.pdf]
    (or: python3 doc.py bundle pack.yaml ...)

pack.yaml (paths are relative to it; the cover fields are raw LaTeX, as in front matter):

    title: "Exam Pack"                     # the pack's cover title
    subtitle: "Session 2021--22"           # optional
    note: "Term final preparation"         # optional
    label: "EXAM PACK"                     # optional, the letter-spaced word above the course code (STUDY PACK)
    course_code: "EEE329"
    course_name: "Basic Communication Engineering"
    accent: 2F5D3A                         # optional, the subject's colour
    date: "October 2026"                   # optional; author: optional
    back_blurb: "..."                      # optional, for the back cover
    back_cover: true                       # optional; false: no back cover
    print_layout: duplex                   # optional, for --print: duplex or booklet
    out: pdf/eee329-exam-pack.pdf          # optional (default: the YAML name, .pdf)
    parts:
      - pdf: pdf/2021-22-term-final.pdf
        title: "Question Paper Solutions 2021--22"
      - pdf: ../level-2/pdf/1-formula-sheet.pdf
        title: "Formula Sheet"
        keep_back_cover: false             # optional: a part's own back cover is left out by default

Build each part first (doc.py build). Each part keeps its own layout, links and bookmarks; its cover stays as
the divider before it. Links from one part into another (a formula sheet's Reference into the theory) become
links inside the pack; the bookmarks show one entry per part with that part's outline under it.

--print uses each part's print copy (NAME_print.pdf beside it) and lays the pack out for double-sided
printing: the "In this pack" page is the back of the cover, every part starts on a right-hand page, and the
back cover is the back of the last sheet (a multiple of 4 pages for print_layout: booklet).
"""
import argparse
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "template"
sys.path.insert(0, str(HERE))
import build as house   # compile_tex, report, tex_escape, spaced_caps

KEYS = {"title", "subtitle", "note", "label", "course_code", "course_name", "accent", "date", "author",
        "back_blurb", "back_cover", "print_layout", "out", "parts"}
PART_KEYS = {"pdf", "title", "keep_back_cover"}
BACK_MARK = "ABOUT THIS DOCUMENT"


def load(path):
    import yaml
    spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    problems = [f"unknown key '{k}' (known: {', '.join(sorted(KEYS))})" for k in spec if k not in KEYS]
    parts = spec.get("parts") or []
    if not parts:
        problems.append("no parts: list the PDFs under 'parts:'")
    for i, p in enumerate(parts, 1):
        if not isinstance(p, dict) or "pdf" not in p:
            problems.append(f"part {i}: give its file as 'pdf: path/to/file.pdf'")
            continue
        problems += [f"part {i}: unknown key '{k}' (known: {', '.join(sorted(PART_KEYS))})" for k in p if k not in PART_KEYS]
    if spec.get("print_layout", "duplex") not in ("duplex", "booklet"):
        problems.append("print_layout must be duplex or booklet")
    if problems:
        sys.exit(f"{path.name}:\n  " + "\n  ".join(problems))
    return spec


def page_text(page):
    try:
        return page.extract_text() or ""
    except Exception:
        return ""


def has_mark(page, mark):
    """True if the page holds this letter-spaced label (text extraction puts spaces between its letters)."""
    return re.sub(r"\s", "", mark) in re.sub(r"\s", "", page_text(page)).upper()


def is_blank(page):
    return not page_text(page).strip() and not page.get("/Annots")


def part_pages(reader, keep_back):
    """Indices of the pages to take: all, less the part's own back cover and the blank pages before it."""
    keep = list(range(len(reader.pages)))
    if not keep_back and keep and has_mark(reader.pages[keep[-1]], BACK_MARK):
        keep.pop()
        while keep and is_blank(reader.pages[keep[-1]]):
            keep.pop()
    return keep


def cover_tex(spec, parts, starts, total, bw):
    """main.tex of the pack's own pages: front cover, "In this pack", back cover (three pages)."""
    esc = lambda s: s if s is not None else ""
    fields = {"CoverCourseCode": esc(spec.get("course_code")), "CoverCourseName": esc(spec.get("course_name")),
              "CoverTitle": esc(spec.get("title")), "CoverSubtitle": esc(spec.get("subtitle")),
              "CoverNote": esc(spec.get("note")), "CoverAuthor": esc(spec.get("author")) or "Nur Mohammad",
              "CoverLabel": esc(spec.get("label")) or "STUDY PACK", "CoverBlurb": esc(spec.get("back_blurb"))}
    fields["CoverSpine"] = "\\quad$\\cdot$\\quad ".join(house.spaced_caps(x) for x in
                                                         (fields["CoverCourseCode"], fields["CoverTitle"], fields["CoverSubtitle"]) if x)
    if spec.get("accent"):
        if not re.fullmatch(r"#?[0-9A-Fa-f]{6}", str(spec["accent"])):
            sys.exit(f"accent: '{spec['accent']}' is not a colour like 5B3A8C")
        fields["CoverAccentHex"] = str(spec["accent"]).lstrip("#").upper()
    if spec.get("date"):
        fields["CoverDate"] = spec["date"]
    items, rows = [], []
    for n, ((title, _r, pages), start) in enumerate(zip(parts, starts), 1):
        rng = f"pages {start}--{start + len(pages) - 1}"
        items.append(f"\\coveritem{{{n}}}{{{title}}}{{{rng}}}")
        rows.append(f"\\packrow{{{n}}}{{{title}}}{{{rng}}}{{{start}}}")
    fields["CoverItems"] = "%\n".join(items)
    fields["CoverBackStats"] = f"\\coverstat{{{len(parts)}}}{{documents}}"
    defs = "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in fields.items())
    bw_line = "\\input{print-bw.tex}" if bw else ""
    pdftitle = re.sub(r"[{}\\$]", "", fields["CoverTitle"])
    rows = "".join(rows)
    return rf"""\documentclass[a4paper, 12pt]{{extarticle}}
\newcommand{{\ReportHeader}}{{}}
\newcommand{{\ReportHeaderRight}}{{}}
{defs}
\input{{main-tex-preamble.tex}}
{bw_line}
\input{{cover-kit.tex}}
\geometry{{left=0.5in, right=0.5in}}
\hypersetup{{pdftitle={{{pdftitle}}}}}
\newcommand{{\packrow}}[4]{{\setpartcolor{{#1}}\noindent\hyperlink{{bundle-part-#1}}{{\begin{{tikzpicture}}[baseline=(c.base)]
	\node[circle, fill=\partcolor, text=white, font=\bfseries, minimum size=0.9cm, inner sep=0pt] (c) at (0,0) {{#1}};
	\node[anchor=west, font=\Large, text=CoverInk, text width=13.2cm, align=left] at (0.75,0.18) {{#2}};
	\node[anchor=west, font=\small\coversans, text=\partcolor!80!black] at (0.75,-0.35) {{#3}};
	\node[anchor=east, font=\Large\bfseries, text=CoverSig] at (17.4,0) {{#4}};
\end{{tikzpicture}}}}\par\vspace{{0.45cm}}}}
\begin{{document}}
\input{{cover-page-main}}
\thispagestyle{{empty}}
\bochead{{IN THIS PACK}}{{{fields["CoverTitle"]}}}
{{\color{{CoverSoft}}Tap a document to open it. Each one keeps its own cover, contents and links; the bookmarks panel lists them all.\par}}
\vspace{{0.8cm}}
{rows}
\docinfo{{{len(parts)} documents, {total} pages.}}
\clearpage
\xdef\HouseContentPages{{{total}}}
\input{{back-cover}}
\end{{document}}
"""


def main():
    ap = argparse.ArgumentParser(description="Combine finished PDFs into one pack (see the module docstring).")
    ap.add_argument("spec", type=Path)
    ap.add_argument("--print", dest="bw", action="store_true", help="use the parts' print copies; lay out for double-sided printing")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import NameObject, TextStringObject
    except ImportError:
        sys.exit("bundle needs pypdf: pip install pypdf (or run scripts/setup.sh)")
    logging.getLogger("pypdf").setLevel(logging.ERROR)   # it warns about every link it re-targets
    spec_path = a.spec.resolve()
    spec = load(spec_path)
    base = spec_path.parent
    out = (a.out or base / (spec.get("out") or spec_path.with_suffix(".pdf").name)).resolve()
    if a.bw and not out.stem.endswith("_print"):
        out = out.with_name(f"{out.stem}_print{out.suffix}")

    parts, names = [], {}
    for i, p in enumerate(spec["parts"], 1):
        pdf = (base / p["pdf"]).resolve()
        if a.bw:
            printed = pdf.with_name(f"{pdf.stem}_print{pdf.suffix}")
            if printed.exists():
                pdf = printed
            else:
                print(f"note: no print copy of {pdf.name} ({printed.name}); using the screen PDF")
        if not pdf.exists():
            sys.exit(f"part {i}: {pdf} not found (build it first: doc.py build ...)")
        reader = PdfReader(pdf)
        pages = part_pages(reader, p.get("keep_back_cover", False))
        title = p.get("title") or pdf.stem
        parts.append((title, reader, pages))
        for n in (pdf.name, pdf.name.replace("_print.pdf", ".pdf")):   # links name the screen PDF
            names[n] = f"p{i}"

    # where each part starts: after the cover and "In this pack" (pages 1-2); in print, on a right-hand page
    starts, page = [], 3
    for _, _, pages in parts:
        if a.bw and page % 2 == 0:
            page += 1
        starts.append(page)
        page += len(pages)
    total = page - 1

    build = out.parent / f"{out.stem}_build"
    shutil.rmtree(build, ignore_errors=True)
    build.mkdir(parents=True)
    for f in ("main-tex-preamble.tex", "cover-kit.tex", "cover-page-main.tex", "back-cover.tex", "print-bw.tex"):
        shutil.copy(TEMPLATE / f, build)
    (build / "main.tex").write_text(cover_tex(spec, parts, starts, total, a.bw), encoding="utf-8")
    ok = house.compile_tex(build)
    house.report(build / "main.log")
    if not ok or not (build / "main.pdf").exists():
        sys.exit(f"BUILD FAILED -- see {build / 'main.log'}")
    own = PdfReader(build / "main.pdf")
    if len(own.pages) != 3:
        sys.exit(f"the pack's own pages came out as {len(own.pages)} pages, not 3 -- see {build / 'main.tex'}")

    def prefix(reader, tag):
        """Rename every named destination of one PDF (and the links and bookmarks that use them) to tag-NAME,
        so two parts can both have sec:intro or toc."""
        root = reader.trailer["/Root"]
        def walk(node):
            node = node.get_object()
            for key in ("/Names", "/Limits"):
                if key in node:
                    arr = node[key]
                    for k in range(0, len(arr), 2 if key == "/Names" else 1):
                        arr[k] = TextStringObject(f"{tag}-{arr[k]}")
            for kid in node.get("/Kids", []):
                walk(kid)
        if "/Names" in root and "/Dests" in root["/Names"]:
            walk(root["/Names"]["/Dests"])
        for pg in reader.pages:
            for annot in pg.get("/Annots", []) or []:
                act = annot.get_object().get("/A")
                if act and act.get_object().get("/S") == "/GoTo" and not isinstance(act.get_object().get("/D"), list):
                    act.get_object()[NameObject("/D")] = TextStringObject(f"{tag}-{act.get_object()['/D']}")
        def outline(item):
            while item is not None:
                item = item.get_object()
                act = item.get("/A")
                if act and act.get_object().get("/S") == "/GoTo" and not isinstance(act.get_object().get("/D"), list):
                    act.get_object()[NameObject("/D")] = TextStringObject(f"{tag}-{act.get_object()['/D']}")
                if isinstance(item.get("/Dest"), str):
                    item[NameObject("/Dest")] = TextStringObject(f"{tag}-{item['/Dest']}")
                if "/First" in item:
                    outline(item["/First"])
                item = item.get("/Next")
        if "/Outlines" in root and "/First" in root["/Outlines"]:
            outline(root["/Outlines"]["/First"])

    w = PdfWriter()
    prefix(own, "p0")
    w.append(own, pages=[0, 1], import_outline=False)
    for i, ((title, reader, pages), start) in enumerate(zip(parts, starts), 1):
        while len(w.pages) + 1 < start:   # print: a blank page so the part starts on a right-hand page
            w.add_blank_page()
        prefix(reader, f"p{i}")
        w.append(reader, outline_item=title, pages=pages)
        w.add_named_destination(f"p0-bundle-part-{i}", start - 1)
    if spec.get("back_cover", True):
        group = 4 if spec.get("print_layout") == "booklet" else 2
        while a.bw and (len(w.pages) + 1) % group:
            w.add_blank_page()
        w.append(own, pages=[2], import_outline=False)
    elif a.bw:
        while len(w.pages) % (4 if spec.get("print_layout") == "booklet" else 2):
            w.add_blank_page()

    # links into another part of the pack become links inside it
    moved = 0
    for pg in w.pages:
        for annot in pg.get("/Annots", []) or []:
            act = annot.get_object().get("/A")
            act = act.get_object() if act else None
            if act and act.get("/S") == "/GoToR" and Path(str(act.get("/F"))).name in names:
                act[NameObject("/S")] = NameObject("/GoTo")
                act[NameObject("/D")] = TextStringObject(f"{names[Path(str(act['/F'])).name]}-{act['/D']}")
                del act["/F"]
                moved += 1
    w.add_metadata({"/Title": re.sub(r"[{}\\$]", "", spec.get("title") or out.stem), "/Author": spec.get("author") or "Nur Mohammad"})
    w.page_mode = "/UseOutlines"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        w.write(f)
    print(f"PDF: {out} ({len(w.pages)} pages, {len(parts)} parts; {moved} links between parts now point inside the pack)")
    print(f"Build folder (the pack's cover pages): {build}")


if __name__ == "__main__":
    main()
