#!/usr/bin/env python3
"""
md2tex.py -- first-draft converter: Engineering Markdown -> house-style LaTeX body file.

It applies the mechanical parts of SKILL.md (heading mapping, labels, tables by column tier,
equations, figures, callouts, question/solution boxes, Unicode table). The judgement parts
(\\keyterm vs plain, captions, column widths that look wrong) still need the review pass
described in SKILL.md, Step 3.

Usage:
    python3 md2tex.py NOTES.md -o latex/NOTES.tex [--type NAME] [--class extarticle|extreport] [--fontsize 12pt] [--textwidth 17.4]

--type NAME loads the default flags of types/NAME/type.json; flags given explicitly still win.

Prints the suggested --title lines for build.py (from YAML title/subtitle, else the first # heading,
which is then removed from the body).

Front matter (scripts/frontmatter.py): `type` and `lang: bn` set this script's flags; every build setting
(type, cover fields, header, ...) is written to OUT.build.json, which build.py reads. Explicit flags win.
Needs pandoc >= 3.0 and Pillow (image sizes).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import commands
import detect_type
import doctype
import frontmatter
import slugs

HERE = Path(__file__).resolve().parent


def image_width(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
    except Exception:
        return "0.8\\linewidth"
    r = w / h
    if r >= 2.2:
        return "\\linewidth"
    if r >= 1.5:
        return "0.9\\linewidth"
    if r >= 1.1:
        return "0.75\\linewidth"
    if r >= 0.8:
        return "0.6\\linewidth"
    return "0.45\\linewidth"


BN = "\u0980-\u09FF\u0964\u0965\u200C\u200D"
BN_RUN = re.compile(f"[{BN}]+(?:[ ,;:!?'\u2018\u2019\u201C\u201D]+[{BN}]+)*")


def wrap_bangla(tex):
    """Wrap every run of Bangla text (outside maths) in \\bn{...}; maths and \\label/\\ref keys untouched."""
    out = []
    for line in tex.split("\n"):
        parts = re.split(r"(\$[^$]*\$|\\(?:label|ref|cref|hyperref)\b(?:\[[^\]]*\])?\{[^}]*\})", line)
        for i, p in enumerate(parts):
            if i % 2 == 0:
                parts[i] = BN_RUN.sub(lambda m: "\\bn{" + m.group(0) + "}", p)
        out.append("".join(parts))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--class", dest="cls", default="extarticle", choices=["extarticle", "extreport"])
    ap.add_argument("--fontsize", default="12pt")
    ap.add_argument("--bangla", action="store_true", help="wrap Bangla text runs in \\bn{...} (build with build.py --bangla)")
    ap.add_argument("--structure", default="notes", choices=["notes", "past-paper"],
                    help="past-paper: # = a question's paper block, ## = one solution (types/past-paper/guide.md)")
    ap.add_argument("--textwidth", type=float, default=17.4, help="text width in cm (17.4 for the house .7in margins)")
    first = ap.parse_known_args()[0]          # only to find the Markdown file and read its front matter
    meta, body, problems = frontmatter.split(first.md.read_text(encoding="utf-8"))
    for p in problems:
        print(f"warning: {first.md.name}: {p}", file=sys.stderr)
    if not meta.get("type") and "--type" not in sys.argv:
        guess = detect_type.detect(meta, body)
        if guess:
            print(f"note: {first.md.name} has no type; it looks like {guess[0][0]} ({guess[0][1]}). "
                  f"Add 'type: {guess[0][0]}' to its front matter to use that type's settings.", file=sys.stderr)
    argv = [sys.argv[0], *frontmatter.md2tex_flags(meta), *sys.argv[1:]]
    a = ap.parse_args(doctype.expand(argv, "md2tex")[1:])
    type_name = [argv[i + 1] for i in range(len(argv) - 1) if argv[i] == "--type"][-1:] or [None]
    own_pre = (first.md.parent / meta["preamble"]).resolve() if meta.get("preamble") else None
    if own_pre and not own_pre.exists():
        sys.exit(f"{first.md.name}: preamble {meta['preamble']} not found")
    registry = commands.registry(type_name[0], own_pre.with_suffix(".yaml") if own_pre else None)

    md = a.md.resolve()
    out = a.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    titles = [t for t in (meta.get("title"), meta.get("subtitle")) if t]
    # Otherwise the first # heading is the title. Exception: in extreport, several # headings are chapters
    # (day-01, day-02, ...) and all stay in the body. Lines inside code fences are not headings.
    tops = re.findall(r"^# .+$", re.sub(r"^(```|~~~).*?^\1", "", body, flags=re.M | re.S), re.M)
    if not titles and a.structure == "notes" and not (a.cls == "extreport" and len(tops) > 1):
        m = re.search(r"^# (.+)$", body, re.M)
        if m:
            t = m.group(1).strip()
            titles = [p.strip() + (":" if i == 0 and ": " in t else "") for i, p in enumerate(t.split(": ", 1))]
            body = body[:m.start()] + body[m.end():]

    cmd = ["pandoc", "-f", "markdown+lists_without_preceding_blankline-fancy_lists-implicit_figures",
           "-t", "latex", "--wrap=none", "--lua-filter", str(HERE / "house.lua"),
           "-M", f"house_class={a.cls}", "-M", f"house_fontsize={a.fontsize}", "-M", f"house_textwidth={a.textwidth}", "-M", f"house_structure={a.structure}", "-M", f"house_cmds={commands.encode(registry)}",
           "-M", "house_gfm=" + " ".join(slugs.heading_slugs(body))]   # GitHub anchors, so [..](#gh-anchor) links work
    r = subprocess.run(cmd, input=body, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    tex = r.stdout

    def rel(src):
        return os.path.relpath((md.parent / src).resolve(), out.parent).replace(os.sep, "/")

    def missing_image(m):   # references/latex-rules.md Section 6: an image that doesn't exist yet stays commented out
        if (md.parent / m.group(2)).exists():
            return m.group(0)
        return f"{m.group(1)}% TODO: insert graphic\n{m.group(1)}% \\includegraphics[width=0.8\\linewidth]{{{rel(m.group(2))}}}"
    tex = re.sub(r"^([ \t]*)\\includegraphics\[width=@@W:(.+?)@@\]\{@@P:\2@@\}$", missing_image, tex, flags=re.M)
    tex = re.sub(r"@@W:(.+?)@@", lambda m: image_width((md.parent / m.group(1)).resolve()), tex)
    tex = re.sub(r"@@P:(.+?)@@", lambda m: rel(m.group(1)), tex)
    if a.bangla:
        tex = wrap_bangla(tex)
    tex = re.sub(r"\n{3,}", "\n\n", tex).strip() + "\n"
    header = f"% Generated from {md.name} by md2tex.py, then reviewed against SKILL.md.\n\n"
    out.write_text(header + tex, encoding="utf-8")
    sidecar = out.with_suffix(".build.json")
    build = frontmatter.build_flags(meta)
    for item in build:   # the document's own preamble: a path relative to the sidecar, so the folder can move
        if item[0] == "--type-preamble":
            item[1] = os.path.relpath(own_pre, out.parent).replace(os.sep, "/")
    if build:
        items = ",\n  ".join(json.dumps(x, ensure_ascii=False) for x in build)   # one option per line
        sidecar.write_text(f'{{\n "source": {json.dumps(md.name, ensure_ascii=False)},\n "build": [\n  {items}\n ]\n}}\n', encoding="utf-8")
    else:
        sidecar.unlink(missing_ok=True)
    print(json.dumps({"titles": titles}, ensure_ascii=False))


if __name__ == "__main__":
    main()
