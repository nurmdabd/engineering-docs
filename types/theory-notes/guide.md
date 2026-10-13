# Document type: theory-notes

Lecture or theory notes written like a teacher explaining at the board to one student before a test: connected prose, every formula motivated, every figure explained. Built from the user's COM I "Complete Theory" (`COM_Complete_Theory_L24-38.md`) and the style guides used to write it.

Everything in `SKILL.md` and `references/authoring.md` applies; this guide adds what is specific to theory notes.

## Settings

```yaml
---
title: "COM --- Communication Engineering I:"
subtitle: "Complete Theory (Lectures 24--38)"
type: theory-notes
header: "COM I --- Complete Theory (L24--38)"
cover: true
course_code: "COM I"
course_name: "Communication Engineering I"
cover_title: "Complete Theory"
cover_subtitle: "Lectures 24--38"
cover_note: "Term test preparation"
accent: 005F73                    # the subject's colour, the same on every document of the course
prerequisites:                    # "Before you start" on the back of the cover
  - "Fourier transform and its main properties"
back_blurb: "The theory of Lectures 24--38, taught like a lesson."
---
```

The type uses the house defaults (`extarticle`, 12pt, 0.5in margins). Its cover lists the parts with their lecture ranges and whether they hold worked examples and self-checks (read from the `#` part and `## Lecture NN` headings, so keep those names); the back of the cover explains the layout and boxes; the pages carry edge tabs per part (`references/covers-and-print.md`). A Bangla version is the same file translated, with `lang: bn` (see Bangla version below).

## Structure

```markdown
# Part 1 — Frequency modulation (L24–26)

A short paragraph (3–5 sentences): the big story of this part and how it continues from the previous one.

## Lecture 24 — PM bandwidth, FM generation, FM demodulation

> 📌 **Where we are.** What we have built so far, in plain words.
>
> **Today's question.** The problem this lecture answers, and why we need it.
>
> **Plan.** The steps of the lecture, in order.

### 24.1 Bandwidth of PM

One to three sentences of bridge prose before any formula: why this topic comes next.
...

### 24.5 Summary: what we learned

### Lecture 24 — self-check

1. A question? **Answer:** ...
```

- **Heading levels:** `#` part, `##` lecture, `###` numbered section (`### 24.1 …`). Avoid `####`.
- **Self-check:** each lecture ends with `### Lecture NN — self-check` and a numbered list of questions with answers. The word "self-check" puts it in a self-check box.
- **Numbers in headings** (`24.1`) are written in the Markdown; the PDF numbers sections itself and drops them.

## Writing the content

Use this when Claude writes or rewrites notes.

**Sources first:** the user's lecture transcriptions, class notes, errata and textbook references. Keep every formula, number, derivation step, worked example, table, correction and exam tip from the source; reorder within a lecture only if the story flows better. Never change a number or a formula silently: if the source looks wrong, keep it and tell the user.

**The lesson voice:** plain, short sentences ("we", "you", "let's"), as for a reader whose first language is not English. No filler, no hype, no chains of em-dashes. Vary the openings; don't start every section with "In this section we will".

**What every lecture has:**
1. **Lecture opener:** the 📌 box above (Where we are / Today's question / Plan), all in one blockquote.
2. **Topic openers:** before any formula, table or list in a `###` section, 1–3 sentences on why this topic comes next and what question it answers.
3. **Explanation inside topics:** before a derivation, the idea in words ("the trick is…"); between steps, why we take each step; after a boxed result, what it means physically and how to use it. Add intuition, analogies and "a common confusion is…" where they help. Every added sentence must help understanding.
4. **Figures:** every figure is explained in the paragraph right after it, starting with `**Reading the figure.**`. Look at the image first and describe what is actually drawn: axes, blocks, line styles, panels (a)/(b), what to notice first, what it shows, how it connects to the formula just derived (typically 4–8 sentences). Name each curve or region by line style and colour together ("the dashed orange curve"), so the paragraph still fits the black-and-white print copy (`references/authoring.md`, Figures).
5. **Wrap-up:** a short paragraph or `### NN.k Summary` before the self-check: what we learned and how it leads into the next lecture.

**Boxes and markers:**
- `> ⚠ **…**` for a correction of the class notes or a common mistake.
- `> 🎯 …` for what to write in the exam.
- `**Worked example.**` or `**Example — X.**` starts an example box; keep the whole example in that one paragraph (and the list right after it).

**Length:** depth over volume. A rewrite of terse notes into this style is typically about twice as long.

## Bangla version

The Bangla file is a translation of the English file, not a new text. Write it the way a Bangladeshi engineering teacher explains at the board ("তুমি" form), natural Bangla, not word for word.

- **Technical terms stay in English** (bandwidth, carrier, modulation index, sampling, block names). Bangla suffixes attach with a hyphen: "carrier-এর", "FM-এ".
- **Maths is copied byte for byte:** every `$…$` and `$$…$$` identical to the English file; no number changes.
- **Same structure:** headings at the same levels and numbering (`Part N`, `Lecture NN`, `### 24.1` stay), the same figures with the same paths (captions may be translated), tables with the same rows and columns, the same ⚠ 🎯 📌 markers, and `### Lecture NN — self-check` unchanged (the word "self-check" is what makes the box).
- **Fixed phrases:** `**Reading the figure.**` → `**চিত্রের ব্যাখ্যা।**`; the opener box → `**আমরা কোথায় আছি।**`, `**আজকের প্রশ্ন।**`, `**পরিকল্পনা।**`; `**Worked example.**` → `**সমাধানকৃত উদাহরণ।**`; `**Example — X.**` → `**উদাহরণ — X।**`; `**Step 1 — …**` → `**ধাপ ১ — …।**`.
- **Sentences end with "।".** Avoid em-dashes or hyphen runs between two Bangla words.
- **Check mechanically** after translating: the counts of `$$` blocks, images, tables, markers, headings and numbered items must match the English file (`references/bangla.md`).

## Review checklist

For notes Claude wrote (mode 2). When converting finished notes, nothing is added to meet this list.


- [ ] Every lecture has its 📌 opener, topic openers, a wrap-up and a self-check with answers.
- [ ] Every figure has a `**Reading the figure.**` paragraph that matches the image.
- [ ] No formula, number or example from the source was lost or changed.
- [ ] The linter reports no errors.
