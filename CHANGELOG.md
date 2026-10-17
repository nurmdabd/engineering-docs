# Changelog

## October 2026: past-paper wording

- **Fix:** the back of a past paper's cover (*the paper at a glance*) found the total time only in "Time: 3 Hours"
  and the number of questions to answer only in "Answer any two …". Papers that print "Exam Duration: 3 Hours" or
  "(Answer two of the following questions)" lost the time, the questions to answer and the minutes per sub-part.
  `coverdata.py` now reads "Duration" as well as "Time", and "Answer two of / from …" as well as "any two".

## October 2026: share copy

- **New `--share` copy** (`doc.py build … --share`, `NAME_share.pdf`), for handing a PDF to other people: printing
  and editing are locked in the PDF (it opens without a password; text can still be copied, and readers can
  highlight and comment); a small "Free shared
  copy · AUTHOR" line sits in the footer of every page but the covers; the same text is a large diagonal stamp on
  a layer that is hidden on screen and always printed; the red and blue headings are a step lighter (`#BF4040`,
  `#4560D0`) and on a layer that is never printed. Both layers start visible (Firefox can hide a layer in print
  but not show one that starts hidden) and are written with xdvipdfmx specials, not ocgx2, whose handling of a
  layer open at a page break put whole pages on the headings layer once the stamp was added.
  `template/share.tex` holds the look.
- **Share pack:** `doc.py bundle pack.yaml --share` takes each part's `_share.pdf`, stamps the pack's own pages
  too and locks the pack.
- **Fix:** a pack lost its parts' PDF layers (pypdf copies the pages but not the list of layers, and a viewer
  shows content on an unlisted layer). `bundle.py` now joins the parts' layers into the pack.
- **Fix:** a pack part without `title:` took its file name raw, so an underscore in it broke the pack cover; the
  default title now uses the screen PDF's name, escaped.
- The house headings take their colours from `headblue` and `headred` (unchanged: `blue!75!black`,
  `red!70!black`) and pass their number and title through `\headingwrap` (does nothing by default), so a copy
  can recolour them or put them on a layer in one place; the print copy sets both colours black.
- Tests: `build example-body --share` and `bundle --share` check the lock, the two layers (headings never
  printed; the stamp off on screen, on in print, on every page; neither starting hidden), that every layer mark
  closes on its own page, and the footer line.

## October 2026: print copies stay black and white

- **Fix:** a link into another PDF (a mind-map card title, a formula sheet's Reference) printed cyan in the print
  copy: hyperref's `filecolor` was not set. `print-bw.tex` now sets `filecolor`, `runcolor` and `menucolor` to
  black too, and the `core-elements` fixture (which has such a link) is built in print and checked for colour.
- **Same top margin for every type:** 0.7in top and bottom (the past-paper type's), so the headers of a
  solution, its formula sheet and its mind map sit at the same height, also inside a pack (before: 0.83in top
  for every type but past papers).
- **Fix:** on a pack cover a long course name ran under the stack of sheets; the name now wraps at 12.8 cm
  there (`\CoverNameWidth` in the cover kit, 16 cm on every other cover).
- **Fix:** hatching in a figure kept its colour in the grey print copy (a hatch takes the colour of the edge it
  was drawn with). `figures_bw` now greys the hatch colour of patches and collections, and its test checks it.

## October 2026: pack cover

- **A pack has its own cover** (`template/pack-cover.tex`) instead of the default study-notes cover: a faint fan
  of pages in the white middle (light tints, fading out at both ends, clear of the title); the parts
  as fanned sheets on the band, each with a strip in its document type's colour; a strip under the band and the
  spine split into the parts by their page counts; the parts as linked cards (type, title, pages, page count)
  in an "In this pack" panel. Its signature colour is plum (`8E3B5E`). The type of a part is read from the
  label on its cover; `type:` on a part sets it.
- **The pack's back cover** says "ABOUT THIS PACK" and lists the parts in their colours under a strip split
  like the front's (`\CoverBackLabel` and `\CoverBackExtra` in the cover kit; other types are unchanged).
- **"In this pack" page:** each part's heading now carries its type and colour, followed by its outline in two
  columns (each line linked to its page); long outlines are cut to fit the page.
- **Page count on the back cover:** the whole PDF's, blank pages and the back cover included, so it matches the
  viewer (before, a print copy left out its padding pages and the back cover). A pack's covers say the same.
- **No build line:** the back of the cover no longer ends with "Built <date> from <file>.md", and the pack's
  "In this pack" page no longer ends with its documents-and-pages line. `conventions`, when given, still shows.
- **Key formulas page:** taller rows, and a row with a fraction, root or sum gets extra height, so the formula no
  longer touches the lines above and below it.
- **Fix: links inside a pack.** pypdf dropped every link of every part when it merged them (the parts' named
  destinations were renamed so two parts could not clash, and pypdf drops a link whose name it cannot find), so
  contents pages, the question paper's sub-part links and every cross-reference did nothing; links from one part
  into another pointed nowhere. The pack now rebuilds each part's links and bookmarks after the merge, pointing
  each at its page and position in the pack. The test checks that the pack keeps every link of its parts.
- **Fix: links into a past paper.** A sub-part's question box had no label, so a link to its heading (from a
  formula sheet or mind map, `2020-21-term-final.md#2a-elmore-delay`, or "see 3(d)" inside the paper) went
  nowhere. Each box now carries `sec:<GitHub anchor>` (`sec:2a_elmore_delay`; pandoc's own id drops the leading
  number). Reconvert a past paper to get them.
 showed its raw title ("2020--21"); bookmarks and the PDF title now show real dashes.
- **Fix:** the links on the pack's cover and "In this pack" page were dropped when the pages were merged (pypdf
  drops a link whose destination the page's own file does not define), so they did nothing. They are copied
  after the parts are in, and the test checks that both pages link to every part.

## October 2026: mind-map pages

- **Fitting order:** more columns come before cards lose their formulas: on the main map a part takes up to
  three columns where there is room (gaps, grey lines, two then three columns, title-only cards, "+n more");
  without room, the same minus the columns. Grey lines come back after a split wherever they fit.
- **Title-only cards** are limited to a third of a column's cards (at least 2; `map_titles` changes the share,
  `0` turns them off) and never used on sub-map pages, where a group takes up to the page's width in columns
  (4 on A4, 5 on A3) and then continues.
- **Fix:** a part heading's sub-line ("Part 2 · L5--8") was left out when the heading was measured, so a long one
  that wrapped could push the main map off its page.
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
