#!/usr/bin/env python3
"""
build.py -- assemble body .tex file(s) with the house preamble and main.tex
template, compile with XeLaTeX, and report problems from the log.

Usage:
    python3 build.py BODY.tex [BODY2.tex ...] --out OUT.pdf
        [--type NAME]                         # load the default flags of types/NAME/type.json (explicit flags win)
    Settings from front matter: BODY.build.json beside the first body (written by md2tex.py) is applied first.
        [--title "Line 1" --title "Line 2"]   # title lines on page 1 (default: body file name)
        [--header "Running header text"]      # left page header (default: titles joined)
        [--header-right "Session 2020--21"]   # text before the TOC button on the right of the header
        [--author "Nur Mohammad"]
        [--class extarticle|extreport]        # default extarticle
        [--fontsize 12pt]                      # 8pt..20pt for ext* classes; default 12pt
        [--margin-x 0.4in]                     # narrower left/right margins for dense sheets (house default .7in)
        [--bangla]                             # Bangla text: body must wrap Bangla runs in \\bn{...} (md2tex --bangla does it)
        [--no-toc]
        [--figures DIR ...]                    # extra image folders (body dir and body_dir/figures are added automatically)
        [--cover]                              # add the bundled study-notes cover page, with:
        [--course-code "COM I"] [--course-name "Communication Engineering I"]
        [--cover-title "Complete Theory"] [--cover-subtitle "Lectures 24--38"] [--cover-note "..."]
        [--cover-contents "Item 1" --cover-contents "Item 2"] [--date "October 2026"]
        [--cover-dir DIR]                      # use your own cover-page-preamble.tex / cover-page-main.tex instead
        [--no-cover]                           # leave out a cover the type adds by default (past-paper)
        [--paper | --no-paper]                 # past papers: the typeset question paper before the contents
        [--paper-header "University" --paper-header "Course Code: ..."] [--paper-info "Total Marks: 100" ...]
        [--paper-instruction "[Answer any ...]"] [--paper-part "Part-A: 1-3"] [--paper-appendix equations.tex]
        [--build-dir DIR]                      # default: <OUT stem>_build next to OUT
        [--print]                              # black-and-white copy for printing (template/print-bw.tex):
                                               # uses figures/print/NAME for each image that has one, greys the rest

Exit code 0 = PDF built (warnings may still be printed). 1 = compile failed.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import doctype
import json

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / "template"


# Bangla font: Noto Serif Bengali (Linux/Claude), else Nirmala UI or Vrinda (Windows/MikTeX).
# Each Bangla run is wrapped as \bn{...}; Latin text, maths and terms stay in the house font.
BANGLA = r"""\IfFontExistsTF{Noto Serif Bengali}{\newfontfamily\bengalifont{Noto Serif Bengali}[Script=Bengali, AutoFakeSlant=0.15]}{%
  \IfFontExistsTF{Nirmala UI}{\newfontfamily\bengalifont{Nirmala UI}[Script=Bengali, AutoFakeSlant=0.15]}{%
    \newfontfamily\bengalifont{Vrinda}[Script=Bengali, AutoFakeSlant=0.15]}}
