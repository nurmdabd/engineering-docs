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
        [--build-dir DIR]                      # default: <OUT stem>_build next to OUT

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


REPEATED = ("--title", "--cover-contents")   # options that collect values; the user's replace the sidecar's


def with_sidecar(argv):
    """Put the first body's NAME.build.json settings (written by md2tex.py from front matter) before argv."""
    body = next((Path(x) for x in argv[1:] if x.endswith(".tex")), None)
    sidecar = body.with_suffix(".build.json") if body else None
    if not sidecar or not sidecar.exists():
        return argv
    saved = json.loads(sidecar.read_text(encoding="utf-8")).get("build", [])
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
    ap.add_argument("--course-code", default="")
    ap.add_argument("--course-name", default="")
    ap.add_argument("--cover-title")
    ap.add_argument("--cover-subtitle", default="")
    ap.add_argument("--cover-note", default="")
    ap.add_argument("--cover-contents", action="append", default=[])
    ap.add_argument("--date")
    ap.add_argument("--cover-dir", type=Path)
    ap.add_argument("--build-dir", type=Path)
    a = ap.parse_args(doctype.expand(with_sidecar(sys.argv), "build")[1:])

    out = a.out.resolve()
    build = (a.build_dir or out.parent / f"{out.stem}_build").resolve()
    build.mkdir(parents=True, exist_ok=True)
    shutil.copy(TEMPLATE / "main-tex-preamble.tex", build)
    type_inputs = []
    for old in build.glob("type-*-preamble.tex"):
        old.unlink()
    for tp in dict.fromkeys(p.resolve() for p in a.type_preamble):
        name = f"type-{tp.parent.name}-preamble.tex"
        shutil.copy(tp, build / name)
        type_inputs.append(f"\\input{{{name}}}")
    for f in ("cover-page-preamble.tex", "cover-page-main.tex"):
        (build / f).unlink(missing_ok=True)
        src = (a.cover_dir / f) if a.cover_dir else (TEMPLATE / f if a.cover else None)
        if src and src.exists():
            shutil.copy(src, build)

    used, includes, gdirs = set(), [], []
    for body in a.bodies:
        body = body.resolve()
        if not body.exists():
            sys.exit(f"missing body file: {body}")
        name = safe_stem(body, used)
        shutil.copy(body, build / f"{name}.tex")
        includes.append(f"\\include{{{name}}}")
        gdirs += [body.parent, body.parent / "figures"]
    gdirs += [d.resolve() for d in a.figures]
    gdirs = [d for d in dict.fromkeys(gdirs) if d.is_dir()]
    if any(" " in str(d) for d in gdirs):
        print("warning: an image folder path contains spaces; XeLaTeX may not find images there")
    graphicspath = "{figures/}" + "".join(f"{{{d.as_posix()}/}}" for d in gdirs)

    titles = a.title or [a.bodies[0].stem]
    title_lines = " \\\\[0.1cm]\n".join(f"\t{{\\LARGE{{\\keyterm{{{tex_escape(t)}}}}}}}" for t in titles)
    header = tex_escape(a.header) if a.header else " ".join(tex_escape(t) for t in titles)
    toc = "" if a.no_toc else ("\\begingroup\n\\setstretch{1}\n\\phantomsection\n\\hypertarget{toc}{}\n"
                               "\\tableofcontents\n\\endgroup\n\\hfill")

    cover = ""
    if a.cover and not a.cover_dir:
        fields = {"CoverCourseCode": a.course_code, "CoverCourseName": a.course_name,
                  "CoverTitle": a.cover_title or " ".join(titles), "CoverSubtitle": a.cover_subtitle,
                  "CoverNote": a.cover_note, "CoverAuthor": a.author,
                  "CoverContents": " \\\\ ".join(a.cover_contents)}
        cover = "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in fields.items())
        if a.date:
            cover += f"\n\\newcommand{{\\CoverDate}}{{{a.date}}}"
    pdftitle = re.sub(r"[{}\\$]", "", " ".join(titles)).replace("%", "\\%").replace("#", "\\#").replace("&", "\\&")

    if a.bangla:   # title lines, header and cover fields are typed on the command line, so wrap them here
        title_lines, header, cover = bn_wrap(title_lines), bn_wrap(header), bn_wrap(cover)

    main = (TEMPLATE / "main.tex").read_text()
    for key, val in {"CLASS": a.cls, "FONTSIZE": a.fontsize, "HEADER": header, "GRAPHICSPATH": graphicspath,
                     "TITLE_LINES": title_lines, "TOC_BLOCK": toc, "AUTHOR": tex_escape(a.author),
                     "BODY_INPUTS": "\n".join(includes),
                     "COVER_FIELDS": cover, "PDFTITLE": pdftitle,
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
