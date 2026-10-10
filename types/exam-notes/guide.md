# Document type: exam-notes

The memorize-version of a `theory-notes` document: the same parts, lectures and section numbers, cut down to what earns marks. Under every heading, an *Explained in §…* link leads back to the full explanation. Built from the user's COM I Exam Notes (`COM_Exam_Notes_L24-38.md` and its Bangla version).

Everything in `SKILL.md` and `references/authoring.md` applies; this guide adds what is specific to exam notes.

## Settings

The type uses the house defaults. Front matter as for theory notes, with `type: exam-notes` (and `lang: bn` for the Bangla version).

**Links into the main PDF:** the *Explained in* links point at the theory notes' Markdown with GitHub anchors (`COM_Complete_Theory_L24-38.md#241-bandwidth-of-pm`), so they work on GitHub. In the PDF they must point at the labels of the theory PDF, which differ. Build the theory notes first, then give the converter a copy of the exam notes whose links use the theory `.tex` labels; the COM repo does this with `complete-theory/_tools/notes_links_for_pdf.py` in `latex/build-notes.sh`. The committed Markdown keeps the GitHub anchors.

## Structure

Same headings as the theory notes, in the same order, with the same numbers:

```markdown
# Part 1 — Lectures 24, 25, 26: Frequency Modulation

## Lecture 24 — PM bandwidth, FM generation, FM demodulation

*Explained in [Lecture 24](COM_Complete_Theory_L24-38.md#lecture-24--pm-bandwidth-fm-generation-fm-demodulation)*

> 📌 **Follows:** AM family, PM/FM definitions. **Answers:** how wide is PM/FM? **Order:** PM bandwidth → Carson → FM vs AM.

### 24.1 Bandwidth of PM

*Explained in [§24.1](COM_Complete_Theory_L24-38.md#241-bandwidth-of-pm)*

**Steps.**
1. ...

$$\boxed{B_{PM} \approx 2(\Delta f + B)}$$

**Draw / label** (3 panels, same time axis): ...

**Worked example.** ...

> 🎯 **Exam answer.** ...

### Lecture 24 — self-check

1. Question? (Answer.)
```

- **Front page:** a short introduction (what the notes are for), **How to use** (rewrite from memory, learn the 🎯 boxes word for word, answer the self-checks), the **pattern** of the labels and the **legend** of the markers.
- **Headings** are exactly those of the theory notes (same text and numbers), so the two files can be read side by side. In the Bangla version, they equal the headings of the Bangla theory notes.
- **Every heading** is followed by its *Explained in* line.
- **Lecture opener:** one 📌 line, **Follows:** / **Answers:** / **Order:**, instead of the theory notes' three-paragraph box.

## Writing the content

The source is the finished theory notes; exam notes add nothing new.

- **Keep only what earns marks:** definitions, formulas, derivation steps, worked examples with their numbers, diagrams with their labels, the ⚠ corrections, ready-made exam answers, and the self-checks.
- **Drop the teaching prose:** openers, analogies and long figure explanations stay in the theory notes; the *Explained in* link covers them.
- **The fixed labels:**
  - `**Def.**` the definition to write;
  - `**Steps.**` a numbered derivation or procedure, one step per line;
  - `**Draw / label**` what the diagram must show;
  - `**Worked example.**` the numbers to reproduce;
  - `> 🎯 **Exam answer.**` a sentence to learn word for word.
- **Results are boxed:** `$$\boxed{…}$$`.
- **Self-checks** with the answers in brackets: `1. Question? (Answer.)`.
- **Never change a formula or a number:** copy them byte for byte from the theory notes.
- **Keep in sync:** when the theory notes change a formula, number or heading, update the exam notes (English first, then the Bangla version).

**Bangla version:** the rules of the theory-notes Bangla version apply (`types/theory-notes/guide.md`): technical terms in English, maths byte for byte, the same figures, tables and markers, sentences ending in "।". A script comparing the two files must find the same maths, figure paths, tables, ⚠/🎯/📌 boxes and self-check items.

## Review checklist

- [ ] The headings match the theory notes one to one, and each has its *Explained in* link.
- [ ] Every formula, number and figure path equals the theory notes.
- [ ] Each lecture ends with its self-check, answers in brackets.
- [ ] The English and Bangla versions match (maths, figures, tables, markers, self-checks).
