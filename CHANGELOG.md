# Changelog

## October 2026: mind-map pages

- **Fitting order:** with room for a second column, a part that is too tall splits before its cards lose their
  formulas (gaps, grey lines, two columns, title-only cards, "+n more"); without room, the same minus the
  split. Grey lines come back after a split wherever they fit.
- **Main map over several pages:** more parts than a page holds (six) continue on the next page, spread evenly,
  with "page n of m" and a link to the next page. Before, seven or more parts stopped the build with a Python
  error. Part colours repeat after the eighth part.
- **Page order:** every part's continuation comes first after the main map, then the sub-maps.
- **Sub-maps beside their cards:** where a page has space left over right of a card's column, the card's
  sub-map sits there, level with it and joined to its ▸ button by a line, if it fits in one column without
  title-only cards or "+n more".

## October 2026: covers, print layout, packs, mind maps

- **Margins:** 0.5in left and right for every document by default; a type may set its own (formula sheets
  0.4in) and `margin_x` sets one document's. The converter sizes table columns from the margin.
- **Covers:** a front cover per type in one family (theory notes, exam notes, formula sheet, question bank,
  project report, mind map; the past-paper cover is unchanged), each showing facts counted from the document.
  A back-of-the-cover page per type (how to use, revision plan, how to read a row, the paper at a glance, how to
  practise) and a back cover in its own style, in the print copy (`back_cover: true` adds it on screen). `accent` gives each subject its colour. With a cover, the
  title is no longer repeated above the contents.
- **Print copy:** laid out for double-sided printing (page 2 is the back of the cover; the back cover is the
  back of the last sheet); `print_layout: booklet` pads to a multiple of 4.
- **Packs:** `doc.py bundle pack.yaml` combines finished PDFs into one, with a pack cover, an "In this pack"
  page, every part's links and bookmarks kept, and links between parts made internal.
- **Mind maps:** the `mind-map` type turns a nested `::: {.mindmap}` list into a map you click through, A4
  (screen) or A3 (print), the same structure on both: a course heading over numbered parts; cards with their
  formula, ★ and a button strip (i: the definition; ▸n: the card's sub-map); sub-maps that extend a card; an
  outline table with every definition (cards coloured, details grey). The build measures every card in LaTeX
  and fits a column that is too tall in six steps (gaps, grey lines, title-only cards, two columns, again,
  "+n more", a solid card in the part colour), splitting only when no other part pays for it.
- **Formula sheets:** a Key formulas page (bold rows, starred in the sheet) and a Symbol index, both linked.
- **Edge tabs:** a clickable tab per part on the page edge for theory notes, exam notes and formula sheets;
  the whole chip is the link; light grey chips, the current part in its colour.
- **Docs:** `references/front-matter-keys.md` lists every setting (generated, drift-tested);
  `references/covers-and-print.md` (Section 15); the user guide has an "I want to…" table and sections on
  covers, printing and packs.
- **Fixes:** the EXAM and NOTE markers read as words in PDF bookmarks; the top margin is 0.83in as the
  earlier builds had it in effect (the header height used to be dropped after the layout was set).
