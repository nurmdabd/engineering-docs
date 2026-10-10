#!/usr/bin/env python3
"""
run_tests.py -- regression tests for the converter and the build.

    python3 tests/run_tests.py            # convert every fixture, compare with tests/expected/; lint tests/lint/*.md
    python3 tests/run_tests.py --update   # accept the current output as the new expected output
    python3 tests/run_tests.py --build    # also compile every expected body and the example; each log must be clean,
                                          # and the PDF text must match a case's pdf_has / pdf_lacks lists

Corpus check, for real notes that live in another repo (run before and after a converter change):

    python3 tests/run_tests.py --snapshot DIR  notes.md other.md:--bangla ...
    python3 tests/run_tests.py --compare  DIR  notes.md other.md:--bangla ...

Each corpus entry is a Markdown path, optionally followed by ':' and md2tex flags separated by commas
(for example sheet.md:--fontsize,10pt,--textwidth,18.9). Snapshots go to DIR, outside the skill.
"""
import argparse
import difflib
import shutil
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TESTS = Path(__file__).resolve().parent
SKILL = TESTS.parent
FIXTURES = TESTS / "fixtures"
EXPECTED = TESTS / "expected"
MD2TEX = SKILL / "scripts" / "md2tex.py"
LINT = SKILL / "scripts" / "lint_md.py"
DOC = SKILL / "scripts" / "doc.py"
BUILD = SKILL / "scripts" / "build.py"


def convert(md, out, flags):
    r = subprocess.run([sys.executable, str(MD2TEX), str(md), "-o", str(out), *flags],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"md2tex failed on {md.name}:\n{r.stderr}")
    return out.read_text(encoding="utf-8")


def diff(expected, actual, name):
    return "".join(difflib.unified_diff(expected.splitlines(True), actual.splitlines(True),
                                        f"expected/{name}", f"actual/{name}", n=2))


def check_skill():
    """SKILL.md front matter must parse (a bad one stops the skill loading), and every type must be complete."""
    import yaml
    problems = []
    try:
        fm = yaml.safe_load((SKILL / "SKILL.md").read_text(encoding="utf-8").split("---")[1])
        if not fm.get("name") or not fm.get("description"):
            problems.append("SKILL.md front matter lacks name or description")
        elif len(fm["description"]) > 1024:
            problems.append(f"SKILL.md description is {len(fm['description'])} characters (limit 1024)")
    except Exception as e:
        problems.append(f"SKILL.md front matter is not valid YAML: {str(e).splitlines()[0]}")
    for reg in [SKILL / "template" / "commands.yaml", *sorted((SKILL / "types").glob("*/commands.yaml"))]:
        try:
            for name, e in (yaml.safe_load(reg.read_text(encoding="utf-8")) or {}).items():
                if e.get("kind") not in ("command", "environment") or e.get("markdown") not in ("span", "div", "auto", "none"):
                    problems.append(f"{reg.relative_to(SKILL)}: '{name}' needs kind command|environment and markdown span|div|auto|none")
        except Exception as ex:
            problems.append(f"{reg.relative_to(SKILL)} is not valid YAML: {str(ex).splitlines()[0]}")
    for t in sorted((SKILL / "types").iterdir()):
        for f in ("type.json", "guide.md"):
            if t.is_dir() and not (t / f).exists():
                problems.append(f"types/{t.name} has no {f}")
    print(f"{'ok' if not problems else 'FAILED':8} skill files")
    for p in problems:
        print("  " + p)
    return len(problems)


