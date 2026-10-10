# Tests

`run_tests.py` converts each fixture in `fixtures/` with the flags in `cases.json` and compares the result with `expected/`. With `--build` it also compiles every expected body and `examples/example-body.tex`; each log must be clean. Usage is in the script's docstring and in SKILL.md, "Changing the skill".

The expected files record what the converter does today, including the gaps below. When one is fixed, its expected output changes; check the diff and accept it with `--update`.

## Known converter gaps

Found while writing these fixtures. Each one is handled in the hand review (SKILL.md Step 3) until it is fixed.

1. **Consecutive `$$` lines** become separate `equation`s, not one `align` as Section 7 of `references/latex-rules.md` asks (`core-elements`, Equations).
2. **Generic captions** when the Markdown sets none: code listings get "Listing", and a table gets its section title, repeated when a section has two tables (`core-elements`). The Markdown can set both (`references/authoring.md`).
3. **Lettered sub-parts** (`(a)`, `(b)` on consecutive lines) run together into one paragraph; they are not made into a lettered list.

Fixed so far:
- A figure whose image is missing is commented out with a TODO instead of breaking the build.
- In `extreport`, several `#` headings all stay as chapters instead of the first becoming the title.
- A `####` run-in label ending in `?` no longer gets a colon after it.
- In-file links written with GitHub's anchors (`#2-tables`, `#lecture-24--pm-bandwidth`) now reach their heading; before, they became plain text.

`lint/` holds Markdown for the linter: `clean.md` must give no findings, `problems.md` one of each. Their output is compared with the `.expected` files.
