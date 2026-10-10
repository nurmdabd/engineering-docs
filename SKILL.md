---
name: engineering-docs
description: "Writes and builds engineering documents in Nur Mohammad's house LaTeX style and compiles them to interactive PDFs with XeLaTeX: lecture and theory notes, formula sheets, question banks, derivation and exam sheets, full solutions of previous years' exam papers, and multi-day project or lab reports, each kind with its own document type and writing guide. English, or Bangla with English technical terms. Covers the whole path: writing the Markdown content when asked, converting Markdown to house-style LaTeX (draft converter plus rules), and building the PDF with the bundled preamble, cover page, callout boxes, linked question/solution boxes and links between PDFs. Use whenever the user wants notes, solutions, a report or exam material as a PDF or .tex in \"my format\" or \"my LaTeX style\", even if they never say LaTeX, or asks how a Markdown element renders in this style. When converting the user's finished Markdown, content is preserved exactly (grammar fixes only)."
---

# Engineering documents in the house LaTeX style

Read this file first. It is the workflow; the detailed rules are in `references/` and are read when a step needs them.

| File | Read it when |
|---|---|
| `references/authoring.md` | Writing or checking Markdown: front matter, and how each construct must be written so it converts cleanly |
| `references/latex-rules.md` | Converting or reviewing LaTeX: custom commands, and Sections 1–12 (headings, inline text, lists, tables, code, figures, maths, cross-references, repo blocks, Unicode, callouts and questions, `mainquestion`/`eqnote`) |
| `references/commands.md` | Using a custom command from Markdown (`::: {.name}`, `[text]{.name}`), or adding a new command for a document, a type or the core |
| `references/pdf-links.md` | Building several PDFs that link to each other (Section 13) |
| `references/bangla.md` | The document is in Bangla (Section 14) |
| `types/<name>/guide.md` | Writing or converting a document of that type |

Section numbers (0–14) are shared across these files, so "Section 7" always means the same rules.

## Two ways this skill is used

1. **Convert the user's finished Markdown.** Preserve the content exactly; fix grammar only. Never summarize, trim, add or reword explanations.
2. **Write the content, then build.** When the user asks Claude to produce the document (solutions, a report section, notes), first read the type's `guide.md`. Write the Markdown to `references/authoring.md` (front matter with the type, headings without a trailing colon, `**Label:**` lead-ins, `> ⚠`/`> 🎯`/`> 📌` callouts, `#### N1` questions, `$$ … $$` equations), and run the linter on it until it reports no errors. Never invent data the user has to supply, such as measured results or exam questions. **Show the Markdown to the user and get it approved before building;** from then on it is finished Markdown and mode 1 applies.

## Bundled files

| File | What it is |
|---|---|
| `template/main-tex-preamble.tex` | The **live** house preamble. It is the user's own preamble with two portable changes: the header text comes from `\ReportHeader`, and the emoji font falls back to DejaVu Sans when Segoe UI Emoji is missing. |
| `template/main.tex` | The user's main-file layout: title lines, TOC with the `toc` anchor, "Created by …", `\newpage`, then `\include` of each body file. A cover page is included automatically if `cover-page-preamble.tex` and `cover-page-main.tex` are present in the build. It also passes hyperref's `destlabel` option (Section 13). |
| `template/cover-page-*.tex` | The **study-notes cover page** (course code band, document title, subtitle, note, optional "Inside" box, author and date). It is filled by `build.py --cover …`. The user's other covers are for other purposes; pass `--cover-dir` to use one of those instead. |
| `scripts/md2tex.py` + `scripts/house.lua` | A pandoc-based **draft converter** that applies the mechanical rules: headings, labels, table tiers, equations, figures, callouts, question/solution boxes, `eqnote` and Unicode. Its output still gets the Step 3 review. |
| `scripts/setup.sh` | Installs XeLaTeX, every package the preamble loads, pandoc, PyYAML and Pillow (Debian/Ubuntu). Re-running it is safe. |
| `scripts/doc.py` | One command for the whole path: `types`, `new`, `check`, `build` (see Workflow). |
| `scripts/commands.py` + `template/commands.yaml` | The custom-command registry: `list`, `check NAME`, `add` (references/commands.md). Types and documents add their own `commands.yaml`. |
| `scripts/lint_md.py` | Checks Markdown against `references/authoring.md` before converting: front matter, headings, questions and solutions, links, images, equations, glyphs. |
| `scripts/check_structure.py` | A fast check for unbalanced braces and `\begin`/`\end` pairs, with no compile. |
| `scripts/build.py` | Fills the template, compiles with latexmk/XeLaTeX, and summarizes errors, undefined references, **missing glyphs** and wide overfull lines. |
| `examples/example-body.tex` | A body file that uses every rule. It compiles clean, so copy its patterns. |
| `types/<name>/` | **Document types:** `type.json` (default flags) and `guide.md` (how to write and lay out that kind of document). |
| `tests/run_tests.py` | Regression tests for the converter and the build (see Changing the skill). |

