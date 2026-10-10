# Writing the Markdown (input spec)

How to write Markdown that the converter turns into the house style without hand fixes. Follow it when Claude writes content (SKILL.md, mode 2), and check any Markdown with the linter before converting:

```bash
python3 <skill>/scripts/lint_md.py NOTES.md
```

Errors must be fixed. Each warning is a place where the PDF would differ from what the writer probably meant. The LaTeX each construct becomes is in `references/latex-rules.md`; this file covers only the Markdown side.

## Front matter

An optional YAML block at the very top. `md2tex.py` applies `type` and `lang` itself and writes every build setting to `NAME.build.json` next to the `.tex`, which `build.py` reads. A flag given on the command line always wins.

```yaml
---
title: "COM I --- Formula Sheet (Lectures 24--38)"
subtitle: "Every formula you need, grouped by topic"
type: project-report
lang: bn
cover: true
course_code: "COM I"
course_name: "Communication Engineering I"
cover_title: "Formula Sheet"
cover_subtitle: "Lectures 24--38"
cover_note: "Term test preparation"
cover_contents:
  - "Every formula, grouped by topic"
date: "October 2026"
---
```

| Key | Meaning |
|---|---|
| `title`, `subtitle` | The title lines on page 1 (without them, the first `#` heading is the title) |
| `type` | A folder in `types/`; sets that type's defaults |
| `lang` | `en` (default) or `bn` for Bangla; `bn` adds `--bangla` to both scripts |
| `header` | The running header, left (default: the titles) |
| `header_right` | Text on the right of the header, before the TOC button |
| `author`, `date` | Cover and title page |
| `cover` | `true` adds the study-notes cover page |
| `course_code`, `course_name`, `cover_title`, `cover_subtitle`, `cover_note`, `cover_contents` | Cover fields; `cover_contents` is a list |
| `exam`, `year` | Records for past papers (which exam, which session); they don't change the PDF, so put the session in `subtitle` and `header_right` too |
| `toc` | `false` leaves out the table of contents (a one-table sheet) |
| `label_prefix` | A prefix for every label of this file, such as `d03_`; needed when several files are built into one PDF (a report's days) |
| `first_number` | The number of the first chapter (or section), when a file is built on its own: `first_number: 3` for Day 3 of a report, `first_number: 24` for Lecture 24 taken out of longer notes |
| `preamble` | This document's own commands: a `.tex` file next to it, with a registry `.yaml` of the same name (`references/commands.md`) |

Values are raw LaTeX on the cover and title: write `--` for an en-dash, `---` for an em-dash and `\&` for `&`. Quote any value that contains `:`. Unknown keys are reported by the linter.

## Headings

| Markdown | Becomes |
|---|---|
| `#` | the title (first one, if there is no front-matter title), else `\section`; with `extreport`, every `#` is a `\chapter` |
| `##`, `###` | the next levels down |
| `####` | a bold run-in label in `extarticle`, `\subsubsection` in `extreport` |
| `#####` and deeper | not supported |

- **No colon at the end.** The colon is added automatically, and skipped for a title that ends in `?`, `!`, `.` or `।`. Write `## Results`, not `## Results:`.
- **Numbers are fine** (`## 3 Quantization`); they are removed because LaTeX numbers headings itself.
- **A file that starts at `##`** (an excerpt of longer notes, with no `#` heading) has its headings moved up one level, so `##` becomes the first numbered level.
- **Don't skip levels** (`##` straight to `####`), except for question headings.
- **Page breaks:** a heading or a lone bold label (`**Derivation:**` on its own line) is kept on the same page as the equation, box, table, figure or code block right after it. Nothing to write for it.
- **Special headings:** a heading named `Contents` is dropped with its list (the PDF has its own table of contents). A heading containing `self-check` puts its section in a self-check box. `#### N1` and `#### Solution N1` are questions (below).

## Inline text

- **Bold lead-in label:** a bold phrase ending in `:` (or `.`, `?`, `।`) at the start of a paragraph, such as `**Objective:**`, stays bold as a label. Labels carry their own colon.
- **Bold term:** any other bold phrase becomes a key term (`\keyterm`), lowercase ones included (**granular noise**). Only stress words in bold (**not**, **before**, **the same**) become italics. Bold only terms a reader might look up; use `*italic*` for stress.
- **Code:** `` `data_out` `` for identifiers, file names and exact tokens.
- **Side remark:** `[in bits when the log is base 2]{.note}` prints a small parenthetical note.
- **Line breaks:** a single line break inside a paragraph does nothing. Leave a blank line to start a new paragraph.

## Lists

- `-` bullets and `1.` numbered lists, nested by indenting.
- **Sub-parts** written as `(a)`, `(ii)` or `(3)` at the start of a line each start a new paragraph, even without a blank line between them. They are not made into a lettered list.

## Tables

- Pipe tables with a header row. Every row needs the same number of cells.
- `<br>` inside a cell starts a new line in that cell.
- **Caption:** a line `Table: Caption text` right after the table, after a blank line. Without it, the caption is the section title.
- Inline maths in cells is fine; tall maths (`\frac`, `\int`, matrices) is padded automatically.

## Equations

- **Display:** `$$ … $$`, on its own line or across several lines. Each `$$ … $$` becomes one numbered equation.
- **Multi-line derivations:** write one `$$ … $$` block with `\\` between lines and `&` before each `=`; it becomes one numbered equation with the lines aligned (`aligned`). Without `&`, the lines are centred (`gathered`). Two `$$` blocks back to back are two separate equations, and the linter warns about them.
- **Boxed result:** `$$\boxed{…}$$`.
- **"where" list:** a paragraph `where:` followed by a bullet list right after the equation.
- **Side note:** a paragraph starting with `*Write also:*` right after a display equation becomes the equation's side note (`eqnote`).
- **Inline:** `$…$`, with no spaces just inside the dollars.
- **Numbers with units** in running text: join them with `~` (`9.995~MHz`) or write them in maths (`$9.995~\text{MHz}$`) so they never split across a line.
- **Symbols in bold labels and box titles** go in maths: `**Units of $k_f$:**`, not `**Units of k_f:**` (that prints `k\_f`).

## Code blocks

- Fenced with ```` ``` ````. Give the language for code (```` ```bash ````, `python`, `Verilog`, `json`); leave it out for terminal output and text diagrams.
- **Caption:** ```` ```{.bash caption="Run synthesis"} ````, or ```` ```{caption="Directory tree"} ```` for a block without a language. The caption is Markdown (`run_synthesis` and `$\Delta f$` come out right). Without one, the caption is "Listing".
- **Trees and diagrams:** ASCII only (`|`, `+--`, `->`, `v`). Box-drawing characters and arrows are missing from the listing font.

