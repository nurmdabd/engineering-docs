"""
doctype.py -- document types. A type is a folder types/<name>/ with:
  type.json   {"description": ..., "md2tex": [default flags], "build": [default flags]}
  guide.md    how to write and lay out that kind of document (read it before writing the content)

`--type NAME` on md2tex.py or build.py puts the type's default flags in front of the command line,
so any flag given explicitly still wins (argparse keeps the last value).
"""
import json
import sys
from pathlib import Path

TYPES = Path(__file__).resolve().parents[1] / "types"


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
        i += 2
    return [argv[0], *defaults, *rest]
