"""
formulasheet.py -- the pages build.py adds at the end of a formula sheet, from its own tables:

  Key formulas   every row whose Title is bold (the sheet's key formulas), title and equation, each linking
                 back to its row; those rows also get a star in the sheet.
  Symbol index   every symbol the Notation column defines ("$k_f$ = frequency sensitivity"), in order of first
                 use, with its meaning and a link to that row.

Works on the build copy of a body (never on the user's .tex): mark_rows() puts a link target in front of each
row's title and returns the rows; pages() writes the two sections.
"""
import re

ROW_END = re.compile(r"(\\\\\s*\\hline)")
BOLD = re.compile(r"^\s*\\(?:textbf|keyterm)\{(.*)\}\s*$", re.S)


def split_cells(row):
    cells, depth, cur, i = [], 0, "", 0
    while i < len(row):
        c = row[i]
        if c == "\\" and i + 1 < len(row):
            cur += row[i:i + 2]
            i += 2
            continue
        depth += (c == "{") - (c == "}")
        if c == "&" and depth == 0:
            cells.append(cur)
            cur = ""
        else:
            cur += c
        i += 1
    return cells + [cur]


def mark_rows(tex, start=0):
    """Add \\hypertarget{fsrow-N}{} (and a star for a bold title) to every table row; return (tex, rows).
    rows: [{'n', 'title', 'equation', 'notation', 'key'}] in order."""
    rows = []
    out, pos = [], 0
    for t in re.finditer(r"\\begin\{tabularx\}.*?\\end\{tabularx\}", tex, re.S):
        out.append(tex[pos:t.start()])
        table = t.group(0)
        head_end = table.find("\\endhead")
        if head_end < 0:
            out.append(table)
            pos = t.end()
            continue
        head, body = table[:head_end + len("\\endhead")], table[head_end + len("\\endhead"):]
        pieces = ROW_END.split(body)
        for k in range(0, len(pieces), 2):
            row = pieces[k]
            cells = split_cells(row)
            if len(cells) < 2 or "\\caption" in row:
                continue
            n = start + len(rows) + 1
            title = cells[0].strip()
            key = bool(BOLD.match(title))
            lead = re.match(r"\s*", cells[0]).group(0)
            star = "{\\color{orange!80!black}$\\bigstar$}\\," if key else ""
            cells[0] = f"{lead}\\hypertarget{{fsrow-{n}}}{{}}{star}{cells[0][len(lead):]}"
            pieces[k] = "&".join(cells)
            eq = unwrap(cells[1])
            rows.append({"n": n, "title": BOLD.sub(r"\1", title), "equation": eq,
                         "notation": unwrap(cells[2]) if len(cells) > 3 else "", "key": key})
        out.append(head + "".join(pieces))
        pos = t.end()
    out.append(tex[pos:])
    return "".join(out), rows


def unwrap(cell):
    """The content of a cell without a \\tallcell{...} wrapper."""
    cell = cell.strip()
    m = re.match(r"\\tallcell\{", cell)
    if m and cell.endswith("}"):
        return cell[m.end():-1]
    return cell


def split_definition(entry):
    """'$k_f$ = frequency sensitivity' -> ('$k_f$', 'frequency sensitivity'), splitting only at an = outside
    maths; None when there is none (a definition written wholly inside $...$ is left out)."""
    in_math, i = False, 0
    while i < len(entry):
        c = entry[i]
        if c == "\\":
            i += 2
            continue
        if c == "$":
            in_math = not in_math
        elif c == "=" and not in_math and entry[i - 1:i] == " " and entry[i + 1:i + 2] == " ":
            return entry[:i].strip(), entry[i + 1:].strip()
        i += 1
    return None


def balanced(text):
    depth = 0
    for i, c in enumerate(text):
        if c in "{}" and (i == 0 or text[i - 1] != "\\"):
            depth += 1 if c == "{" else -1
            if depth < 0:
                return False
    return depth == 0 and text.count("$") % 2 == 0


def symbols(rows):
    """[(symbol, meaning, row)] from the Notation cells, first use only."""
    seen, out = set(), []
    for r in rows:
        for entry in re.split(r"\\newline|<br\s*/?>|\\\\(?!\[)", unwrap(r["notation"])):
            parts = split_definition(entry)
            if not parts or not all(balanced(x) for x in parts):
                continue
            sym, meaning = parts
            key = re.sub(r"\s+", "", sym)
            if key in seen or len(sym) > 40:
                continue
            seen.add(key)
            out.append((sym, meaning, r))
    return out


def pages(rows):
    """LaTeX of the two sections (each one only if it has entries)."""
    out = []
    keys = [r for r in rows if r["key"]]
    if keys:
        # a fraction, root or big operator gets a strut, so it stays clear of the rules above and below
        tall = lambda eq: "\\rule[-2.9ex]{0pt}{6.9ex}" if re.search(r"\\(?:[dt]?frac|sqrt|sum|int|prod)\b", eq) else ""
        body = "\n".join(f"    \\hyperlink{{fsrow-{r['n']}}}{{{r['title']}}} &\n    {tall(r['equation'])}{r['equation']} \\\\ \\hline"
                         for r in keys)
        out.append("\\clearpage\n\\section{Key formulas}\n\\label{sec:key_formulas}\n"
                   "The formulas marked {\\color{orange!80!black}$\\bigstar$} in the sheet, on one page. "
                   "Each title links back to its row.\n\n"
                   # taller rows than the sheet's, so a fraction does not touch the rules (one formula a row)
                   "{\\renewcommand{\\arraystretch}{1.5}\n"
                   "\\begin{tabularx}{\\textwidth}{|x{4.2cm}|L|}\n    \\hline\n    \\rowcolor{gray!15}\n"
                   "    \\yy{Title}{4.2cm} &\n    \\CC{Equation} \\\\ \\hline\n\\endhead\n\n" + body + "\n\\end{tabularx}}\n")
    syms = symbols(rows)
    if syms:
        body = "\n".join(f"    {s} & {m} & \\hyperlink{{fsrow-{r['n']}}}{{{r['title']}}} \\\\ \\hline" for s, m, r in syms)
        out.append("\\clearpage\n\\section{Symbol index}\n\\label{sec:symbol_index}\n"
                   "Every symbol the sheet defines, in the order it first appears. The last column links to that row.\n\n"
                   "\\begin{tabularx}{\\textwidth}{|>{\\raggedright\\arraybackslash}p{3.0cm}|L|x{4.6cm}|}\n    \\hline\n"
                   "    \\rowcolor{gray!15}\n    \\yy{Symbol}{3.0cm} &\n    \\CC{Meaning} &\n    \\yy{First used in}{4.6cm} \\\\ \\hline\n"
                   "\\endhead\n\n" + body + "\n\\end{tabularx}\n")
    return "\n".join(out)
