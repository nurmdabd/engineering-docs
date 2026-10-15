# Covers, print copies and packs (Section 15)

Part of the engineering-docs rules; SKILL.md has the workflow. Every front-matter key named here is in
`references/front-matter-keys.md` with its default.

## 15.1 What a document with a cover contains

| Page | Screen PDF | Print copy (`--print`) |
|---|---|---|
| 1 | the type's front cover | same, light tints instead of solid bands |
| 2 | the back-of-the-cover page, if the type has one | same; a blank page if the type has none |
| 3 ... | (past paper: the question paper), contents, body | same, starting on a right-hand page |
| end | nothing (`back_cover: true` adds the back cover) | blank pages, then the back cover, so it is the back of the last sheet |

With a cover, the title is not repeated above the contents (the cover carries it). `cover: false` removes the
cover and with it the back-of-cover page and the back cover; `inside_cover: false` and `back_cover: false`
remove one of them. The back cover is for the printed copy: the screen PDF ends with the last body page unless
the front matter says `back_cover: true`.

## 15.2 The covers

All covers share `template/cover-kit.tex`: the colours, the band, the left spine, the pinned info panel, the
footer and the faint motifs. Each type draws its own front cover from those pieces:

| Type | Cover file | Motif | Info panel (read from the document) |
|---|---|---|---|
| no type, `theory-notes` | `template/cover-page-main.tex` | waves | the parts, with lecture range, lecture count, worked examples, self-check |
| `exam-notes` | `types/exam-notes/cover-page-main.tex` | diagonal cut, REVISION stamp, diagonal lines | what every section gives you |
| `formula-sheet` | `types/formula-sheet/...` | graph-paper band, dot grid | the topics with their formula counts |
| `question-bank` | `types/question-bank/...` | large ?, rings | counts per kind (N, S, L), questions per topic |
| `past-paper` | `types/past-paper/...` (own preamble too) | rings, side band | question map, how each answer is laid out |
| `project-report` | `types/project-report/...` | double frame, no bands | institution lines (course name and code), `cover_contents` lines |
| `mind-map` | `types/mind-map/...` | landscape band, node network | none |
| a pack (`doc.py bundle`) | `template/pack-cover.tex` | a stack of sheets, one per part in its type's colour | the parts as linked cards: type, title, pages |

- **Every number on a cover is counted** from the body (`scripts/coverdata.py`): parts from `\section`
  headings, lectures from `Lecture NN` subsections, formulas from table rows, questions from `questionbox`
  labels, marks and minutes from the paper. Never type a count into a cover field.
- **A hand-written `cover_contents` list wins** on the default and theory covers; the formula-sheet and
  question-bank covers always show the counted data.
- **Two colours:** `accent` is the subject's (one per subject, the same on every document of it); the type's
  signature colour (`type.json` `"cover": {"signature": ...}`) is fixed per type. Headings and boxes keep the
  house colours.
- **Leave the cover out** rather than invent a course code or name the sources don't give, and say so.
- **Your own cover:** `--cover-dir DIR` with a `cover-page-preamble.tex` and `cover-page-main.tex` uses it
  instead; the kit's fields and lists are still available to it.

## 15.3 The back of the cover

| Type | Page | Comes from |
|---|---|---|
| `theory-notes` | How to use these notes: lecture layout, the boxes, getting around, before you start | `prerequisites` |
| `exam-notes` | My revision plan: one row per lecture, days 1, 3, 7 and the exam eve, confidence | the `Lecture NN` headings |
| `formula-sheet` | Before you use the sheet: the sheet's first row, annotated; in the exam | the first table row |
| `past-paper` | The paper at a glance: time, marks, how many to answer, each sub-part's marks and minutes | `paper_info`, `paper_parts`, `[Marks: n]` |
| `question-bank` | How to practise, and a practice log with two boxes per question | the question labels |

The foot of every such page says when and from which Markdown it was built, plus `conventions` if given.
It is in English also for a Bangla document (see ROADMAP.md).

## 15.4 The back cover

`template/back-cover.tex`, for every type, in the print copy (and the screen PDF with `back_cover: true`): an accent strip on the right edge (the spine side) carrying course,
title and subtitle; faint rings; "About this document" with the title, `back_blurb` and up to three numbers
counted from the document plus the page count; course, author and date at the foot. Write `back_blurb` in
plain words: what the document is and how it teaches, one or two sentences.

## 15.5 Edge tabs

`template/edge-tabs.tex`: a tab per part (the same parts as the cover) on the right edge of every body page;
the chips are light grey so they stay out of the way while reading, except the current part's, which is wider
and in that part's colour (the colour it has on the cover); the whole chip is a link to its part (not only its number). On by default for theory notes,
exam notes and formula sheets (`edge_tabs: false` turns them off; `--edge-tabs` adds them to any build).
Never in the print copy: printers cannot print to the edge.

## 15.6 Print copy

`--print` (only when the user asks) builds `NAME_print.pdf`: `template/print-bw.tex` greys every colour, the
covers turn to light tints, and the page order above makes double-sided printing come out right.
`print_layout: booklet` pads to a multiple of 4 pages for a folded booklet. Figures: see SKILL.md Step 4.

## 15.7 Packs: several documents in one PDF

`doc.py bundle pack.yaml` (scripts/bundle.py; its docstring shows the YAML) combines finished PDFs:

- the pack's own cover (`template/pack-cover.tex`, label `STUDY PACK` or `label:`, signature colour plum
  `8E3B5E`): the parts drawn as fanned sheets on the band, each with a strip in its type's colour; under the
  band a strip, and down the spine a line, split into the parts in proportion to their pages; the parts as
  linked cards (type, title, pages, page count) pinned above the footer. A part's type is read from the label
  on its cover (`type:` on the part sets it; a part without a cover is grey, "DOCUMENT"). In print the parts
  take different greys;
- an "In this pack" page: every part's heading (linked to its cover) with its outline in two columns, each
  line linked to its page. The outline is the part's top-level bookmarks, or the level below when there are
  fewer than four (a solution's sub-parts). Too many lines for one page: the longest lists are cut ("and n
  more in the bookmarks"); if it still overflows, the page lists the parts only;
- the parts; one back cover (print pack; a screen pack too with `back_cover: true`);
- each part keeps its layout, cover, links and bookmarks; its own back cover is left out;
- links from one part into another (`file.pdf#label`) become links inside the pack, so the folder rule of
  Section 13 no longer applies to them;
- `--print` uses the parts' `NAME_print.pdf`, starts every part on a right-hand page and ends on a full sheet.

Build every part first, then the pack. Rebuild the pack after any part changes.

## 15.8 Checking

- Look at page 1, page 2, the first body page and the last page of every build (Step 5).
- Edge tabs: each chip is a link over its whole area (a link annotation the size of the chip); click two of them.
- A print copy: the page count is even (a multiple of 4 for a booklet) and the back cover is last.
- A pack: open the "In this pack" links and two links that cross between parts.
