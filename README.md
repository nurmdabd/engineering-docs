# engineering-docs

A Claude Code skill that turns engineering Markdown into LaTeX in Nur Mohammad's house style and compiles it to an interactive PDF with XeLaTeX. Everything it needs is inside this folder: the preamble, the `main.tex` template, cover pages, the Markdown→LaTeX converter and the build scripts.

`SKILL.md` is the entry point: the workflow, the two ways the skill is used (convert finished Markdown, or write the content first) and when to ask. The detailed rules are in `references/`.

## Layout

| Path | What it is |
|---|---|
| `SKILL.md` | Workflow, output rules, when to ask |
| `references/` | `authoring.md` (how to write the Markdown), `latex-rules.md` (Sections 1–12), `pdf-links.md` (13), `bangla.md` (14) |
| `template/` | House preamble, `main.tex`, study-notes cover page |
| `scripts/` | `doc.py` (one command: types, new, check, build), `setup.sh`, `lint_md.py` (Markdown checks), `md2tex.py` + `house.lua` (converter), `check_structure.py`, `build.py` |
| `examples/` | A body file that uses every rule |
| `types/` | Document types (theory-notes, formula-sheet, question-bank, past-paper, project-report): settings (`type.json`), writing and layout guide (`guide.md`), starting file (`template.md`), own commands (`preamble.tex`, optional) |
| `tests/` | Regression tests: `python3 tests/run_tests.py --build` |

## Using it in a repo

This repo is the master copy. A working repo keeps a copy in `.claude/skills/engineering-docs/` (cloud sessions load skills from there) and refreshes it with a SessionStart hook:

```bash
#!/bin/bash
# .claude/hooks/session-start.sh: refresh the engineering-docs skill from its master repo
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
DEST="$CLAUDE_PROJECT_DIR/.claude/skills/engineering-docs"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
git clone --quiet --depth 1 https://github.com/nurmdabd/engineering-docs.git "$TMP/skill" || exit 0
rm -rf "$TMP/skill/.git"
diff -rq --exclude=__pycache__ "$TMP/skill" "$DEST" >/dev/null 2>&1 && exit 0
rm -rf "$DEST"; mkdir -p "$(dirname "$DEST")"; cp -a "$TMP/skill" "$DEST"
echo "skill sync: refreshed .claude/skills/engineering-docs; commit the changed copy."
```

Register it under `hooks.SessionStart` in the repo's `.claude/settings.json`. See `nurmdabd/Temp-3501` for a working setup.

## Improving the skill

Make changes here, run `python3 tests/run_tests.py --build`, then commit and push. Working repos pick them up at their next cloud session.
