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
Needs pandoc >= 3.0 and Pillow (image sizes).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import doctype

HERE = Path(__file__).resolve().parent


def front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"').strip("'")
        return meta, text[m.end():]
    return meta, text


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
    ap.add_argument("--textwidth", type=float, default=17.4, help="text width in cm (17.4 for the house .7in margins)")
    a = ap.parse_args(doctype.expand(sys.argv, "md2tex")[1:])

    md = a.md.resolve()
    out = a.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    text = md.read_text(encoding="utf-8")
    meta, body = front_matter(text)
    titles = [t for t in (meta.get("title"), meta.get("subtitle")) if t]
    # Otherwise the first # heading is the title. Exception: in extreport, several # headings are chapters
    # (day-01, day-02, ...) and all stay in the body. Lines inside code fences are not headings.
    tops = re.findall(r"^# .+$", re.sub(r"^(```|~~~).*?^\1", "", body, flags=re.M | re.S), re.M)
    if not titles and not (a.cls == "extreport" and len(tops) > 1):
        m = re.search(r"^# (.+)$", body, re.M)
        if m:
            t = m.group(1).strip()
            titles = [p.strip() + (":" if i == 0 and ": " in t else "") for i, p in enumerate(t.split(": ", 1))]
            body = body[:m.start()] + body[m.end():]

    cmd = ["pandoc", "-f", "markdown+lists_without_preceding_blankline-fancy_lists-implicit_figures",
           "-t", "latex", "--wrap=none", "--lua-filter", str(HERE / "house.lua"),
           "-M", f"house_class={a.cls}", "-M", f"house_fontsize={a.fontsize}", "-M", f"house_textwidth={a.textwidth}"]
    r = subprocess.run(cmd, input=body, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    tex = r.stdout

    def rel(src):
        return os.path.relpath((md.parent / src).resolve(), out.parent).replace(os.sep, "/")

    def missing_image(m):   # SKILL.md Section 6: an image that doesn't exist yet stays commented out
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
    print(json.dumps({"titles": titles}, ensure_ascii=False))


if __name__ == "__main__":
    main()
