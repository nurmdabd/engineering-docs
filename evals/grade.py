#!/usr/bin/env python3
"""
grade.py -- check the outputs of one eval run against its assertions (evals/evals.json).

    python3 evals/grade.py WORKSPACE/iteration-N        # grades every <eval>/with_skill run in it

Writes grading.json next to each run's outputs/ (fields: text, passed, evidence). Every check is mechanical:
it re-runs the linter on the run's Markdown and recompiles its LaTeX body, so a result does not depend on what
the run claimed.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
FILES = SKILL / "evals" / "files"
sys.path.insert(0, str(SCRIPTS))
import frontmatter  # noqa: E402


def main_md(out):
    mds = [p for p in out.rglob("*.md") if p.name.upper() != "NOTES.MD" and "_build" not in str(p)]
    return max(mds, key=lambda p: p.stat().st_size) if mds else None


def lint(md):
    r = subprocess.run([sys.executable, str(SCRIPTS / "lint_md.py"), str(md)], capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or ["?"])[-1]
    return r.returncode == 0, last


def rebuild(md):
    body = md.parent / "latex" / f"{md.stem}.tex"
    if not body.exists():
        bodies = list(md.parent.rglob("latex/*.tex"))
        body = bodies[0] if bodies else None
    if not body:
        return False, "no latex/*.tex body found"
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(SCRIPTS / "build.py"), str(body), "--out", f"{tmp}/x.pdf",
                            "--build-dir", f"{tmp}/b"], capture_output=True, text=True)
        ok = r.returncode == 0 and "Log clean" in r.stdout
        summary = [l for l in r.stdout.splitlines() if l and not l.startswith(("PDF:", "Build folder", "settings from"))]
        return ok, f"{body.relative_to(md.parent)}: " + " | ".join(summary)[:300]


def has(text, *needles):
    missing = [n for n in needles if n not in text]
    return not missing, ("all present" if not missing else "missing: " + ", ".join(missing))


def common(md, kind):
    meta, body, _ = frontmatter.split(md.read_text(encoding="utf-8"))
    checks = []
    if kind:
        checks.append((f"front matter sets type: {kind}", meta.get("type") == kind, f"type = {meta.get('type')!r}"))
    ok, ev = lint(md)
    checks.append(("linter reports no errors", ok, ev))
    ok, ev = rebuild(md)
    checks.append(("PDF builds with a clean log", ok, ev))
    return meta, body, checks


def display_maths(text):
    return [m.strip() for m in re.findall(r"\$\$(.+?)\$\$", text, re.S)]


def grade(name, out):
    md = main_md(out)
    if not md:
        return [("a Markdown source was produced", False, f"no .md in {out}")]
    t = md.read_text(encoding="utf-8")
    src_notes = (FILES / "fm-theory.md").read_text(encoding="utf-8")

    if name == "past-paper-solutions":
        meta, body, c = common(md, "past-paper")
        c.append(("paper block keeps both parts with Marks 4 and Marks 5",
                  bool(re.search(r"\[\s*Marks:?\s*4\s*\]", body)) and bool(re.search(r"\[\s*Marks:?\s*5\s*\]", body)),
                  "found [Marks: 4] and [Marks: 5]" if re.search(r"\[\s*Marks:?\s*5", body) else "marks missing"))
        c.append(("question text copied exactly (key phrase of 1(b) present)",
                  *has(body, "Five channels, each with 100 kHz bandwidth")))
        c.append(("one solution heading per part: 1(a) and 1(b)",
                  bool(re.search(r"^## 1\.?\s*\(a\)", body, re.M)) and bool(re.search(r"^## 1\.?\s*\(b\)", body, re.M)),
                  ", ".join(re.findall(r"^## .{0,40}", body, re.M))))
        c.append(("a Final Concise Answer section exists", *has(body, "### Final Concise Answer")))
        three_volts = re.search(r"(?<![\d.])3(?:\.0+)?\s*(?:~|\\,|\\ )?\s*(?:\\text\{|\\mathrm\{)?\s*V\b", body)
        ok, ev = has(body, "0.6", "9.995", "10.005")
        c.append(("1(a) results correct: m = 0.6, 9.995 and 10.005 MHz, 3 V", ok and bool(three_volts),
                  ev + ("; 3 V found" if three_volts else "; 3 V missing")))
        c.append(("1(b) result correct: 540 kHz", *has(body, "540")))
    elif name == "formula-sheet":
        meta, body, c = common(md, "formula-sheet")
        c.append(("uses the Title | Equation | Notation | Reference table",
                  bool(re.search(r"^\|\s*Title\s*\|\s*Equation\s*\|\s*Notation\s*\|\s*Reference\s*\|", body, re.M)),
                  "header row found" if re.search(r"^\|\s*Title\s*\|", body, re.M) else "no Title | Equation header"))
        compact = lambda s: re.sub(r"\s+|\\[,;!]|\\[dt]frac|\\frac", "", s)
        want = [compact(m) for m in display_maths(src_notes)]
        sheet = compact(body)
        missing = [m for m in want if m not in sheet]
        c.append(("every display formula of the notes appears on the sheet", not missing,
                  f"{len(want) - len(missing)}/{len(want)} found" + (f"; missing {missing}" if missing else "")))
        rows = [l for l in body.splitlines() if l.startswith("|") and not re.match(r"^\|\s*(Title|-)", l)]
        empty = [r for r in rows if len(r.split("|")) > 3 and not r.split("|")[3].strip()]
        c.append(("every table row has a non-empty Notation cell", bool(rows) and not empty,
                  f"{len(rows)} rows, {len(empty)} with empty Notation"))
    elif name == "question-bank":
        meta, body, c = common(md, "question-bank")
        ids = all(re.search(rf"^#### N{i}\s*$", body, re.M) and re.search(rf"^#### Solution N{i}\s*$", body, re.M)
                  for i in (1, 2, 3))
        c.append(("three numericals N1, N2, N3, each with its #### Solution", ids,
                  ", ".join(re.findall(r"^#### .+$", body, re.M))))
        sols = re.split(r"^#### Solution N\d+\s*$", body, flags=re.M)[1:]
        bold = [bool(re.search(r"\*\*[^*]+\*\*|\\mathbf\{", s)) for s in sols]
        c.append(("every solution states a bold result", bool(sols) and all(bold), f"bold result in {sum(bold)}/{len(sols)} solutions"))
        c.append(("solutions use Carson's rule as written in the notes (2(Δf + B))",
                  bool(re.search(r"2\s*\(\s*\\Delta f\s*\+\s*B\s*\)|2\s*\(\s*Δf\s*\+\s*B\s*\)", body)), "2(\\Delta f + B) found"
                  if re.search(r"2\s*\(\s*\\Delta f\s*\+\s*B", body) else "not found"))
    elif name == "convert-finished-notes":
        meta, body, c = common(md, None)
        maths = re.findall(r"\$\$.+?\$\$|\$[^$\n]+\$", src_notes, re.S)
        missing = [m for m in maths if m not in body]
        c.append(("every equation of the notes is in the Markdown unchanged", not missing,
                  f"{len(maths) - len(missing)}/{len(maths)} unchanged" + (f"; changed: {missing[:3]}" if missing else "")))
        sentences = [l.strip() for l in src_notes.splitlines()                       # every prose line of the notes
                     if l.strip() and not l.lstrip().startswith(("#", "$$")) and "$$" not in l]
        gone = [s for s in sentences if s not in body]
        c.append(("no sentence of the notes was removed or reworded", not gone,
                  f"{len(sentences) - len(gone)}/{len(sentences)} prose lines intact" + (f"; e.g. {gone[0][:80]!r}" if gone else "")))
        tex = next(iter(md.parent.rglob("latex/*.tex")), None)
        texs = tex.read_text(encoding="utf-8") if tex else ""
        inner = [re.sub(r"\s+", "", m) for m in display_maths(src_notes)]
        found = [m for m in inner if m in re.sub(r"\s+", "", texs)]
        first = re.search(r"\\(chapter|section|subsection|subsubsection)\*?\{", texs)
        c.append(("headings start at the first numbered level (no 0.x numbering)", bool(first) and first.group(1) == "section",
                  f"first heading command: \\{first.group(1) if first else 'none'}"))
        c.append(("every display equation reaches the LaTeX body", tex is not None and len(found) == len(inner),
                  f"{len(found)}/{len(inner)} in {tex.name if tex else 'no .tex'}"))
    elif name == "project-report-day":
        meta, body, c = common(md, "project-report")
        log = (FILES / "day-03-log.txt").read_text(encoding="utf-8")
        c.append(("a '# Day 03' (or Day 3) chapter heading", bool(re.search(r"^# Day 0?3\b", body, re.M)),
                  ", ".join(re.findall(r"^# .+$", body, re.M)) or "no # heading"))
        c.append(("Command and Output Snippet labels used for the flow commands", *has(body, "**Command:**", "**Output")))
        c.append(("the log's results are reported: 13850 cells, overflow 0.0995, core area 551.17 x 562.85",
                  *has(body, "13850", "0.0995", "551.17", "562.85")))
        nums = set(re.findall(r"(?<![\w.])\d{3,}(?:\.\d+)?", re.sub(r"https?://\S+", "", body)))
        invented = sorted(n for n in nums if n not in log and n not in ("130",))   # sky130 appears as 130 inside names
        c.append(("no invented numbers: every number of 3+ digits in the Markdown appears in the log", not invented,
                  "none invented" if not invented else "not in the log: " + ", ".join(invented[:8])))
        tex = next(iter(md.parent.rglob("latex/*.tex")), None)
        texs = tex.read_text(encoding="utf-8") if tex else ""
        labels = re.findall(r"\\label\{([^}]+)\}", texs)
        bad = [l for l in labels if not re.search(r"d0?3", l)]
        c.append(("every label carries the day prefix (d03 or d3)", bool(labels) and not bad,
                  f"{len(labels) - len(bad)}/{len(labels)} prefixed" + (f"; e.g. {bad[:3]}" if bad else "")))
        numbered = bool(re.search(r"\\setcounter\{chapter\}\{2\}", texs)) or str(meta.get("first_number")) == "3"
        c.append(("Day 3 is numbered Chapter 3", numbered, "first_number 3 / \\setcounter{chapter}{2} found" if numbered else "Day 3 would be Chapter 1"))
        c.append(("the OpenLane repo is given as a repocard", bool(re.search(r"^:::+\s*\{\.repocard", body, re.M)),
                  "repocard div found" if re.search(r"\{\.repocard", body) else "no repocard"))
    return c


def main():
    it = Path(sys.argv[1])
    evals = {e["name"]: e for e in json.load(open(SKILL / "evals" / "evals.json"))["evals"]}
    for run in sorted(it.glob("*/with_skill")):
        name = run.parent.name
        checks = grade(name, run / "outputs")
        want = evals[name]["assertions"]
        got = {t: (p, e) for t, p, e in checks}
        exps = [{"text": t, "passed": bool(got.get(t, (False, "check not run"))[0]),
                 "evidence": got.get(t, (False, "check not run"))[1]} for t in want]
        n = sum(e["passed"] for e in exps)
        json.dump({"expectations": exps, "summary": {"passed": n, "failed": len(exps) - n, "total": len(exps),
                                                      "pass_rate": round(n / len(exps), 2)}},
                  open(run / "grading.json", "w"), indent=1, ensure_ascii=False)
        print(f"{name:26} {n}/{len(exps)}")
        for e in exps:
            if not e["passed"]:
                print(f"   FAIL {e['text']}: {e['evidence']}")


if __name__ == "__main__":
    main()
