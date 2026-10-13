"""
coverdata.py -- the facts the covers show, read from the body .tex files (never typed in by hand).

build.py calls cover_macros(); the result is a block of \\newcommand lines for main.tex that fill the lists
cover-kit.tex declares (\\CoverItems, \\CoverStats, \\CoverTracker, \\CoverGroups, \\CoverLog, \\CoverSampleRow,
\\CoverPaperFacts, \\CoverPaperRows). Each list is a run of item macros (\\coveritem{..}{..}{..}, ...), so a
cover lays the items out however it likes and a title with commas or slashes never breaks a loop.

What is read, per type (the default applies to any type not named):
  default, theory-notes  parts (\\section) with their lecture range, lecture count and the boxes they hold
  exam-notes             the same parts on the back cover; one revision-tracker row per lecture
  formula-sheet          topics with their formula counts (table rows); the first row as the sample row
  question-bank          question counts per kind (N, S, L, ...) and per topic; every label for the practice log
  past-paper             time, marks and how many questions to answer; each sub-part with its marks and minutes
"""
import re

SEP = "\\quad$\\cdot$\\quad "
SECTION = re.compile(r"\\(chapter|section|subsection)\*?\{")


def spaced_caps(text):
    """Upper case for letter-spaced labels, outside LaTeX commands, with --- and -- as real dashes."""
    text = text.replace("---", "\u2014").replace("--", "\u2013")
    return re.sub(r"(\\[A-Za-z]+)|([^\\]+)", lambda m: m.group(1) or m.group(2).upper(), text)


def braced(text, start):
    """The content of the {...} group whose opening brace is at text[start], and the index after it."""
    depth, i = 0, start
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    return text[start + 1:], len(text)


def headings(tex):
    """[(level, title, start, end)] for every chapter/section/subsection; end is where the next one of the
    same or a higher level starts."""
    found = []
    for m in SECTION.finditer(tex):
        title, _ = braced(tex, m.end() - 1)
        found.append([m.group(1), title.strip(), m.start(), len(tex)])
    rank = {"chapter": 0, "section": 1, "subsection": 2}
    for i, h in enumerate(found):
        for later in found[i + 1:]:
            if rank[later[0]] <= rank[h[0]]:
                h[3] = later[2]
                break
    return [tuple(h) for h in found]


def top_level(tex):
    """The headings that act as parts: chapters if there are any, else sections. A lone section that only holds
    subsections (a "Formula Sheet" heading over the topics) gives way to its subsections."""
    hs = headings(tex)
    for level, sub in (("chapter", "section"), ("section", "subsection")):
        tops = [h for h in hs if h[0] == level]
        if len(tops) == 1 and any(h[0] == sub for h in hs):
            return [h for h in hs if h[0] == sub]
        if tops:
            return tops
    return [h for h in hs if h[0] == "subsection"]


def esc(text):
    """Keep a heading safe inside a macro argument: drop \\label and \\texorpdfstring wrappers."""
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    return re.sub(r"\\texorpdfstring\{((?:[^{}]|\{[^{}]*\})*)\}\{(?:[^{}]|\{[^{}]*\})*\}", r"\1", text).strip()


def lecture_range(text):
    """'Lectures 24, 25, 26' -> 'L24--26'; 'Lecture 34' -> 'L34'; else ''."""
    m = re.search(r"Lectures?\s+(\d+(?:\s*(?:,|--|–|and)\s*\d+)*)", text)
    if not m:
        return ""
    nums = re.findall(r"\d+", m.group(1))
    return f"L{nums[0]}" if len(nums) == 1 else f"L{nums[0]}--{nums[-1]}"


def split_title(title):
    """'Part 1 --- Lectures 24, 25, 26: Frequency Modulation' -> ('Frequency Modulation', 'Part 1 --- Lectures ...')."""
    if ":" in title and not re.search(r"\$[^$]*:[^$]*\$", title):
        head, _, rest = title.partition(":")
        if rest.strip():
            return rest.strip(), head.strip()
    return title, ""


