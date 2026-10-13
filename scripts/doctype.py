"""
doctype.py -- document types. A type is a folder types/<name>/ with:
  type.json   {"description": ..., "md2tex": [default flags], "build": [default flags]}
  guide.md    how to write and lay out that kind of document (read it before writing the content)
  preamble.tex  optional: commands and environments only this type uses; build.py loads it after the house preamble
  cover-page-preamble.tex + cover-page-main.tex  optional: the type's own cover, used instead of the study-notes
                cover when the build has --cover (fields are filled the same way)

`--type NAME` on md2tex.py or build.py puts the type's default flags in front of the command line,
so any flag given explicitly still wins (argparse keeps the last value).
"""
import json
import re
import sys
from pathlib import Path

TYPES = Path(__file__).resolve().parents[1] / "types"

# Left/right page margin of every document unless its type (type.json) or its front matter (margin_x) says
# otherwise. md2tex.py sizes table columns from the text width this leaves on an A4 page.
MARGIN_X = "0.5in"
A4_WIDTH_CM = 21.0
_UNIT_CM = {"in": 2.54, "cm": 1.0, "mm": 0.1, "pt": 2.54 / 72.27}


def length_cm(length):
    """'0.5in' -> 1.27. Units: in, cm, mm, pt."""
    m = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*(in|cm|mm|pt)\s*", str(length))
    if not m:
        sys.exit(f"cannot read the length '{length}' (write it like 0.5in, 1.27cm, 12mm)")
    return float(m.group(1)) * _UNIT_CM[m.group(2)]


def text_width_cm(margin_x, paper_width_cm=A4_WIDTH_CM):
    return paper_width_cm - 2 * length_cm(margin_x)


def available():
    return sorted(p.parent.name for p in TYPES.glob("*/type.json"))


def expand(argv, tool):
    """Return argv with each --type NAME replaced by that type's default flags for `tool` ('md2tex' or 'build').

    The defaults go in front of everything else, in order, so a later --type (the user's) beats an earlier one
    (from front matter) and any flag given explicitly beats them all.
    """
    defaults, rest, i = [], [], 1
    while i < len(argv):
        if argv[i] != "--type":
            rest.append(argv[i]); i += 1
            continue
        if i + 1 >= len(argv):
            sys.exit("--type needs a name: " + ", ".join(available()))
        name = argv[i + 1]
        spec = TYPES / name / "type.json"
        if not spec.exists():
            sys.exit(f"unknown document type '{name}'. Available: " + ", ".join(available()))
        defaults += json.loads(spec.read_text(encoding="utf-8")).get(tool, [])
        if tool == "build" and (TYPES / name / "preamble.tex").exists():   # the type's own commands
            defaults += ["--type-preamble", str(TYPES / name / "preamble.tex")]
        if tool == "build" and (TYPES / name / "cover-page-main.tex").exists():   # the type's own cover
            defaults += ["--type-cover-dir", str(TYPES / name)]
        i += 2
    return [argv[0], *defaults, *rest]
