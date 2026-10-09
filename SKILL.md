---
name: latex-engineering-pdf
description: Converts finalized Engineering Markdown (lecture notes, theory files, lab reports, study sheets, question banks, day-0X write-ups) into LaTeX in Nur Mohammad's house style AND compiles it to a finished, interactive PDF right here with XeLaTeX — bundled preamble, main.tex template, study-notes cover page, callout boxes, question/solution links, and a Markdown→LaTeX draft converter. No local MikTeX step needed. Use whenever the user asks to turn Markdown/notes into a PDF, a LaTeX/.tex file, "my format", "my LaTeX style", a report section, or an exam-ready PDF — even if they never say LaTeX. Also use when asked how a Markdown element (table, code block, equation, figure, list, repo reference) should render in this style. Content is preserved exactly — structural/formatting-only conversion (grammar fixes only).
---

# Engineering Markdown → House-Style LaTeX → PDF (self-contained)

This skill does the whole job in the session:

1. **Set up** XeLaTeX once (`scripts/setup.sh`).
2. **Convert** the Markdown to LaTeX **body content** by the rules in Sections 0–13 (draft with `scripts/md2tex.py`, then review by hand).
3. **Check** the structure (`scripts/check_structure.py`).
4. **Build** the PDF with the house preamble and `main.tex` template (`scripts/build.py`).
5. **Look** at the rendered pages and fix what's wrong.
6. **Deliver** the PDF plus the compile-ready source folder.

