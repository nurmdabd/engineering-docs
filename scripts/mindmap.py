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
    1 tighten the gaps   2 hide grey lines (bottom card first)   3 collapse cards with one button to their title
    (non-star first, bottom first)   4 split into two columns (formulas and grey lines back where they fit)
    5 collapse again inside the two columns   6 move the last cards to a continuation column ("+n more")
  Guard: on the main map a split narrows every column, so a split is kept only if no other part needs a later
  step because of it; otherwise that part continues instead (step 6 in one column).
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
            part["n"] = i
            for j, k in enumerate(part["kids"], 1):
                self._number(k, f"{i}-{j}", None, i)
        self.keys = {}
        for x in walk(self.parts):
            self.keys.setdefault(x["key"], x)

    def _number(self, n, ident, parent, part):
        n.update(id=ident, parent=parent, part=part)
        for j, k in enumerate(n["kids"], 1):
            self._number(k, f"{ident}-{j}", n, part)

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
            out.append(rf"\mmchip{{{n['part']}}}{{{mp.shown(target) if target else ''}}}{{{c['text']}}}")
    return r"\\[1pt]".join(out)


def star(n):
    return r"\,{\color{mmstar}$\bigstar$}" if n["star"] else ""


VARIANTS = {"full": dict(grey=True, full=True), "nogrey": dict(grey=False, full=True), "title": dict(grey=False, full=False)}


def text_w(cardw, z):
    return cardw - z["strip"] - z["sep"] * PT


def slot(z, width, slots):
    """The width of one main-map column when the page holds `slots` of them (never wider than maxslot)."""
    return min(width / slots, z["maxslot"])


def main_widths(mp, z, width):
    n = len(mp.parts)
    out = {}
    for slots in range(n, 2 * n + 1):
        s = slot(z, width, slots)
        if s >= z["minslot"]:
            out[slots] = round(s - z["sgap"] - 0.3, 3)
    return out


def sub_width(z, width):
    return round(width / z["subslots"] - z["sgap"] - 0.3, 3)


def measure(maps, z, width, build, main_tex):
    """Heights (cm) of every card in every variant at every width it can get, part headings, and the text
    height: one XeLaTeX run with the build's own preamble."""
    keys, seen, body = [], set(), [r"\newsavebox\mmmb"]

    def box(key, content):
        if key in seen:
            return
        seen.add(key)
        keys.append(key)
        body.append(rf"\sbox\mmmb{{{content}}}\typeout{{MMH|{len(keys) - 1}|\the\ht\mmmb|\the\dp\mmmb}}")
    for mp in maps:
        mains = sorted(set(main_widths(mp, z, width).values()) | {sub_width(z, width)})
        for x in walk(mp.parts):
            if not is_card(x):
                continue
            ws = mains if x["parent"] is None else [sub_width(z, width)]
            for w in ws:
                for v, opt in VARIANTS.items():
                    box((mp.p, x["id"], w, v), rf"{z['font']}\begin{{minipage}}[t]{{{text_w(w, z):.3f}cm}}\raggedright "
                                              rf"{lines(mp, x, z, **opt)}\end{{minipage}}")
        n = len(mp.parts)
        for part in mp.parts:
            for slots in range(n, 2 * n + 1):
                for k in (1, 2):
                    span = round(k * slot(z, width, slots) - z["sgap"], 3)
                    box((mp.p, f"head{part['n']}", span, "head"),
                        rf"\begin{{minipage}}[t]{{\dimexpr{span:.3f}cm-12pt}}\centering\bfseries{z['part']} {part['name']}\\[-1pt]"
                        rf"{{\normalfont\footnotesize Part {part['n']}}}\end{{minipage}}")
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
        """Steps 1-3 (or 4-5 inside two columns): gaps, grey lines, collapsing, each as little as needed."""
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

    def one_column(self, cards, w, avail):
        f = Fit(cards)
        return f if self.shrink(f, w, avail, (1, 2, 3), False) else None

    def two_columns(self, cards, w, avail):
        f = Fit(cards)
        f.step = 4
        return f if len(cards) > 1 and self.shrink(f, w, avail - 0.2, (4, 4, 5), True) else None

    def continue_on(self, cards, w, avail, two):
        """Step 6: keep the first cards (whole if possible), the rest moves to a continuation column."""
        room = avail - self.z["more"] - self.z["gapmin"] - (0.2 if two else 0)
        for collapse in (False, True):
            for keep in range(len(cards) - 1, 0, -1):
                f = Fit(cards[:keep])
                if self.shrink(f, w, room, (6, 6, 6), two, collapse):
                    f.step, f.moved = 6, list(cards[keep:])
                    return f
        return None