Never edit the bundled preamble to suit one document. If the user changes their live preamble, they send the new file and it replaces `template/main-tex-preamble.tex`. Keep the two portable changes above, the **Study-notes additions** block at its end (callout boxes, markers, `\golink`, PDF navigation), and the punctuation-aware `\addcolon`, when you do that.

## Document types

A type is a preset for one kind of document. `type:` in the front matter (or `--type NAME` on the scripts) loads `types/NAME/type.json`, and flags you pass yourself still win. A type may also bring its own `preamble.tex` with commands only it uses; the build loads it after the house preamble. Before writing or converting a document of that kind, read `types/NAME/guide.md`: it says how to write the content and which rules differ from the defaults in this file and the references. `types/NAME/template.md` is a starting file.

| Type | For |
|---|---|
| `theory-notes` | Lecture or theory notes taught like a lesson: lecture openers, explained figures, worked examples, a self-check per lecture; Bangla versions too |
| `exam-notes` | The memorize-version of theory notes: same headings, each linked back to its full explanation; definitions, steps, labels, worked examples, exam answers |
| `formula-sheet` | Every formula of a course in Title / Equation / Notation / Reference tables, 10pt with narrow margins |
| `question-bank` | Practice numericals, short and long questions, each linked to its solution |
| `past-paper` | Solutions of a previous year's exam paper: the paper's questions with marks, then a solution block per sub-part (Theory, Answer, Keyword Explanation, Notes and Remarks, Final Concise Answer); tighter layout |
| `project-report` | Multi-day project or lab reports (RTL-to-GDSII flow): one chapter per day, `extreport` at 14pt |

- **Choosing the type:** the user's request usually names it. For existing Markdown without `type:`, the linter and the converter suggest one from the content (`scripts/detect_type.py`); confirm it with the user before adding it to the front matter. When nothing fits (a derivation sheet, a mind map), use the house defaults with no type, then offer to add a type for that kind of document.
- **New types:** a folder `types/NAME/` with `type.json`, `guide.md` and `template.md` (and `preamble.tex` if it needs its own commands). `tests/run_tests.py` checks that every type has them and that its template lints and builds clean.

## Workflow

**Quick path:** `scripts/doc.py` runs the steps below in order for a Markdown file with front matter:
```bash
python3 <skill>/scripts/doc.py types                  # what each type is for
python3 <skill>/scripts/doc.py new question-bank notes.md
python3 <skill>/scripts/doc.py check notes.md         # Step 2's lint
python3 <skill>/scripts/doc.py build notes.md         # lint, convert to latex/notes.tex, check, build notes.pdf
```
`build` reuses an existing `latex/NAME.tex` (it may hold hand edits) and stops if the Markdown is newer; `--reconvert` regenerates it. The steps still apply: review the draft (Step 3) and look at the pages (Step 5).


### Step 1: Setup (once per session)
```bash
bash <skill>/scripts/setup.sh
```

### Step 2: Lint, then convert (draft)
Check the Markdown first. Fix every error; for each warning, fix it or confirm the result is what the user wants:
```bash
python3 <skill>/scripts/lint_md.py NOTES.md
```

Write one `.tex` body file per logical document part, for example one per lecture or day, or one per sheet. Each file is raw body content that starts at its outermost heading. Save it in a `latex/` folder beside the Markdown so image paths resolve.

For anything longer than a page, draft it with the converter instead of typing it out:
```bash
python3 <skill>/scripts/md2tex.py NOTES.md -o latex/NOTES.tex [--class extarticle|extreport] [--fontsize 12pt]
```
The converter prints the suggested `--title` lines: the YAML `title`/`subtitle`, or else the first `#` heading, which it then removes from the body.

