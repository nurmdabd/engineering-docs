"""
mindmap.py -- the mind-map diagram: a Markdown list inside ::: {.mindmap} ... ::: becomes one TikZ page.

    ::: {.mindmap}
    ## Analog FM | L24--27                       a part: a node on the spine, in story order (left to right)
    - **Carson's rule** ★: $B_T \\approx 2(\\Delta f + B)$   a card: bold title, optional ★ (often asked), key formula
      - NBFM $\\beta \\ll 1$, WBFM $\\beta \\gg 1$     a detail line (shown on A3, or with map_detail: true)
      - → TDM                                    "used again in": a chip that jumps to the card titled TDM
    - **[Demodulation](theory.md#fm-demodulation)**: limiter, then discriminator   a title that is a link
    ## Sampling | L27--28
    ...
    :::

md2tex.py takes each such block out of the Markdown first (its # and ## lines are not document headings),
then puts convert()'s LaTeX back in as a raw block before pandoc runs. The
layout is computed here: parts spread evenly across the page on one line (the story of the course), their
cards stacked above and below, joined to the part by a stem. Sizes follow the paper: A4 landscape for the
screen, A3 landscape for a printed wall or desk copy (front matter map_size: a3). Styles live in
types/mind-map/preamble.tex.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLOCK = re.compile(r"^:::\s*\{\s*\.mindmap\s*\}\s*\n(.*?)^:::\s*$", re.S | re.M)
STAR = "★"

# per paper: column width cap (cm), gap between cards (cm), card font, detail lines shown by default
SIZES = {"a4": {"cap": 4.6, "gap": 2.3, "font": "\\footnotesize", "detail": False, "title": "\\fontsize{20}{24}"},
         "a3": {"cap": 7.2, "gap": 3.6, "font": "\\normalsize", "detail": True, "title": "\\fontsize{28}{32}"}}
PAGE_HEIGHT = {"a4": 21.0, "a3": 29.7}


def parse(text):
    """{'title', 'parts': [{'name', 'sub', 'cards': [{'title', 'star', 'formula', 'details', 'refs'}]}]}"""
    title, parts, problems = "", [], []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            name, _, sub = line[3:].partition("|")
            parts.append({"name": name.strip(), "sub": sub.strip(), "cards": []})
        elif re.match(r"[-*+] ", line):
            if not parts:
                problems.append(f"line {n}: a card before the first part (## Part name)")
                continue
            m = re.match(r"[-*+]\s+\*\*(.+?)\*\*\s*(★)?\s*:?\s*(.*)$", line)
            if not m:
                problems.append(f"line {n}: a card starts with its **bold title**: {line.strip()}")
                continue
            t, star, rest = m.group(1).strip(), bool(m.group(2)), m.group(3).strip()
            if rest.startswith(STAR):
                star, rest = True, rest[1:].lstrip(" :")
            parts[-1]["cards"].append({"title": t, "star": star, "formula": rest, "details": [], "refs": []})
        elif re.match(r"\s+[-*+] ", line):
            if not parts or not parts[-1]["cards"]:
                problems.append(f"line {n}: a sub-item outside a card")
                continue
            item = re.sub(r"^\s+[-*+]\s+", "", line).strip()
            card = parts[-1]["cards"][-1]
            ref = re.match(r"(?:→|->)\s*(.+)$", item)
            (card["refs"] if ref else card["details"]).append(ref.group(1).strip() if ref else item)
        else:
            problems.append(f"line {n}: not a part (##), a card (- **Title**: ...) or a sub-item: {line.strip()}")
    if not parts:
        problems.append("no parts: start each part with '## Name | lectures'")
    return {"title": title, "parts": parts}, problems


def plain(md):
    """A title as plain words, to match → references against: no markup, no link targets, lower case."""
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    return re.sub(r"[*_`$\\{}]", "", md).strip().lower()


def inline_latex(fragments, lua, pandoc_args=(), context=""):
    """Convert Markdown fragments to LaTeX with the house filter, in one pandoc run. context: the document's
    heading lines, put in front (their output is dropped) so [text](#anchor) finds the same labels as the
    main conversion."""
    if not fragments:
        return []
    sep = "MMSPLIT7Q"
    src = f"\n\n{sep}\n\n".join([context or "MMEMPTY7Q", *(f if f.strip() else "MMEMPTY7Q" for f in fragments)])
    r = subprocess.run(["pandoc", "-f", "markdown-implicit_figures", "-t", "latex", "--wrap=none", "--lua-filter", str(lua),
                        *pandoc_args],
                       input=src, capture_output=True, text=True)
    if r.returncode:
        sys.exit("mind map: pandoc failed:\n" + r.stderr)
    out = [x.strip() for x in r.stdout.split(sep)][1:]
    if len(out) != len(fragments):
        sys.exit("mind map: could not convert the card texts (a separator was lost)")
    return ["" if x == "MMEMPTY7Q" else x for x in out]


def convert(text, paper="a4", text_width=27.16, detail=None, lua=HERE / "house.lua", pandoc_args=(), context=""):
    """The LaTeX for one ::: {.mindmap} block, and a list of problems (empty when it is fine)."""
    spec, problems = parse(text)
    if problems:
        return "", problems
    size = SIZES[paper]
    show_detail = size["detail"] if detail is None else detail
    parts = spec["parts"]
    titles = {}
    for i, p in enumerate(parts, 1):
        for j, c in enumerate(p["cards"], 1):
            titles.setdefault(plain(c["title"]), (i, f"mm-{i}-{j}"))
    # Markdown -> LaTeX for every text, in one pass
    frags = [spec["title"]]
    for p in parts:
        frags += [p["name"], p["sub"]]
        for c in p["cards"]:
            frags += [c["title"], c["formula"], *c["details"], *c["refs"]]
    conv = iter(inline_latex(frags, lua, pandoc_args, context))
    map_title = next(conv)

    n = len(parts)
    col = text_width / n
    pw = min(col - 0.75, size["cap"])
    cw = pw - 0.1
    side = max(max((len(p["cards"]) + 1) // 2 for p in parts), max(len(p["cards"]) // 2 for p in parts), 1)
    avail = (PAGE_HEIGHT[paper] - 2.54 - 1.78 - 2.6) / 2 - 1.0   # half the text height under the title, less the spine
    gap = min(size["gap"], avail / side)
    if gap < 1.45:
        problems.append(f"{side} cards on one side of a part is too many for {paper.upper()}: "
                        "split the part, move cards to another part, or use map_size: a3")
    lines = [f"% generated by mindmap.py from the ::: {{.mindmap}} block: {n} parts, {paper.upper()}",
             f"\\begin{{mindmappage}}{{{size['font']}}}{{{size['title']}}}{{{map_title}}}",
             f"\\begin{{tikzpicture}}[x=1cm, y=1cm, mmpartw/.style={{text width={pw:.2f}cm}}, mmcardw/.style={{text width={cw:.2f}cm}}]"]
    for i, p in enumerate(parts, 1):
        name, sub = next(conv), next(conv)
        x = (i - 1) * col
        lines.append(f"\\mmpart{{{i}}}{{{x:.2f}}}{{{name}}}{{{sub}}}")
        cards = p["cards"]
        up = (len(cards) + 1) // 2
        for j, c in enumerate(cards, 1):
            ctitle, formula = next(conv), next(conv)
            details = [next(conv) for _ in c["details"]]
            refs = [next(conv) for _ in c["refs"]]
            chips = []
            for raw, tex in zip(c["refs"], refs):
                hit = titles.get(plain(raw))
                if not hit:
                    problems.append(f"'→ {raw}' in card '{c['title']}': no card has that title")
                    continue
                chips.append(f"\\mmref{{{hit[0]}}}{{{hit[1]}}}{{{tex}}}")
            y = (j * gap) if j <= up else -((j - up) * gap)
            body = "\\\\[1pt]".join([x for x in [formula] if x] + ([f"{{\\color{{CoverSoft}}{d}}}" for d in details] if show_detail else []))
            lines.append(f"\\mmcard{{{i}}}{{mm-{i}-{j}}}{{{x + 0.3:.2f}}}{{{y:.2f}}}{{{ctitle}}}{{{1 if c['star'] else 0}}}"
                         f"{{{body}}}{{{''.join(chips)}}}")
    for i in range(1, n):
        lines.append(f"\\mmstory{{{i}}}{{{i + 1}}}")
    lines += ["\\end{tikzpicture}", "\\end{mindmappage}"]
    return "\n".join(lines), problems