def describe(f, z):
    if not f.step:
        return ""
    bits = ["split into two columns"] if len(f.columns) == 2 else []
    if f.gap == z["gapmin"]:
        bits.append("gaps tightened")
    if f.hidden:
        bits.append(f"grey lines hidden on {f.hidden} card{'s' * (f.hidden > 1)}")
    if f.collapsed:
        bits.append(f"{f.collapsed} card{'s' * (f.collapsed > 1)} shown as the title only")
    if f.moved:
        bits.append(f"{len(f.moved)} card{'s' * (len(f.moved) > 1)} continue on a sub-map page")
    return f"step {f.step} ({', '.join(bits)})"


def layout_main(mp, fit, z, width, th, split):
    """Each part's Fit and the column width. split=False never splits (a part that is too tall continues)."""
    base = th - RESERVE_MAIN - (z["heading"] + 0.55 if mp.d["title"] else 0) - (z["gap"] + 0.15)
    widths = main_widths(mp, z, width)
    cols = {p["n"]: 1 for p in mp.parts}
    for _ in range(2 * len(mp.parts) + 2):
        slots = sum(cols.values())
        s = slot(z, width, slots)
        w = widths[slots]
        out, changed = {}, False
        for p in mp.parts:
            span = round(cols[p["n"]] * s - z["sgap"], 3)
            avail = base - max(fit.H[(mp.p, f"head{p['n']}", span, "head")] + 8 * PT, z["partmin"])
            f = fit.one_column(p["kids"], w, avail) if cols[p["n"]] == 1 else None
            if f is None and cols[p["n"]] == 1 and split and slots + 1 in widths:
                cols[p["n"]] = 2
                changed = True
                break
            if f is None and cols[p["n"]] == 2:
                f = fit.two_columns(p["kids"], w, avail) or fit.continue_on(p["kids"], w, avail, True)
            if f is None:
                f = fit.continue_on(p["kids"], w, avail, False)
            if f is None:
                sys.exit(f"mind map: part '{p['name']}' does not fit the {width:.0f} cm wide map even with a continuation "
                         "column; give it fewer cards or use map_size: a3")
            out[p["n"]] = f
        if not changed:
            return out, s
    sys.exit("mind map: the layout did not settle")


def fit_main(mp, fit, z, width, th):
    """Splits allowed, unless a split makes another part take a later step (then nothing splits)."""
    calm, s_calm = layout_main(mp, fit, z, width, th, split=False)
    bold, s_bold = layout_main(mp, fit, z, width, th, split=True)
    split = [n for n, f in bold.items() if len(f.columns) == 2]
    if split and all(bold[n].step <= calm[n].step for n in bold if n not in split):
        return bold, s_bold
    return calm, s_calm


def sub_groups(mp, fit, z, width, th, main):
    """The sub-map pages' groups, in course order: a part's continuation, then every card with a sub-map."""
    w = sub_width(z, width)
    avail = th - RESERVE_SUB
    groups = []

    def add(title, trail, cards, head_node, back, target, part, cont):
        while cards:
            f = fit.one_column(cards, w, avail) or fit.two_columns(cards, w, avail) or fit.continue_on(cards, w, avail, True)
            if f is None:
                sys.exit(f"mind map: '{title}' does not fit a sub-map page")
            groups.append(dict(title=title, trail=trail, fit=f, node=head_node, back=back, target=target, part=part, cont=cont))
            if not f.moved:
                break
            cards = f.moved
            title, cont, back = title.split(" (continued)")[0] + " (continued)", True, target
            target = target + "c"

    def nested(n):
        for k in n["kids"]:
            if has_map(k):
                par = k["parent"]
                trail = mp.parts[k["part"] - 1]["name"] if par is None else (
                    par["title"] if par["parent"] is None else f"{par['parent']['title']} \\mmsep {par['title']}")
                if par is None:
                    trail = mp.parts[k["part"] - 1]["name"]
                add(k["title"] + star(k), trail, k["kids"], k, mp.card(k), mp.sub(k), k["part"], False)
            nested(k)
    for p in mp.parts:
        f = main[p["n"]]
        if f.moved:
            add(f"{p['name']} (continued)", f"Part {p['n']}", f.moved, None, f"{mp.p}part-{p['n']}", f"{mp.p}cont-{p['n']}",
                p["n"], True)
        nested(p)
    return groups, width / z["subslots"]