**Front matter** (`references/authoring.md`) does the flag work: `type` and `lang: bn` set the converter's flags, and every build setting (type, cover fields, header, titles) is saved to `latex/NOTES.build.json`, which Step 4 applies automatically. For a document with front matter, `md2tex.py NOTES.md -o latex/NOTES.tex` and `build.py latex/NOTES.tex --out NOTES.pdf` are enough.

### Step 3: Review the draft, then check its structure
The converter cannot make the judgement calls. Read the draft against Section 0 below and `references/latex-rules.md`, and fix by hand:
- **`\keyterm` vs plain:** the converter turns every bold span into `\keyterm`, except short all-lowercase stress words like "not" or "before", which become `\emph`.
- **Captions** that came out generic, for example "Listing" or a repeated section title. Better: set them in the Markdown (`Table:` lines, `caption=` on code blocks; `references/authoring.md`).
- **Ambiguous callouts:** any blockquote whose box type is unclear.
- **Columns** that the page render (Step 5) shows wrapping badly.

Never re-run the converter over a body file you have hand-edited; it overwrites the file. Then run:
```bash
python3 <skill>/scripts/check_structure.py body.tex
```

### Step 4: Build
```bash
python3 <skill>/scripts/build.py body1.tex [body2.tex ...] --out path/Name.pdf \
    --title "First title line:" --title "Second title line" \
    --header "Short running header" \
    [--class extarticle|extreport] [--fontsize 12pt] [--author "Nur Mohammad"] \
    [--figures extra/image/dir ...] [--no-toc] \
    [--cover --course-code "COM I" --course-name "Communication Engineering I" \
     --cover-title "Formula Sheet" --cover-subtitle "Lectures 24--38" --cover-note "Term test preparation" \
     --cover-contents "Item" --cover-contents "Item" --date "October 2026"]
```

- **Settings from front matter:** if `NAME.build.json` sits beside the first body, its settings are applied first and printed. A flag you pass overrides it; your `--title` or `--cover-contents` lines replace the saved ones.
- **Cover page:** add `--cover` for study notes and exam material. The cover fields are raw LaTeX, so write `--` for an en-dash and `\&` for `&`. Use `--cover-dir DIR` to use another cover pair instead.
- **Several documents:** when one project produces several PDFs, write a small `build-all.sh` next to the bodies that calls `build.py` once per document. Commit it so the PDFs can be rebuilt later.

- **Defaults** match the user's latest main file: `extarticle`, `12pt`, author "Nur Mohammad". The title lines are rendered as `{\LARGE{\keyterm{…}}}`.
- **Choosing the class:** use `--class extreport` when the source has chapter-level `#` headings, as in a multi-day report; `--type project-report` sets that with `14pt`. In `extreport`, a file with several `#` headings keeps them all as chapters; otherwise the first `#` heading becomes the title.
- **Image search path:** each body file's folder and its `figures/` subfolder are added automatically, so `\includegraphics{name.png}` works with a bare filename. Use `--figures` for images stored anywhere else.
- **Build folder:** the build writes `<Name>_build/` next to the PDF. It holds `main.tex`, the preamble and the body files, and it compiles as-is on the user's MikTeX.

### Step 5: Look at the result
The build log summary must say **"Log clean"**, or every item it lists must be understood. Then render the pages and view them:
```bash
pdftoppm -r 60 -png Name.pdf /scratch/pg
```
Check the following, and fix the body file and rebuild if anything is off:
- Tables are not running off the page.
- No equation overflows the margin.
- Figures are sized sensibly. Use `width=0.8\linewidth` by default and narrower for tall images.
- Nothing is blank where a glyph should be.

### Step 6: Deliver
Give the user:
- the PDF;
- the body `.tex` files;
- the `_build/` folder (or a zip of it), so they can recompile locally.

If the work is in a git repo, commit the body `.tex` files and the PDF. Add `*_build/` (and LaTeX aux files) to `.gitignore` unless the user wants the build folder kept.

## Output rules for the body file (non-negotiable)

