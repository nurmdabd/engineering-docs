# Front-matter keys

Generated from `scripts/frontmatter.py` (`python3 scripts/doc.py keys --write`); do not edit by hand.
Values are raw LaTeX: `--` is an en-dash, `\&` an ampersand; quote a value that contains `:`.

## Document

| Key | Default | What it does |
|---|---|---|
| `title` | the first # heading | First title line (on page 1 without a cover; in the PDF properties) |
| `subtitle` |  | Second title line |
| `type` | none (house defaults) | A folder in `types/`: its layout, cover and writing guide (`doc.py types`) |
| `lang` | `en` | `bn` for Bangla (technical terms stay English) |
| `header` | the first title line | Running header, left |
| `header_right` |  | Running header, right, before the TOC button |
| `author` | Nur Mohammad | Author on the cover, title page and back cover |
| `date` | today | Date on the cover and back cover (raw LaTeX, e.g. `October 2026`) |
| `toc` | `true` | `false` leaves out the table of contents |
| `margin_x` | `0.5in` (formula sheet `0.4in`) | Left and right page margins; table columns follow it |
| `label_prefix` |  | Prefix for every label (`d03_`), when several files go into one PDF |
| `first_number` |  | Number of the first chapter or section when a file is built on its own |
| `preamble` |  | This document's own commands: a `.tex` next to it with a registry `.yaml` |

## Cover

| Key | Default | What it does |
|---|---|---|
| `cover` | the type's (past paper: on) | `true` adds the type's front cover (and, by default, its back cover) |
| `course_code` |  | Large code on the cover band, e.g. `COM I` |
| `course_name` |  | Course name under the code |
| `cover_title` | the title lines | The document's name on the cover |
| `cover_subtitle` |  | The pill under the cover title, e.g. `Lectures 24--38` |
| `cover_note` | formula sheet: its counts | One italic line beside the pill |
| `cover_contents` | the parts, read from the document | A hand-written "Inside" list (theory and default covers) |
| `accent` | `005F73` (ocean) | The subject's colour on the cover, back cover and spine, as hex |
| `inside_cover` | `true` when the type has one | `false`: no page on the back of the cover |
| `back_cover` | in the print copy only | `true`: also in the screen PDF; `false`: no back cover at all |
| `back_blurb` |  | One or two sentences on the back cover about the document |
| `prerequisites` |  | List shown as "Before you start" on the back of a theory-notes cover |
| `conventions` |  | One line on the textbook and conventions, at the foot of the back-of-cover page |
| `edge_tabs` | on for theory, exam notes, formula sheets | A clickable tab per part on the page edge (screen PDF only) |

## Print

| Key | Default | What it does |
|---|---|---|
| `print_layout` | `duplex` | Print copy page order: `duplex` (even pages) or `booklet` (a multiple of 4) |

## Mind map

| Key | Default | What it does |
|---|---|---|
| `map_size` | `a4` | `a4` (screen) or `a3` (print) landscape |
| `map_detail` | on A3 only | Show the cards' detail lines |

## Past paper

| Key | Default | What it does |
|---|---|---|
| `paper` | `true` | `false` leaves out the typeset question paper |
| `paper_header` |  | List: the paper's centred header lines (raw LaTeX) |
| `paper_info` |  | List: the marks / credits / time row; also feeds the paper-at-a-glance page |
| `paper_instruction` |  | The instruction line under the header |
| `paper_parts` |  | List: `Part-A: 1-3 | [Answer any two ...]`, a part heading before its first question |
| `paper_appendix` |  | A `.tex` file printed at the end of the paper (an equation sheet) |
| `exam` |  | Record only: which exam (put it in `cover_note` to show it) |
| `year` |  | Record only: the session |
