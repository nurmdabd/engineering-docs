# engineering-docs

A Claude Code skill that turns engineering Markdown into LaTeX in Nur Mohammad's house style and compiles it to an interactive PDF with XeLaTeX. Everything it needs is inside this folder: the preamble, the `main.tex` template, a cover system (a front cover per type, the back of the cover, a back cover), the Markdown→LaTeX converter and the build scripts, including print copies for double-sided printing and packs that combine several PDFs.

**New here? Read [USER-GUIDE.md](USER-GUIDE.md):** how to ask for each kind of document and get the best output.

`SKILL.md` is the entry point: the workflow, the two ways the skill is used (convert finished Markdown, or write the content first) and when to ask. The detailed rules are in `references/`.

## Layout

| Path | What it is |
|---|---|
| `USER-GUIDE.md` | For you: how to use every feature, with example prompts |
| `SKILL.md` | Workflow, output rules, when to ask |
| `references/` | `authoring.md` (how to write the Markdown), `front-matter-keys.md` (every setting, generated), `commands.md` (custom commands: registry, adding new ones), `latex-rules.md` (Sections 1–12), `pdf-links.md` (13), `bangla.md` (14), `covers-and-print.md` (15: covers, print copies, packs) |
| `template/` | House preamble, `main.tex`, the cover kit, default cover and back cover, the pack cover (`pack-cover.tex`: a pack's cover and "In this pack" page), edge tabs, `print-bw.tex` (black-and-white print copy), `share.tex` (share copy: footer line, print-only stamp) |
| `scripts/` | `doc.py` (one command: types, new, check, build, bundle, keys; `--print` for the black-and-white copy, `--share` for the share copy), `build.py`, `md2tex.py` + `house.lua` (converter), `lint_md.py` (Markdown checks), `check_structure.py`, `coverdata.py` (the facts covers show), `formulasheet.py` (Key formulas, Symbol index), `mindmap.py` (mind-map layout), `bundle.py` (packs), `figures_bw.py` (grey print copies of matplotlib figures), `commands.py` (custom-command registry), `setup.sh` |
| `examples/` | A body file that uses every rule |
| `types/` | Document types (theory-notes, exam-notes, formula-sheet, question-bank, past-paper, project-report, mind-map): settings (`type.json`), writing and layout guide (`guide.md`), starting file (`template.md`), own commands (`preamble.tex`), front cover (`cover-page-main.tex`) and back-of-cover page (`inside-cover.tex`), the last three optional |
| `tests/` | Regression tests: `python3 tests/run_tests.py --build` |
| `CHANGELOG.md`, `ROADMAP.md` | What changed, and the ideas saved for later |

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
