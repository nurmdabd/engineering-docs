"""
mindmap.py -- mind maps: a Markdown outline inside ::: {.mindmap} ... ::: becomes the main map, sub-maps and an
outline table (types/mind-map/guide.md).

    ::: {.mindmap}
    # COM I · Communication Engineering I | Lectures 24--38      the heading over every part (optional)
    ## Analog FM | L24--27                                       a part: a column of the main map
    - **Carson's rule** ★: $B_T \\approx 2(\\Delta f + B)$        a card: bold title, ★ (often asked), key formula
      - def: Swing plus message rate.                            its definition (the outline table's "What it is")
      - **NBFM**: $B_T \\approx 2B$                               a child: a grey line on the card, or a card of
        - def: Narrowband FM, beta << 1.                         its own on a sub-map (see below)
      - → TDM                                                    "used again in": a link to the card titled TDM
    :::

Two halves:

convert() runs inside md2tex.py: it parses the block, converts every text to LaTeX with the house filter and
writes the result into the body as one %MMDATA comment line (JSON), so the .tex compiles to nothing on its own.

render() runs inside build.py, where the page layout is known: it measures every card with the document's own
preamble and fonts (one extra XeLaTeX run), fits each column, and replaces the comment with the pages.

  Cards and details. A part's items are its cards. A card whose children do not fit on it as one grey line (4 or
  more children, or children with children of their own) gets a sub-map: its children become cards there, and
  the card's strip gets a map button. Otherwise its children are details, listed in grey on the card.

  Fitting a column that is too tall, one step at a time, each as little as needed:
    with room for two columns   1 tighten the gaps   2 hide grey lines (bottom card first)   3 split into two
                                columns (grey lines back where they fit)   4 title-only cards (non-star first,
                                bottom first)   5 move the last cards to a continuation ("+n more")
    without                     1 gaps   2 grey lines   3 title-only cards   4 "+n more"
  Room: on the main map a split narrows every column, so it is kept only if each column stays at least minslot
  wide and no other part needs a later step because of it.

  Pages: the main map (more parts than a page holds continue on the next page, spread evenly), then every part's
  continuation, then the sub-maps in course order, then the outline table. A sub-map sits beside its card instead
  when the page has room right of the card's column, it fits in one column with at most steps 1-2, and it can
  start level with its card (the first of a column may start higher).
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLOCK = re.compile(r"^:::\s*\{\s*\.mindmap\s*\}\s*\n(.*?)^:::\s*$", re.S | re.M)
DATA = re.compile(r"^%MMDATA (.*)$", re.M)
STAR = "★"
PT = 2.54 / 72.27   # cm per pt

# Per paper: card fonts, the button strip, gaps (cm), the narrowest main-map column, sub-map columns per page.
SIZE = {
    "a4": dict(font=r"\small", title=r"\normalsize", detail=r"\scriptsize", part=r"\large", strip=0.66, sep=4.0, tall=1.15,
               gap=0.36, gapmin=0.16, sgap=0.35, minslot=4.3, maxslot=7.0, subslots=4, heading=1.25, headfont=r"\Large", partmin=1.45,
               more=0.75, fonts=r"\def\mmifont{\scriptsize}\def\mmisep{0.5pt}\def\mmmfont{\scriptsize}"),
    "a3": dict(font=r"\large", title=r"\Large", detail=r"\normalsize", part=r"\LARGE", strip=0.9, sep=6.0, tall=1.7,
               gap=0.5, gapmin=0.22, sgap=0.5, minslot=6.0, maxslot=9.5, subslots=5, heading=1.8, headfont=r"\huge", partmin=2.1,
               more=1.05, fonts=r"\def\mmifont{\footnotesize}\def\mmisep{0.8pt}\def\mmmfont{\normalsize}"),
}
RESERVE_MAIN = 2.4      # cm of the text height the header, legend and centring take on a map page
RESERVE_SUB = 4.6       # the same on a sub-map page, with its sub-heading
TABLE_W = {"l2": 3.5, "l3": 3.5, "l4": 3.1, "fx": 6.2, "bk": 1.5}   # outline-table columns (cm); "What it is" takes the rest
TINT = {2: 16, 3: 9, 4: 4}


# ================================================================ Markdown side (md2tex.py)
def item_node(item):
    m = re.match(r"\*\*(.+?)\*\*\s*(★)?\s*:?\s*(.*)$", item)
    if m:
        title, star, rest = m.group(1).strip(), bool(m.group(2)), m.group(3).strip()
    else:
        title, star, rest = item, False, ""
        if title.endswith(STAR):
            title, star = title[:-1].rstrip(), True
    if rest.startswith(STAR):
        star, rest = True, rest[1:].lstrip(" :")
    return {"title": title, "star": star, "formula": rest, "defn": "", "kids": [], "chips": []}


def parse(text):
    """{'title', 'sub', 'parts': [{'name', 'sub', 'kids': [node]}]}; node: {'title', 'star', 'formula', 'defn',
    'kids', 'chips'}. Nesting follows the indentation."""
    title, sub, parts, problems = "", "", [], []
    stack = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip().expandtabs(4)
        if not line.strip():
            continue
        if line.startswith("# "):
            title, _, sub = line[2:].partition("|")
            title, sub = title.strip(), sub.strip()
            continue
        if line.startswith("## "):
            name, _, psub = line[3:].partition("|")
            parts.append({"name": name.strip(), "sub": psub.strip(), "kids": []})
            stack = []
            continue
        m = re.match(r"(\s*)[-*+]\s+(.*)$", line)
        if not m:
            problems.append(f"line {n}: not a part (##), a card (- **Title**: ...) or an item under one: {line.strip()}")
            continue
        if not parts:
            problems.append(f"line {n}: an item before the first part (## Part name)")
            continue
        indent, item = len(m.group(1)), m.group(2).strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else None
        d = re.match(r"def:\s*(.*)$", item)
        ref = re.match(r"(?:→|->)\s*(.+)$", item)
        if d or ref:
            if parent is None:
                problems.append(f"line {n}: '{item}' must be indented under the card it belongs to")
            elif d:
                parent["defn"] = (parent["defn"] + " " + d.group(1).strip()).strip()
            else:
                parent["chips"].append(ref.group(1).strip())
            continue
        node = item_node(item)
        (parent["kids"] if parent else parts[-1]["kids"]).append(node)
        stack.append((indent, node))
    if not parts:
        problems.append("no parts: start each part with '## Name | lectures'")
    keys = {plain(x["title"]) for x in walk(parts)}
    for x in walk(parts):
        for c in x["chips"]:
            if plain(c) not in keys:
                problems.append(f"'→ {c}' in '{x['title']}': no card or item has that title")
    return {"title": title, "sub": sub, "parts": parts}, problems


def colour(part):
    """The colour number of a part: the preamble has eight (CoverPart1-8), so a ninth part takes the first again."""
    return (part - 1) % 8 + 1


def walk(items):
    """Every node under a list of parts or nodes, depth first."""
    for it in items:
        for k in it["kids"]:
            yield k
            yield from walk([k])


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


def convert(text, detail=None, lua=HERE / "house.lua", pandoc_args=(), context="", wrap=None):
    """The %MMDATA line for one ::: {.mindmap} block, and a list of problems (empty when it is fine).
    detail: False never shows the grey detail lines on the maps (True or None: where they fit).
    wrap: applied to every converted text (md2tex passes its Bangla wrapper)."""
    spec, problems = parse(text)
    if problems:
        return "", problems
    nodes = list(walk(spec["parts"]))
    frags = [spec["title"], spec["sub"]]
    for p in spec["parts"]:
        frags += [p["name"], p["sub"]]
    for x in nodes:
        frags += [x["title"], x["formula"], x["defn"], *x["chips"]]
    conv = iter(wrap(t) if wrap else t for t in inline_latex(frags, lua, pandoc_args, context))
    data = {"v": 1, "title": next(conv), "sub": next(conv), "detail": detail, "parts": []}
    for p in spec["parts"]:
        data["parts"].append({"name": next(conv), "sub": next(conv), "kids": p["kids"]})

    def out(x):
        raw = x["title"]
        x.update(title=next(conv), formula=next(conv), defn=next(conv), key=plain(raw))
        x["chips"] = [{"text": next(conv), "key": plain(c)} for c in x["chips"]]
    for x in nodes:
        out(x)
    return ("% mind map: scripts/mindmap.py draws it at build time (main map, sub-maps, outline table)\n"
            "%MMDATA " + json.dumps(data, ensure_ascii=True, separators=(",", ":"))), []


# ================================================================ build side (build.py)
def has_data(tex):
    return bool(DATA.search(tex))


def has_map(n):
    """A card with its own sub-map: its children do not fit on it as one grey line."""
    return bool(n["kids"]) and (len(n["kids"]) >= 4 or any(k["kids"] for k in n["kids"]))


def is_card(n):
    """A card on some map: an item of a part, or a child of a card that has a sub-map. Otherwise a detail."""
    p = n["parent"]
    return p is None or has_map(p)


def stats(tex):
    """(parts, cards) of every map in a body, for the cover."""
    parts = cards = 0
    for m in DATA.finditer(tex):
        d = json.loads(m.group(1))
        parts += len(d["parts"])
        for p in d["parts"]:
            for k in p["kids"]:
                k["parent"] = None
            for x in walk([p]):
                for k in x["kids"]:
                    k["parent"] = x
            cards += sum(1 for x in walk([p]) if is_card(x))
    return parts, cards


class Map:
    """One ::: {.mindmap} block of a build: its data, link names and colours."""
    def __init__(self, data, index):
        self.d, self.p = data, f"mm{index}-"
        self.parts = data["parts"]
        for i, part in enumerate(self.parts, 1):
            part["n"], part["col"] = i, colour(i)
            for j, k in enumerate(part["kids"], 1):
                self._number(k, f"{i}-{j}", None, i)
        self.keys = {}
        for x in walk(self.parts):
            self.keys.setdefault(x["key"], x)

    def _number(self, n, ident, parent, part):
        n.update(id=ident, parent=parent, part=part, col=colour(part))
        for j, k in enumerate(n["kids"], 1):
            self._number(k, f"{ident}-{j}", n, part)

    def paginate(self, z, width):
        """The parts of each main-map page; P: the parts a page is laid out for (the fullest page)."""
        sizes = page_sizes(len(self.parts), per_page(z, width))
        self.P, self.pages, i = sizes[0], [], 0
        for n in sizes:
            self.pages.append(self.parts[i:i + n])
            i += n

    def card(self, n):
        return f"{self.p}card-{n['id']}"

    def row(self, n):
        return f"{self.p}row-{n['id']}"

    def sub(self, n):
        return f"{self.p}map-{n['id']}"

    def shown(self, n):
        """The card that shows n: n itself, or the card that lists it as a grey line."""
        return self.card(n) if is_card(n) else self.shown(n["parent"])


# ---------------------------------------------------------------- card contents
def lines(mp, n, z, grey=True, full=True):
    out = [rf"{{{z['title']}\bfseries {n['title']}}}{star(n)}"]
    if full and n["formula"]:   # an equation alone is scaled down if it is wider than the card; text wraps
        out.append(rf"\mmfit{{{n['formula']}}}" if re.fullmatch(r"\$[^$]+\$", n["formula"]) else n["formula"])
    if full and grey and n["kids"] and not has_map(n) and mp.d.get("detail") is not False:
        out.append(rf"{{\color{{mmsoft}}{z['detail']} " + r" $\cdot$ ".join(k["title"] for k in n["kids"]) + "}")
    if full:
        for c in n["chips"]:
            target = mp.keys.get(c["key"])
            out.append(rf"\mmchip{{{n['col']}}}{{{mp.shown(target) if target else ''}}}{{{c['text']}}}")
    return r"\\[1pt]".join(out)


def star(n, space=r"\,"):
    return space + r"{\color{mmstar}$\bigstar$}" if n["star"] else ""


VARIANTS = {"full": dict(grey=True, full=True), "nogrey": dict(grey=False, full=True), "title": dict(grey=False, full=False)}


def text_w(cardw, z):
    return cardw - z["strip"] - z["sep"] * PT


def slot(z, width, slots):
    """The width of one main-map column when the page holds `slots` of them (never wider than maxslot)."""
    return min(width / slots, z["maxslot"])


def per_page(z, width):
    """The most parts one main-map page holds: each column at least minslot wide."""
    return max(1, int(width / z["minslot"] + 1e-9))


def page_sizes(n, most):
    """n parts over as few main-map pages as hold them, spread evenly (7 over pages of 6: 4 + 3)."""
    pages = -(-n // most)
    q, r = divmod(n, pages)
    return [q + 1] * r + [q] * (pages - r)


def main_widths(parts, z, width):
    """{columns on the page: card width} for a page laid out for `parts` parts, each splittable once."""
    out = {}
    for slots in range(parts, 2 * parts + 1):
        s = slot(z, width, slots)
        if s >= z["minslot"]:
            out[slots] = round(s - z["sgap"] - 0.3, 3)
    return out


def sub_width(z, width):
    return round(width / z["subslots"] - z["sgap"] - 0.3, 3)


def trail(mp, n):
    """The grey line over a sub-map's heading: where its card sits."""
    par = n["parent"]
    if par is None:
        return mp.parts[n["part"] - 1]["name"]
    return par["title"] if par["parent"] is None else f"{par['parent']['title']} \\mmsep {par['title']}"