def parts(tex, limit=8):
    """\\coveritem{n}{title}{sub-line} for each part: lecture range, how many lectures (or sections), and
    whether it has worked examples and a self-check."""
    tops = top_level(tex)
    items = []
    for n, (_, title, start, end) in enumerate(tops[:limit], 1):
        body = tex[start:end]
        name, head = split_title(esc(title))
        subs = [t for lvl, t, s, e in headings(body) if lvl == "subsection"]
        lectures = [t for t in subs if re.match(r"Lecture\s+\d+", t)]
        bits = [lecture_range(head or title)] if lecture_range(head or title) else []
        if lectures:
            bits.append(f"{len(lectures)} lecture{'s' if len(lectures) > 1 else ''}")
        elif subs:
            bits.append(f"{len(subs)} section{'s' if len(subs) > 1 else ''}")
        if "\\begin{examplebox}" in body:
            bits.append("worked examples")
        if "\\begin{selfcheckbox}" in body:
            bits.append("self-check")
        sub = SEP.join(bits)
        items.append(f"\\coveritem{{{n}}}{{{name}}}{{{sub}}}")
    if len(tops) > limit:
        items.append(f"{{\\small\\color{{CoverSoft}}\\dots\\ and {len(tops) - limit} more\\par}}")
    return items, len(tops)


def tracker(tex):
    """Exam notes: \\covertrackrow{label}{topic}{part} per lecture (or per section when there are no lectures)."""
    rows, part = [], 0
    for level, title, _, _ in headings(tex):
        if level in ("chapter", "section"):
            part += 1
            continue
        m = re.match(r"Lecture\s+(\d+)\s*(?:---|--|—|–|:)\s*(.+)", esc(title))
        if m:
            rows.append(f"\\covertrackrow{{\\hyperref[{label_after(tex, title)}]{{L{m.group(1)}}}}}{{{m.group(2)}}}{{{max(part, 1)}}}"
                        if label_after(tex, title) else f"\\covertrackrow{{L{m.group(1)}}}{{{m.group(2)}}}{{{max(part, 1)}}}")
    if not rows:   # no "Lecture NN" headings: one row per section
        for n, (_, title, _, _) in enumerate(top_level(tex), 1):
            rows.append(f"\\covertrackrow{{{n}}}{{{split_title(esc(title))[0]}}}{{{n}}}")
    return rows


def label_after(tex, title):
    """The \\label written right after the heading with this title, or ''."""
    i = tex.find(title)
    m = re.match(r"\}\s*\\label\{([^}]+)\}", tex[i + len(title):i + len(title) + 200]) if i >= 0 else None
    return m.group(1) if m else ""


ROW_END = re.compile(r"\\\\\s*\\hline")


def table_rows(text):
    """Body rows of every tabularx in text (the header row before \\endhead is not counted)."""
    rows = []
    for t in re.findall(r"\\begin\{tabularx\}(.*?)\\end\{tabularx\}", text, re.S):
        body = t.split("\\endhead", 1)[1] if "\\endhead" in t else t.split("\\hline", 2)[-1]
        rows += [r for r in ROW_END.split(body) if "&" in r]   # a caption or \\rowcolor line is not a row
    return rows


def topics(tex):
    """Formula sheet: \\coveritem{n}{title + lecture tag}{N formulas} per topic; total formulas; topic count."""
    items, total = [], 0
    tops = top_level(tex)
    for n, (_, title, start, end) in enumerate(tops, 1):
        count = len(table_rows(tex[start:end]))
        total += count
        name = esc(title)
        tag = re.search(r"\s*\(([^()]*)\)\s*$", name)
        if tag:
            name = name[:tag.start()]
        sub = f"\\\\[1pt]{{\\scriptsize\\coversans\\color{{CoverSoft}}{tag.group(1)}}}" if tag else ""
        items.append(f"\\coveritem{{{n}}}{{{name}{sub}}}{{{count} formula{'s' if count != 1 else ''}}}")
    return items, total, len(tops)


def sample_row(tex):
    """The first body row of the first table, as \\coversamplerow{title}{equation}{notation}{reference}."""
    rows = table_rows(tex)
    if not rows:
        return ""
    cells, depth, cur = [], 0, ""
    for c in rows[0]:
        depth += (c == "{") - (c == "}")
        if c == "&" and depth == 0 and not cur.endswith("\\"):
            cells.append(cur.strip()); cur = ""
        else:
            cur += c
    cells.append(cur.strip())
    if len(cells) != 4:
        return ""
    cells = [re.sub(r"^\\tallcell\{(.*)\}$", r"\1", c, flags=re.S).replace("\\newline", "\\\\") for c in cells]
    return "\\coversamplerow" + "".join(f"{{{c}}}" for c in cells)


KINDS = {"N": "Numericals", "S": "Short questions", "L": "Long questions", "D": "Derivations", "M": "MCQs"}


