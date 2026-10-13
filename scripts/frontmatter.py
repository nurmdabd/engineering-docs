"""
frontmatter.py -- the YAML block at the top of a Markdown file (references/authoring.md, "Front matter").

    ---
    title: "COM I --- Formula Sheet (Lectures 24--38)"
    subtitle: "Every formula you need"
    type: project-report          # a folder in types/
    lang: bn                      # bn = Bangla (adds --bangla); en is the default
    cover: true
    course_code: "COM I"
    ...
    ---

md2tex.py turns `type` and `lang` into its own flags, and writes every build setting to NAME.build.json
beside the .tex it produces; build.py reads that file. Flags given on the command line always win.
"""
import re

# key -> (kind, build.py flag or None). kind: str, bool, list
KEYS = {
    "title": ("str", "--title"),
    "subtitle": ("str", "--title"),
    "type": ("str", "--type"),
    "lang": ("str", None),
    "header": ("str", "--header"),
    "header_right": ("str", "--header-right"),
    "author": ("str", "--author"),
    "date": ("str", "--date"),
    "cover": ("bool", "--cover"),
    "course_code": ("str", "--course-code"),
    "course_name": ("str", "--course-name"),
    "cover_title": ("str", "--cover-title"),
    "cover_subtitle": ("str", "--cover-subtitle"),
    "cover_note": ("str", "--cover-note"),
    "cover_contents": ("list", "--cover-contents"),
    "accent": ("str", "--accent"),           # the subject's colour on cover and back cover, hex like 5B3A8C
    "inside_cover": ("bool", None),          # false: no page on the back of the cover
    "back_cover": ("bool", None),            # false: no back cover
    "back_blurb": ("str", "--back-blurb"),
    "print_layout": ("str", "--print-layout"),   # print copy: duplex (default) or booklet (pages padded to a multiple of 4)   # back cover: one or two sentences on what the document is
    "prerequisites": ("list", "--prerequisite"),   # back of the cover (theory notes): what to know first
    "conventions": ("str", "--conventions"),       # back of the cover: the textbook and conventions followed
    "edge_tabs": ("bool", "--edge-tabs"),     # a clickable tab per part on the page edge (false: none)
    "map_size": ("str", "--paper-size"),     # mind maps: a4 (screen, default) or a3 (print)
    "map_detail": ("bool", None),            # mind maps: show the cards' detail lines (default: on A3 only)
    "margin_x": ("str", "--margin-x"),       # left/right margin, e.g. 0.6in (default: the type's, else 0.5in)
    "preamble": ("str", "--type-preamble"),
    "toc": ("bool", None),                   # false: no table of contents (build.py --no-toc)
    "label_prefix": ("str", None),           # md2tex.py --label-prefix: d03_ makes sec:d03_objective, ...
    "first_number": ("str", None),           # md2tex.py --first-number: number of the first chapter/section   # this document's own commands (references/commands.md)
    "paper": ("bool", "--paper"),            # past papers: the typeset question paper before the solutions
    "paper_header": ("list", "--paper-header"),          # its centred header lines (raw LaTeX)
    "paper_info": ("list", "--paper-info"),              # the marks / credits / time row
    "paper_instruction": ("str", "--paper-instruction"),
    "paper_parts": ("list", "--paper-part"),             # "Part-A: 1-3": a part heading before question 1
    "paper_appendix": ("str", "--paper-appendix"),       # a .tex file printed at the end of the paper
    "exam": ("str", None),        # past papers: exam name and year, used by the type's guide
    "year": ("str", None),
}
# The reference table of every key (references/front-matter-keys.md is generated from this; doc.py keys).
# key -> (group, default, what it does). tests/run_tests.py fails when a key in KEYS has no entry here.
DOCS = {
    "title": ("Document", "the first # heading", "First title line (on page 1 without a cover; in the PDF properties)"),
    "subtitle": ("Document", "", "Second title line"),
    "type": ("Document", "none (house defaults)", "A folder in `types/`: its layout, cover and writing guide (`doc.py types`)"),
    "lang": ("Document", "`en`", "`bn` for Bangla (technical terms stay English)"),
    "header": ("Document", "the first title line", "Running header, left"),
    "header_right": ("Document", "", "Running header, right, before the TOC button"),
    "author": ("Document", "Nur Mohammad", "Author on the cover, title page and back cover"),
    "date": ("Document", "today", "Date on the cover and back cover (raw LaTeX, e.g. `October 2026`)"),
    "toc": ("Document", "`true`", "`false` leaves out the table of contents"),
    "margin_x": ("Document", "`0.5in` (formula sheet `0.4in`)", "Left and right page margins; table columns follow it"),
    "label_prefix": ("Document", "", "Prefix for every label (`d03_`), when several files go into one PDF"),
    "first_number": ("Document", "", "Number of the first chapter or section when a file is built on its own"),
    "preamble": ("Document", "", "This document's own commands: a `.tex` next to it with a registry `.yaml`"),
    "cover": ("Cover", "the type's (past paper: on)", "`true` adds the type's front cover (and, by default, its back cover)"),
    "course_code": ("Cover", "", "Large code on the cover band, e.g. `COM I`"),
    "course_name": ("Cover", "", "Course name under the code"),
    "cover_title": ("Cover", "the title lines", "The document's name on the cover"),
    "cover_subtitle": ("Cover", "", "The pill under the cover title, e.g. `Lectures 24--38`"),
    "cover_note": ("Cover", "formula sheet: its counts", "One italic line beside the pill"),
    "cover_contents": ("Cover", "the parts, read from the document", "A hand-written \"Inside\" list (theory and default covers)"),
    "accent": ("Cover", "`005F73` (ocean)", "The subject's colour on the cover, back cover and spine, as hex"),
    "inside_cover": ("Cover", "`true` when the type has one", "`false`: no page on the back of the cover"),
    "back_cover": ("Cover", "`true` with a cover", "`false`: no back cover"),
    "back_blurb": ("Cover", "", "One or two sentences on the back cover about the document"),
    "prerequisites": ("Cover", "", "List shown as \"Before you start\" on the back of a theory-notes cover"),
    "conventions": ("Cover", "", "One line on the textbook and conventions, at the foot of the back-of-cover page"),
    "edge_tabs": ("Cover", "on for theory, exam notes, formula sheets", "A clickable tab per part on the page edge (screen PDF only)"),
    "print_layout": ("Print", "`duplex`", "Print copy page order: `duplex` (even pages) or `booklet` (a multiple of 4)"),
    "map_size": ("Mind map", "`a4`", "`a4` (screen) or `a3` (print) landscape"),
    "map_detail": ("Mind map", "on A3 only", "Show the cards' detail lines"),
    "paper": ("Past paper", "`true`", "`false` leaves out the typeset question paper"),
    "paper_header": ("Past paper", "", "List: the paper's centred header lines (raw LaTeX)"),
    "paper_info": ("Past paper", "", "List: the marks / credits / time row; also feeds the paper-at-a-glance page"),
    "paper_instruction": ("Past paper", "", "The instruction line under the header"),
    "paper_parts": ("Past paper", "", "List: `Part-A: 1-3 | [Answer any two ...]`, a part heading before its first question"),
    "paper_appendix": ("Past paper", "", "A `.tex` file printed at the end of the paper (an equation sheet)"),
    "exam": ("Past paper", "", "Record only: which exam (put it in `cover_note` to show it)"),
    "year": ("Past paper", "", "Record only: the session"),
}


