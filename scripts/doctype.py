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
    """Return argv with --type NAME replaced by that type's default flags for `tool` ('md2tex' or 'build')."""
    if "--type" not in argv:
        return argv
    i = argv.index("--type")
    if i + 1 >= len(argv):
        sys.exit("--type needs a name: " + ", ".join(available()))
    name = argv[i + 1]
    spec = TYPES / name / "type.json"
    if not spec.exists():
        sys.exit(f"unknown document type '{name}'. Available: " + ", ".join(available()))
    defaults = json.loads(spec.read_text(encoding="utf-8")).get(tool, [])
    rest = argv[1:i] + argv[i + 2:]
    return [argv[0], *defaults, *rest]
