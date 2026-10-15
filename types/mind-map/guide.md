# Mind map

A whole course as a map you can click through: a heading for the course, its parts in the order the course
tells them, each part's key ideas as cards with their formula, sub-maps for cards with more inside, and an
outline table with every idea's definition. Pages are landscape: **A4** for the screen (the default) or **A3**
for a printed wall or desk copy (`map_size: a3`). Both sizes have the same structure; A3 has room for more.
Anything after the map (compare-and-contrast tables, notes) follows on normal landscape pages.

## What the reader gets

- **The main map:** the course heading on top, joined to every part (numbered, with its lectures); under each
  part, its cards. A card shows its title, ★ when exams ask it often, its key formula and, in grey, the names
  of what is inside it.
- **Two buttons on every card,** in a strip on its right edge, each clickable over its whole area: **i** (top)
  opens the card's row in the outline table (definition and formula); **▸n** (bottom, only on cards with a
  sub-map) opens the sub-map with its n cards.
- **Sub-maps** extend a card, never repeat it: the heading is the card (click it to go back), its children are
  the cards below. Several sub-maps share a page, in course order. Where the page has room right of a card's
  column, its sub-map sits there instead, level with the card and joined to its ▸ button by a line.
- **The outline table:** one row per idea, every level in its own column, with *What it is*, *Key formula* and a
  ↩ map link back to the card. Cards are bold and coloured; details (grey lines on a card) are dark grey.

## Writing the map

The map is a nested list inside one `::: {.mindmap}` block. `scripts/mindmap.py` lays it out at build time; you
never place a box by hand.

```markdown
::: {.mindmap}
# COM I · Communication Engineering I | Lectures 24--38    <- the heading over every part ("| ..." is its sub-line)

## Analog FM | L24--27                                     <- a part; "| ..." is its lecture range
- **Carson's rule** ★: $B_T \approx 2(\Delta f + B)$      <- a card: bold title, ★ if often asked, key formula
  - def: Swing plus message rate: about 98% of the power. <- its definition (the table's "What it is")
  - **NBFM**: $B_T \approx 2B$                            <- a child (any depth): a detail or a card, see below
    - def: beta << 1: as wide as AM.
  - → TDM                                                 <- "used again in": a link to the card titled TDM
- **[Demodulation](COM_Complete_Theory.md#fm-demodulation)**: limiter, then discriminator
:::
```

- **Parts** (`##`) go left to right in course order. A page holds up to six (on A4 and on A3; A3 has bigger
  cards, not more columns); five fit A4 best. More parts continue the main map on the next page, spread evenly
  (7 parts: 4 + 3; 20 parts: 4 pages of 5), each page under the course heading with "page 2 of 3" and a link
  to the next. A ninth part takes the first part's colour again.
- **Cards** (`- **Title**: formula`): one idea and one formula each. The formula is scaled down if it is wider
  than the card, so keep it short; a text formula wraps.
- **Children** decide the shape. A card with 1 to 3 children, none of which has children of its own, lists them
  as one grey line (details). A card with 4 or more, or with grandchildren, gets a **sub-map**: its children
  become cards there, with their own buttons. Plain sub-items (no bold title) are details with no formula.
- **def:** lines are the outline table's definitions: one or two plain sentences. Give every card one.
- **★** marks what exams ask most, about one card in three. Star cards are the last to be shortened.
- **→ chips** name another card or item exactly (case and markup do not matter); a chip that names nothing
  stops the build.
- **Links:** a title that is a Markdown link (to another `.md` of the set, with its anchor) becomes a link to
  that section of the other PDF (Section 13).

## When a column is too tall

The build measures every card in LaTeX and fits each column, one step at a time, each step as little as
needed, and says in its output which step each part needed. More columns keep every formula on the map, so they
come before cards lose theirs:

| Step | Main map, room for more columns | Main map, no room | Sub-map pages |
|---|---|---|---|
| 1 | tighten the gaps between cards | tighten the gaps | tighten the gaps |
| 2 | hide the grey detail lines, bottom card first (they stay in the outline table) | hide the grey lines | hide the grey lines |
| 3 | two columns under the part's heading, then three; grey lines come back where they fit | title-only cards | two, three, … columns, up to the page's width (4 on A4, 5 on A3) |
| 4 | title-only cards | **+n more ▸** | **+n more ▸** |
| 5 | keep the first cards and end the column with **+n more ▸**; the rest continue on a sub-map page | | |

**Title-only cards** show a card's title alone (its formula stays in the outline table): non-★ cards only,
bottom first, and at most a third of the column's cards (at least 2): 2 of 6, 4 of 12, 5 of 15.
`map_titles` changes the share (`0.5`: half; `0`: never, so a column that does not fit always ends with
**+n more**). Sub-map pages never shorten cards: a group there takes more columns, then continues.

**Room for more columns:** on the main map each column a part takes narrows every column of the page, so a part
widens only while each column stays at least the narrowest width and no other part needs a later step because of
it; otherwise it takes the one-column steps. A main-map page with fewer parts than the fullest page keeps that
page's column width, so its parts widen for free.

**+n more** keeps as many whole cards as fit (formulas back, grey lines hidden).

If even that cannot fit, the build stops and names the part. `map_detail: false` never shows the grey lines.

## Page order

1. **The main map,** on as many pages as its parts need.
2. **Continuations** of every part that ended with **+n more**, first on the sub-map pages, in part order, so
   the main map is complete before anything deeper. A continuation that is too tall again carries on in the
   next group beside it.
3. **Sub-maps,** in course order, filling the rest of those pages.
4. **The outline table.**

**A sub-map beside its card.** A sub-map leaves the sub-map pages and sits right of its card when all of this
holds:

- the space is left over after the page is laid out: no column is narrowed for it (on the main map that means
  fewer than about five parts on the page; on a sub-map page, free slots at the end of the page, or the next
  sub-map in order extending a card of the group just before it);
- its card is in the column directly to its left (the line never crosses a column);
- it fits in one column with at most tighter gaps and hidden grey lines (never title-only cards, two columns or
  **+n more**: then it stays on a sub-map page at full size);
- it starts level with its card; only the first one in a column may start higher, as low as it fits, and
  never above the bottom of the heading over its card's column.

Several can stack in one column, in course order, and a card in one of them can take the next column the same
way. The build output names every sub-map placed beside its card.

## Front matter

```yaml
type: mind-map
map_size: a4            # a4 (screen) or a3 (print)
map_titles: 1/3         # share of a main-map column's cards that may lose their formula (0: never)
cover: true             # the landscape mind-map cover
course_code: "COM I"
course_name: "Communication Engineering I"
cover_title: "How the whole course fits together"
cover_subtitle: "Lectures 24--38"
```

There is no table of contents (the map is the overview) and no back-of-the-cover page; the print copy keeps a
blank page 2 so the map starts on a right-hand page.

## Review checklist (mode 2)

- Every part of the course is on the map, in the order it is taught; the heading names the course.
- Every card has a formula or a one-line fact, and a `def:`; nothing on a card is a paragraph.
- The ★ cards match what past papers ask.
- Each → chip points at a real later use.
- Build it and read the build output: a part that needed step 3 or more is a hint to move cards into a sub-map
  (give the card children) or to a later part. Look at the main map, one sub-map page and the table.
