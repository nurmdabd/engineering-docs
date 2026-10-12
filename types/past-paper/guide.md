# Document type: past-paper

Full solutions of a previous year's exam paper. Each main question starts on a new page with the paper's own text in a grey box (`mainquestion`); then every sub-part gets a solution block (`questionblock`): the question highlighted at the top, then numbered sections (Theory, Answer, Keyword Explanation, Notes and Remarks, Final Concise Answer). Built from the user's own EEE329 session 2020–21 solutions.

Everything in `SKILL.md` and `references/authoring.md` applies; this guide adds what is specific to past papers.

## Settings

Front matter is enough:

```yaml
---
title: "EEE329: Basic Communication Engineering"
subtitle: "Solution of Session 2020--21"
type: past-paper
header: "EEE329: Basic Communication Engineering"
header_right: "Solution of Session 2020--21"
exam: "EEE329 Term Final"
year: "2020--21"
course_code: "EEE329"
course_name: "Basic Communication Engineering"
cover_title: "Question Paper Solutions"
cover_subtitle: "Session 2020--21"
cover_note: "EEE329 Term Final Examination"
date: "October 2026"
paper_header:
  - "University Name"
  - "\\textbf{Department of ...}"
  - "\\textbf{B.Sc. (Engg.) ... Final Examination-2024}"
  - "Course Code: EEE 329 \\qquad Session: 2020-2021"
  - "Course Title: Basic Communication Engineering"
paper_info: ["Total Marks: 100", "Credits: 3.0", "Total Time: 3 Hours"]
paper_instruction: "[Answer any \\textbf{two} questions from each part. The figure in the right margin indicate full marks.]"
paper_parts: ["Part-A: 1-3", "Part-B: 4-6"]
paper_appendix: "latex/2020-21-term-final-paper-equations.tex"
---
```

Then `md2tex.py paper.md -o latex/paper.tex` and `build.py latex/paper.tex --out paper.pdf`. The type adds its own cover (`types/past-paper/cover-page-*.tex`): course code and name, `cover_title`, the session in a pill (`cover_subtitle`), the exam as printed on the paper (`cover_note`), a question map with each question's total marks (counted by the build from the `[Marks: …]` in each paper block), and the order every answer follows. Take the course code, name and exam from the question paper; never invent them. The print copy gets a light version of the same cover, with tints and outlines instead of solid bands. `cover: false` leaves it out.

**The question paper.** Right after the cover, before the contents, the build typesets the whole question paper so it reads like the printed one: the header lines (`paper_header`, first line larger), the marks / credits / time row (`paper_info`, three items), the instruction (`paper_instruction`), part headings (`paper_parts`, each `"Name: first-last"`), then every question with its marks in the right margin. The questions, marks and figures come from the paper blocks (`# Question N` lists), so nothing is typed twice and the paper never disagrees with the solutions. Each sub-part on the paper, label and text (its (i), (ii) items too), links to its solution; the text stays black and the label is coloured as the cue. The header's PAPER button jumps back to the current question on the paper. Material printed at the end of the paper (a list of equations, a table) goes in a `.tex` file named by `paper_appendix`, copied exactly. Copy every header line, the instruction and the parts from the question paper word for word; leave out a field the paper does not have rather than invent it. `paper: false` leaves the paper out of a document; `--no-paper` leaves it out of one build. `exam` and `year` are records only; the session shows through `subtitle` and `header_right`. The type sets `--structure past-paper` for the converter and loads `types/past-paper/preamble.tex` (the `questionblock` environment and the section commands) in the build.

## Markdown structure

````markdown
# Question 1

- **1. (a)** Find the entropy of a single-bit binary memoryless source. [Marks: 5]
- **(b)** Briefly explain the three major bands of the EM spectrum. [Marks: 6]
- **(c)** Write short notes on:
  - **(i)** Thermal Noise
  - **(ii)** Transit Time Noise [Marks: 4]

## 1(a) Entropy of a Single-Bit Binary Memoryless Source

### Theory
#### 1. What is Entropy? (Core Idea)
...

### Answer
**Given:** ...

### Keyword Explanation
#### 1. Bandwidth
...

### Notes and Remarks
...

## 1(b) Major Bands of the EM Spectrum
...

### Final Concise Answer
**(a)** ...

**(b)** ...
````