# ---------------------------------------------------------------- drawing
def draw_card(mp, n, where, w, z, variant):
    sub = mp.sub(n) if has_map(n) else ""
    tall = f", minimum height={z['tall']}cm" if sub else ""
    return (rf"\node[mmcard={{CoverPart{n['part']}}}{tall}, anchor=north west, font={z['font']}, inner sep={z['sep']}pt, "
            rf"text width={w:.3f}cm-{2 * z['sep']}pt] ({mp.card(n)}) at ({where}) {{\hypertarget{{{mp.card(n)}}}{{}}"
            rf"\begin{{minipage}}[t]{{{text_w(w, z):.3f}cm}}\raggedright {lines(mp, n, z, **VARIANTS[variant])}\end{{minipage}}}};" "\n"
            rf"\mmstrip{{{mp.card(n)}}}{{{n['part']}}}{{{z['strip']}}}{{{mp.row(n)}}}{{{sub}}}{{{len(n['kids'])}}}")


def draw_group(mp, head_code, head, part, s, f, z, more=None):
    """A heading over one or two columns of cards; the stems hang from the heading (from a short bus for two)."""
    out = [head_code]
    two = len(f.columns) == 2
    w = s - z["sgap"] - 0.3
    drop = 0.2 if two else 0
    last = None
    for j, col in enumerate(f.columns):
        stem = f"($({head}.south west)+({j * s + 0.12:.3f},{-drop})$)"
        prev = None
        for c in col:
            where = (f"$({head}.south west)+({j * s + 0.3:.3f},-{f.gap + 0.15 + drop:.3f})$" if prev is None
                     else f"$({mp.card(prev)}.south west)+(0,-{f.gap:.3f})$")
            out.append(draw_card(mp, c, where, w, z, f.variant[c["id"]]))
            out.append(rf"\draw[mmstem=CoverPart{part}] {stem} |- ({mp.card(c)}.west);")
            prev = c
        last = (prev, stem)
    if more:
        prev, stem = last
        out.append(rf"\node[mmmore={{CoverPart{part}}}, anchor=north west, text width={w:.3f}cm-12pt, font={z['font']}] "
                   rf"({mp.p}more{part}) at ($({mp.card(prev)}.south west)+(0,-{f.gap:.3f})$) "
                   rf"{{\bfseries +{len(f.moved)} more \hfill $\blacktriangleright$}};" "\n"
                   rf"\mmnodelink{{{mp.p}more{part}}}{{{more}}}" "\n"
                   rf"\draw[mmstem=CoverPart{part}] {stem} |- ({mp.p}more{part}.west);")
    if two:
        out.append(rf"\draw[mmstem=CoverPart{part}] ($({head}.south west)+(0.12,0)$) -- ++(0,-0.2) -- ++({s:.3f},0);")
    return "\n".join(out)


def header(mp, left, right):
    return rf"\mmheader{{{left}}}{{{right}}}"