## Figures

- An image alone in its paragraph: `![Caption text](figures/name.png)`. The alt text is the caption; keep it a short sentence.
- Paths are relative to the Markdown file; keep images in a `figures/` folder beside it.
- An image that doesn't exist yet is fine: it becomes a commented-out TODO.
- Explain a figure in the paragraph after it, starting with `**Purpose:**` if it helps.

## Callouts

| Markdown | Box |
|---|---|
| `> ⚠ …` | warning (Watch Out) |
| `> 🎯 …` | exam focus |
| `> 📌 …`, or a plain `> …` | note |
| a paragraph starting `**Example 2:**` or `**Worked example.**` (Bangla: `**উদাহরণ …**`) | example box |

- **Box title:** a bold label right after the marker becomes the title: `> ⚠ **Sign note:** …` gives a box titled "Sign note". The text after the label then opens the box, so start it with a capital letter.
- **One paragraph:** an example box takes only its own paragraph. Keep an example to one paragraph, or continue it as normal text after the box.
- **No tables inside callouts** that may cross a page break; leave those unboxed.
- Other emoji are dropped; say the meaning in words.

## Questions and solutions

```markdown
#### N1

Broadcast FM uses Δf = 75 kHz and B = 15 kHz. Find β. [→ Solution](#solution-n1)

#### Solution N1

β = Δf/B = 5. [← Back](#n1)
```

- **IDs** are one or two capital letters and a number, optionally a lowercase letter: `N1`, `S12`, `L3`, `Q4a`.
- Every question needs its `#### Solution …` and the other way round; the boxes link to each other.
- The `[→ Solution]` and `[← Back]` links are optional; the box title bars replace them.
- A past paper's questions are not written this way; see `types/past-paper/guide.md`.

## Links

- **In the same file:** `[text](#anchor)`, with the anchor as GitHub makes it (`#lecture-24--pm-bandwidth`) or as pandoc makes it. Both reach the heading in the PDF.
- **Another document of the same set:** `[text](other.md#anchor)` becomes a link into `other.pdf`. The PDFs must sit in one folder (`references/pdf-links.md`).
- **Web:** `[text](https://…)`.

## Symbols and Unicode

- Greek letters and relation symbols (β ≈ ≤ ⇒ …), superscript and subscript digits (10⁻⁶, x₁), and ✅ ❌ ✔ ✘ ⚠ 🎯 📌 ★ are converted automatically (`references/latex-rules.md`, Section 10). Writing `$\beta$` is just as good.
- Other emoji are dropped.
- Inside code blocks nothing is converted, so keep code ASCII.

## Bangla

Set `lang: bn`. Technical terms, maths, numbers, figure paths and the callout markers stay in English; sentences end with `।`. The rest is in `references/bangla.md`.

## Registered commands

Any registered command can be written directly: a box as `::: {.repocard title="OpenLane repo"}` … `:::`, an inline command as `[text]{.note}`. `scripts/commands.py list` shows every one with its syntax; `references/commands.md` explains the rules. A box written this way may hold several paragraphs.

A single real past-exam question inside other material goes in `::: mainquestion` … `:::` (`references/latex-rules.md`, Section 12); a whole past paper uses the `past-paper` type.