| Markdown | Becomes |
|---|---|
| `# Question N` + a list | the paper block: one item per sub-part, the bold label as the item label; the heading itself is not printed |
| `[Marks: 5]` at the end of an item | `\hfill Marks: 5` (right-aligned); `[5 marks]` also works |
| `## 1(a) Short title` | a solution block; the short title goes in the table of contents, and the full question text is taken from the paper item `1(a)` automatically |
| a `> …` blockquote right after `##` | the question text, for a part that is not in the paper list |
| `### Theory`, `### Answer`, `### Keyword Explanation`, `### Notes and Remarks`, `### Final Concise Answer`, `### Derivation / Explanation` | the numbered sections (`\theory`, `\answer`, `\keyword`, `\notes`, `\answersummary`, `\derivation`); any other `###` is a plain numbered section |
| `####` | an unnumbered sub-heading; write the numbering yourself (`#### 1. …`, `#### i. …`, `#### Step 1: …`) |
| `$$ … $$` | unnumbered display maths; lines with `&` and `\\` become `aligned` |
| `[remark]{.note}` | a small parenthetical side remark (`\note`) |
| `**(a)**` anywhere | a bold part label |

- **Part keys:** `## 1(a)`, `## 1.(a)` and `## (d)` all work; `(d)` takes the number of the question it sits under.
- **Labels in the paper list:** the first item carries the question number (`**1. (a)**`), the rest only the letter (`**(b)**`).
- **Copy the paper exactly.** The paper text is what was printed in the exam: never reword, shorten or correct it. Unclear words stay as printed. A misprint (a wrong symbol, sign or word in the paper) also stays as printed, followed by a marker that names the correction, `[should be $\sin\theta$]{.sic}`, which prints a small red *[sic: should be sin θ]* in the paper page, the question box and the solution title (black in the print copy); `[]{.sic}` prints *[sic]* alone. Then open that sub-part's solution with a `> ⚠ **Note on the paper:**` box that says what is wrong and why, and solve the corrected question.
- **Diagrams:** a block diagram or waveform is an image (`![Caption](figures/2020_2_7.png)`), named `<session>_<question>_<n>`. A diagram drawn in TikZ goes in a raw block: ```` ```{=latex} ```` … ```` ``` ````.

## Writing the solutions

Use this when Claude writes the solutions. The paper (photo, PDF or text) must come from the user; Claude never invents a question.

**Order of sections in one solution:**
1. **Theory** (optional): when the topic needs to be built up from basics before the answer makes sense. Numbered `####` sub-topics that ask and answer the natural questions in turn: "1. What is X? (Core Idea)", "2. Why does it happen?", "3. What does the formula mean?", including unit checks and practical reference numbers.
2. **Answer** (always): what a student should write in the exam, sized to the marks (roughly half a page for 4–5 marks, a page or more for 10).
3. **Keyword Explanation** (optional): numbered `####` entries for the terms the answer relies on, a few lines each.
4. **Notes and Remarks** (optional): derivations behind a formula used in the answer, conceptual points, common confusions, related results.
5. **Final Concise Answer**: once per main question, in its last solution block, one paragraph per part (`**(a)** …`) with the key result of each.

**Numerical answers:**
- **Given:** a bullet list of every quantity with symbol, value and unit, converted to base units (`f_m = 5~\text{kHz} = 5000~\text{Hz}`).
- **Relationships:** state the formulas before using them, each with a short "where" list for new symbols.
- **Steps:** `#### Step 1: …` or `#### Case 1: …` for each stage. In each: the formula, the substitution with numbers, the result with its unit, then the result again in its own `$$\boxed{…}$$`, then one sentence on what it means.
- **Arithmetic:** compute every number with a script before writing it, and show intermediate values to a sensible number of digits.
- **Assumptions:** state any assumption the question leaves open, and give the other answer too if it changes the result (for example guard bands at the ends of an FDM band).
- **Close** with `**Final Answer:**` or `**Final Summary:**` and a short list of the results.

**Theory answers:**
- Open with a one or two sentence definition, then `**Key Points:**`, the formula with its "where" list, `**Interpretation:**` and `**Practical Note:**` as the question needs.
- Answer every part the question names (a "with block diagram" question needs the diagram; "draw the curve" needs the figure).
- `**Label:**` lead-ins structure the answer; `####` sub-headings only for real sub-topics or for the parts (i), (ii) of a short-notes question.

**Accuracy:** formulas and numbers must agree with the course notes when they exist (for COM, `level-2/complete-theory/`); where a textbook convention differs from the class notes, say which one is used.

## Review checklist

- [ ] The paper block matches the exam paper word for word, with every mark.
- [ ] Every paper item has a `##` solution, and every solution's key matches a paper item (the linter checks both).
- [ ] Every numerical result was computed, not estimated, and carries its unit.
- [ ] The last solution of each question has a Final Concise Answer covering all its parts.
- [ ] Figures the question asks for are present (or marked as TODO for the user to supply).