def head_text(z, trail_text, title, formula=""):
    """A sub-map heading's lines: the trail in grey, the card's title, its formula."""
    return (rf"{{\color{{white!85!black}}\scriptsize {trail_text}}}\\{{{z['part']}\bfseries $\hookleftarrow$ {title}}}"
            + (rf"\\{formula}" if formula else ""))


def cont_title(title):
    return title.split(" (continued)")[0] + " (continued)"


def measure(maps, z, width, build, main_tex):
    """Heights (cm) of every card in every variant at every width it can get, part and sub-map headings, and the
    text height: one XeLaTeX run with the build's own preamble."""
    keys, seen, body = [], set(), [r"\newsavebox\mmmb"]

    def box(key, content):
        if key in seen:
            return
        seen.add(key)
        keys.append(key)
        body.append(rf"\sbox\mmmb{{{content}}}\typeout{{MMH|{len(keys) - 1}|\the\ht\mmmb|\the\dp\mmmb}}")

    def head(key, w, text):   # a sub-map heading over one column: text width w + 0.3 - 12pt
        box(key, rf"{z['font']}\hyphenpenalty10000\exhyphenpenalty10000\begin{{minipage}}[t]{{\dimexpr{w + 0.3:.3f}cm-12pt}}"
                 rf"\raggedright {text}\end{{minipage}}")
    for mp in maps:
        sw = sub_width(z, width)
        ws = sorted(set(main_widths(mp.P, z, width).values()) | {sw})
        for x in walk(mp.parts):
            if not is_card(x):
                continue
            for w in ws:   # every width: a card may sit on the main map, a sub-map page or beside its parent
                for v, opt in VARIANTS.items():
                    box((mp.p, x["id"], w, v), rf"{z['font']}\begin{{minipage}}[t]{{{text_w(w, z):.3f}cm}}\raggedright "
                                              rf"{lines(mp, x, z, **opt)}\end{{minipage}}")
            if has_map(x):
                for w in ws:
                    head((mp.p, "sh-" + x["id"], w, "head"), w, head_text(z, trail(mp, x), x["title"] + star(x), x["formula"]))
                head((mp.p, "ch-" + x["id"], sw, "head"), sw, head_text(z, trail(mp, x), cont_title(x["title"] + star(x))))
        for part in mp.parts:
            for slots in range(mp.P, 2 * mp.P + 1):
                for k in (1, 2):
                    span = round(k * slot(z, width, slots) - z["sgap"], 3)
                    box((mp.p, f"head{part['n']}", span, "head"),
                        rf"\begin{{minipage}}[t]{{\dimexpr{span:.3f}cm-12pt}}\centering\bfseries{z['part']} {part['name']}\\[-1pt]"
                        rf"{{\normalfont\footnotesize Part {part['n']}}}\end{{minipage}}")
            head((mp.p, f"ch-p{part['n']}", sw, "head"), sw, head_text(z, f"Part {part['n']}", cont_title(part["name"])))
    body.append(r"\typeout{MMH|TH|\the\textheight|0pt}")
    pre = main_tex[:main_tex.index("\\begin{document}")]
    (build / "mmmeasure.tex").write_text(pre + "\\begin{document}\n" + "\n".join(body) + "\n\\end{document}\n", encoding="utf-8")
    engine = shutil.which("xelatex") or "xelatex"
    subprocess.run([engine, "-interaction=nonstopmode", "-halt-on-error", "mmmeasure.tex"], cwd=build,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log = (build / "mmmeasure.log").read_text(errors="replace") if (build / "mmmeasure.log").exists() else ""
    heights, th = {}, None
    for m in re.finditer(r"MMH\|(\w+)\|([\d.]+)pt\|([\d.]+)pt", log):
        if m.group(1) == "TH":
            th = float(m.group(2)) * PT
        else:
            heights[keys[int(m.group(1))]] = (float(m.group(2)) + float(m.group(3))) * PT
    if th is None or len(heights) != len(keys):
        sys.exit(f"mind map: measuring the cards failed -- see {build / 'mmmeasure.log'}")
    return heights, th


# ---------------------------------------------------------------- fitting
# A column that is too tall takes these steps, each as little as needed (types/mind-map/guide.md):
#   with room for two columns:  1 gaps  2 grey lines  3 split into two  4 title-only cards  5 "+n more"
#   without:                    1 gaps  2 grey lines  3 title-only cards  4 "+n more"
# Fit.step holds the first list's number; describe() prints the second list's number for a column that did not split.
GAPS, GREY, SPLIT, TITLE, MORE = 1, 2, 3, 4, 5


class Fit:
    """How one column group (a part, a sub-map or a continuation) is laid out."""
    def __init__(self, cards):
        self.cards = list(cards)
        self.gap = None
        self.variant = {c["id"]: "full" for c in cards}
        self.columns = [self.cards]
        self.moved = []
        self.step = 0
        self.hidden = self.collapsed = 0


class Fitter:
    def __init__(self, mp, z, H):
        self.mp, self.z, self.H = mp, z, H

    def card_h(self, c, variant, w):
        h = self.H[(self.mp.p, c["id"], w, variant)] + 2 * self.z["sep"] * PT + 0.03
        return max(h, self.z["tall"]) if has_map(c) else h

    def col_h(self, cards, f, w):
        if not cards:
            return 0.0
        return sum(self.card_h(c, f.variant[c["id"]], w) for c in cards) + f.gap * (len(cards) - 1)

    def fits(self, f, w, avail):
        return all(self.col_h(col, f, w) <= avail for col in f.columns)

    def balance(self, cards, f, w):
        """Two columns in reading order, the taller one as short as possible."""
        best = None
        for k in range(1, len(cards)):
            t = max(self.col_h(cards[:k], f, w), self.col_h(cards[k:], f, w))
            if best is None or t < best[0]:
                best = (t, k)
        k = best[1] if best else len(cards)
        return [cards[:k], cards[k:]]

    def shrink(self, f, w, avail, steps, two, collapse=True):
        """Gaps, grey lines, title-only cards, each as little as needed; steps: the step number of each."""
        z = self.z

        def again():
            if two:
                f.columns = self.balance(f.cards, f, w)
            return self.fits(f, w, avail)
        f.gap = z["gap"]
        if again():
            return True
        f.gap = z["gapmin"]
        f.step = max(f.step, steps[0])
        if again():
            return True
        for c in [c for c in reversed(f.cards) if c["kids"] and not has_map(c)]:
            f.variant[c["id"]] = "nogrey"
            f.step, f.hidden = max(f.step, steps[1]), f.hidden + 1
            if again():
                return True
        if not collapse:
            return False
        one = [c for c in reversed(f.cards) if not has_map(c)]
        for c in [c for c in one if not c["star"]] + [c for c in one if c["star"]]:
            f.variant[c["id"]] = "title"
            f.step, f.collapsed = max(f.step, steps[2]), f.collapsed + 1
            if again():
                return True
        return False

    def one_column(self, cards, w, avail, collapse=True):
        """Steps 1-2, and title-only cards when collapse is True."""
        f = Fit(cards)
        return f if self.shrink(f, w, avail, (GAPS, GREY, TITLE), False, collapse) else None

    def two_columns(self, cards, w, avail):
        """The split (step 3): grey lines back wherever they fit, then title-only cards (step 4)."""
        f = Fit(cards)
        f.step = SPLIT
        return f if len(cards) > 1 and self.shrink(f, w, avail - 0.2, (SPLIT, SPLIT, TITLE), True) else None

    def continue_on(self, cards, w, avail, two):
        """The last step: keep the first cards (whole if possible), the rest moves to a continuation group."""
        room = avail - self.z["more"] - self.z["gapmin"] - (0.2 if two else 0)
        for collapse in (False, True):
            for keep in range(len(cards) - 1, 0, -1):
                f = Fit(cards[:keep])
                if two and keep < 2:
                    break
                if self.shrink(f, w, room, (MORE, MORE, MORE), two, collapse):
                    f.step, f.moved = MORE, list(cards[keep:])
                    return f
        return None

    def column(self, cards, w, avail, room):
        """A group in the agreed order; room: a second column is free (the two-column sequence)."""
        if room:
            return (self.one_column(cards, w, avail, collapse=False) or self.two_columns(cards, w, avail)
                    or self.continue_on(cards, w, avail, True))
        return self.one_column(cards, w, avail) or self.continue_on(cards, w, avail, False)

    def beside(self, cards, w, avail):
        """A sub-map beside its card: one column, at most steps 1-2, never continued."""
        return self.one_column(cards, w, avail, collapse=False)


def describe(f, z):
    if not f.step:
        return ""
    two = len(f.columns) == 2
    bits = ["split into two columns"] if two else []
    if f.gap == z["gapmin"]:
        bits.append("gaps tightened")
    if f.hidden:
        bits.append(f"grey lines hidden on {f.hidden} card{'s' * (f.hidden > 1)}")
    if f.collapsed:
        bits.append(f"{f.collapsed} card{'s' * (f.collapsed > 1)} shown as the title only")
    if f.moved:
        bits.append(f"{len(f.moved)} card{'s' * (len(f.moved) > 1)} continue on a sub-map page")
    step = f.step if two or f.step < TITLE else f.step - 1
    return f"step {step} ({', '.join(bits)})"


def head_h(fit, mp, z, p, span):
    """The drawn height of a part heading over `span` cm."""
    return max(fit.H[(mp.p, f"head{p['n']}", span, "head")] + 8 * PT, z["partmin"])


def layout_main(mp, parts, fit, z, width, budget, split):
    """One main-map page: each part's Fit and the column width. split=False never splits (a part that is too tall
    takes the one-column sequence). A page with fewer parts than mp.P keeps the width of a full page, so it can
    split parts without narrowing anything."""
    base = budget - (z["gap"] + 0.15)
    widths = main_widths(mp.P, z, width)
    cols = {p["n"]: 1 for p in parts}
    for _ in range(2 * len(parts) + 2):
        slots = max(sum(cols.values()), mp.P)
        s = slot(z, width, slots)
        w = widths[slots]
        out, changed = {}, False
        for p in parts:
            span = round(cols[p["n"]] * s - z["sgap"], 3)
            avail = base - head_h(fit, mp, z, p, span)
            if cols[p["n"]] == 1:
                f = fit.one_column(p["kids"], w, avail, collapse=False)
                if f is None and split and len(p["kids"]) > 1 and max(sum(cols.values()) + 1, mp.P) in widths:
                    cols[p["n"]] = 2
                    changed = True
                    break
                f = f or fit.one_column(p["kids"], w, avail) or fit.continue_on(p["kids"], w, avail, False)
            else:
                f = fit.two_columns(p["kids"], w, avail) or fit.continue_on(p["kids"], w, avail, True)
            if f is None:
                sys.exit(f"mind map: part '{plain(p['name'])}' does not fit the {width:.0f} cm wide map even with a "
                         "continuation column; give it fewer cards or use map_size: a3")
            out[p["n"]] = f
        if not changed:
            return out, s
    sys.exit("mind map: the layout did not settle")


def fit_main(mp, parts, fit, z, width, budget):
    """Splits allowed, unless a split makes another part take a later step (then nothing splits)."""
    calm, s_calm = layout_main(mp, parts, fit, z, width, budget, split=False)
    bold, s_bold = layout_main(mp, parts, fit, z, width, budget, split=True)
    split = [n for n, f in bold.items() if len(f.columns) == 2]
    if split and all(bold[n].step <= calm[n].step for n in bold if n not in split):
        return bold, s_bold
    return calm, s_calm


def sub_groups(mp, fit, z, width, th, main, skip):
    """The sub-map pages' groups in order: every part's continuation first (the main map ends there), then every
    card with a sub-map, in course order. skip: cards whose sub-map already sits beside them on a main-map page."""
    w = sub_width(z, width)
    avail = th - RESERVE_SUB
    groups = []

    def add(title, trail_text, cards, head_node, back, target, part, cont, hh):
        while cards:
            f = fit.column(cards, w, avail, True)
            if f is None:
                sys.exit(f"mind map: '{plain(title)}' does not fit a sub-map page")
            groups.append(dict(title=title, trail=trail_text, fit=f, node=head_node, back=back, target=target, part=part,
                               cont=cont, hh=hh))
            if not f.moved:
                break
            cards = f.moved
            title, cont, back, target = cont_title(title), True, target, target + "c"
            hh = fit.H[(mp.p, f"ch-p{part}" if head_node is None else "ch-" + head_node["id"], w, "head")] + 12 * PT

    def nested(n):
        for k in n["kids"]:
            if has_map(k) and k["id"] not in skip:
                add(k["title"] + star(k), trail(mp, k), k["kids"], k, mp.card(k), mp.sub(k), k["part"], False,
                    fit.H[(mp.p, "sh-" + k["id"], w, "head")] + 12 * PT)
            nested(k)
    for p in mp.parts:
        f = main[p["n"]]
        if f.moved:
            add(cont_title(p["name"]), f"Part {p['n']}", f.moved, None, f"{mp.p}part-{p['n']}", f"{mp.p}cont-{p['n']}",
                p["n"], True, fit.H[(mp.p, f"ch-p{p['n']}", w, "head")] + 12 * PT)
    for p in mp.parts:
        nested(p)
    return groups


def column_tops(fit, f, col, top, w):
    """[(card, its top)] of one column of a group whose cards start `top` cm below the picture's top."""
    out, y = [], top
    for c in col:
        out.append((c, y))
        y += fit.card_h(c, f.variant[c["id"]], w) + f.gap
    return out


def side_columns(mp, fit, z, left, ceiling, x, free, budget, widths, pending):
    """Sub-maps beside their cards, in the space right of the last column. left: [(card, top)] of that column;
    ceiling: the bottom of the heading over it; pending: ids of cards whose sub-map may move here. A sub-map takes
    the next column only when its card is in the column directly to its left; it starts level with its card (the
    first one of a column may start higher, but never above the ceiling) and fits in one column with at most
    steps 1-2. Returns [(x, card width, [placement])] and updates pending."""
    out = []
    while left:
        ws = [w for w in widths if w + 0.3 <= free + 1e-6]
        if not ws:
            break
        w = max(ws)
        placed, bottom = [], None
        for c, ctop in left:
            if not has_map(c) or c["id"] not in pending:
                continue
            hh = fit.H[(mp.p, "sh-" + c["id"], w, "head")] + 12 * PT
            lead = hh + 0.15 + z["gap"] + 0.1   # heading, the drop to the first card, a margin
            f, top = None, ctop
            if bottom is None or ctop >= bottom + 0.4:
                f = fit.beside(c["kids"], w, budget - ctop - lead)
            if f is None and bottom is None:   # the first sub-map of a column may start higher, down from the ceiling
                f = fit.beside(c["kids"], w, budget - ceiling - lead)
                if f is not None:
                    top = max(ceiling, budget - (lead + fit.col_h(f.cards, f, w)))
            if f is None:
                continue
            placed.append(dict(node=c, fit=f, top=top, hh=hh, level=top == ctop))
            bottom = top + lead + fit.col_h(f.cards, f, w)
            pending.discard(c["id"])
        if not placed:
            break
        out.append((x, w, placed))
        ceiling = placed[0]["top"] + placed[0]["hh"]
        left = [t for p in placed for t in column_tops(fit, p["fit"], p["fit"].cards, p["top"] + p["hh"] + p["fit"].gap + 0.15, w)]
        step = w + 0.3 + z["sgap"]
        x, free = x + step, free - step
    return out


# ---------------------------------------------------------------- drawing
def draw_card(mp, n, where, w, z, variant):
    sub = mp.sub(n) if has_map(n) else ""
    tall = f", minimum height={z['tall']}cm" if sub else ""
    return (rf"\node[mmcard={{CoverPart{n['col']}}}{tall}, anchor=north west, font={z['font']}, inner sep={z['sep']}pt, "
            rf"text width={w:.3f}cm-{2 * z['sep']}pt] ({mp.card(n)}) at ({where}) {{\hypertarget{{{mp.card(n)}}}{{}}"
            rf"\begin{{minipage}}[t]{{{text_w(w, z):.3f}cm}}\raggedright {lines(mp, n, z, **VARIANTS[variant])}\end{{minipage}}}};" "\n"
            rf"\mmstrip{{{mp.card(n)}}}{{{n['col']}}}{{{z['strip']}}}{{{mp.row(n)}}}{{{sub}}}{{{len(n['kids'])}}}")


def draw_group(mp, head_code, head, col, s, f, z, more=None):
    """A heading over one or two columns of cards (col: the part colour number); the stems hang from the heading (from a short bus for two)."""
    out = [head_code]
    two = len(f.columns) == 2
    w = s - z["sgap"] - 0.3
    drop = 0.2 if two else 0
    last = None
    for j, cards in enumerate(f.columns):
        stem = f"($({head}.south west)+({j * s + 0.12:.3f},{-drop})$)"
        prev = None
        for c in cards:
            where = (f"$({head}.south west)+({j * s + 0.3:.3f},-{f.gap + 0.15 + drop:.3f})$" if prev is None
                     else f"$({mp.card(prev)}.south west)+(0,-{f.gap:.3f})$")
            out.append(draw_card(mp, c, where, w, z, f.variant[c["id"]]))
            out.append(rf"\draw[mmstem=CoverPart{col}] {stem} |- ({mp.card(c)}.west);")
            prev = c
        last = (prev, stem)
    if more:
        prev, stem = last
        out.append(rf"\node[mmmore={{CoverPart{col}}}, anchor=north west, text width={w:.3f}cm-12pt, font={z['font']}] "
                   rf"({head}more) at ($({mp.card(prev)}.south west)+(0,-{f.gap:.3f})$) "
                   rf"{{\bfseries +{len(f.moved)} more \hfill $\blacktriangleright$}};" "\n"
                   rf"\mmnodelink{{{head}more}}{{{more}}}" "\n"
                   rf"\draw[mmstem=CoverPart{col}] {stem} |- ({head}more.west);")
    if two:
        out.append(rf"\draw[mmstem=CoverPart{col}] ($({head}.south west)+(0.12,0)$) -- ++(0,-0.2) -- ++({s:.3f},0);")
    return "\n".join(out)


def draw_subgroup(mp, g, hn, where, s, z):
    """A sub-map (or continuation) group: its heading at `where`, linked back to the card it extends."""
    f, n = g["fit"], g["node"]
    span = len(f.columns) * s - z["sgap"]
    formula = n["formula"] if n is not None and not g["cont"] else ""
    head = (rf"\node[mmsubhead={{CoverPart{colour(g['part'])}}}, text width={span:.3f}cm-12pt, anchor=north west, font={z['font']}] "
            rf"({hn}) at ({where}) {{\hypertarget{{{g['target']}}}{{}}{head_text(z, g['trail'], g['title'], formula)}}};" "\n"
            rf"\mmnodelink{{{hn}}}{{{g['back']}}}")
    return draw_group(mp, head, hn, colour(g["part"]), s, f, z, more=g["target"] + "c" if f.moved else None)


def draw_sides(mp, sides, z):
    """Sub-maps beside their cards, each joined to its card's map button by a line."""
    out = []
    for x, w, placed in sides:
        for pl in placed:
            n = pl["node"]
            hn = f"{mp.p}side-{n['id']}"
            where = rf"{mp.card(n)}.north -| {x:.3f},0" if pl["level"] else f"{x:.3f},{-pl['top']:.3f}"
            g = dict(fit=pl["fit"], node=n, cont=False, part=n["part"], trail=trail(mp, n), title=n["title"] + star(n),
                     target=mp.sub(n), back=mp.card(n))
            out.append(draw_subgroup(mp, g, hn, where, w + 0.3 + z["sgap"], z))
            gx = x - z["sgap"] / 2
            out.append(rf"\coordinate ({hn}btn) at ($({mp.card(n)}.south east)!0.25!({mp.card(n)}.north east)$);" "\n"
                       rf"\draw[mmstem=CoverPart{n['col']}] ({hn}btn) -- ({hn}btn -| {gx:.3f},0) |- ({hn}.west);")
    return "\n".join(out)


def header(mp, left, right):
    return rf"\mmheader{{{left}}}{{{right}}}"


def main_page(mp, i, pages, main, s, z, sides):
    """Main-map page i (0-based) of len(pages): its parts under the course heading, sub-maps beside their cards."""
    d, parts, k = mp.d, pages[i], len(pages)
    rng = f"{parts[0]['n']}--{parts[-1]['n']}" if len(parts) > 1 else f"{parts[0]['n']}"
    nxt = (rf"\mmlinkbox{{{mp.p}page{i + 2}}}{{parts {pages[i + 1][0]['n']}--{pages[i + 1][-1]['n']} \mmarrow}}\quad "
           if i + 1 < k else "")
    title = r"{\bfseries Mind map}" + (rf": {d['title']}" if d["title"] else "") + (rf" \mmsep page {i + 1} of {k}" if k > 1 else "")
    out = [r"\clearpage", rf"\hypertarget{{{mp.p}top}}{{}}" if i == 0 else "", rf"\hypertarget{{{mp.p}page{i + 1}}}{{}}",
           header(mp, title, nxt + rf"\mmlinkbox{{{mp.p}table}}{{outline table \mmarrow}}"),
           r"\mmlegend", r"\vfill\begin{center}" + z["fonts"] + r"\begin{tikzpicture}[x=1cm, y=1cm]"]
    x, heads = 0.0, []
    for p in parts:
        f, n = main[p["n"]], p["n"]
        span = len(f.columns) * s - z["sgap"]
        hn = f"{mp.p}head{n}"
        sub = rf"Part {n}" + (rf" $\cdot$ {p['sub']}" if p["sub"] else "")
        head = (rf"\node[mmpart={{CoverPart{p['col']}}}, text width={span:.3f}cm-12pt, font=\bfseries{z['part']}, minimum height={z['partmin']}cm, "
                rf"anchor=north west] ({hn}) at ({x:.3f},0) {{\hypertarget{{{mp.p}part-{n}}}{{}}{p['name']}\\[-1pt]"
                rf"{{\normalfont\footnotesize {sub}}}}};" "\n" rf"\mmnodelink{{{hn}}}{{{mp.p}table-{n}}}")
        out.append(draw_group(mp, head, hn, p["col"], s, f, z, more=f"{mp.p}cont-{n}" if f.moved else None))
        heads.append(hn)
        x += len(f.columns) * s
    if d["title"]:
        mid = (x - z["sgap"]) / 2
        sub = d["sub"] + (rf" $\cdot$ parts {rng}" if k > 1 else "")
        out.append(rf"\node[mmcourse, anchor=south, font=\bfseries{z['headfont']}] ({mp.p}course{i}) at ({mid:.3f},0.55) "
                   rf"{{{d['title']}" + (rf"\\[-1pt]{{\normalfont\footnotesize {sub}}}" if sub else "") + "};\n"
                   rf"\mmnodelink{{{mp.p}course{i}}}{{{mp.p}table}}")
        # every line straight: drops fall from each heading's own centre, the bus runs between the outer ones
        out.append(rf"\draw[mmbus] ({mp.p}course{i}.south) -- ({mp.p}course{i}.south |- 0,0.27);")
        out.append(rf"\draw[mmbus] ({heads[0]}.north |- 0,0.27) -- ({heads[-1]}.north |- 0,0.27);")
        out += [rf"\draw[mmbus] ({h}.north |- 0,0.27) -- ({h}.north);" for h in heads]
    out.append(draw_sides(mp, sides, z))
    out.append(r"\end{tikzpicture}\end{center}\vfill")
    return "\n".join(o for o in out if o)


def sub_pages(mp, pages, s, z):
    out = []
    for items in pages:
        body = [r"\clearpage",
                header(mp, rf"\mmlinkbox{{{mp.p}top}}{{Mind map}} \mmsep {{\bfseries Sub-maps}}: each heading is the card it extends",
                       rf"\mmlinkbox{{{mp.p}top}}{{$\hookleftarrow$ the map}}"),
                r"\mmlegend", r"\vfill\begin{center}" + z["fonts"] + r"\begin{tikzpicture}[x=1cm, y=1cm]"]
        for kind, x, it in items:
            if kind == "group":
                body.append(draw_subgroup(mp, it, f"{mp.p}sh-{it['target']}", f"{x:.3f},0", s, z))
            else:
                body.append(draw_sides(mp, [it], z))
        body.append(r"\end{tikzpicture}\end{center}\vfill")
        out.append("\n".join(body))
    return "\n\n".join(out)


def pack_sub(mp, fit, z, width, th, groups, pending):
    """Sub-map pages: the groups in order, as many as fit side by side. A group that is the sub-map of a card in
    the column just to its left sits beside that card (level with it, joined by a line) when it fits there; a
    page's free columns at the end take such sub-maps from later in the order."""
    ss, sw = width / z["subslots"], sub_width(z, width)
    budget = th - RESERVE_MAIN - 0.3
    queue, pages = list(groups), []

    def regular(g):
        return g["node"] is not None and not g["cont"]

    def beside(left, ceiling, x, free, ids):
        sides = side_columns(mp, fit, z, left, ceiling, x, free, budget, [sw], ids)
        moved = {pl["node"]["id"] for _, _, placed in sides for pl in placed}
        return sides, moved
    while queue:
        items, x, left, ceiling = [], 0.0, None, 0.0
        while queue:
            g = queue[0]
            if left and regular(g):   # the next sub-map in order extends a card of the column on its left
                cards = {c["id"] for c, _ in left}
                run = set()
                for h in queue:
                    if not (regular(h) and h["node"]["id"] in cards):
                        break
                    run.add(h["node"]["id"])
                if run:
                    sides, moved = beside(left, ceiling, x, width - x, run & pending)
                    if moved:
                        for col in sides:
                            items.append(("side", col[0], col))
                            x = col[0] + col[1] + 0.3 + z["sgap"]
                        pending -= moved
                        queue = [h for h in queue if h["node"] is None or h["node"]["id"] not in moved]
                        last_x, last_w, placed = sides[-1]
                        ceiling = placed[0]["top"] + placed[0]["hh"]
                        left = [t for pl in placed for t in column_tops(fit, pl["fit"], pl["fit"].cards,
                                                                       pl["top"] + pl["hh"] + pl["fit"].gap + 0.15, last_w)]
                        continue
            k = len(g["fit"].columns)
            if items and x + k * ss > width + 1e-6:
                break
            queue.pop(0)
            items.append(("group", x, g))
            f = g["fit"]
            left = column_tops(fit, f, f.columns[-1], g["hh"] + f.gap + 0.15 + (0.2 if k == 2 else 0), sw)
            ceiling = g["hh"]
            x += k * ss
        if left and queue:   # free columns at the end of the page: sub-maps pulled forward to sit beside their cards
            ids = {g["node"]["id"] for g in queue if regular(g)} & pending
            sides, moved = beside(left, ceiling, x, width - x, ids)
            for col in sides:
                items.append(("side", col[0], col))
            pending -= moved
            queue = [h for h in queue if h["node"] is None or h["node"]["id"] not in moved]
        pages.append(items)
    return pages, ss


# ---------------------------------------------------------------- outline table
class Table:
    def __init__(self, mp, width):
        self.mp, self.defw = mp, width - sum(TABLE_W.values())

    def m(self, w, extra="", rules=1, pads=2, align=r"\raggedright", indent=False):
        """A column w cm wide in all: less its padding (none beside an @{}) and the rules beside it."""
        post = r"\leftskip\tabcolsep" if indent else ""
        return rf">{{{extra}{align}\arraybackslash{post}}}m{{\dimexpr{w:.3f}cm-{pads}\tabcolsep-{rules}\arrayrulewidth}}"

    def tint(self, n, level):
        if n is not None and is_card(n):
            return rf"\columncolor{{CoverPart{n['col']}!{TINT[level]}}}[0pt][\tabcolsep]"
        return r"\columncolor{white}[0pt][\tabcolsep]"

    def name(self, n):
        label = rf"\mmname{{{n['col']}}}{{{n['title']}}}" if is_card(n) else rf"\mmdetail{{{n['title']}}}"
        return rf"\hypertarget{{{self.mp.row(n)}}}{{}}{label}{star(n, ' ')}"   # the star may wrap in a narrow column

    def leaf(self, label_w, label, n, level, back, rules=1):
        """[label | what it is | key formula | map] as one tabular; label None: the node's own "in general" row."""
        W = TABLE_W
        spec = ("@{}" + self.m(label_w, self.tint(n if label is not None else None, level), rules=rules, pads=1, indent=True)
                + "|" + self.m(self.defw) + "|" + self.m(W["fx"]) + "|@{}" + self.m(W["bk"], pads=0, align=r"\centering") + "@{}")
        if label is None:
            label = r"{\itshape\color{mmsoft} in general}"
        defn = n["defn"] or r"{\color{mmsoft}--}"
        return (rf"\begin{{tabular}}{{{spec}}}{label} & {defn} & {n['formula']} & \mmback{{{n['col']}}}{{{back}}}\\"
                r"\end{tabular}")

    def nest(self, n, level):
        """n's children, in column `level` (3 or 4), as one tabular. Deeper levels are listed in column 4."""
        W, mp = TABLE_W, self.mp
        widths = {3: W["l3"] + W["l4"], 4: W["l4"]}
        rows = []
        if n["defn"] or n["formula"]:
            rows.append(self.leaf(widths[level], None, n, level, mp.shown(n)))
        for k in n["kids"]:
            if k["kids"] and level == 3:
                spec = ("@{}" + self.m(W["l3"], self.tint(k, 3), pads=1, indent=True) + "|@{}"
                        + self.m(W["l4"] + self.defw + W["fx"] + W["bk"], pads=0) + "@{}")
                rows.append(rf"\begin{{tabular}}{{{spec}}}{self.name(k)} & {self.nest(k, 4)}\\\end{{tabular}}")
            else:
                rows.append(self.leaf(widths[level], self.name(k), k, level, mp.shown(k)))
                if k["kids"]:   # below the fourth level: listed under it, in the same column
                    for x in walk([k]):
                        rows.append(self.leaf(widths[level], r"\quad$\cdot$\ " + self.name(x), x, level, mp.shown(x)))
        return r"\begin{tabular}{@{}l@{}}" + r"\\ \hline ".join(rows) + r"\\ \end{tabular}"

    def render(self):
        mp, W = self.mp, TABLE_W
        total = sum(W.values()) + self.defw
        rest = total - W["l2"]
        out = [r"\clearpage", rf"\hypertarget{{{mp.p}table}}{{}}",
               header(mp, rf"\mmlinkbox{{{mp.p}top}}{{Mind map}} \mmsep {{\bfseries Outline table}}",
                      rf"\mmlinkbox{{{mp.p}top}}{{back to the map \mmarrow}}"),
               r"{\color{mmsoft}\small One row per idea, every level in its own column. {\bfseries\color{CoverPart1!75!black}Coloured}: "
               r"a card on a map; \mmdetail{dark grey}: a detail, shown as a grey line on its card. "
               rf"\mmback{{w}}{{{mp.p}top}} goes back to the card on the map.\par}}\vspace{{4pt}}"]
        hd = r"\columncolor{gray!12}"
        for p in mp.parts:
            i = p["n"]
            spec = "|" + self.m(W["l2"], rf"\columncolor{{CoverPart{p['col']}!{TINT[2]}}}", rules=2) + "|@{}" + self.m(rest, pads=0) + "@{}|"
            band = (rf"\multicolumn{{2}}{{|>{{\columncolor{{CoverPart{p['col']}}}}}m{{\dimexpr{total:.3f}cm-2\tabcolsep-2\arrayrulewidth}}|}}"
                    rf"{{\rule{{0pt}}{{14pt}}\color{{white}}\bfseries \hypertarget{{{mp.p}table-{i}}}{{}}PART {i}\quad {p['name']}\quad"
                    rf"{{\normalfont\small {p['sub']}}}\hfill{{\normalfont\small\mmlinkbox{{{mp.p}part-{i}}}{{\color{{white}}the map \mmarrow}}}}}}")
            head = (r"{\scriptsize\bfseries TOPIC} & \begin{tabular}{@{}" + self.m(W["l3"], hd + "[0pt][\\tabcolsep]", pads=1, indent=True)
                    + "|" + self.m(W["l4"], hd) + "|" + self.m(self.defw, hd) + "|" + self.m(W["fx"], hd) + "|@{}"
                    + self.m(W["bk"], hd + "[0pt][0pt]", pads=0, align=r"\centering") + "@{}}"
                    r"\scriptsize\bfseries INSIDE & \scriptsize\bfseries INSIDE & \scriptsize\bfseries WHAT IT IS & "
                    r"\scriptsize\bfseries KEY FORMULA & \scriptsize\bfseries MAP\end{tabular}")
            cont = (rf"\multicolumn{{2}}{{|>{{\columncolor{{CoverPart{p['col']}!65}}}}m{{\dimexpr{total:.3f}cm-2\tabcolsep-2\arrayrulewidth}}|}}"
                    rf"{{\rule{{0pt}}{{12pt}}\color{{white}}\bfseries\small PART {i}\quad {p['name']}\quad\normalfont(continued)}}")
            out += [rf"\begin{{longtable}}{{{spec}}}",
                    r"\hline " + band + r" \\ \hline " + head + r" \\ \hline \endfirsthead",
                    r"\hline " + cont + r" \\ \hline " + head + r" \\ \hline \endhead",
                    r"\hline \endfoot \endlastfoot"]
            for k in p["kids"]:
                if k["kids"]:
                    out.append(rf"{self.name(k)} & {self.nest(k, 3)} \\ \hline")
                else:
                    leaf = self.leaf(W["l2"] + W["l3"] + W["l4"], self.name(k), k, 2, mp.shown(k), rules=2)
                    out.append(rf"\multicolumn{{2}}{{|@{{}}l@{{}}|}}{{{leaf}}} \\ \hline")
            out.append(r"\end{longtable}")
        return "\n".join(out)


# ---------------------------------------------------------------- the build step
def render(copies, build, main_tex, paper, width, log=print):
    """Replace every %MMDATA line in the body copies with its pages. width: the text width in cm."""
    z = SIZE[paper]
    found = []
    for copy in copies:
        for m in DATA.finditer(copy.read_text(encoding="utf-8")):
            found.append((copy, m.group(0), Map(json.loads(m.group(1)), len(found) + 1)))
    if not found:
        return
    for _, _, mp in found:
        mp.paginate(z, width)
    H, th = measure([mp for _, _, mp in found], z, width, build, main_tex)
    for copy, line, mp in found:
        fit = Fitter(mp, z, H)
        budget = th - RESERVE_MAIN - (z["heading"] + 0.55 if mp.d["title"] else 0)
        widths = sorted(set(main_widths(mp.P, z, width).values()) | {sub_width(z, width)})
        pending = {x["id"] for x in walk(mp.parts) if has_map(x)}
        main, mains = {}, []
        for i, parts in enumerate(mp.pages):
            fits, s = fit_main(mp, parts, fit, z, width, budget)
            main.update(fits)
            last, p = fits[parts[-1]["n"]], parts[-1]
            w = round(s - z["sgap"] - 0.3, 3)
            ceiling = head_h(fit, mp, z, p, round(len(last.columns) * s - z["sgap"], 3))
            top = ceiling + last.gap + 0.15 + (0.2 if len(last.columns) == 2 else 0)
            x = sum(len(fits[q["n"]].columns) for q in parts) * s
            sides = side_columns(mp, fit, z, column_tops(fit, last, last.columns[-1], top, w), ceiling, x, width - x, budget - 0.2,
                                 widths, pending)
            mains.append((s, sides))
            for _, _, placed in sides:
                for pl in placed:
                    where = f"main-map page {i + 1}" if len(mp.pages) > 1 else "the main map"
                    log(f"mind map: sub-map {plain(pl['node']['title'])} sits beside its card on {where}"
                        + (f": {describe(pl['fit'], z)}" if pl["fit"].step else ""))
        placed = {x["id"] for x in walk(mp.parts) if has_map(x)} - pending
        groups = sub_groups(mp, fit, z, width, th, main, placed)
        subs, ss = pack_sub(mp, fit, z, width, th, groups, pending)
        if len(mp.pages) > 1:
            log(f"mind map: {len(mp.parts)} parts on {len(mp.pages)} main-map pages ({' + '.join(str(len(q)) for q in mp.pages)})")
        for p in mp.parts:
            if main[p["n"]].step:
                log(f"mind map: part {p['n']} ({plain(p['name'])}): {describe(main[p['n']], z)}")
        for g in [it for items in subs for kind, _, it in items if kind == "group"]:
            if g["fit"].step:
                log(f"mind map: sub-map {plain(g['title'])}: {describe(g['fit'], z)}")
        for items in subs:
            for _, _, placed in [it for kind, _, it in items if kind == "side"]:
                for pl in placed:
                    log(f"mind map: sub-map {plain(pl['node']['title'])} sits beside its card on a sub-map page")
        pages = [main_page(mp, i, mp.pages, main, s, z, sides) for i, (s, sides) in enumerate(mains)]
        pages += [sub_pages(mp, subs, ss, z) if subs else "", Table(mp, width).render()]
        tex = copy.read_text(encoding="utf-8")
        copy.write_text(tex.replace(line, "\n\n".join(p for p in pages if p)), encoding="utf-8")
