# Tests

`run_tests.py` converts each fixture in `fixtures/` with the flags in `cases.json` and compares the result with `expected/`. With `--build` it also compiles every expected body and `examples/example-body.tex`; each log must be clean. Usage is in the script's docstring and in SKILL.md, "Changing the skill".

The expected files record what the converter does today, including the gaps below. When one is fixed, its expected output changes; check the diff and accept it with `--update`.

## Known converter gaps

Found while writing these fixtures. Each one is handled in the hand review (SKILL.md Step 3) until it is fixed.

1. **Consecutive `$$` blocks** stay separate equations; they are not merged into one `align`. Writers are steered away from it instead: the linter warns, and `references/authoring.md` says to write one `$$` block with `\\` and `&`, which becomes an `aligned` equation. (The COM notes never use back-to-back `$$` blocks.)
2. **Generic captions** when the Markdown sets none: code listings get "Listing", and a table gets its section title, repeated when a section has two tables (`core-elements`). The Markdown can set both (`references/authoring.md`).

Fixed so far:
- A figure whose image is missing is commented out with a TODO instead of breaking the build.
- In `extreport`, several `#` headings all stay as chapters instead of the first becoming the title.
- A `####` run-in label ending in `?` no longer gets a colon after it.
- Sub-parts `(iv)`, `(12)` at the start of a line now start a new paragraph like `(b)` did; before, only single-character labels did.
- One `$$` block with `\\` and `&` becomes an `aligned` equation; before, its lines were centred.
- Tables (`table-layout`): a column of short symbols no longer takes the spare width from a prose column; header cells no longer draw double rules between them; a table of up to 6 rows no longer splits across pages (it reserves its height with `\needspace`, together with a heading or label right above it).
- In-file links written with GitHub's anchors (`#2-tables`, `#lecture-24--pm-bandwidth`) now reach their heading; before, they became plain text.

`--build` also builds the example and the cases marked `"print": true` with `--print`: no rendered page of those may hold colour. A small check draws two coloured curves and runs `figures_bw.to_bw` on them: they must get different dashes, the legend must match, and nothing may stay coloured.

`lint/` holds Markdown for the linter: `clean.md` must give no findings, `problems.md` one of each. Their output is compared with the `.expected` files.
