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
    if meta.get("paper") is False:   # turns off the question paper the past-paper type adds by default
        flags.append(["--no-paper"])
    return flags
