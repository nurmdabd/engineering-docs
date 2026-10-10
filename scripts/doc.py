#!/usr/bin/env python3
"""
doc.py -- one entry point for the whole path, Markdown to PDF.

    python3 doc.py types                        # the document types and what each is for
    python3 doc.py new TYPE notes.md            # start a document from types/TYPE/template.md
    python3 doc.py check notes.md [--type T]    # lint (references/authoring.md)
    python3 doc.py build notes.md [--out notes.pdf] [--reconvert] [build.py options ...]

`build` lints the Markdown (and stops on errors), converts it to latex/NAME.tex beside it, checks the
structure, then builds the PDF (default: NAME.pdf beside the Markdown). An existing latex/NAME.tex may have
been edited by hand, so it is reused, never overwritten, unless --reconvert is given; if the Markdown is newer
than it, `build` stops and asks for one or the other. Any other options go to build.py unchanged.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TYPES = HERE.parent / "types"


def run(script, *args):
    return subprocess.run([sys.executable, str(HERE / script), *map(str, args)]).returncode


def types():
    for spec in sorted(TYPES.glob("*/type.json")):
        desc = json.loads(spec.read_text(encoding="utf-8")).get("description", "")
        print(f"{spec.parent.name:16} {desc}")
    print("\nWithout a type, the house defaults apply. Details: types/NAME/guide.md")


def new(kind, path):
    template = TYPES / kind / "template.md"
    if not template.exists():
        sys.exit(f"no template for type '{kind}'. Types: " + ", ".join(p.parent.name for p in sorted(TYPES.glob("*/type.json"))))
    path = Path(path)
    if path.exists():
        sys.exit(f"{path} already exists; not overwriting it")
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(template, path)
    print(f"created {path} from types/{kind}/template.md. Read types/{kind}/guide.md before writing.")


def build(args):
    reconvert = "--reconvert" in args
    args = [a for a in args if a != "--reconvert"]
    mds = [a for a in args if a.endswith(".md")]
    if len(mds) != 1:
        sys.exit("doc.py build: give exactly one Markdown file (doc.py build notes.md [--out notes.pdf] [--reconvert] ...)")
    md = Path(mds[0]).resolve()
    if not md.exists():
        sys.exit(f"doc.py build: {md} not found")
    rest = [a for a in args if a != mds[0]]
    out = None
    if "--out" in rest:
        i = rest.index("--out")
        out, rest = Path(rest[i + 1]), rest[:i] + rest[i + 2:]
    body = md.parent / "latex" / f"{md.stem}.tex"
    out = out or md.parent / f"{md.stem}.pdf"

    if run("lint_md.py", md):
        sys.exit("doc.py: fix the errors above first")
    if body.exists() and not reconvert:
        if md.stat().st_mtime > body.stat().st_mtime:
            sys.exit(f"doc.py: {md.name} is newer than {body.relative_to(md.parent)}, which may hold hand edits.\n"
                     "  --reconvert regenerates it (hand edits are lost); or edit the .tex and touch it to build as is.")
        print(f"using the existing {body.relative_to(md.parent)} (pass --reconvert to regenerate it)")
    else:
        if run("md2tex.py", md, "-o", body):
            sys.exit("doc.py: conversion failed")
    if run("check_structure.py", body):
        sys.exit("doc.py: structure check failed")
    sys.exit(run("build.py", body, "--out", out, *rest))


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    cmd, args = a[0], a[1:]
    if cmd == "types":
        types()
    elif cmd == "new" and len(args) == 2:
        new(*args)
    elif cmd == "check" and args:
        sys.exit(run("lint_md.py", *args))
    elif cmd == "build" and args and not {"-h", "--help"} & set(args):
        build(args)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