\DeclareRobustCommand{\bn}[1]{{\bengalifont #1}}
\AtBeginDocument{\pdfstringdefDisableCommands{\def\bn#1{#1}}}
% Bangla words cannot be hyphenated and English terms carry Bangla suffixes ("transmitter-এর"),
% so give TeX room to loosen a line instead of letting it overflow
\setlength{\emergencystretch}{3em}"""


BN_RUN = re.compile("[\u0980-\u09FF\u0964\u0965\u200C\u200D]+(?:[ ,;:!?']+[\u0980-\u09FF\u0964\u0965\u200C\u200D]+)*")


def bn_wrap(text):
    return BN_RUN.sub(lambda m: "\\bn{" + m.group(0) + "}", text)


def tex_escape(text):
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}")]:
        text = text.replace(a, b) if a != "\\" else text.replace(a, "\x00")
    return text.replace("\x00", r"\textbackslash{}")


def safe_stem(path, used):
    stem = re.sub(r"[^A-Za-z0-9-]", "-", path.stem).strip("-") or "body"
    name, i = stem, 2
    while name in used:
        name, i = f"{stem}-{i}", i + 1
    used.add(name)
    return name


def compile_tex(build):
    if shutil.which("latexmk"):
        cmd = ["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "main.tex"]
        ok = subprocess.run(cmd, cwd=build, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    else:
        ok = True
        for _ in range(3):  # TOC + cleveref need several passes
            r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "main.tex"],
                               cwd=build, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r.returncode:
                ok = False
                break
    return ok


def report(log_path):
    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    errors = re.findall(r"^(?:\./)?[^\s:]+\.tex:\d+: .*$|^! .*$", log, re.M)
    undef = sorted(set(re.findall(r"(?:Reference|Citation) `([^']+)' .*undefined", log)))
    missing = sorted(set(re.findall(r"Missing character: There is no (\S+)", log)))
    overfull = [float(x) for x in re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide", log)]
    big = [x for x in overfull if x > 10]
    lines = []
    if errors:
        lines.append("ERRORS:\n  " + "\n  ".join(dict.fromkeys(errors)))
    if undef:
        lines.append("Undefined references: " + ", ".join(undef))
    if missing:
        lines.append("Missing glyphs (character not in font, will be blank): " + " ".join(missing))
    if big:
        lines.append(f"Overfull lines > 10pt: {len(big)} (largest {max(big):.0f}pt) -- check wide tables/equations/URLs")
    print("\n".join(lines) if lines else "Log clean: no errors, undefined references, missing glyphs or big overfull lines.")


# ---------- --print: black-and-white copy ----------
GRAPHIC = re.compile(r"(\\includegraphics\s*(?:\[[^\]]*\])?\s*\{)([^}]+)(\})")
COLOUR_WORD = re.compile(r"\b(red|blue|green|orange|purple|violet|yellow|pink|magenta|cyan|teal|brown)\b", re.I)
STYLE_WORD = re.compile(r"\b(?:solid|dash\w*|dott\w*|thick(?:er)?|thin(?:ner)?|bold|gr[ae]y|black|white|hatch\w*|shaded|"
                        r"filled|labell?ed|markers?|dots?|arrows?|circles?|squares?|triangles?|diamonds?)\b", re.I)
LATEX_COLOUR = re.compile(r"\\(?:color|textcolor|rowcolor|cellcolor|colorbox|definecolor|colorlet)\b(?:\[[^\]]*\])?"
                          r"(?:\{[^}]*\})*|\[[^\]]*\]")


def print_figures(tex, body_dir, gdirs, store):
    """Point each image at its print copy: DIR/print/NAME when the figure script made one, else a greyscale
    copy made here. Returns the new text and the counts (print copies, greyed here, left as is)."""
    used, greyed, kept = 0, [], []

    def find(path):
        for d in [body_dir, *gdirs]:
            for cand in (d / path, *(d / f"{path}{e}" for e in (".png", ".jpg", ".jpeg", ".pdf"))):
                if cand.is_file():
                    return cand.resolve()
        return None

    def swap(m):
        nonlocal used
        src = find(m.group(2).strip())
        if src is None:
            return m.group(0)
        bw = src.parent / "print" / src.name
        if bw.is_file():
            used += 1
            return m.group(1) + bw.as_posix() + m.group(3)
        if src.suffix.lower() in (".png", ".jpg", ".jpeg"):
            try:
                from PIL import Image
            except ImportError:
                kept.append(src.name)
                return m.group(0)
            store.mkdir(exist_ok=True)
            out = store / f"{len(greyed):02d}-{src.name}"
            Image.open(src).convert("L").save(out)
            greyed.append(src.name)
            return m.group(1) + out.as_posix() + m.group(3)
        kept.append(src.name)
        return m.group(0)

    return GRAPHIC.sub(swap, tex), used, greyed, kept


def colour_only(tex, name):
    """Sentences that point at something by colour alone ("the red curve"): they lose their meaning in print."""
    hits = []
    for n, line in enumerate(tex.splitlines(), 1):
        if line.lstrip().startswith("%"):
            continue
        for sentence in re.split(r"(?<=[.:])\s+", LATEX_COLOUR.sub(" ", line)):
            if COLOUR_WORD.search(sentence) and not STYLE_WORD.search(sentence):
                hits.append(f"{name}:{n}: {sentence.strip()[:110]}")
    return hits


REPEATED = ("--title", "--cover-contents", "--paper-header", "--paper-info", "--paper-part")   # options that collect values; the user's replace the sidecar's


def question_marks(bodies):
    """Past papers: 'N/marks' for each mainquestion box, comma-separated, for the cover's question map.

    The marks are the sum of every [Marks: ...] in the box ('5+7' counts 12); a box without marks gives 'N/'.
    """
    out = []
    for body in bodies:
        for box in re.findall(r"\\begin\{mainquestion\}(.*?)\\end\{mainquestion\}", body.read_text(encoding="utf-8"), re.S):
            nums = [float(x) for m in re.findall(r"Marks:\s*([0-9.+\s]+)", box) for x in re.findall(r"[0-9.]+", m)]
            total = f"{sum(nums):g}" if nums else ""
            out.append(f"{len(out) + 1}/{total}")
    return ",".join(out)


MQ = re.compile(r"\\begin\{mainquestion\}\n?(.*?)\\end\{mainquestion\}", re.S)
QB = re.compile(r"\\begin\{questionblock\}(\[[^\]]*\])?\{(\d+)\.\s*\(([a-z]+)\)")


def paper_page(a, copies):
    """Past papers: the question paper typeset like the original, from the mainquestion boxes of the bodies.

    Each sub-part label links to its solution (a target is added before each questionblock), and each
    mainquestion box sets the header's PAPER button to its question on the paper. Returns the page's
    LaTeX, or "" when the bodies have no mainquestion box.
    """
    def num(box, n):
        m = re.search(r"\\item\[(\d+)\.", box)
        return m.group(1) if m else str(n)

    texts, targets, boxes = [], set(), []
    for copy in copies:
        tex = copy.read_text(encoding="utf-8")
        targets |= {f"{q}{p}" for _, q, p in QB.findall(tex)}
        tex = QB.sub(lambda m: f"\\hypertarget{{sol-{m.group(2)}{m.group(3)}}}{{}}\n" + m.group(0), tex)
        def mark(m):
            boxes.append(m.group(1))
            return f"\\begin{{mainquestion}}\\papersetq{{{num(m.group(1), len(boxes))}}}\n{m.group(1)}\\end{{mainquestion}}"
        tex = MQ.sub(mark, tex)
        copy.write_text(tex, encoding="utf-8")
    if not boxes:
        return ""

    parts = {}
    for p in a.paper_part:
        name, _, rng = p.rpartition(":")
        first = re.match(r"\s*(\d+)", rng)
        if name.strip() and first:
            parts[first.group(1)] = name.strip()

    def figure(m):   # unnumbered, so the solutions keep their figure numbers; no label, so none is defined twice
        body = re.sub(r"\\label\{[^}]*\}|\\centering", "", m.group(1))
        body = re.sub(r"width=([0-9.]*)\\(linewidth|textwidth)",   # smaller than in the solutions, as on a paper
                      lambda w: f"width={0.6 * float(w.group(1) or 1):.2f}\\linewidth", body)
        cap = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", body)
        body = body.replace(cap.group(0), "") if cap else body
        return ("\\begin{center}" + body.strip() + (f"\\\\[2pt]{{\\small {cap.group(1)}}}" if cap else "")
                + "\\end{center}")

    out = []
    for i, box in enumerate(boxes, 1):
        q = num(box, i)
        if q in parts:
            out.append(f"\\paperpart{{{parts[q]}}}")
        box = re.sub(r"\\begin\{figure\}(?:\[[^\]]*\])?(.*?)\\end\{figure\}", figure, box, flags=re.S)
        box = re.sub(r"\\label\{[^}]*\}", "", box)
        box = re.sub(r"\\hfill Marks: ([^\n]+?)\s*$", r"\\papermarks{\1}", box, flags=re.M)
        box = re.sub(r"\{\[\}Marks: ([^{]+?)\{\]\}", r"\\papermarks{\1}", box)
        lines, depth, cur = [], 0, None
        for line in box.split("\n"):   # link each sub-part (label and text) to its solution
            depth += line.count("\\begin{itemize}") + line.count("\\begin{enumerate}")
            m = re.match(r"(\s*)\\item\[((?:\d+\.\s*)?\(([a-z]+)\))\]", line)
            if m and depth == 1:
                cur = f"sol-{q}{m.group(3)}" if f"{q}{m.group(3)}" in targets else None
                if cur:
                    line = line.replace(m.group(0), f"{m.group(1)}\\item[\\paperlink{{{cur}}}{{{m.group(2)}}}]", 1)
            t = re.match(r"(\s*\\item\[.*?\]\]?\s*)(.*?)(\s*\\papermarks\{[^}]*\})?$", line)
            if cur and t and t.group(2).strip():   # the text of the sub-part, or of its (i), (ii) items
                line = t.group(1) + f"\\paperqlink{{{cur}}}{{{t.group(2)}}}" + (t.group(3) or "")
            depth -= line.count("\\end{itemize}") + line.count("\\end{enumerate}")
            lines.append(line)
        out.append(f"\\paperquestion{{{q}}}\n" + "\n".join(lines))
    header = "\n".join(f"\\paperheaderline{{{h}}}" for h in a.paper_header) or f"\\paperheaderline{{{tex_escape(' '.join(a.title or ['Question Paper']))}}}"
    info = "\\paperinfo{" + "}{".join(a.paper_info) + "}" if a.paper_info else ""
    instr = f"\\paperinstruction{{{a.paper_instruction}}}" if a.paper_instruction else ""
    appendix = ""
    if a.paper_appendix:
        if not a.paper_appendix.exists():
            sys.exit(f"missing paper appendix: {a.paper_appendix}")
        appendix = "\\paperappendix\n" + a.paper_appendix.read_text(encoding="utf-8")
    return ("\\begin{questionpaper}\n" + header + "\n" + info + "\n" + instr + "\n\\begin{paperquestions}\n"
            + "\n\n".join(out) + "\n\\end{paperquestions}\n" + appendix + "\n\\end{questionpaper}\n")


def with_sidecar(argv):
    """Put the first body's NAME.build.json settings (written by md2tex.py from front matter) before argv."""
    body = next((Path(x) for x in argv[1:] if x.endswith(".tex")), None)
    sidecar = body.with_suffix(".build.json") if body else None
    if not sidecar or not sidecar.exists():
        return argv
    saved = json.loads(sidecar.read_text(encoding="utf-8")).get("build", [])
    for item in saved:   # paths in the sidecar are relative to it
        if item[0] in ("--type-preamble", "--paper-appendix"):
            item[1] = str((sidecar.parent / item[1]).resolve())
    kept = [x for item in saved if not (item[0] in REPEATED and item[0] in argv) for x in item]
    print(f"settings from {sidecar.name}: {' '.join(kept)}")
    return [argv[0], *kept, *argv[1:]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bodies", nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--title", action="append", default=[])
    ap.add_argument("--header")
    ap.add_argument("--header-right", default="")
    ap.add_argument("--type-preamble", action="append", default=[], type=Path)
    ap.add_argument("--author", default="Nur Mohammad")
    ap.add_argument("--class", dest="cls", default="extarticle", choices=["extarticle", "extreport"])
    ap.add_argument("--fontsize", default="12pt")
    ap.add_argument("--no-toc", action="store_true")
    ap.add_argument("--margin-x")
    ap.add_argument("--bangla", action="store_true")
    ap.add_argument("--figures", nargs="*", default=[], type=Path)
    ap.add_argument("--cover", action="store_true")
    ap.add_argument("--no-cover", dest="cover", action="store_false")
    ap.add_argument("--type-cover-dir", type=Path)
    ap.add_argument("--paper", action="store_true")
    ap.add_argument("--no-paper", dest="paper", action="store_false")
    ap.add_argument("--paper-header", action="append", default=[])
    ap.add_argument("--paper-info", action="append", default=[])
    ap.add_argument("--paper-instruction", default="")
    ap.add_argument("--paper-part", action="append", default=[])
    ap.add_argument("--paper-appendix", type=Path)
    ap.add_argument("--course-code", default="")
    ap.add_argument("--course-name", default="")
    ap.add_argument("--cover-title")
    ap.add_argument("--cover-subtitle", default="")
    ap.add_argument("--cover-note", default="")
    ap.add_argument("--cover-contents", action="append", default=[])
    ap.add_argument("--date")
    ap.add_argument("--cover-dir", type=Path)
    ap.add_argument("--build-dir", type=Path)
    ap.add_argument("--print", dest="bw", action="store_true")
    a = ap.parse_args(doctype.expand(with_sidecar(sys.argv), "build")[1:])

    out = a.out.resolve()
    build = (a.build_dir or out.parent / f"{out.stem}_build").resolve()
    build.mkdir(parents=True, exist_ok=True)
    shutil.copy(TEMPLATE / "main-tex-preamble.tex", build)
    type_inputs = []
    for old in [*build.glob("type-*-preamble.tex"), *build.glob("pre-doc-*.tex")]:
        old.unlink()
    for tp in dict.fromkeys(p.resolve() for p in a.type_preamble):
        name = f"type-{tp.parent.name}-preamble.tex" if tp.name == "preamble.tex" else f"pre-doc-{tp.name}"
        shutil.copy(tp, build / name)
        type_inputs.append(f"\\input{{{name}}}")
    (build / "print-bw.tex").unlink(missing_ok=True)
    if a.bw:   # last, so it recolours the type's own commands too
        shutil.copy(TEMPLATE / "print-bw.tex", build)
        type_inputs.append("\\input{print-bw.tex}")
    for f in ("cover-page-preamble.tex", "cover-page-main.tex"):
        (build / f).unlink(missing_ok=True)
        src = (a.cover_dir / f) if a.cover_dir else ((a.type_cover_dir or TEMPLATE) / f if a.cover else None)
        if src and src.exists():
            shutil.copy(src, build)

    used, includes, gdirs = set(), [], []
    bodies = []
    for body in a.bodies:
        body = body.resolve()
        if not body.exists():
            sys.exit(f"missing body file: {body}")
        name = safe_stem(body, used)
        shutil.copy(body, build / f"{name}.tex")
        includes.append(f"\\include{{{name}}}")
        bodies.append((body, build / f"{name}.tex"))
        gdirs += [body.parent, body.parent / "figures"]
    gdirs += [d.resolve() for d in a.figures]
    gdirs = [d for d in dict.fromkeys(gdirs) if d.is_dir()]
    if a.bw:
        store = build / "print-figures"
        shutil.rmtree(store, ignore_errors=True)
        used_bw, greyed, kept, words = 0, [], [], []
        for body, copy in bodies:
            tex, n, g, k = print_figures(copy.read_text(encoding="utf-8"), body.parent, gdirs, store)
            copy.write_text(tex, encoding="utf-8")
            used_bw, greyed, kept = used_bw + n, greyed + g, kept + k
            words += colour_only(tex, body.name)
        print(f"print: {used_bw} figure(s) from print/ copies, {len(greyed)} greyed here"
              + (f", {len(kept)} left in colour: {', '.join(kept)}" if kept else ""))
        if greyed:
            print("  greyed here (curves told apart only by colour may merge; make print/ copies with "
                  "scripts/figures_bw.py): " + ", ".join(greyed))
        if words:
            print("  text naming a colour without a line style or shape (reads wrongly in print):\n    "
                  + "\n    ".join(words))
    paper = paper_page(a, [c for _, c in bodies]) if a.paper else ""
    (build / "paper-page.tex").unlink(missing_ok=True)
    if paper:
        (build / "paper-page.tex").write_text(paper, encoding="utf-8")
    elif a.paper:
        print("note: --paper given, but the bodies have no mainquestion box; no question paper added")
    if any(" " in str(d) for d in gdirs):
        print("warning: an image folder path contains spaces; XeLaTeX may not find images there")
    graphicspath = "{figures/}" + "".join(f"{{{d.as_posix()}/}}" for d in gdirs)

    titles = a.title or [a.bodies[0].stem]
    title_lines = " \\\\[0.1cm]\n".join(f"\t{{\\LARGE{{\\keyterm{{{tex_escape(t)}}}}}}}" for t in titles)
    # default running header: the first title line only (both lines together wrap), without its trailing colon
    header = tex_escape(a.header) if a.header else tex_escape(titles[0].rstrip().rstrip(":"))
    toc = "" if a.no_toc else ("\\begingroup\n\\setstretch{1}\n\\phantomsection\n\\hypertarget{toc}{}\n"
                               "\\tableofcontents\n\\endgroup\n\\hfill")

    cover = ""
    if a.cover and not a.cover_dir:
        fields = {"CoverCourseCode": a.course_code, "CoverCourseName": a.course_name,
                  "CoverTitle": a.cover_title or " ".join(titles), "CoverSubtitle": a.cover_subtitle,
                  "CoverNote": a.cover_note, "CoverAuthor": a.author,
                  "CoverContents": " \\\\ ".join(a.cover_contents),
                  "CoverQuestions": question_marks([b for _, b in bodies])}
        cover = "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in fields.items())
        if a.date:
            cover += f"\n\\newcommand{{\\CoverDate}}{{{a.date}}}"
    pdftitle = re.sub(r"[{}\\$]", "", " ".join(titles)).replace("%", "\\%").replace("#", "\\#").replace("&", "\\&")

    if a.bangla:   # title lines, header and cover fields are typed on the command line, so wrap them here
        title_lines, header, cover = bn_wrap(title_lines), bn_wrap(header), bn_wrap(cover)

    main = (TEMPLATE / "main.tex").read_text()
    for key, val in {"CLASS": a.cls, "FONTSIZE": a.fontsize, "HEADER": header, "GRAPHICSPATH": graphicspath,
                     "TITLE_LINES": title_lines, "TOC_BLOCK": toc, "AUTHOR": tex_escape(a.author),
                     # without a contents list, the body follows the title on the same page and the header's
                     # TOC button (which would point nowhere) jumps to the title instead
                     "BODY_INPUTS": "\n".join(includes if not a.no_toc else [i.replace("\\include{", "\\input{") for i in includes]),
                     "AFTER_TITLE": "\\newpage" if not a.no_toc else "\\hypertarget{toc}{}",
                     "COVER_FIELDS": cover, "PDFTITLE": pdftitle,
                     "BEFORE_TITLE": "\\input{paper-page}" if paper else "",
                     "BANGLA": BANGLA if a.bangla else "",
                     "TYPE_PREAMBLE": "\n".join(type_inputs),
                     "HEADER_RIGHT": bn_wrap(tex_escape(a.header_right)) if a.bangla else tex_escape(a.header_right),
                     "GEOMETRY": f"\\geometry{{left={a.margin_x}, right={a.margin_x}}}" if a.margin_x else ""}.items():
        main = main.replace(f"<<{key}>>", val)
    (build / "main.tex").write_text(main)

    ok = compile_tex(build)
    report(build / "main.log")
    if not ok or not (build / "main.pdf").exists():
        print(f"BUILD FAILED -- see {build / 'main.log'}")
        sys.exit(1)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(build / "main.pdf", out)
    pages = re.search(r"Output written on main.pdf \((\d+) page", (build / "main.log").read_text(errors="replace"))
    sys.stdout.flush()
    print(f"PDF: {out}" + (f" ({pages.group(1)} pages)" if pages else ""))
    print(f"Build folder (main.tex + preamble + bodies, compile-ready): {build}")


if __name__ == "__main__":
    main()