def bank(tex):
    """Question bank: counts per kind (by label letter), per topic, and the log entries."""
    labels = re.findall(r"(?:\\label\{([^}]+)\}\s*)?\\begin\{questionbox\}\{([^}]*)\}", tex)
    kinds = {}
    for _, q in labels:
        kinds.setdefault(re.match(r"[A-Za-z]*", q).group(0) or "Q", []).append(q)
    stats = [f"\\coverstat{{{len(v)}}}{{{KINDS.get(k, 'Questions' if k == 'Q' else k + ' questions')}}}" for k, v in kinds.items()]
    sols = tex.count("\\begin{solutionbox}")
    if sols:
        stats.append(f"\\coverstat{{{sols}}}{{Solutions}}")
    groups = []
    for level, title, start, end in headings(tex):
        n = tex[start:end].count("\\begin{questionbox}")
        if level == "subsection" and n:
            m = re.match(r"([A-Z]\d+)\s+(.*)", esc(title))
            lab, name = (m.group(1), m.group(2)) if m else (str(len(groups) + 1), esc(title))
            groups.append(f"\\covergroup{{{lab}}}{{{name}}}{{{n}}}")
    log, last = [], None
    for lab, q in labels:
        kind = re.match(r"[A-Za-z]*", q).group(0) or "Q"
        if kind != last:
            log.append(f"\\coverloghead{{{KINDS.get(kind, 'Questions').upper()}}}")
            last = kind
        log.append(f"\\coverlog{{{q}}}{{{lab}}}" if lab else f"\\coverlog{{{q}}}{{}}")
    return stats[:3], groups[:9], log


WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}


def strip_tex(text):
    """Plain words for matching: \\textbf{TWO} -> TWO."""
    return re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", text)


def duration(text):
    """Minutes in 'Time: 3 Hours' or 'Time: 20 min', else None."""
    m = re.search(r"time\W*(\d+(?:\.\d+)?)\s*(hours?|hrs?|h\b|minutes?|mins?)", text, re.I)
    return float(m.group(1)) * (60 if m.group(2).lower().startswith("h") else 1) if m else None


def total_marks_in(text):
    m = re.search(r"marks\W*(\d+(?:\.\d+)?)", text, re.I)
    return float(m.group(1)) if m else None


def paper(tex, info, parts_spec, linked):
    """Past paper: (facts, rows, note). Time and marks come from the paper's info row, how many to answer from
    each part's instruction ("Answer any two ..."); minutes = marks x total time / total marks. A part whose
    instruction gives its own time and marks (a term test in the same document) uses those instead, and is
    not counted in the paper's totals."""
    info_text = " ".join(strip_tex(x) for x in info)
    minutes, total_marks = duration(info_text), total_marks_in(info_text)
    parts = []                       # (first, last, label, answer, own rate or None)
    for p in parts_spec:
        head, _, note = p.partition("|")
        name, _, rng = head.rpartition(":")
        nums = re.findall(r"\d+", rng)
        if not nums:
            continue
        plain = strip_tex(note)
        m = re.search(r"any\s+(\w+)", plain, re.I)
        answer = (WORDS.get(m.group(1).lower(), int(m.group(1)) if m.group(1).isdigit() else 0)) if m else 0
        own_time, own_marks = duration(plain), total_marks_in(plain)
        note = spaced_caps(plain.strip().strip("[]"))
        parts.append((int(nums[0]), int(nums[-1]), spaced_caps(strip_tex(name.strip())) + (SEP + note if note else ""),
                      answer, own_time / own_marks if own_time and own_marks else None))
    def part_of(q):
        return next((pt for pt in parts if pt[0] <= q <= pt[1]), None)
    blocks = re.findall(r"\\begin\{questionblock\}\[([^\]]*)\]\{(\d+)\.\s*\(([a-z]+)\)(.*)", tex)
    questions = sorted({int(q) for _, q, _, _ in blocks})
    main_q = [q for q in questions if not (part_of(q) and part_of(q)[4])]     # not in a part with its own time
    answer = sum(pt[3] for pt in parts if not pt[4])
    facts = []
    if minutes:
        facts.append(f"\\paperfact{{{minutes / 60:g} h}}{{Total time}}" if minutes >= 60 else f"\\paperfact{{{minutes:g} min}}{{Total time}}")
    if total_marks:
        facts.append(f"\\paperfact{{{total_marks:g}}}{{Total marks}}")
    if answer and main_q:
        facts.append(f"\\paperfact{{{answer} of {len(main_q)}}}{{Questions to answer}}")
    if minutes and answer:
        facts.append(f"\\paperfact{{{round(minutes / answer):g} min}}{{Per question}}")
    rate = minutes / total_marks if minutes and total_marks else None
    rows = []
    for q in questions:
        subs = [(t, p, rest) for t, qq, p, rest in blocks if int(qq) == q]
        pt = part_of(q)
        if pt and pt[0] == q:
            rows.append(f"\\paperpartrow{{{pt[2]}}}")
        q_rate = pt[4] if pt and pt[4] else rate
        for i, (title, p, rest) in enumerate(subs):
            m = re.search(r"Marks:\s*([0-9.+\s]+)", rest)
            mk = sum(float(x) for x in re.findall(r"[0-9.]+", m.group(1))) if m else None
            name = re.sub(rf"^\s*{q}\s*\(\s*{p}\s*\)\s*", "", title)
            label = f"({p}) {name}"
            cell = f"\\hyperlink{{sol-{q}{p}}}{{{label}}}" if linked else label
            tm = f"{round(mk * q_rate):g} min" if mk and q_rate else ""
            first = f"{{\\large\\bfseries\\color{{CoverSig}}Q{q}}}" if i == 0 else ""
            pick = "\\tickbox" if i == 0 else ""
            rows.append(f"{first} & {cell} & {f'{mk:g}' if mk else ''} & {tm} & {pick} \\\\")
        rows.append("\\arrayrulecolor{black!12}\\hline\\arrayrulecolor{black}")
    note = ""
    if rate:
        note = (f"Time = marks $\\times$ {rate:.2g} min ({minutes:g} min for {total_marks:g} marks)"
                + ("; a part with its own time (a term test) uses that." if any(pt[4] for pt in parts) else ".")
                + (" Tick the questions you will answer; each sub-part links to its solution." if linked else
                   " Tick the questions you will answer."))
    return facts, rows, note


