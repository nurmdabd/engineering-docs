"""
slugs.py -- GitHub-style heading anchors.

Notes written for GitHub link to headings by GitHub's anchor ("#lecture-24--pm-bandwidth"), while pandoc gives the
same heading another id ("lecture-24-pm-bandwidth", leading numbers dropped). md2tex.py passes the GitHub anchors to
house.lua in heading order, so a link written either way reaches the heading in the PDF.
"""
import re
import unicodedata

FENCE = re.compile(r"^(```+|~~~+)")
ATX = re.compile(r"^(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")


def plain(md):
    """Heading Markdown -> the text GitHub slugs: links and images keep their text, emphasis and code marks go."""
    md = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"<[^>]+>", "", md)
    return md.replace("`", "").replace("*", "")


def github_slug(text):
    """GitHub's anchor: lowercase; keep letters, marks, numbers, '_', '-' and spaces; spaces become '-'."""
    out = []
    for c in plain(text).lower():
        if c == " ":
            out.append("-")
        elif c == "-" or c == "_" or unicodedata.category(c)[0] in "LMN":
            out.append(c)
    return "".join(out)


def heading_slugs(body):
    """GitHub anchors of every ATX heading outside code fences, in order, numbered like GitHub for repeats."""
    seen, slugs, fence = {}, [], None
    for line in body.split("\n"):
        m = FENCE.match(line)
        if m:
            fence = None if fence and line.strip().startswith(fence) else (fence or m.group(1))
            continue
        if fence:
            continue
        h = ATX.match(line)
        if h:
            s = github_slug(h.group(2))
            n = seen.get(s, 0)
            seen[s] = n + 1
            slugs.append(s if n == 0 else f"{s}-{n}")
    return slugs