def reference():
    """The Markdown table of every key, grouped (doc.py keys)."""
    out = ["# Front-matter keys", "",
           "Generated from `scripts/frontmatter.py` (`python3 scripts/doc.py keys --write`); do not edit by hand.",
           "Values are raw LaTeX: `--` is an en-dash, `\\&` an ampersand; quote a value that contains `:`.", ""]
    for group in dict.fromkeys(g for g, _, _ in DOCS.values()):
        out += [f"## {group}", "", "| Key | Default | What it does |", "|---|---|---|"]
        out += [f"| `{k}` | {d} | {w} |" for k, (g, d, w) in DOCS.items() if g == group]
        out.append("")
    return "\n".join(out)


LANGS = ("en", "bn")
FENCE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def split(text):
    """Return (meta, body, problems). meta is {} when there is no front matter."""
    m = FENCE.match(text)
    if not m:
        return {}, text, []
    try:
        import yaml
        meta = yaml.safe_load(m.group(1)) or {}
        if not isinstance(meta, dict):
            return {}, text[m.end():], ["front matter is not a set of key: value lines"]
    except Exception as e:
        return {}, text[m.end():], [f"front matter is not valid YAML: {str(e).splitlines()[0]}"]
    problems = []
    for k, v in list(meta.items()):
        if k not in KEYS:
            problems.append(f"unknown front matter key '{k}' (known: {', '.join(KEYS)})")
            continue
        kind = KEYS[k][0]
        if kind == "bool" and not isinstance(v, bool):
            problems.append(f"'{k}' must be true or false")
        elif kind == "list" and not isinstance(v, list):
            meta[k] = [v]
        elif kind == "str" and v is not None:
            meta[k] = str(v)
    if meta.get("map_size") and meta["map_size"] not in ("a4", "a3"):
        problems.append(f"map_size must be a4 or a3, not '{meta['map_size']}'")
    if meta.get("lang") and meta["lang"] not in LANGS:
        problems.append(f"lang must be one of {', '.join(LANGS)}, not '{meta['lang']}'")
    return meta, text[m.end():], problems


def md2tex_flags(meta):
    flags = []
    if meta.get("label_prefix"):
        flags += ["--label-prefix", meta["label_prefix"]]
    if meta.get("first_number"):
        flags += ["--first-number", meta["first_number"]]
    if meta.get("type"):
        flags += ["--type", meta["type"]]
    if meta.get("margin_x"):   # after --type, so it beats the type's margin
        flags += ["--margin-x", meta["margin_x"]]
    if meta.get("map_size"):
        flags += ["--paper-size", meta["map_size"]]
    if meta.get("map_detail") is not None:
        flags += ["--map-detail", "true" if meta["map_detail"] else "false"]
    if meta.get("lang") == "bn":
        flags.append("--bangla")
    return flags


def build_flags(meta):
    """build.py options for the front matter, as [flag] or [flag, value] items; [] when it only holds title/subtitle."""
    if not set(meta) - {"title", "subtitle"}:
        return []
    flags = []
    for k, (kind, flag) in KEYS.items():
        v = meta.get(k)
        if flag is None or v in (None, "", False):
            continue
        if kind == "bool":
            flags.append([flag])
        elif kind == "list":
            flags += [[flag, str(item)] for item in v]
        else:
            flags.append([flag, v])
    if meta.get("lang") == "bn":
        flags.append(["--bangla"])
    if meta.get("toc") is False:
        flags.append(["--no-toc"])
    if meta.get("cover") is False:   # turns off a cover the type adds by default
        flags.append(["--no-cover"])
    if meta.get("inside_cover") is False:
        flags.append(["--no-inside-cover"])
    if meta.get("back_cover") is False:
        flags.append(["--no-back-cover"])
    if meta.get("edge_tabs") is False:
        flags.append(["--no-edge-tabs"])
    if meta.get("paper") is False:   # turns off the question paper the past-paper type adds by default
        flags.append(["--no-paper"])
    return flags
