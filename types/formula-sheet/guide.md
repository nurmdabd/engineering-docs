# Document type: formula-sheet

A dense, printable sheet of every formula of a course, grouped by topic: one table per topic with the columns Title, Equation, Notation and Reference. Built from the user's COM I formula sheet (`1-formula-sheet.md`).

Everything in `SKILL.md` and `references/authoring.md` applies; this guide adds what is specific to formula sheets.

## Settings

`type: formula-sheet` sets 10pt text and 0.4in side margins for the build, and tells the converter the wider text block (18.9 cm) so it sizes the columns for it. Add the cover fields in the front matter if the sheet needs a cover.

## Structure

```markdown
# Formula Sheet

Conventions: the units and symbol conventions used throughout (for example "$k_f$ in rad/s per volt").

**Columns:** Title · Equation · Notation · Reference.

## 1. Angle modulation (L24)

| Title | Equation | Notation | Reference |
|------|----------------|----------------|------|
| Peak deviation (FM) | $\Delta f = \dfrac{k_f m_p}{2\pi}$ | Δf = peak frequency deviation (Hz)<br>$m_p = \lvert m(t)\rvert_{max}$ | [L24 · §1.2.2](theory.md#carsons-rule) |
| **Carson's rule** | $B_T \approx 2(\Delta f + B)$ | $B_T$ = transmission bandwidth | [L24 · §1.2.2](theory.md#carsons-rule) |
```

- **One `##` section per topic,** with its lectures in brackets, each holding one table.
- **Title:** a short name. Bold the few formulas a student must know by heart (`**Carson's rule**`).
- **Equation:** the formula in `$…$`. Use `\dfrac` for fractions; tall maths is padded automatically. Two related forms may share a cell, separated by `,\;`.
- **Notation (required):** every symbol that is new in this row, one per line, separated by `<br>`, as `symbol = meaning (unit)`. A symbol already defined in an earlier row of the same table is not repeated.
- **Reference (optional):** the lecture and the section where the formula is derived, as a link into the theory notes (`[L24 · §1.2.2](theory.md#anchor)`). In the PDF it becomes a link into the theory PDF, so the PDFs must sit in one folder (`references/pdf-links.md`).

## Writing the content

- **Source:** the course's theory notes. Every formula is copied exactly as it is derived there, with the same symbols and conventions; never rederive or "simplify" a formula on the sheet.
- **Completeness:** every boxed or numbered result of the notes appears on the sheet, in the order of the notes.
- **One formula per row.** A condition of validity goes in Notation (`valid for $\lvert k_f a(t)\rvert \ll 1$`).
- **No prose** beyond the conventions line and the columns line at the top.

## After converting

The converter sizes the columns from their content. Look at the rendered pages (SKILL.md, Step 5): Notation and Reference should be just wide enough; if they wrap badly, adjust the `x{…}` widths in the `.tex` by hand. Once the `.tex` is hand-edited, never re-run the converter over it.

## Review checklist

- [ ] Every row has a Notation cell defining each new symbol with its unit.
- [ ] Every Reference link points to an existing heading of the theory notes (the linter checks links into the same file only; open the theory PDF to check these).
- [ ] No table runs off the page; no formula touches the row rules.
