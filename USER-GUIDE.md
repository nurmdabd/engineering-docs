# engineering-docs: user guide

How to get the best documents out of this skill: what to ask for, what to give Claude, and what each feature does. `SKILL.md` is written for Claude; this file is written for you.

**In one sentence:** you ask for a document (notes, a formula sheet, past-paper solutions, a lab report…), Claude writes or takes the Markdown, and the skill turns it into a PDF in your own LaTeX style: your preamble, colours, callout boxes, linked questions and a clickable table of contents.

**I want to…**

| … | Say or set | Section |
|---|---|---|
| Turn my Markdown into a PDF | "Convert `notes.md` with the engineering-docs skill" | [2](#2-the-two-ways-to-use-it) |
| Have Claude write it | "Use the engineering-docs skill (TYPE type) to write …" | [2](#2-the-two-ways-to-use-it), [4](#4-document-types) |
| Give it a cover | `cover: true` and the `course_*` / `cover_*` keys | [5](#5-covers-colours-and-the-back-pages) |
| Colour a subject's documents | `accent: 5B3A8C` (the same on every document of that subject) | [5](#5-covers-colours-and-the-back-pages) |
| Change the margins | `margin_x: 0.6in` | [6](#6-front-matter-the-settings-block) |
| Print it double-sided | "make a print version" | [12](#12-printing) |
| Put several PDFs in one | a `pack.yaml`, then `doc.py bundle` | [13](#13-packs-several-documents-in-one-pdf) |
| Draw a course mind map | `type: mind-map` | [4](#mind-map) |
| See every setting | `python3 scripts/doc.py keys` or `references/front-matter-keys.md` | [6](#6-front-matter-the-settings-block) |

---

## Contents

1. [Setup](#1-setup)
2. [The two ways to use it](#2-the-two-ways-to-use-it)
3. [Getting the best content](#3-getting-the-best-content)
4. [Document types](#4-document-types)
5. [Covers, colours and the back pages](#5-covers-colours-and-the-back-pages)
6. [Front matter: the settings block](#6-front-matter-the-settings-block)
7. [Writing Markdown yourself](#7-writing-markdown-yourself)
8. [Custom commands](#8-custom-commands)
9. [Bangla documents](#9-bangla-documents)
10. [Changing a document after the build](#10-changing-a-document-after-the-build)
11. [Layout features you get for free](#11-layout-features-you-get-for-free)
12. [Printing](#12-printing)
13. [Packs: several documents in one PDF](#13-packs-several-documents-in-one-pdf)
14. [Running the scripts yourself](#14-running-the-scripts-yourself)
15. [Checking the result](#15-checking-the-result)
16. [Problems and fixes](#16-problems-and-fixes)
17. [Improving the skill](#17-improving-the-skill)

---

## 1. Setup

**Where it lives.** The master copy is the public repo `nurmdabd/engineering-docs`. A working repo (such as `Temp-3501`) keeps a copy in `.claude/skills/engineering-docs/`. Its SessionStart hook refreshes that copy from the master at the start of every cloud session, so an improvement pushed to the master reaches every session.

| Situation | What to do |
|---|---|
| New session on a repo that already has it (Temp-3501) | Nothing. The hook syncs the skill, and `CLAUDE.md` loads by itself. TeX installs automatically on a fresh container, which takes a few minutes. |
| A new repo | Copy `.claude/hooks/session-start.sh` and `.claude/settings.json` from Temp-3501 (the README shows the hook), start a session, and commit the `.claude/skills/engineering-docs/` it creates. |
| Another claude.ai account | Give that account access to the working repo: add its GitHub user as a collaborator, or make the repo public. Connect GitHub in that account and create an environment whose network setting allows `github.com` and package downloads. Nothing has to be uploaded; the repo carries everything. |
| Claude Chat or Cowork (not Claude Code) | Upload the folder as a claude.ai skill. Only needed there. |
| Your own PC | Each build writes a `<Name>_build/` folder next to the PDF that compiles as-is in MikTeX, so you can tweak and recompile locally. |

The repo's `CLAUDE.md` holds the per-repo rules: where each kind of document goes, which PDFs may be rebuilt, and how the past-paper folder is laid out. Keep it current. It is what makes a brand-new session behave like this one.

---

## 2. The two ways to use it

### Mode 1: convert your finished Markdown

You wrote the content, or approved it earlier. Claude keeps it **exactly**: grammar fixes only, never summarizing, trimming or rewording. A type's writing rules (openers, self-checks, required sections) are **not** applied in this mode; only the formatting is.

> Convert `level-2/7-20-80-notes.md` to a PDF with the engineering-docs skill.

### Mode 2: Claude writes the content, then builds

Claude first reads the type's guide (`types/NAME/guide.md`), which sets how the content is written: section order, how numericals are laid out, answer length per mark, and so on. It then writes the Markdown to that standard and lints it.

- **Normally,** Claude shows you the Markdown, waits for your approval, then builds. From then on it counts as finished Markdown and mode 1 applies.
- **"Make me the PDF"** skips the wait: Claude builds right away, hands you the Markdown and the PDF together, and lists the choices it made for you. Your review of the result is the approval.

> Use the engineering-docs skill (question-bank type). Write 10 FM numericals from `complete-theory/COM_Complete_Theory_L24-38.md`, with full solutions.

**Don't write it "normally" first and then ask for a rewrite "in the skill's format".** A rewrite is where numbers change and steps get lost, and a conversion has to keep the content as it is. Ask for the type from the start, so the content is written to its rules the first time.

---

## 3. Getting the best content

1. **Name the skill and the type** in the first message: "Use the engineering-docs skill (past-paper type) …". The skill usually loads by itself, but naming it removes the chance that a general PDF skill is picked instead. Typing `/engineering-docs` loads it directly.
2. **Point at your sources.** Course notes, logs, the question paper, screenshots. Claude never invents data you must supply, such as exam questions, measured results, terminal output or course codes. When something is missing, it leaves a visible TODO and asks.
3. **Commit input files to the repo** rather than attaching them in chat, for example a question PDF in `past-papers/questions/`. Committed files survive a long session and are there for the next one.
4. **Work in stages and check each stage.** Split the work by what needs checking, not by format:
   - Inputs first (the transcribed paper, the list of topics), checked by you.
   - Then content one chunk at a time (one question, one lecture, one day), with your OK before the next.
   - Then build and review the PDF.
5. **Say what only you know:** the teacher's preferred method, which questions matter most, where your class differs from the textbook, how long answers should be.
6. **One big document per session.** If a session runs long and gets summarized, `RESUME.md` and `CLAUDE.md` let the next session carry on.

**Example prompt (past paper):**
> Use the engineering-docs skill (past-paper type) for `past-papers/questions/2022-23-term-final.pdf`. First transcribe the paper and stop for me to check. Then solve one main question at a time and wait for my OK before the next.

---

## 4. Document types

A type is a preset for one kind of document: page settings, a writing guide, a starting template and sometimes its own commands. Set it with `type:` in the front matter. To list them: `python3 scripts/doc.py types`.

| Type | Use it for | Layout |
|---|---|---|
| `theory-notes` | Lecture notes taught like a lesson | 12pt; cover listing the parts; "how to use" page; edge tabs |
| `exam-notes` | Memorize-version of theory notes, each heading linked back | 12pt; revision cover; revision-plan page; edge tabs |
| `formula-sheet` | Every formula in Title / Equation / Notation / Reference tables | 10pt, 0.4in margins; cover with the topics; Key formulas and Symbol index pages; edge tabs |
| `question-bank` | Practice numericals, short and long questions, linked to solutions | 12pt; cover with the counts; practice-log page |
| `past-paper` | Full solutions of a previous year's paper | tight layout; solutions cover with a question map; paper-at-a-glance page; the typeset question paper linked to the solutions |
| `project-report` | Multi-day lab or project report, one chapter per day | 14pt report (chapters); formal framed cover |
| `mind-map` | A whole course as a map you can click through | landscape A4 (screen) or A3 (print); its own cover |

Every type has 0.5in left and right margins unless the table says otherwise. No type fits (a derivation sheet, a traps sheet)? Leave `type:` out and the house defaults apply. Ask Claude to add a new type if you'll make that kind of document again.

**Not sure which type?** If your Markdown has no `type:`, the linter and converter suggest one from the content ("this looks like exam-notes"). They never apply it on their own.

### theory-notes

- **What you get:**
  - Parts and lectures, each lecture opening with a 📌 box: Where we are, Today's question, Plan.
  - Every section starting with a bridge from the previous one, and derivations that explain why each step is taken.
  - A "Reading the figure" paragraph under every figure.
  - Worked examples, ⚠ corrections, 🎯 exam tips, and a summary and self-check at the end of each lecture.
- **You give:** the raw notes (transcriptions, handwritten PDFs) and the lecture range.
- **Ask:** "Write theory notes for Lectures 39–42 from `level-1/part-06…md` (engineering-docs, theory-notes)."

### exam-notes

- **What you get:** the same headings and numbers as the theory notes, each followed by an *Explained in §…* link back to the full explanation. Under each heading: definitions, numbered steps, what to label in the figures, worked examples and exam answers.
- **You give:** the finished theory notes. Exam notes are always made from them.
- **Note:** for the links to work in the PDF, the theory PDF is built first. The COM repo does this with `latex/build-notes.sh`.

### formula-sheet

- **What you get:** one table per topic, with the columns Title, Equation, Notation and Reference.
  - **Notation** defines every new symbol with its unit.
  - **Reference** links into the theory PDF.
  - Must-know formulas are in bold.
- **You give:** the theory notes. Every formula is copied exactly as derived there, never "simplified".
- **Tip:** after the first build, only the Notation and Reference column widths may need a hand tweak in the `.tex`. After that, don't reconvert.

### question-bank

- **What you get:** numericals `N1…`, short questions `S1…` and long questions `L1…`, each in a box linked to its solution and back. Every solution ends in a bold result.
- **You give:** the topic range and how many of each kind. Optionally, the numerical types your teacher likes (from `important/exam-watchlist.md`).
- **Real past questions** go in a past-paper document, not here.

### past-paper

- **What you get:**
  - Each main question on a new page, with the paper's text in a grey box and its marks.
  - For every sub-part, a solution block with the question highlighted, then:
    - **Theory** (optional), building the topic from basics;
    - **Answer**, sized to the marks;
    - **Keyword Explanation**;
    - **Notes and Remarks**;
    - **Final Concise Answer**, once per main question.
  - Numericals laid out as: Given (in base units), the relationships, numbered steps each ending in a boxed result, then the final answer. Every number is computed with a script.
- **You give:** the question paper (PDF or photo), committed to `past-papers/questions/`. Anything Claude can't read is marked `[unclear: …]` for you to check.
- **The linter checks** that every paper item has a solution, every solution matches a paper item, every item has marks, and every question has a Final Concise Answer.

### project-report

- **What you get:** one chapter per day: Objective, Background, then Steps with **Command:** and **Output Snippet:** listings, then Results and Observations.
  - Repos and tools appear as repo cards.
  - Long file paths wrap cleanly (`[path]{.normalpath}`).
- **You give:** your logs, commands, terminal output and screenshots. No command, output or number is ever invented; a missing result becomes a TODO.
- **Settings:**
  - Several days in one PDF: `label_prefix: d03_` in each day's front matter keeps labels unique.
  - One day built on its own: `first_number: 3` numbers it Chapter 3.

### mind-map

- **What you get:**
  - **The main map:** the course name on top, joined to every part (numbered, in teaching order); under each part, its key ideas as cards with their formula. A ★ marks what exams ask most, and grey text on a card names what is inside it.
  - **Two buttons on every card,** in a strip on its right edge: **i** opens the idea's definition and formula in the outline table; **▸3** (only on cards with more inside) opens its sub-map with 3 more cards. Each button is clickable over its whole area.
  - **Sub-maps** carry on from a card without repeating it: the heading is that card (tap it to go back), its parts are the cards below. Several share a page.
  - **The outline table:** every idea in one table, each level in its own column, with *What it is*, *Key formula* and a ↩ map link back to its card. Cards are coloured; details (the grey lines) are dark grey.
  - Small "→ TDM" chips show where an idea is used again (tap one to jump there); card titles can link into the theory PDF. Anything after the map (a compare-and-contrast table) follows on its own pages.
- **Two sizes, one structure:** `map_size: a4` (the default) for reading on screen; `map_size: a3` for printing, with room for more on each card. Build both if you want both.
- **When a part has too many cards,** the build shortens it step by step (tighter gaps, then the grey lines, then two or three columns where there is room, then up to a third of the cards shown as their title alone (`map_titles` changes the share), then "+n more" carrying on right after the main map) and says what it did. Nothing is ever cut: everything stays in the outline table.
- **More than six parts** continue the main map on the next page (spread evenly), and a sub-map sits right beside its card wherever a page has room left over.
- **You give:** the theory notes, or the topics you want on it. It is written as a nested list with a `def:` line per idea (`types/mind-map/guide.md`); Claude never places boxes by hand.
- **Ask:** "Make a mind map of COM I Lectures 24–38 (engineering-docs, mind-map type), A4 and A3."

---

## 5. Covers, colours and the back pages

With `cover: true` (past papers have it by default), a document gets three extra pages, all filled from the document itself:

- **The front cover,** different for each type but clearly one family: the same band, course block, footer and a faint motif in the middle. The panel at the bottom shows facts read from the document, never typed in: the parts and their lecture ranges, the formula count of each topic, the number of questions of each kind.
- **The back of the cover** (page 2), useful instead of blank:

  | Type | Page 2 |
  |---|---|
  | theory notes | How to use these notes: how a lecture is laid out, what each box means, how to get around, what to know first (`prerequisites:`) |
  | exam notes | My revision plan: a row per lecture to tick on days 1, 3 and 7 and the night before, with a confidence rating |
  | formula sheet | Before you use the sheet: your first row, annotated, and how to use the sheet in the exam |
  | past paper | The paper at a glance: time, marks, how many to answer, and every sub-part with its marks and minutes |
  | question bank | How to practise, and a practice log with two boxes per question |

- **The back cover** (last page of the print copy; add `back_cover: true` to have it in the screen PDF too), in its own style: a strip on the right edge with the course and document name, faint rings, a short "About this document" (`back_blurb:`), a few numbers and the page count.

**Colours:** each type has its own colour, and each subject has one too (`accent:`). Give every document of a subject the same `accent`, and they look like a set. Headings and boxes keep the house colours.

**Turning parts off:** `inside_cover: false` (no page 2), `back_cover: false` (no back cover, not even in print), `cover: false` (none of the three).

**Edge tabs:** theory notes, exam notes and formula sheets also get a clickable coloured tab per part on the right edge of every page; the wide tab is the part you are reading. `edge_tabs: false` removes them. They are never printed.

---

## 6. Front matter: the settings block

The YAML block at the top of the Markdown holds every build setting, so you never need to pass flags.

```yaml
---
title: "COM --- Communication Engineering I:"
subtitle: "Complete Theory (Lectures 24--38)"
type: theory-notes
lang: en                 # bn for Bangla
header: "COM I --- Complete Theory"
header_right: ""         # text before the TOC button, right of the header
cover: true
course_code: "COM I"
course_name: "Communication Engineering I"
cover_title: "Complete Theory"
cover_subtitle: "Lectures 24--38"
cover_note: "Term test preparation"
cover_contents:
  - "Five parts, fifteen lectures"
date: "October 2026"
---
```

| Key | Effect |
|---|---|
| `title`, `subtitle` | Title lines. Without them, the first `#` heading is the title. |
| `type` | Loads that type's layout, cover and writing rules |
| `lang` | `bn` switches on Bangla handling |
| `header`, `header_right` | Running header, left and right |
| `cover` and the `course_*` / `cover_*` keys | The type's cover (Section 5). Claude leaves the cover out rather than invent course details. |
| `accent`, `back_blurb`, `prerequisites` | The subject's colour; the back cover's sentence; "before you start" on a theory cover's back |
| `margin_x` | Left and right margins (default `0.5in`; formula sheets `0.4in`) |
| `author`, `date` | Cover and back cover (author defaults to Nur Mohammad) |
| `toc: false` | No table of contents (one-table sheets) |
| `print_layout: booklet` | Print copy padded to a multiple of 4 pages (Section 12) |
| `map_size`, `map_titles` | Mind maps: `a4` or `a3`; the share of a column's cards that may lose their formula (`1/3`; `0`: never) |

**Every key with its default** is listed in `references/front-matter-keys.md`, or run `python3 scripts/doc.py keys`. That list is generated from the code, so it is always complete; the linter reports any key it doesn't know.

**Writing values:** they are raw LaTeX, so write `--` for an en-dash, `---` for an em-dash and `\&` for `&`. Put quotes around any value that contains a colon.

---

## 7. Writing Markdown yourself

The full spec is in `references/authoring.md`. This is the short version.

| You write | You get |
|---|---|
| `#`, `##`, `###` | Numbered headings (sections; chapters in a report). The colon is added automatically, so don't type one. |
| `####` | A bold run-in label |
| `**Objective:**` at the start of a paragraph | A bold lead-in label |
| `**granular noise**` elsewhere | A key term (`\keyterm`) |
| `**not**`, `**before**` | Italic stress |
| `[text]{.note}` | A small side remark |
| `> ⚠ **Sign note:** …` | A red warning box titled "Sign note" |
| `> 🎯 …` | An exam-focus box |
| `> 📌 …` or a plain `> …` | A note box |
| A paragraph starting `**Example 2:**` | An example box |
| `$$ … $$` | One numbered equation; `\\` and `&` make it a multi-line aligned derivation |
| `$$\boxed{…}$$` | A boxed result |
| `where:` plus a bullet list after an equation | A "where" list |
| `*Write also:* …` right after an equation | A side note next to the equation |
| A pipe table, plus a `Table: Caption` line | A banded table with a caption; `<br>` breaks a line inside a cell |
| ```` ```{.bash caption="Run synthesis"} ```` | A captioned code listing |
| `![Caption](figures/x.png)` | A figure, sized from the image's shape; a missing image becomes a TODO |
| `#### N1` … `#### Solution N1` | A question box and a solution box, linked both ways |
| `[text](#heading-anchor)` | An internal link (GitHub-style anchors work) |
| `[text](other.md#anchor)` | A link into `other.pdf`, which must sit in the same folder |
| β ≈ ≤ 10⁻⁶ ✅ ⚠ | Converted automatically. Other emoji are dropped, so say them in words. |

**Before converting, run the linter:** `python3 scripts/doc.py check notes.md`.
- **Errors** must be fixed: an unclosed `$$`, a question without its solution, an unknown type.
- **Warnings** point to places where the PDF would differ from what you meant: a heading ending in `:`, two `$$` blocks back to back, an unregistered `:::` box, a link to a missing heading.

---

## 8. Custom commands

Every house command is in a registry, which records how Markdown can use it. To list them all: `python3 scripts/commands.py list` (add `--type past-paper` for a type's own).

**Using one from Markdown:**
- **A box:** `::: {.repocard title="OpenLane repo"}` … `:::`. A box written this way can hold several paragraphs, lists and equations.
- **Inline:** `[text]{.note}`, `[path/to/file]{.normalpath}`.
- **One real exam question inside other notes:** `::: mainquestion` … `:::`.

**Adding a new one:** just ask, for example "add a `definitionbox` for the theory notes". Claude checks the name is free, picks the level and compiles a test page; a failed test is rolled back automatically. The levels are:
- **core:** every document;
- **type:** one document type;
- **document:** a `preamble:` file next to a single document.

---

## 9. Bangla documents

Set `lang: bn`. Technical terms, maths, numbers, figure paths and the callout markers stay in English, and sentences end with "।". The Bangla font and the Bangla text handling are switched on automatically.

- **A Bangla version of an English document:** ask for it after the English one is final. The maths is copied byte for byte, and the headings, figures, tables and boxes match one to one.
- **Editing:** the Bangla Markdown is edited directly, never regenerated from the English.

---

## 10. Changing a document after the build

- **Normal fixes go in the Markdown:** wording, a caption, a heading, a box. Then rebuild with `doc.py build notes.md --reconvert`. The Markdown stays the single source.
- **Hand edits to the `.tex`** are only for what Markdown can't express, such as a column width or a forced page break.
  - Once a `.tex` has hand edits, **never reconvert it**, because that overwrites the file. `doc.py build` protects you: it reuses an existing `.tex`, and if the Markdown is newer it stops and asks which you meant.
  - In Temp-3501, `1-formula-sheet.tex` has hand edits. Never run `build-all.sh --reconvert` on it.
- **PDFs are rebuilt only when you ask.** A skill update (new colours, guards) reaches an old PDF only when you ask for that PDF to be rebuilt.

---

## 11. Layout features you get for free

- **Clickable everything:** the table of contents, cross-references, question ↔ solution boxes, links between PDFs, and a **TOC** button in the header of every page.
- **Your colours:** mid-tone blue section headings, red sub-section headings, and a soft red warning box with white title text.
- **Page-break guards:** a heading, or a bold label on its own line, is never left alone at the bottom of a page when an equation, box, table, figure or code block follows. This costs about 1% more pages. To turn it off for one document, convert with `md2tex.py --no-guards`.
- **Automatic colon** after headings, skipped when the title already ends in `?`, `!`, `.` or `।`.
- **Tables** repeat their header row on every page and size their columns from the content. Tall maths in cells gets padding.
- **Numbers and units** stay on one line when written `9.995~MHz` or in maths.
- **Margins** of 0.5in left and right (formula sheets 0.4in); `margin_x` changes one document's, and the tables follow.
- **Covers, the back of the cover and a back cover** for every type (Section 5), and **edge tabs** on theory notes, exam notes and formula sheets.
- **Formula sheets** also get a *Key formulas* page (the bold rows, starred in the sheet) and a *Symbol index*, both linked to the rows.
- **Bookmarks** read cleanly: the EXAM and NOTE markers appear as words.
- **Black-and-white print copy** when you ask (Section 12).

---

## 12. Printing

Say "make a print version of the 2022-23 solution". You get `NAME_print.pdf` beside the normal PDF, which stays as it is:

- **Black and white:** black text and headings, light grey boxes, covers in light tints (little toner), and figures redrawn in grey with dashed and dotted lines in place of colours. Every document is written ready for this from the start (curves differ in line style as well as colour, and the text names both, like "the dashed orange curve"), so the print copy needs no rewriting. The grey figure copies go to `figures/print/`.
- **Laid out for double-sided printing:**
  - page 2 is the back of the cover (or a blank page), so the content starts on a right-hand page;
  - blank pages are added at the end so the back cover is the back of the last sheet: an even page count;
  - `print_layout: booklet` pads to a multiple of 4 pages, for a folded and stapled booklet;
  - without a back cover (`back_cover: false`), the document still ends on a full sheet.
- **No edge tabs** in print: printers cannot print to the edge of the sheet.

---

## 13. Packs: several documents in one PDF

To hand out one file, for example a past paper with the formula sheet, write a small `pack.yaml` beside the PDFs:

```yaml
title: "Exam Pack"
subtitle: "Session 2021--22"
course_code: "EEE329"
course_name: "Basic Communication Engineering"
accent: 2F5D3A
back_blurb: "The solved paper and the formula sheet in one file."
parts:
  - pdf: pdf/2021-22-term-final.pdf
    title: "Question Paper Solutions"
  - pdf: ../level-2/pdf/1-formula-sheet.pdf
    title: "Formula Sheet"
```

Then run `python3 scripts/doc.py bundle pack.yaml` (add `--print` for the print pack). You get one PDF with:
- the pack's own cover: the parts drawn as a stack of sheets in their types' colours, a strip split into the parts by their pages, and one linked card per part;
- an "In this pack" page with every part and its outline (questions, sections), each line linked to its page;
- every part as it was built, its own cover kept as a divider (its back cover is left out);
- one back cover (in the print pack; `back_cover: true` adds it to the screen pack);
- bookmarks with one entry per part and that part's outline under it;
- links between the parts working inside the file, so the "same folder" rule no longer applies.

Build or rebuild the parts first; the pack takes the PDFs as they are. The print pack uses each part's `_print.pdf` and starts every part on a right-hand page. `scripts/bundle.py` lists every key (`label`, `note`, `date`, `out`, `keep_back_cover`, …).

---

## 14. Running the scripts yourself

Claude normally runs these for you. From the folder of the Markdown file:

```bash
S=.claude/skills/engineering-docs/scripts      # adjust the path to where the skill is
python3 $S/doc.py types                         # list the document types
python3 $S/doc.py new past-paper 2023-24.md     # start from the type's template
python3 $S/doc.py check 2023-24.md              # lint
python3 $S/doc.py build 2023-24.md --out pdf/2023-24.pdf             # lint + convert + build
python3 $S/doc.py build 2023-24.md --out pdf/2023-24.pdf --reconvert # regenerate the .tex from the Markdown
DOC_PRINT=1 python3 figures/_src/2023-24.py     # grey copies of the figures, in figures/print/
python3 $S/doc.py build 2023-24.md --out pdf/2023-24.pdf --print     # black-and-white copy: pdf/2023-24_print.pdf
python3 $S/doc.py bundle pack.yaml               # several PDFs as one pack (Section 13)
python3 $S/doc.py keys                           # every front-matter key and its default
bash $S/setup.sh                                 # install TeX, pandoc, fonts, pypdf (safe to re-run)
```

`--out` is relative to the folder you run the command from. The converted body goes to `latex/NAME.tex` beside the Markdown, and its settings to `latex/NAME.build.json`.

---

## 15. Checking the result

Before you call a document done:

- [ ] The build summary says **"Log clean"**: no errors, no missing glyphs, no undefined references.
- [ ] No table or equation runs into the margin.
- [ ] Figures are sensibly sized, and no `TODO` image placeholders are left (unless expected).
- [ ] Links work: click the TOC, a few cross-references, and question ↔ solution.
- [ ] **Content:** every number has its unit, and formulas match the course notes. Past papers: the grey boxes match the paper word for word. Reports: every number is in your logs.
- [ ] The type's own review checklist at the end of `types/NAME/guide.md`.

---

## 16. Problems and fixes

| Problem | Fix |
|---|---|
| The PDF looks plain, not in your style | The skill wasn't used. Say "rebuild this with the engineering-docs skill (TYPE type)". The content stays; only the layout and structure are redone. |
| `doc.py: X.md is newer than latex/X.tex` | You edited the Markdown after a build. Use `--reconvert` if the `.tex` has no hand edits; otherwise make the same change in the `.tex`. |
| A bold word came out as a key term but you meant stress | Use `*italic*` for stress. Only stress words like **not** and **before** become italics automatically. |
| A box or `:::` prints as plain text | The name isn't registered. `commands.py list` shows the right names, or ask Claude to add the command. |
| `\_` appears in a label like k_f | Put symbols in maths: `**Units of $k_f$:**`. |
| Box-drawing characters missing in a code block | Use ASCII in code: `|`, `+--`, `->`. |
| A heading sits alone at the bottom of a page, followed by a list | The guards only cover equations, boxes, tables, figures and code. Ask Claude to add a `\needspace` there by hand. |
| The print copy says "text naming a colour without a line style" | Those sentences say "the red curve" and mean nothing in grey. Reword them to name the style too ("the dotted red curve") in the Markdown. |
| The skill copy in the repo changed at session start | The hook pulled a newer master copy. Commit it. |
| A cover's panel lists the wrong parts, or none | The cover reads the document's top headings. A hand-written `cover_contents` list replaces them on theory covers. |
| "mind map: part … does not fit" | Even "+n more" cannot fit that part. Move cards into a sub-map (give a card children), to another part, or use `map_size: a3`. |
| "mind map: part 3 …: step 3" in the build output | Not an error: that part was shortened to fit (here: some cards show only their title). Moving cards into a sub-map gives them back their room. |
| "'→ X' … no card has that title" | The chip must name another card's title exactly as written (markup and case don't matter). |
| `doc.py bundle` says it needs pypdf | Run `scripts/setup.sh`, or `pip install pypdf`. |
| The edge tab highlights the wrong part | It needs the second LaTeX run; `build.py` does that. On a hand compile, compile twice. |

---

## 17. Improving the skill

All changes go to the master repo `nurmdabd/engineering-docs`: a new type, a new command, a style change. Then run `python3 tests/run_tests.py --build` and push. Working repos pick the change up at their next session, and their copy is committed there. Just tell Claude what you'd like changed, for example "past-paper answers should also have a diagram section". Claude edits the type's guide or the preamble, updates the tests and syncs both repos.

- `CHANGELOG.md` records what changed and when.
- `ROADMAP.md` keeps the ideas saved for later (series pages and QR codes for distribution, Bangla back-of-cover pages, a cover gallery).
