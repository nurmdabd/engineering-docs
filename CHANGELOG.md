# Changelog

## October 2026: covers, print layout, packs, mind maps

- **Margins:** 0.5in left and right for every document by default; a type may set its own (formula sheets
  0.4in) and `margin_x` sets one document's. The converter sizes table columns from the margin.
- **Covers:** a front cover per type in one family (theory notes, exam notes, formula sheet, question bank,
  project report, mind map; the past-paper cover is unchanged), each showing facts counted from the document.
  A back-of-the-cover page per type (how to use, revision plan, how to read a row, the paper at a glance, how to
  practise) and a back cover in its own style. `accent` gives each subject its colour. With a cover, the
  title is no longer repeated above the contents.
- **Print copy:** laid out for double-sided printing (page 2 is the back of the cover; the back cover is the
  back of the last sheet); `print_layout: booklet` pads to a multiple of 4.
- **Packs:** `doc.py bundle pack.yaml` combines finished PDFs into one, with a pack cover, an "In this pack"
  page, every part's links and bookmarks kept, and links between parts made internal.
- **Mind maps:** the `mind-map` type draws a `::: {.mindmap}` list as a one-page TikZ map, A4 (screen) or A3
  (print), with parts in story order, starred key cards, detail lines and "used again in" chips.
- **Formula sheets:** a Key formulas page (bold rows, starred in the sheet) and a Symbol index, both linked.
- **Edge tabs:** a clickable tab per part on the page edge for theory notes, exam notes and formula sheets.
- **Docs:** `references/front-matter-keys.md` lists every setting (generated, drift-tested);
  `references/covers-and-print.md` (Section 15); the user guide has an "I want to…" table and sections on
  covers, printing and packs.
- **Fixes:** the EXAM and NOTE markers read as words in PDF bookmarks.
