# Document type: question-bank

Practice questions for an exam, with full solutions: numericals, short-answer questions and long or derivation questions. Each question links to its solution and back. Built from the user's COM I question bank (`2-question-bank.md`).

Everything in `SKILL.md` and `references/authoring.md` applies; this guide adds what is specific to question banks. Real questions from a previous year's paper belong in a `past-paper` document instead.

## Settings

The type uses the house defaults. A cover with a short contents list suits it:

```yaml
---
title: "COM I --- Practice Question Bank (Lectures 24--38)"
subtitle: "Numericals, short questions and long questions, with full solutions"
type: question-bank
cover: true
course_code: "COM I"
course_name: "Communication Engineering I"
cover_title: "Question Bank"
cover_contents:
  - "35 numericals"
  - "25 short questions"
  - "20 long questions"
  - "Click a question's title bar to jump to its solution"
---
```

## Structure

```markdown
# How to use

Two or three sentences: how the bank is organised and how to use it.

# Part A — Numerical problems

## A1 FM, PM and Armstrong (L24–26)

#### N1

Broadcast FM uses Δf = 75 kHz and B = 15 kHz. Find β and the transmission bandwidth. [→ Solution](#solution-n1)

# Part B — Short-answer questions

#### S1

...

# Part C — Long / derivation questions

#### L1

...

# Solutions

#### Solution N1

$\beta = \Delta f/B = 75/15 = 5$. Carson: $B_T = 2(\Delta f + B) = \mathbf{180}$ **kHz**. [← Back to N1](#n1)
```

- **IDs:** `N` numericals, `S` short answers, `L` long questions, numbered in one sequence each across the whole bank.
- **Only the parts it has:** a bank of numericals only has no Part B or C headings; give it a `header:` so the running header stays on one line.
- **Questions** sit under topic headings (`## A1 …`); **solutions** all go at the end under `# Solutions`, in the same order.
- **Links:** `[→ Solution](#solution-n1)` and `[← Back to N1](#n1)` are optional; the box title bars link both ways anyway.

## Writing the content

- **Coverage:** every topic of the notes gets questions in proportion to its exam weight; numericals cover every formula that takes numbers.
- **Questions:** one clear task each, with every value needed and its unit. Sub-parts as (a), (b), (c) separated by blank lines or written in one sentence.
- **Numerical solutions:** the formula, the substitution, the result in bold with its unit (`$\mathbf{180}$ **kHz**`), and the practical remark if there is one (`200 kHz allocated`). Compute every number with a script; never estimate.
- **Traps:** where a careless answer would be wrong, say so in the solution (`8 bits gives only 49.9 dB — a trap!`).
- **Short answers:** two to five sentences or a short list, the way the exam expects them.
- **Long answers:** the derivation step by step, with the figure if the question asks for one; it may point to the theory notes for the full story.
- **Consistency:** symbols, conventions and results match the course's theory notes and formula sheet.

## Review checklist

- [ ] Every question has its solution and every solution its question (the linter checks this).
- [ ] Every numerical result was computed and carries its unit.
- [ ] The cover contents list matches the real counts.