def main_page(mp, main, s, z):
    d = mp.d
    out = [r"\clearpage", rf"\hypertarget{{{mp.p}top}}{{}}",
           header(mp, r"{\bfseries Mind map}" + (rf": {d['title']}" if d["title"] else ""),
                  rf"\mmlinkbox{{{mp.p}table}}{{outline table \mmarrow}}"),
           r"\mmlegend", r"\vfill\begin{center}" + z["fonts"] + r"\begin{tikzpicture}[x=1cm, y=1cm]"]
    x, heads = 0.0, []
    for p in mp.parts:
        f, i = main[p["n"]], p["n"]
        span = len(f.columns) * s - z["sgap"]
        hn = f"{mp.p}head{i}"
        sub = rf"Part {i}" + (rf" $\cdot$ {p['sub']}" if p["sub"] else "")
        head = (rf"\node[mmpart={{CoverPart{i}}}, text width={span:.3f}cm-12pt, font=\bfseries{z['part']}, minimum height={z['partmin']}cm, "
                rf"anchor=north west] ({hn}) at ({x:.3f},0) {{\hypertarget{{{mp.p}part-{i}}}{{}}{p['name']}\\[-1pt]"
                rf"{{\normalfont\footnotesize {sub}}}}};" "\n" rf"\mmnodelink{{{hn}}}{{{mp.p}table-{i}}}")
        out.append(draw_group(mp, head, hn, i, s, f, z, more=f"{mp.p}cont-{i}" if f.moved else None))
        heads.append((hn, x + span / 2))
        x += len(f.columns) * s
    if d["title"]:
        mid = (x - z["sgap"]) / 2
        out.append(rf"\node[mmcourse, anchor=south, font=\bfseries{z['headfont']}] ({mp.p}course) at ({mid:.3f},0.55) "
                   rf"{{{d['title']}" + (rf"\\[-1pt]{{\normalfont\footnotesize {d['sub']}}}" if d["sub"] else "") + "};\n"
                   rf"\mmnodelink{{{mp.p}course}}{{{mp.p}table}}")
        # every line straight: drops fall from each heading's own centre, the bus runs between the outer ones
        out.append(rf"\draw[mmbus] ({mp.p}course.south) -- ({mp.p}course.south |- 0,0.27);")
        out.append(rf"\draw[mmbus] ({heads[0][0]}.north |- 0,0.27) -- ({heads[-1][0]}.north |- 0,0.27);")
        out += [rf"\draw[mmbus] ({h}.north |- 0,0.27) -- ({h}.north);" for h, _ in heads]
    out.append(r"\end{tikzpicture}\end{center}\vfill")
    return "\n".join(out)