- The body file contains raw LaTeX **body content only**. It has no `\documentclass`, no preamble and no Markdown. The build script supplies the preamble and `main.tex`.
- Preserve all technical content exactly. Do not summarize, remove, add or rewrite explanations; only fix grammar.
- Do not redefine any command or environment the preamble already provides.
- Use only custom commands that are registered (`scripts/commands.py list --type T`). Standard LaTeX is always fine. If a document needs a custom command that doesn't exist, fall back to plain LaTeX, or propose a new command to the user and add it with `scripts/commands.py add` once they agree (`references/commands.md`). Never define a command inside a body file.
- UTF-8 is allowed in running text **only for characters the main font (Latin Modern) has**. See Section 10. The build reports any glyph that went missing, and that report must be empty.

## 0. When to ask instead of guessing

These default fallbacks are safe to apply without asking:
- **A standalone assignment or question prompt:** a plain paragraph with `\textbf{Question:}` as the label.
- **A callout** (blockquote, Note, Warning, Exam tip, Example): the matching box from Section 11. Only when no box fits, use a `\textbf{Label:}` paragraph.
- **An equation followed by a "where …" explanation:** a plain `equation` with a plain `itemize` list underneath (see Section 7).
- **Introductory or front-matter text** that describes the whole document series rather than fitting under one heading: preserve it as a LaTeX `%` comment block near the top, with a short note explaining why it isn't its own section. Don't force it into a heading and don't drop it.
- **A Markdown "Contents" list:** drop it. The template already builds a live table of contents.

Still **stop and ask**, quoting the exact snippet and naming 2–3 concrete options, when:
- A construct doesn't fit any mapping in this file *or* the fallbacks above.
- You're unsure whether content wants the `repocard` treatment, a callout box, a plain paragraph, or some other boxed or special formatting. That includes the unmapped preamble commands listed above.
- Something the user says about their live preamble contradicts `template/main-tex-preamble.tex`, such as a command that supposedly doesn't exist, different styling, or an extra environment. Confirm which is current before relying on it.
- Getting it wrong has a real cost: it would misrepresent technical content, or duplicate or omit a cross-reference.

Convert everything unambiguous first, then ask about the rest. Don't block the whole output on one uncertain piece.

## Changing the skill

After any change to `scripts/` or `template/`, run `python3 <skill>/tests/run_tests.py --build`. Every fixture must convert to its expected output in `tests/expected/`, and every build must log clean. If an output changes on purpose, check the diff and accept it with `--update`.

Before a converter change, also snapshot the user's real notes and compare afterwards, so a change meant for one document can't silently alter another:
```bash
python3 <skill>/tests/run_tests.py --snapshot /scratch/snap notes.md bangla.md:--bangla
# ... change the converter ...
python3 <skill>/tests/run_tests.py --compare /scratch/snap notes.md bangla.md:--bangla
```

## Quick self-check before building

1. **Body files only:** no `\documentclass`, `\usepackage` or commentary.
2. **Content:** when converting the user's Markdown, nothing summarized, trimmed or added, only grammar fixed. When Claude wrote the content, the user has reviewed it.
3. **Labels:**
   - Every heading below the outermost one has a `\label{}` on the next line, with no blank line.
   - Every table, figure and numbered equation is labelled.
   - Labels are unique across the build.
   - Code listings are unlabelled unless cross-referenced.
4. **Inline commands:**
   - `\textbf{}` is used for lead-in labels only.
   - `\keyterm{}` is applied by the glossary test.
   - `\verb` is never nested inside another command's argument; use `\texttt{}` with escaping there.
5. **Tables:**
   - Columns are the narrowest that don't truncate any entry.
   - Only long-prose columns are flexible.
   - The header row has `\rowcolor{gray!15}`; body rows have none.
6. **Diagrams as text:** trees and flow diagrams use a captioned `lstlisting` with no `language`, in ASCII.
7. **References:** `\cref{}` for in-build references; plain prose for anything outside the build.
8. **`repocard`:** used only for tool and repo reference blocks.
9. **Boxes:** callouts use the Section 11 boxes; `mainquestion` and `eqnote` are used only where Section 12 allows (`references/latex-rules.md`).
10. **Unicode:** Section 10 (`references/latex-rules.md`) is applied, so no raw Greek or relation symbols appear in running text.
11. **Ambiguities:** anything unmapped is flagged with a specific question.
12. **Checks:** `check_structure.py` is clean, the build log says "Log clean" (or its warnings are explained), the rendered pages have been viewed, and the links were verified (`references/pdf-links.md`).