def run_cases(cases, update):
    failed = 0
    EXPECTED.mkdir(exist_ok=True)
    for case in cases:
        name = case["name"]
        # Convert next to the fixture so relative figure paths come out exactly as in expected/
        out = FIXTURES / f".{name}.out.tex"
        side = out.with_suffix(".build.json")   # build settings md2tex writes from front matter, if any
        try:
            results = {".tex": convert(FIXTURES / f"{name}.md", out, case.get("md2tex", []))}
            if side.exists():
                results[".build.json"] = side.read_text(encoding="utf-8")
        finally:
            out.unlink(missing_ok=True)
            side.unlink(missing_ok=True)
        for ext in (".tex", ".build.json"):
            exp, actual = EXPECTED / f"{name}{ext}", results.get(ext)
            if actual is None:
                if exp.exists():
                    failed += 1
                    print(f"CHANGED  {name}{ext}: no longer produced")
                continue
            if update or not exp.exists():
                exp.write_text(actual, encoding="utf-8")
                print(f"updated  {name}{ext}")
            elif exp.read_text(encoding="utf-8") == actual:
                print(f"ok       {name}{ext}")
            else:
                failed += 1
                print(f"CHANGED  {name}{ext}\n{diff(exp.read_text(encoding='utf-8'), actual, name + ext)}")
    return failed


def run_lint(update):
    """lint_md.py on each tests/lint/*.md must print exactly tests/lint/NAME.expected."""
    failed = 0
    for md in sorted((TESTS / "lint").glob("*.md")):
        r = subprocess.run([sys.executable, str(LINT), md.name], cwd=md.parent, capture_output=True, text=True)
        actual = r.stdout + r.stderr
        exp = md.with_suffix(".expected")
        if update or not exp.exists():
            exp.write_text(actual, encoding="utf-8")
            print(f"updated  lint {md.name}")
        elif exp.read_text(encoding="utf-8") == actual:
            print(f"ok       lint {md.name}")
        else:
            failed += 1
            print(f"CHANGED  lint {md.name}\n{diff(exp.read_text(encoding='utf-8'), actual, md.stem + '.expected')}")
    return failed


def run_templates(build):
    """Every types/*/template.md must lint with no findings and, with --build, go through doc.py to a clean PDF."""
    failed = 0
    for tpl in sorted((SKILL / "types").glob("*/template.md")):
        name = tpl.parent.name
        r = subprocess.run([sys.executable, str(LINT), str(tpl)], capture_output=True, text=True)
        ok = r.returncode == 0 and r.stdout.strip().endswith("0 error(s), 0 warning(s)")
        if ok and build:
            with tempfile.TemporaryDirectory() as tmp:
                md = Path(tmp) / f"{name}.md"
                md.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")
                b = subprocess.run([sys.executable, str(DOC), "build", str(md)], capture_output=True, text=True)
                ok = b.returncode == 0 and "Log clean" in b.stdout
                r = b
        print(f"{'ok' if ok else 'FAILED':8} template {name}{' (built)' if build and ok else ''}")
        if not ok:
            print("  " + (r.stdout + r.stderr).strip().replace("\n", "\n  "))
        failed += not ok
    return failed


def run_commands_add():
    """commands.py add, on a scratch copy of the skill: adds, refuses a taken name, rolls back a broken definition."""
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        skill = Path(tmp) / "skill"
        shutil.copytree(SKILL, skill, ignore=shutil.ignore_patterns(".git", "__pycache__", "tests"))
        tool = [sys.executable, str(skill / "scripts" / "commands.py")]
        pre = skill / "types" / "past-paper" / "preamble.tex"

        def add(name, latex):
            return subprocess.run(tool + ["add", name, "--kind", "command", "--level", "type", "--type", "past-paper",
                                          "--latex", latex, "--args", "text", "--markdown", "span", "--use", "test"],
                                  capture_output=True, text=True)
        checks = []
        r = add("marksnote", r"\newcommand{\marksnote}[1]{\hfill\textit{#1}}")
        checks.append(("adds a new command", r.returncode == 0 and "\\marksnote" in pre.read_text()
                       and "marksnote:" in (skill / "types" / "past-paper" / "commands.yaml").read_text()))
        r = add("marksnote", r"\newcommand{\marksnote}[1]{#1}")
        checks.append(("refuses a registered name", r.returncode != 0 and "taken" in r.stdout + r.stderr))
        r = add("section", r"\newcommand{\section}[1]{#1}")
        checks.append(("refuses a LaTeX name", r.returncode != 0 and "LaTeX or a loaded package" in r.stdout + r.stderr))
        before = pre.read_text()
        r = add("brokencmd", r"\newcommand{\brokencmd}[1]{\undefinedmacro{#1}}")
        checks.append(("rolls back a definition that does not compile", r.returncode != 0 and pre.read_text() == before))
        for what, ok in checks:
            print(f"{'ok' if ok else 'FAILED':8} commands.py add: {what}")
            failed += not ok
    return failed


