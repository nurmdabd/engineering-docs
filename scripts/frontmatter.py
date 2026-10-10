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
    "preamble": ("str", "--type-preamble"),   # this document's own commands (references/commands.md)
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
    if meta.get("type"):
        flags += ["--type", meta["type"]]
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
    return flags
