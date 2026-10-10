#!/usr/bin/env python3
"""
run_tests.py -- regression tests for the converter and the build.

    python3 tests/run_tests.py            # convert every fixture, compare with tests/expected/
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


def run_cases(cases, update):
    failed = 0
    EXPECTED.mkdir(exist_ok=True)
    for case in cases:
        name = case["name"]
        # Convert next to the fixture so relative figure paths come out exactly as in expected/
        out = FIXTURES / f".{name}.out.tex"
        try:
            actual = convert(FIXTURES / f"{name}.md", out, case.get("md2tex", []))
        finally:
            out.unlink(missing_ok=True)
        exp = EXPECTED / f"{name}.tex"
        if update or not exp.exists():
            exp.write_text(actual, encoding="utf-8")
            print(f"updated  {name}")
        elif exp.read_text(encoding="utf-8") == actual:
            print(f"ok       {name}")
        else:
            failed += 1
            print(f"CHANGED  {name}\n{diff(exp.read_text(encoding='utf-8'), actual, name + '.tex')}")
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
            body.write_text((EXPECTED / f"{case['name']}.tex").read_text(encoding="utf-8"), encoding="utf-8")
            try:
                failed += build_one(body, case.get("build_flags", []), case["name"],
                                    case.get("pdf_has", []), case.get("pdf_lacks", []))
            finally:
                body.unlink(missing_ok=True)
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
        failed = run_cases(cases, a.update)
        if a.build:
            failed += run_builds(cases)
    print("\nAll passed." if not failed else f"\n{failed} failed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
