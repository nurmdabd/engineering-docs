# Mind map

A one-page picture of a whole course: its parts in the order the course tells them, each part's key ideas as
cards with their formula, and chips that show where an idea is used again. Pages are landscape: **A4** for the
screen (the default) or **A3** for a printed wall or desk copy (`map_size: a3`). Anything after the map
(compare-and-contrast tables, notes) follows on normal landscape pages.

## Writing the map

The map is a list inside one `::: {.mindmap}` block. `scripts/mindmap.py` lays it out; you never place a box by
hand.

```markdown
::: {.mindmap}
# COM I: the whole course on one page          <- optional title above the map

## Analog FM | L24--27                         <- a part; "| ..." is its sub-line (lecture range)
- **Carson's rule** ★: $B_T \approx 2(\Delta f + B)$    <- a card: bold title, ★ if often asked, key formula
  - NBFM $\beta \ll 1$, WBFM $\beta \gg 1$      <- a detail line (shown on A3, or with map_detail: true)
  - → TDM                                       <- "used again in": a chip that jumps to the card titled TDM
- **[Demodulation](COM_Complete_Theory.md#fm-demodulation)**: limiter, then discriminator
:::
```

- **Parts** (`##`) go left to right in story order, joined by arrows. Five parts fit A4 well; up to seven work
  on A3.
- **Cards** (`- **Title**: ...`): half go above the part, the rest below, the first card nearest the spine. Keep
  each to one idea and one formula: the card is about 4.5 cm wide on A4. Three cards per side fit A4, four or
  five A3; the build stops and says so when a part has too many.
- **★** marks what exams ask most. Use it for about one card in three, or it stops meaning anything.
- **Detail lines** are the second line of memory: a condition, a number, the name of a variant. A4 hides them
  so the map stays readable on screen; A3 shows them. `map_detail: true` or `false` overrides that.
- **→ chips** name another card's title exactly (case and markup do not matter). They are the links between
  topics; a chip that names no card stops the build.
- **Links:** a card or part title that is a Markdown link (to another `.md` of the set, with its anchor)
  becomes a link to that section of the other PDF (Section 13); keep the PDFs in one folder.

## Front matter

```yaml
type: mind-map
map_size: a4            # a4 (screen) or a3 (print)
cover: true             # the landscape mind-map cover
course_code: "COM I"
course_name: "Communication Engineering I"
cover_title: "How the whole course fits together"
cover_subtitle: "Lectures 24--38"
```

There is no table of contents (the map is the overview) and no back-of-the-cover page; the print copy keeps a
blank page 2 so the map starts on a right-hand page.

## Review checklist (mode 2)

- Every part of the course is on the map, in the order it is taught.
- Every card has a formula or a one-line fact; nothing is a paragraph.
- The ★ cards match what past papers ask.
- Each → chip points at a real later use (a block diagram that reuses it, a formula that needs it).
- Build both sizes once and look at them: nothing overlaps, no card wraps to more than three lines on A4.