Bundled files (paths relative to this skill's folder):

| File | What it is |
|---|---|
| `template/main-tex-preamble.tex` | The **live** house preamble. It is the user's own preamble with two portable changes: the header text comes from `\ReportHeader`, and the emoji font falls back to DejaVu Sans when Segoe UI Emoji is missing. |
| `template/main.tex` | The user's main-file layout: title lines, TOC with the `toc` anchor, "Created by …", `\newpage`, then `\include` of each body file. A cover page is included automatically if `cover-page-preamble.tex` and `cover-page-main.tex` are present in the build. It also passes hyperref's `destlabel` option (Section 13). |
| `template/cover-page-*.tex` | The **study-notes cover page** (course code band, document title, subtitle, note, optional "Inside" box, author and date). It is filled by `build.py --cover …`. The user's other covers are for other purposes; pass `--cover-dir` to use one of those instead. |
| `scripts/md2tex.py` + `scripts/house.lua` | A pandoc-based **draft converter** that applies the mechanical rules: headings, labels, table tiers, equations, figures, callouts, question/solution boxes, `eqnote` and Unicode. Its output still gets the Step 3 review. |
| `scripts/setup.sh` | Installs XeLaTeX and every package the preamble loads (Debian/Ubuntu). Re-running it is safe. |
| `scripts/check_structure.py` | A fast check for unbalanced braces and `\begin`/`\end` pairs, with no compile. |
| `scripts/build.py` | Fills the template, compiles with latexmk/XeLaTeX, and summarizes errors, undefined references, **missing glyphs** and wide overfull lines. |
| `examples/example-body.tex` | A body file that uses every rule below. It compiles clean, so copy its patterns. |

Never edit the bundled preamble to suit one document. If the user changes their live preamble, they send the new file and it replaces `template/main-tex-preamble.tex`. Keep the two portable changes above, and the **Study-notes additions** block at its end (callout boxes, markers, `\golink`, PDF navigation), when you do that.

## Workflow

### Step 1: Setup (once per session)
```bash
bash <skill>/scripts/setup.sh
```

### Step 2: Convert (draft)
Write one `.tex` body file per logical document part, for example one per lecture or day, or one per sheet. Each file is raw body content that starts at its outermost heading. Save it in a `latex/` folder beside the Markdown so image paths resolve.

For anything longer than a page, draft it with the converter instead of typing it out:
```bash
python3 <skill>/scripts/md2tex.py NOTES.md -o latex/NOTES.tex [--class extarticle|extreport] [--fontsize 12pt]
```
The converter prints the suggested `--title` lines: the YAML `title`/`subtitle`, or else the first `#` heading, which it then removes from the body.

### Step 3: Review the draft, then check its structure
The converter cannot make the judgement calls. Read the draft against Sections 0–13 and fix by hand:
- **`\keyterm` vs plain:** the converter turns every bold span into `\keyterm`, except short all-lowercase stress words like "not" or "before", which become `\emph`.
- **Captions** that came out generic, for example "Summary" or a repeated section title.
- **Ambiguous callouts:** any blockquote whose box type is unclear.
- **Columns** that the page render (Step 5) shows wrapping badly.

Never re-run the converter over a body file you have hand-edited; it overwrites the file. Then run:
```bash
python3 <skill>/scripts/check_structure.py body.tex
```

### Step 4: Build
```bash
python3 <skill>/scripts/build.py body1.tex [body2.tex ...] --out path/Name.pdf \
    --title "First title line:" --title "Second title line" \
    --header "Short running header" \
    [--class extarticle|extreport] [--fontsize 12pt] [--author "Nur Mohammad"] \
    [--figures extra/image/dir ...] [--no-toc] \
    [--cover --course-code "COM I" --course-name "Communication Engineering I" \
     --cover-title "Formula Sheet" --cover-subtitle "Lectures 24--38" --cover-note "Term test preparation" \
     --cover-contents "Item" --cover-contents "Item" --date "October 2026"]
```

- **Cover page:** add `--cover` for study notes and exam material. The cover fields are raw LaTeX, so write `--` for an en-dash and `\&` for `&`. Use `--cover-dir DIR` to use another cover pair instead.
- **Several documents:** when one project produces several PDFs, write a small `build-all.sh` next to the bodies that calls `build.py` once per document. Commit it so the PDFs can be rebuilt later.

- **Defaults** match the user's latest main file: `extarticle`, `12pt`, author "Nur Mohammad". The title lines are rendered as `{\LARGE{\keyterm{…}}}`.
- **Choosing the class:** use `--class extreport` when the source has chapter-level `#` headings, as in a multi-day report. That project used `extreport` at `14pt`, so pass `--fontsize 14pt`.
- **Image search path:** each body file's folder and its `figures/` subfolder are added automatically, so `\includegraphics{name.png}` works with a bare filename. Use `--figures` for images stored anywhere else.
- **Build folder:** the build writes `<Name>_build/` next to the PDF. It holds `main.tex`, the preamble and the body files, and it compiles as-is on the user's MikTeX.

### Step 5: Look at the result
The build log summary must say **"Log clean"**, or every item it lists must be understood. Then render the pages and view them:
```bash
pdftoppm -r 60 -png Name.pdf /scratch/pg
```
Check the following, and fix the body file and rebuild if anything is off:
- Tables are not running off the page.
- No equation overflows the margin.
- Figures are sized sensibly. Use `width=0.8\linewidth` by default and narrower for tall images.
- Nothing is blank where a glyph should be.

### Step 6: Deliver
Give the user:
- the PDF;
- the body `.tex` files;
- the `_build/` folder (or a zip of it), so they can recompile locally.

If the work is in a git repo, commit the body `.tex` files and the PDF. Add `*_build/` (and LaTeX aux files) to `.gitignore` unless the user wants the build folder kept.

## Active custom commands

| Command / environment | Use for |
|---|---|
| `x{<w>}`, `y{<w>}`, `z{<w>}` | fixed-width table columns (left/center/right aligned) |
| `C`, `L`, `R` | flexible-width table columns (center/left/right aligned) |
| plain `l`, `c`, `r` | table columns for short, non-wrapping content (used with `\cc{}`) |
| `\cc{Text}`, `\yy{Text}{width}`, `\CC{Text}` | table header cells (plain/fixed/flexible column) |
| `\keyterm{text}` | an inline technical term, tool/framework name, acronym expansion, or a "Term = definition" pattern (including at the start of a sentence/item) |
| `\verb\|token\|` | a short literal identifier in running prose/lists (never nested inside another command's argument) |
| `\graphicspath{{figures/}}` | already set (build.py adds the body folders); bare filenames work in `\includegraphics` |
| custom `json` language | `language=json` in `lstlisting`, for JSON content specifically |
| `repocard{title}` | a tool/repo/external-resource reference block (Section 9) |
| `{\emojifont …}` | symbols Latin Modern lacks (★) in running text (Section 10) |
| `notebox`, `examplebox`, `exambox`, `warnbox`, `selfcheckbox` `[title]` | callouts (Section 11) |
| `questionbox{title}{solution label}`, `solutionbox{title}{question label}` | linked practice questions and solutions (Section 11) |
| `\exammark`, `\pinmark`, `\warnmark`, `\okmark`, `\nomark` | inline markers that replace 🎯 📌 ⚠ ✔ ✘ (Section 10) |
| `\golink{label}{text}` | a small clickable chip that jumps to a label |
| `eqnote{<equation>}{<note>}` | an equation with a short side note, in limited cases (Section 12) |
| `mainquestion` | previous-year exam questions only (Section 12) |

The preamble also defines these, which stay **unmapped**:
- `\codechip{}`, `\seqtt{}`
- `\hlblack{}`, `\grayhl{}`, `\blackhl{}`
- `\note{}`, `\normalpath{}`
- the `myCPP` listing style

They exist and compile. Don't use them unless the user asks, or confirms a mapping when asked under Section 0.

Everything else is not customized beyond this table: headings, paragraphs, lists, other code languages, equations and figures. This table lists commands unique to this house style, not the full universe of usable LaTeX. Standard LaTeX, and whatever the loaded packages provide, is always available too: `\href`, `\cref`, `\texttt`, `\textit`, `\vspace`, `\multicolumn`, `equation`, `align`, `itemize`, `\checkmark`, `physics` macros, `circuitikz`, and so on. Use them as needed.

## Output rules for the body file (non-negotiable)

- The body file contains raw LaTeX **body content only**. It has no `\documentclass`, no preamble and no Markdown. The build script supplies the preamble and `main.tex`.
- Preserve all technical content exactly. Do not summarize, remove, add or rewrite explanations; only fix grammar.
- Do not redefine any command or environment the preamble already provides.
- Do not invent a *custom* command or environment that isn't in the Active custom commands table or `template/main-tex-preamble.tex`. Standard LaTeX is always fine. If a natural mapping seems to need a custom command that doesn't exist, fall back to plain LaTeX (see Section 0).
- UTF-8 is allowed in running text **only for characters the main font (Latin Modern) has**. See Section 10. The build reports any glyph that went missing, and that report must be empty.

## 0. When to ask instead of guessing

These default fallbacks are safe to apply without asking:
- **A standalone assignment or question prompt:** a plain paragraph with `\textbf{Question:}` as the label.
- **A callout** (blockquote, Note, Warning, Exam tip, Example): the matching box from Section 11. Only when no box fits, use a `\textbf{Label:}` paragraph.
- **An equation followed by a "where …" explanation:** a plain `equation` with a plain `itemize` list underneath (see Section 7).
- **Introductory or front-matter text** that describes the whole document series rather than fitting under one heading: preserve it as a LaTeX `%` comment block near the top, with a short note explaining why it isn't its own section. Don't force it into a heading and don't drop it.
- **A Markdown "Contents" list:** drop it. The template already builds a live table of contents.

Still **stop and ask**, quoting the exact snippet and naming 2–3 concrete options, when:
- A construct doesn't fit any mapping in this file *or* the fallbacks above.
- You're unsure whether content wants the `repocard` treatment, a callout box, a plain paragraph, or some other boxed or special formatting. That includes the unmapped preamble commands listed above.
- Something the user says about their live preamble contradicts `template/main-tex-preamble.tex`, such as a command that supposedly doesn't exist, different styling, or an extra environment. Confirm which is current before relying on it.
- Getting it wrong has a real cost: it would misrepresent technical content, or duplicate or omit a cross-reference.

Convert everything unambiguous first, then ask about the rest. Don't block the whole output on one uncertain piece.

## 1. Section mapping

| Markdown | `extarticle` (default) | `extreport` |
|---|---|---|
| `# Title` | `\section{Title}` | `\chapter{Title}` |
| `## Title` | `\subsection{Title}` | `\section{Title}` |
| `### Title` | `\subsubsection{Title}` | `\subsection{Title}` |
| `#### Title` | `\textbf{Title:}` run-in label | `\subsubsection{Title}` |

- Use the Markdown heading text exactly as written. Strip a trailing colon if there is one, because the preamble's `\addcolon` already adds a colon to every section title. Never apply manual colour or numbering; title formatting is entirely the preamble's job.
- Strip manual numbering from the heading text (`## 3 Quantization` → `\subsection{Quantization}`), because LaTeX numbers the headings itself.
- Leave the file's single **outermost** heading unlabeled, typically. Every other heading gets a label, per Section 8.
- Don't go deeper than the table above.

## 2. Paragraph and inline text formatting

### `\textbf{...}`
Use it for a run-in phrase that works as a mini sub-heading, labelling or introducing a paragraph, list or block of explanation that follows. The preamble colours `\textbf` green, so don't use it for casual mid-sentence emphasis.

- **Short field labels always take a colon:** `\textbf{Objective:}`, `\textbf{Goal:}`, `\textbf{Result:}`, `\textbf{Observation:}`, `\textbf{Command:}`, `\textbf{Output:}` / `\textbf{Output Snippet:}`, `\textbf{Purpose:}`, `\textbf{Question:}`, `\textbf{Solution:}`, `\textbf{Proof:}`.
- **A longer descriptive lead-in** names a construct or topic before explaining it at length. It takes whatever punctuation reads naturally (colon, em-dash or period), not a colon by default.
- **The test is function, not punctuation:** does this phrase open or label a block of explanation? If yes, use `\textbf{}`. If it is a term referenced within a single sentence or compact bullet, even as the first word, use `\keyterm{}`.

### `\keyterm{...}`
Apply it to technical terms, tool or framework names, key concepts and acronym expansions, on first meaningful mention. That includes the leading word of a sentence or bullet when it names a term within that single line, for example `\keyterm{FSM} = states + inputs + outputs + transitions.`

- **Judge by content, not syntax.** Markdown's `*italic*` and `**bold**` markers are an inconsistent signal in hand-written study notes, so don't wrap every emphasized span. Ask whether the phrase would make sense as a glossary entry. If it is rhetorical emphasis instead, leave it plain.
- **Re-apply it per context.** It's fine to use `\keyterm{}` again when a term resurfaces in a new subsection or a later paragraph.
- **Wrap a full "Term (ACRONYM)" phrase in one call,** for example `\keyterm{Pulse Code Modulation (PCM)}`.

### `` \verb|token| ``
Use it only for short literal identifiers in running prose or lists: module and signal names, filenames, exact code tokens.

- **Not for multi-word concepts;** those get `\keyterm`.
- **`\verb` cannot appear inside the argument of another command.** That includes `\textbf{}`, `\keyterm{}`, `\caption{}` and every table cell. This is a hard LaTeX constraint, not a style preference.
- **Inside another command, use `\texttt{}`** with special characters escaped by hand: `\&`, `\$`, `\#`, `\_`, `\%`, `\{`, `\}`, `\textasciicircum{}`, `\textasciitilde{}`.

### Hard line breaks
Two-space Markdown line breaks inside a paragraph become separate sentences or paragraphs. Don't use `\\` in running text.

## 3. Lists

```latex
\begin{itemize}
    \item ...
\end{itemize}
```
```latex
\begin{enumerate}
    \item ...
\end{enumerate}
```

- **Nesting:** preserve it exactly. The preamble sets the bullets (• / ➢ / ∘).
- **Lettered items:** for `(a) (b) (c)` items, use `\begin{enumerate}[label=(\alph*)]` (from enumitem).

## 4. Tables

Pick a column tier per column, based on its content. Don't force one tier across a whole table.

| Content | Column type | Header macro |
|---|---|---|
| Genuinely short *and* uniform (every entry comparably short: IDs, single words, flags, numbers) | plain `l` / `c` / `r` | `\cc{Text}` (always centered, regardless of body alignment) |
| Varies in length, or has one or a few longer entries mixed with short ones | `x{w}` / `y{w}` / `z{w}` | `\yy{Text}{w}` (**text first, width second**) |
| Long descriptive text that fills the remaining space | `X` / `C` / `L` / `R` (`tabularx`-based) | `\CC{Text}` |

**Sizing principle:** pick the narrowest column (type and width) that doesn't truncate any entry, favouring wrapping over stretching.

- **Why plain columns go wrong:** a plain `l`/`c`/`r` column sizes itself to fit its single longest entry on one line, with *no* wrapping. One long entry in an otherwise short column forces the whole column wide.
- **The fix:** in that case use a fixed-width `x`/`y`/`z` column, sized just wide enough that the longest entry wraps to two lines.

```latex
% Avoid: plain `l` forces the column wide to fit the single longest entry
\begin{tabularx}{\textwidth}{|l|x{3.2cm}|L|}

% Prefer: a fixed width lets the long entry wrap, keeps the column narrow
\begin{tabularx}{\textwidth}{|y{2.4cm}|x{3.2cm}|L|}
```

Reserve the flexible `C`/`L`/`R` tier for the column or columns that genuinely hold long prose. That column absorbs the space the others don't need. Avoid all-flexible tables (`|C|C|C|`) unless every column truly needs equal flex.

**Maths in table cells:** maths in cells is fine (`$\Delta v^2/12$`). Use `\dfrac` sparingly, because it makes rows tall.

**Row banding:** a preamble hook applies it **automatically** to every `tabularx`, starting from row 2. **Do not** add `\rowcolor` to body rows. The header row is the one exception: give it an explicit `\rowcolor{gray!15}`.

**No float wrapper:** don't use `\begin{table}`. `ltablex` lets `tabularx` handle captions, labels and page breaks directly. Put each cell on its own line.

```latex
\begin{tabularx}{\textwidth}{|c|y{2.8cm}|L|}
    \hline
    \rowcolor{gray!15}
    \cc{ID}            &
    \yy{Module}{2.8cm} &
    \CC{Description}                                                                                                    \\ \hline

    M01                &
    Control Unit       &
    Manages instruction sequencing, state transitions, and coordination between datapath components during execution.   \\ \hline
\caption{<caption>}
\label{tab:<snake_case_label>}
\end{tabularx}
```

Preserve every row and cell exactly. Generate a meaningful caption and label if the Markdown doesn't provide them.

## 5. Code blocks

```latex
\begin{lstlisting}[language=<language>, caption={<caption>}]
...
\end{lstlisting}
```

**Styling:** the preamble's `\lstset` handles line numbers, the frame and the colours. Don't add manual style overrides. Detect the language from the content, and preserve indentation, comments and blank lines exactly. Always give a block a `caption`.

What to use for each kind of block:
- **A command the user runs:** `language=bash`, or the true language.
- **Raw terminal output or text dumps:** omit `language` entirely, but still give a `caption`.
- **Directory trees, flow diagrams, hierarchy diagrams:** `lstlisting` with **no `language`** but **with a `caption`**. Don't use bare `verbatim`.
  - **Characters in listings:** the listing font is Latin Modern Mono, so box-drawing glyphs (`│└├`) and arrows like `▼` drop silently. Use the ASCII equivalents (`|`, `+--`, `->`, `v`). The build's missing-glyph report catches any you miss.
- **JSON:** `language=json`.
- **Verilog/SystemVerilog, Python, C++, MATLAB:** `language=Verilog` / `Python` / `C++` / `Matlab`.
- **No `\label` by default.** Only add an `lst:` label when the prose cross-references the block.
- **Command/Output idiom:** when the Markdown shows a command and its result as *separate* pieces, put `\textbf{Command:}` above the command listing and `\textbf{Output Snippet:}` (or `\textbf{Output:}`) above the output listing. If the Markdown already shows them combined as one transcript, keep a single `lstlisting`.

## 6. Figures

```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\linewidth]{filename.png}
    \caption{OpenLane container launch.}
    \label{fig:openlane_container_launch}
\end{figure}
```

- **Images that exist:** use a real `\includegraphics`. The build adds the body's folder and `figures/` to the search path, so a bare filename works. For a Markdown path like `../figures/part-01/x.png`, either pass `--figures` for that folder, or use the relative path from the body file's folder.
- **Images that don't exist yet:** leave the `\includegraphics` line commented, with a `% TODO: insert graphic` note.
- **Width:** start at `0.8\linewidth`. Use `0.5–0.6` for tall or portrait images and up to `\linewidth` for wide block diagrams.
- **Caption and label:** use the Markdown alt text or the nearby heading as the caption, and generate a `fig:` label from it.
- **After the figure:** preserve any "Purpose:"-style explanation as body text with `\textbf{Purpose:}`, per Section 2.

## 7. Mathematical expressions

- **Inline maths** (`$...$`) stays unchanged. Fix only broken spacing, such as `$ x $` → `$x$`.
- **Single display equations** use plain `equation` with a label:
  ```latex
  \begin{equation}
      f = \frac{1}{T}
      \label{eq:<snake_case_label>}
  \end{equation}
  ```
- **A multi-line derivation** (consecutive `$$ … $$` lines, or `=` chains) uses `align`. Label only the lines that are referenced or that are final results, and put `\nonumber` on the rest:
  ```latex
  \begin{align}
      \overline{q^2} &= \frac{1}{\Delta v}\int_{-\Delta v/2}^{\Delta v/2} q^2\,dq \nonumber\\
                     &= \frac{\Delta v^2}{12}
      \label{eq:quantization_noise_power}
  \end{align}
  ```
- **Boxed final results** (shown in bold or with a box in the Markdown) use `\boxed{…}` inside the equation (mathtools).
- **A "where …" explanation** directly after an equation becomes a plain `itemize` list:
  ```latex
  \begin{equation}
      f = \frac{1}{T}
      \label{eq:<snake_case_label>}
  \end{equation}
  where:
  \begin{itemize}
      \item $f$ is frequency in Hz
      \item $T$ is the period in seconds
  \end{itemize}
  ```
- **Text inside maths** uses `\text{}`, for example `\text{SQNR}_{\text{dB}}`. Units go outside the maths or inside `\text{ }`.

## 8. Cross-references

Auto-generate a meaningful snake_case `\label{}` for every labelable element, derived from the heading or caption text (lowercased, spaces → underscores):

| Element | Prefix | Example |
|---|---|---|
| Section | `sec:` | `\label{sec:day01_rtl_analysis}` |
| Figure | `fig:` | `\label{fig:openlane_container}` |
| Table | `tab:` | `\label{tab:verification_results}` |
| Code listing | `lst:` | `\label{lst:top_module_verilog}` (only if actually cross-referenced; see Section 5) |
| Equation | `eq:` | `\label{eq:clock_frequency}` |

- **Placement:** put the `\label{}` on the line immediately after the heading, with no blank line in between.
- **Unique labels:** labels must be unique **across all body files built together**. When building several files into one PDF, prefix the labels per file, for example `sec:l24_carson_rule`.
- **Using `\cref`:** when the prose refers back to a labelled element in the same build ("as derived above", "see the Carson's rule section"), use `\cref{…}`. Leave references to content outside the build as plain prose.
- **Markdown anchor links:** `[text](#anchor)` links to an in-build heading become `\hyperref[sec:…]{text}`, or `\cref{}` when the text is just a reference. Links to other files become plain prose, or `\href` if a URL exists.

## 9. Tool and repo reference blocks

`repocard{title}` wraps a tool, repo or external-resource reference with its own descriptive block (for example "OpenLane repo" or "PDK source"), instead of a plain paragraph:

```latex
\begin{repocard}{<title>}
...
\end{repocard}
```

For a block listing **multiple** resources, use `\textbf{Label:}` followed by `\href{<url>}{\textit{<display text>}}`, with `\vspace{2mm}` between entries:

```latex
\begin{repocard}{Project Repository References}

\textbf{Public Repository:}
\href{https://github.com/user/repo}{\textit{repo-name/}}

\vspace{2mm}

\textbf{Week-04 Assignment Directory:}
\href{https://github.com/user/repo/tree/master/some/path}{\textit{some\_path/}}

\end{repocard}
```

Escape special characters in the **display text** only, never in the URL.

## 10. Unicode in running text (verified against the build)

The main font is Latin Modern, because the preamble sets no `\setmainfont`, so this applies on the user's MikTeX too. These characters **render**: Δ µ → ← × ± √ ∞ Σ — ° ½ ² and accented Latin letters.

These characters **vanish silently** and must be converted:

| Raw | Write instead |
|---|---|
| Greek letters other than Δ and µ (β ω π θ φ λ τ …) | inline maths: `$\beta$`, `$\omega$` … |
| ≈ ≤ ≥ ≠ ⊕ ⇒ ↔ ∝ ∫ | `$\approx$`, `$\le$`, `$\ge$`, `$\neq$`, `$\oplus$`, `$\Rightarrow$`, `$\leftrightarrow$`, `$\propto$`, `$\int$` |
| ✔ ✅ / ✘ ❌ / ⚠ | `\okmark` / `\nomark` / `\warnmark` (coloured symbols) |
| 🎯 / 📌 | `\exammark` / `\pinmark` (small EXAM / NOTE chips). At the start of a blockquote, these markers choose the box instead (Section 11). |
| ★ ⭐ | `{\emojifont ★}` |
| ¹²³⁴⁻ superscripts, ₁₂ subscripts, ⅓, ①②③ | `$^{-6}$`, `$_{12}$`, `$\tfrac13$`, `\textcircled{\scriptsize 1}` |
| m̂ (combining hat) | `$\hat{m}$` |
| Other pictographic emoji (💡 📝 ➕) | drop the emoji and keep the meaning in words |

In headings and captions, wrap maths replacements as `\texorpdfstring{$\beta$}{β}` so the PDF bookmarks stay readable. The converter does this everywhere.

The build's **"Missing glyphs"** line lists anything that slipped through. It must be empty before delivery.

## 11. Callout boxes and practice questions

These boxes make study material easy to scan. They share the `repocard` look (a rounded box with a coloured title bar) and break across pages. The optional `[title]` replaces the default title.

| Source | Box | Default title |
|---|---|---|
| `> ⚠ …` (a class-note correction, a common mistake, a caution) | `warnbox` | Watch Out |
| `> 🎯 …` (exam focus, what to write in the exam) | `exambox` | Exam Focus |
| `> 📌 …`, or a plain `> …` blockquote (a note or notice) | `notebox` | Note |
| A paragraph that starts with `**Example …:**` or `**Worked example.**` | `examplebox` | the bold lead-in |
| The body of a heading containing "self-check" | `selfcheckbox` | Self-check |

**Box titles:** if the callout starts with a bold lead-in label (`> ⚠ **Sign note:** …`), that label, without its colon, becomes the box title. Otherwise the box gets its default title. Remove the marker emoji, because the box colour carries its meaning.

**Practice questions:**
- **Question format:** a heading that is just an ID (`#### N1`, `#### S12`, `#### L3`) becomes `questionbox`, and `#### Solution N1` becomes `solutionbox`.
- **Labels:** put `\phantomsection\label{q:n1}` or `\label{sol:n1}` on the line just before the box. The title bar carries the link to the partner box ("Solution →" / "← Back to question"). Drop the Markdown's own `[→ Solution](#…)` and `[← Back](#…)` links, since the title bar replaces them.
```latex
\phantomsection\label{q:n1}
\begin{questionbox}{N1}{sol:n1}
Broadcast FM uses peak deviation ...
\end{questionbox}
...
\phantomsection\label{sol:n1}
\begin{solutionbox}{Solution N1}{q:n1}
$\beta = \Delta f/B = 75/15 = 5$ ...
\end{solutionbox}
```

**Boxes and tables:** don't put a `tabularx` inside a callout box when the box might break across pages; leave that callout unboxed. A short table inside a solution box is fine.

## 12. `mainquestion` and `eqnote`: where they may be used

**`mainquestion`** starts a new page and frames one question as a grey block. It was built for solving **previous years' exam questions**.

Use it only when **all** of these hold:
- The source identifies the question as a real past-exam question, with its year or exam name and question number. For example, "Term Test 2024, Q3(b)" or "Final 2023 Q2".
- The question gets a full worked solution, roughly half a page or more.

Then lay it out as follows:
```latex
\begin{mainquestion}
\textbf{Term Test 2024, Q3(b):} Draw the Armstrong modulator ... [5 marks]
\end{mainquestion}
\textbf{Solution:}
...
```
Put the question text in the box and the solution below it as normal body text, using headings, equations, figures and callouts as usual.

**Never use `mainquestion`** for:
- practice questions, question banks or self-checks (use `questionbox`/`solutionbox`; a page break per question wastes pages);
- short answers;
- questions inside theory notes;
- invented example questions.

If it is unclear whether a question is a real past-exam question, ask.

**`eqnote{<equation>}{<note>}`** puts the equation in the left 65% and a small side note in the right 32%. It works well, but only in a narrow case.

Use it when **all** of these hold:
- A single display equation, typically a **final or boxed result**, is immediately followed by one short comment about it: a condition, units, "also write …", or a trap.
- The comment is at most about 3 short points (separate points with `\\`).
- The equation fits in 65% of the line.

```latex
\begin{eqnote}{
\begin{equation}
    \boxed{B_{PM} = 2(\Delta f + B)}
    \label{eq:d1_bandwidth_of_pm_1}
\end{equation}
}{\textit{Write also:} for FM, $\Delta f = k_f m_p/2\pi$ \\ PM bandwidth grows with message frequency}
\end{eqnote}
```

**Don't use `eqnote`** for:
- running derivations, multi-line `align` blocks or wide equations;
- "where …" variable lists (Section 7 keeps those as an `itemize`);
- notes longer than a few lines, since the note text is `\scriptsize`.

In this repo's derivation sheet, the converter applies it automatically when a display equation is followed by a paragraph that starts with *Write also*.

## 13. Interactivity and links across PDFs

The PDFs are meant to be clicked through. The template and preamble already provide:
- the bookmarks panel, which opens on launch and is numbered;
- the **TOC** button in every page header;
- a clickable table of contents and `\cref` references;
- question ↔ solution links in the box title bars.

**Linking between PDFs of one set:** hyperref's `destlabel` option is passed by `main.tex`, so every `\label` is also a named destination in the PDF. That makes another PDF in the **same folder** linkable:
```latex
\href{3-derivation-sheet.pdf\#sec:d1_bandwidth_of_pm}{D1}
```
- **Link targets:** a Markdown link `other.md#anchor` becomes `\href{other.pdf\#sec:<anchor with - → _>}{…}`. Section labels are derived the same way (`sec:` + the Markdown anchor, with `-` → `_`), so both ends agree.
- **Check after building:** read each PDF's annotations with pypdf and confirm every internal and cross-file destination exists.
- **Tell the user:** the PDFs must stay in one folder for these links to work.

## Quick self-check before building

1. **Body files only:** no `\documentclass`, `\usepackage` or commentary.
2. **Content preserved:** nothing summarized, trimmed or added; only grammar fixed.
3. **Labels:**
   - Every heading below the outermost one has a `\label{}` on the next line, with no blank line.
   - Every table, figure and numbered equation is labelled.
   - Labels are unique across the build.
   - Code listings are unlabelled unless cross-referenced.
4. **Inline commands:**
   - `\textbf{}` is used for lead-in labels only.
   - `\keyterm{}` is applied by the glossary test.
   - `\verb` is never nested inside another command's argument; use `\texttt{}` with escaping there.
5. **Tables:**
   - Columns are the narrowest that don't truncate any entry.
   - Only long-prose columns are flexible.
   - The header row has `\rowcolor{gray!15}`; body rows have none.
6. **Diagrams as text:** trees and flow diagrams use a captioned `lstlisting` with no `language`, in ASCII.
7. **References:** `\cref{}` for in-build references; plain prose for anything outside the build.
8. **`repocard`:** used only for tool and repo reference blocks.
9. **Boxes:** callouts use the Section 11 boxes; `mainquestion` and `eqnote` are used only where Section 12 allows.
10. **Unicode:** Section 10 is applied, so no raw Greek or relation symbols appear in running text.
11. **Ambiguities:** anything unmapped is flagged with a specific question.
12. **Checks:** `check_structure.py` is clean, the build log says "Log clean" (or its warnings are explained), the rendered pages have been viewed, and the links were verified (Section 13).
