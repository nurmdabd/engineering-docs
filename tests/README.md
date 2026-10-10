# Tests

`run_tests.py` converts each fixture in `fixtures/` with the flags in `cases.json` and compares the result with `expected/`. With `--build` it also compiles every expected body and `examples/example-body.tex`; each log must be clean. Usage is in the script's docstring and in SKILL.md, "Changing the skill".

The expected files record what the converter does today, including the gaps below. When one is fixed, its expected output changes; check the diff and accept it with `--update`.

## Known converter gaps

Found while writing these fixtures. Each one is handled in the hand review (SKILL.md Step 3) until it is fixed.

1. **Consecutive `$$` lines** become separate `equation`s, not one `align` as SKILL.md Section 7 asks (`core-elements`, Equations).
2. **In-document links whose anchor keeps the heading number** (`[…](#2-tables)`) lose the link, because the label is built from the heading without its number (`sec:tables`). The text stays (`core-elements`, Unicode and links).
3. **Generic captions:** code listings get "Listing", and a table gets its section title, repeated when a section has two tables (`core-elements`).

Fixed so far: a figure whose image is missing is now commented out with a TODO instead of breaking the build; in `extreport`, several `#` headings now all stay as chapters instead of the first becoming the title.