def stats_for(kind, tex):
    """The numbers on the back cover (the page count is added there)."""
    tops = top_level(tex)
    lectures = len([1 for lvl, t, _, _ in headings(tex) if lvl == "subsection" and re.match(r"Lecture\s+\d+", esc(t))])
    figures = tex.count("\\begin{figure}")
    out = []
    if kind == "formula-sheet":
        out += [(len(table_rows(tex)), "formulas"), (len(tops), "topics")]
    elif kind == "question-bank":
        out += [(tex.count("\\begin{questionbox}"), "questions"), (tex.count("\\begin{solutionbox}"), "solutions")]
    elif kind == "mind-map":
        out += [(tex.count("\\mmpart{"), "parts"), (tex.count("\\mmcard{"), "cards")]
    elif kind == "past-paper":
        out += [(len(re.findall(r"\\begin\{mainquestion\}", tex)), "questions"),
                (len(re.findall(r"\\begin\{questionblock\}", tex)), "solved sub-parts")]
    else:
        out += [(len(tops), "parts" if lectures else "sections")]
        if lectures:
            out.append((lectures, "lectures"))
    if figures:
        out.append((figures, "figures"))
    single = {"parts": "part", "sections": "section", "lectures": "lecture", "figures": "figure", "formulas": "formula",
              "topics": "topic", "questions": "question", "solutions": "solution", "cards": "card"}
    return [f"\\coverstat{{{n}}}{{{single.get(label, label) if n == 1 else label}}}" for n, label in out if n][:3]


def cover_macros(kind, texs, a, linked_paper=False):
    """(main.tex lines that fill the generated lists for this type, fields to set instead of the given ones).
    kind is the type name, or None."""
    tex = "\n".join(texs)
    macros, fields = {}, {}
    if kind == "formula-sheet":
        items, total, n = topics(tex)
        macros["CoverItems"] = items
        macros["CoverSampleRow"] = [sample_row(tex)]
        if not a.cover_note and total:
            fields["CoverNote"] = f"{total} formulas in {n} topic{'s' if n != 1 else ''}"
    elif kind == "question-bank":
        stats, groups, log = bank(tex)
        macros["CoverStats"] = stats
        macros["CoverGroups"] = groups
        macros["CoverLog"] = log
    elif kind == "past-paper":
        facts, rows, note = paper(tex, a.paper_info, a.paper_part, linked_paper)
        macros["CoverPaperFacts"] = facts
        macros["CoverPaperRows"] = rows
        macros["CoverPaperNote"] = [note]
    else:
        items, _ = parts(tex)
        macros["CoverItems"] = items
        if kind == "exam-notes":
            rows = tracker(tex)
            macros["CoverTracker"] = rows[:30]
            if len(rows) > 12:   # tighter rows, so the plan stays on one page
                macros["CoverTrackerCompact"] = ["1"]
    back = stats_for(kind, tex)
    out = []
    for name, lines in macros.items():
        out.append(f"\\newcommand{{\\{name}}}{{%\n" + "\n".join(x for x in lines if x) + "}")
    # the back cover's numbers go in their own list, so a cover that shows \CoverStats keeps its own
    out.append("\\newcommand{\\CoverBackStats}{" + "".join(back) + "}")
    return "\n".join(out), fields