def sub_pages(mp, groups, s, z):
    pages, page, used = [], [], 0
    for g in groups:
        k = len(g["fit"].columns)
        if page and used + k > z["subslots"]:
            pages.append(page)
            page, used = [], 0
        page.append(g)
        used += k
    if page:
        pages.append(page)
    out = []
    for pg in pages:
        body = [r"\clearpage",
                header(mp, rf"\mmlinkbox{{{mp.p}top}}{{Mind map}} \mmsep {{\bfseries Sub-maps}}: each heading is the card it extends",
                       rf"\mmlinkbox{{{mp.p}top}}{{$\hookleftarrow$ the map}}"),
                r"\mmlegend", r"\vfill\begin{center}" + z["fonts"] + r"\begin{tikzpicture}[x=1cm, y=1cm]"]
        x = 0.0
        for idx, g in enumerate(pg):
            f = g["fit"]
            span = len(f.columns) * s - z["sgap"]
            hn = f"{mp.p}sh{idx}"
            n = g["node"]
            formula = r"\\" + n["formula"] if n is not None and n["formula"] and not g["cont"] else ""
            head = (rf"\node[mmsubhead={{CoverPart{g['part']}}}, text width={span:.3f}cm-12pt, anchor=north west, font={z['font']}] "
                    rf"({hn}) at ({x:.3f},0) {{\hypertarget{{{g['target']}}}{{}}{{\color{{white!85!black}}\scriptsize {g['trail']}}}\\"
                    rf"{{{z['part']}\bfseries $\hookleftarrow$ {g['title']}}}{formula}}};" "\n"
                    rf"\mmnodelink{{{hn}}}{{{g['back']}}}")
            more = g["target"] + "c" if f.moved else None
            body.append(draw_group(mp, head, hn, g["part"], s, f, z, more=more))
            x += len(f.columns) * s
        body.append(r"\end{tikzpicture}\end{center}\vfill")
        out.append("\n".join(body))
    return "\n\n".join(out)


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
            return rf"\columncolor{{CoverPart{n['part']}!{TINT[level]}}}[0pt][\tabcolsep]"
        return r"\columncolor{white}[0pt][\tabcolsep]"

    def name(self, n):
        label = rf"\mmname{{{n['part']}}}{{{n['title']}}}" if is_card(n) else rf"\mmdetail{{{n['title']}}}"
        return rf"\hypertarget{{{self.mp.row(n)}}}{{}}{label}{star(n)}"

    def leaf(self, label_w, label, n, level, back, rules=1):
        """[label | what it is | key formula | map] as one tabular; label None: the node's own "in general" row."""
        W = TABLE_W
        spec = ("@{}" + self.m(label_w, self.tint(n if label is not None else None, level), rules=rules, pads=1, indent=True)
                + "|" + self.m(self.defw) + "|" + self.m(W["fx"]) + "|@{}" + self.m(W["bk"], pads=0, align=r"\centering") + "@{}")
        if label is None:
            label = r"{\itshape\color{mmsoft} in general}"
        defn = n["defn"] or r"{\color{mmsoft}--}"
        return (rf"\begin{{tabular}}{{{spec}}}{label} & {defn} & {n['formula']} & \mmback{{{n['part']}}}{{{back}}}\\"
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
            spec = "|" + self.m(W["l2"], rf"\columncolor{{CoverPart{i}!{TINT[2]}}}", rules=2) + "|@{}" + self.m(rest, pads=0) + "@{}|"
            band = (rf"\multicolumn{{2}}{{|>{{\columncolor{{CoverPart{i}}}}}m{{\dimexpr{total:.3f}cm-2\tabcolsep-2\arrayrulewidth}}|}}"
                    rf"{{\rule{{0pt}}{{14pt}}\color{{white}}\bfseries \hypertarget{{{mp.p}table-{i}}}{{}}PART {i}\quad {p['name']}\quad"
                    rf"{{\normalfont\small {p['sub']}}}\hfill{{\normalfont\small\mmlinkbox{{{mp.p}part-{i}}}{{\color{{white}}the map \mmarrow}}}}}}")
            head = (r"{\scriptsize\bfseries TOPIC} & \begin{tabular}{@{}" + self.m(W["l3"], hd + "[0pt][\\tabcolsep]", pads=1, indent=True)
                    + "|" + self.m(W["l4"], hd) + "|" + self.m(self.defw, hd) + "|" + self.m(W["fx"], hd) + "|@{}"
                    + self.m(W["bk"], hd + "[0pt][0pt]", pads=0, align=r"\centering") + "@{}}"
                    r"\scriptsize\bfseries INSIDE & \scriptsize\bfseries INSIDE & \scriptsize\bfseries WHAT IT IS & "
                    r"\scriptsize\bfseries KEY FORMULA & \scriptsize\bfseries MAP\end{tabular}")
            cont = (rf"\multicolumn{{2}}{{|>{{\columncolor{{CoverPart{i}!65}}}}m{{\dimexpr{total:.3f}cm-2\tabcolsep-2\arrayrulewidth}}|}}"
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
    H, th = measure([mp for _, _, mp in found], z, width, build, main_tex)
    for copy, line, mp in found:
        fit = Fitter(mp, z, H)
        main, s = fit_main(mp, fit, z, width, th)
        groups, ss = sub_groups(mp, fit, z, width, th, main)
        for p in mp.parts:
            if main[p["n"]].step:
                log(f"mind map: part {p['n']} ({plain(p['name'])}): {describe(main[p['n']], z)}")
        for g in groups:
            if g["fit"].step:
                log(f"mind map: sub-map {plain(g['title'])}: {describe(g['fit'], z)}")
        pages = [main_page(mp, main, s, z), sub_pages(mp, groups, ss, z) if groups else "", Table(mp, width).render()]
        tex = copy.read_text(encoding="utf-8")
        copy.write_text(tex.replace(line, "\n\n".join(p for p in pages if p)), encoding="utf-8")
