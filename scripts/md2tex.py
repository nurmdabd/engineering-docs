#!/usr/bin/env python3
"""
md2tex.py -- first-draft converter: Engineering Markdown -> house-style LaTeX body file.

It applies the mechanical parts of SKILL.md (heading mapping, labels, tables by column tier,
equations, figures, callouts, question/solution boxes, Unicode table). The judgement parts
(\\keyterm vs plain, captions, column widths that look wrong) still need the review pass
described in SKILL.md, Step 3.

Usage:
    python3 md2tex.py NOTES.md -o latex/NOTES.tex [--class extarticle|extreport] [--fontsize 12pt] [--textwidth 17.4]

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--class", dest="cls", default="extarticle", choices=["extarticle", "extreport"])
    ap.add_argument("--fontsize", default="12pt")
    ap.add_argument("--textwidth", type=float, default=17.4, help="text width in cm (17.4 for the house .7in margins)")
    a = ap.parse_args()

    md = a.md.resolve()
    out = a.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    text = md.read_text(encoding="utf-8")
    meta, body = front_matter(text)
    titles = [t for t in (meta.get("title"), meta.get("subtitle")) if t]
    if not titles:
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

    def fix_path(m):
        src = (md.parent / m.group(1)).resolve()
        return os.path.relpath(src, out.parent).replace(os.sep, "/")
    tex = re.sub(r"@@W:(.+?)@@", lambda m: image_width((md.parent / m.group(1)).resolve()), tex)
    tex = re.sub(r"@@P:(.+?)@@", fix_path, tex)
    tex = re.sub(r"\n{3,}", "\n\n", tex).strip() + "\n"
    header = f"% Generated from {md.name} by md2tex.py, then reviewed against SKILL.md.\n\n"
    out.write_text(header + tex, encoding="utf-8")
    print(json.dumps({"titles": titles}, ensure_ascii=False))


if __name__ == "__main__":
    main()