def build_one(body, flags, label, has=(), lacks=()):
    """Compile body; the log must be clean, and the PDF text must contain every `has` and no `lacks` string."""
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(BUILD), str(body), "--out", f"{tmp}/t.pdf",
                            "--build-dir", f"{tmp}/b", *flags], capture_output=True, text=True)
        problems = [] if r.returncode == 0 and "Log clean" in r.stdout else [(r.stdout + r.stderr).strip()]
        if not problems and (has or lacks):
            text = subprocess.run(["pdftotext", f"{tmp}/t.pdf", "-"], capture_output=True, text=True).stdout
            problems += [f"PDF text lacks {s!r}" for s in has if s not in text]
            problems += [f"PDF text has {s!r}" for s in lacks if s in text]
        print(f"{'ok' if not problems else 'FAILED':8} build {label}")
        for p in problems:
            print("  " + p.replace("\n", "\n  "))
        return 1 if problems else 0


def run_builds(cases):
    failed = build_one(SKILL / "examples" / "example-body.tex", [], "example-body")
    for case in cases:
        if case.get("build", True):
            body = FIXTURES / f".{case['name']}.tex"   # beside the fixture, so figures/ resolves
            side = body.with_suffix(".build.json")
            body.write_text((EXPECTED / f"{case['name']}.tex").read_text(encoding="utf-8"), encoding="utf-8")
            if (EXPECTED / f"{case['name']}.build.json").exists():
                side.write_text((EXPECTED / f"{case['name']}.build.json").read_text(encoding="utf-8"), encoding="utf-8")
            try:
                failed += build_one(body, case.get("build_flags", []), case["name"],
                                    case.get("pdf_has", []), case.get("pdf_lacks", []))
            finally:
                body.unlink(missing_ok=True)
                side.unlink(missing_ok=True)
    return failed


def corpus(entries, folder, mode):
    folder.mkdir(parents=True, exist_ok=True)
    failed = 0
    for entry in entries:
        path, _, flags = entry.partition(":")
        md = Path(path).resolve()
        flags = [f for f in flags.split(",") if f]
        key = md.stem + ".tex"
        with tempfile.TemporaryDirectory(dir=md.parent) as tmp:
            actual = convert(md, Path(tmp) / key, flags)
        snap = folder / key
        if mode == "snapshot":
            snap.write_text(actual, encoding="utf-8")
            print(f"saved    {key}")
        elif not snap.exists():
            failed += 1
            print(f"MISSING  {key} (no snapshot)")
        elif snap.read_text(encoding="utf-8") == actual:
            print(f"ok       {key}")
        else:
            failed += 1
            print(f"CHANGED  {key}\n{diff(snap.read_text(encoding='utf-8'), actual, key)}")
    return failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--snapshot", type=Path)
    ap.add_argument("--compare", type=Path)
    ap.add_argument("corpus", nargs="*")
    a = ap.parse_args()

    if a.snapshot or a.compare:
        failed = corpus(a.corpus, a.snapshot or a.compare, "snapshot" if a.snapshot else "compare")
    else:
        cases = json.loads((TESTS / "cases.json").read_text())
        failed = check_skill() + run_cases(cases, a.update) + run_lint(a.update) + run_templates(a.build)
        if a.build:
            failed += run_builds(cases) + run_commands_add()
    print("\nAll passed." if not failed else f"\n{failed} failed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
