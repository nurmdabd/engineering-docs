# Document type: project-report

A multi-day project or lab report, such as the RTL-to-GDSII flow report: one chapter per day (or per stage), each with its commands, outputs, results and observations. This type replaces the separate `markdown-to-latex-engineering-report` skill. Everything in `SKILL.md` applies; this guide adds what is specific to reports.

## Settings

`--type project-report` on `md2tex.py` and `build.py` sets `--class extreport --fontsize 14pt`. Flags you pass yourself still win.

```bash
python3 <skill>/scripts/md2tex.py day-01.md -o latex/day-01.tex --type project-report
python3 <skill>/scripts/build.py latex/day-01.tex latex/day-02.tex --out Report.pdf --type project-report \
    --title "RTL-to-GDSII Flow:" --title "Lab Report" --header "RTL-to-GDSII Flow Report"
```

- **Front matter instead of flags:** put `type: project-report` (and `title`, `subtitle`, `header`, cover fields) at the top of the Markdown; then `md2tex.py day-01.md -o latex/day-01.tex` and `build.py latex/day-01.tex … --out Report.pdf` need no flags (`references/authoring.md`).
- **One body file per day,** for example `day-01.tex`, `day-02.tex`, built together into one PDF.
- **Labels:** prefix them per day (`sec:d01_…`), because labels must be unique across the whole build.
- **No cover by default.** Add `--cover` with the cover fields if the report needs one.

## Writing the content

Use this when Claude writes or completes the Markdown, not only when converting it.

**Sources:** the user's own logs, commands, terminal output, screenshots and repo. Never invent a command, an output, a number or a file name. If a result is missing, leave a visible placeholder (`**Result:** TODO, waiting for the run`) and ask.

**Structure of one day** (`#` is the chapter):

````markdown
# Day 01: RTL Analysis

## Objective
One or two sentences: what this day sets out to do.

## Background
The theory needed to follow the steps, with equations where they help.

## Steps
### Synthesis
**Command:**
```bash
./flow.tcl -design picorv32a
```
**Output Snippet:**
```
[INFO]: Synthesis complete
```
**Observation:** what the output shows and why it matters.

## Results
| Metric | Value |
|---|---|
| Cells | 14876 |

## Observations
What was learned, what went wrong and how it was fixed.

## References
::: {.repocard title="Project Repository References"}
**Public Repository:** [repo-name/](https://github.com/user/repo)
:::
````

- **Command and output:** when the source shows a command and its output separately, keep them as two code blocks under `**Command:**` and `**Output Snippet:**`. A combined transcript stays one block.
- **Trim long outputs** to the lines that matter and say so (`… 120 lines omitted …`). The trimmed text itself is never edited.
- **Results** go in a table whenever there are two or more numbers to compare.
- **Figures:** screenshots go in `figures/` beside the Markdown. A screenshot that isn't taken yet is written as a normal image link; the converter leaves it commented out with a TODO.
- **Repos and tools:** a block that points to a repo, a tool or an external resource goes in a `repocard`: `::: {.repocard title="OpenLane repo"}` … `:::` (`references/latex-rules.md`, Section 9).
- **Study-notes boxes** (`notebox`, `exambox`, question boxes) are not used in reports unless the user asks.

## Differences from the old report skill

- **Unicode:** follow Section 10 of `references/latex-rules.md`. The old skill allowed raw Greek letters and arrows in running text, but the main font (Latin Modern) drops most of them.
- **Headings:** reports use the house automatic colon like every other document (the user's choice). The old report skill had no automatic colon, so its Markdown sometimes ended headings with a colon by hand. Never write one (`## Results`, not `## Results:`); a heading that ends with `?` gets no added colon (`references/latex-rules.md`, Section 1).
- **Display maths:** follow Section 7 of `references/latex-rules.md` (`align` for derivations, `\boxed` for final results). The old skill used a plain `equation` for every display.
