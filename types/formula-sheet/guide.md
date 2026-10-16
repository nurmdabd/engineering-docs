# Document type: formula-sheet

A dense, printable sheet of every formula of a course, grouped by topic: one table per topic with the columns Title, Equation, Notation and Ref. (reference). Built from the user's COM I formula sheet (`1-formula-sheet.md`).

Everything in `SKILL.md` and `references/authoring.md` applies; this guide adds what is specific to formula sheets.

## Settings

`type: formula-sheet` sets 11pt text (Notation and Ref. columns 8pt) and 0.4in side margins (the converter sizes the columns from the margin; `margin_x` changes it). Add the cover fields in the front matter for its cover, which shows each topic with its formula count.

**Added at build time** (the body `.tex` is not changed):
- **Key formulas:** a row whose Title is bold gets a star, and all of them are gathered on a *Key formulas* page at the end, each linking back to its row. Bold only the formulas that are truly key (about one in five).
- **Symbol index:** every symbol the Notation column defines (`$k_f$ = frequency sensitivity`, one per line) is listed in order of first use with a link to that row. A definition written wholly inside `$...$` is left out, so write the symbol in maths and the meaning in words.
- **Edge tabs:** one per topic on the right page edge (`edge_tabs: false` turns them off).
- **The back of the cover** explains how to read a row, using the sheet's own first row.

## Structure

```markdown
Conventions: the units and symbol conventions used throughout (for example "$k_f$ in rad/s per volt").

**Columns:** Title · Equation · Notation · Ref. (reference).

## 1. Angle modulation (L24)

| Title | Equation | Notation | Ref. |
|------|----------------|----------------|------|
| Peak deviation (FM) | $\Delta f = \dfrac{k_f m_p}{2\pi}$ | Δf = peak frequency deviation (Hz)<br>$m_p = \lvert m(t)\rvert_{max}$ | [L24 · §1.2.2](theory.md#carsons-rule) |
| **Carson's rule** | $B_T \approx 2(\Delta f + B)$ | $B_T$ = transmission bandwidth | [L24 · §1.2.2](theory.md#carsons-rule) |
```

- **No `#` heading:** the title is in the front matter, so the topics (`##`) are the numbered sections.
- **One `##` section per topic,** with its lectures in brackets, each holding one table.
- **A short sheet** (one or two tables) may leave out the contents page with `toc: false`.
- **Title:** a short name. Bold the few formulas a student must know by heart (`**Carson's rule**`).
- **Equation:** the formula in `$…$`. Use `\dfrac` for fractions; tall maths is padded automatically. Two related forms may share a cell, separated by `,\;`.
- **Notation (required):** every symbol that is new in this row, one per line, separated by `<br>`, as `symbol = meaning (unit)`. A symbol already defined in an earlier row of the same table is not repeated.
- **Ref. (optional; the header is `Ref.`, `Reference` also works):** the lecture and the section where the formula is derived, as a link into the theory notes (`[L24 · §1.2.2](theory.md#anchor)`). In the PDF it becomes a link into the theory PDF, so the PDFs must sit in one folder (`references/pdf-links.md`). When there is no theory PDF to link to, write it as plain text (`L24 · §24.1`).
- **Completeness:** every formula of the notes, boxed or not.

## Writing the content

- **Source:** the course's theory notes. Every formula is copied exactly as it is derived there, with the same symbols and conventions; never rederive or "simplify" a formula on the sheet.
- **Completeness:** every boxed or numbered result of the notes appears on the sheet, in the order of the notes.
- **One formula per row.** A condition of validity goes in Notation (`valid for $\lvert k_f a(t)\rvert \ll 1$`).
- **No prose** beyond the conventions line and the columns line at the top.

## After converting

The converter sizes the columns from their content, making the Equation column the flexible one. A table headed exactly `Title | Equation | Notation | Ref.` gets column font sizes: Title and Equation at the body size, 11 pt (the sheet is set in 11 pt: the text above the tables, the header and the footer), so the formulas read easily; Notation and Ref. at 8 pt, since they are only looked up, which also keeps those two columns narrow. The user's own COM sheet keeps Notation and Reference narrow (hand-edited smaller), so only widen Notation when its entries wrap badly on the rendered page. Look at the rendered pages (SKILL.md, Step 5): Notation and Reference should be just wide enough; if they wrap badly, adjust the `x{…}` widths in the `.tex` by hand. Once the `.tex` is hand-edited, never re-run the converter over it.

## Review checklist

- [ ] Every row has a Notation cell defining each new symbol with its unit.
- [ ] Every Reference link points to an existing heading of the theory notes (the linter checks links into the same file only; open the theory PDF to check these).
- [ ] No table runs off the page; no formula touches the row rules.
