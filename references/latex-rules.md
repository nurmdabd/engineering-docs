# LaTeX rules (Sections 1–12)

The detailed conversion rules. SKILL.md has the workflow, the output rules and Section 0 (when to ask instead of guessing).

## Active custom commands

The full list, with the Markdown that produces each one, is the registry: `scripts/commands.py list --type T` (`references/commands.md`). The table below explains the core ones.

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
| `questionblock`, `\theory`, `\answer`, `\keyword`, `\notes`, `\answersummary`, `\derivation` | past-paper solutions only; defined by `types/past-paper/preamble.tex` |

The preamble also defines these, which stay **unmapped**:
- `\codechip{}`, `\seqtt{}`
- `\hlblack{}`, `\grayhl{}`, `\blackhl{}`
- `\note{}`, `\normalpath{}`
- the `myCPP` listing style

They exist and compile. Don't use them unless the user asks, or confirms a mapping when asked under Section 0 of SKILL.md.

Everything else is not customized beyond this table: headings, paragraphs, lists, other code languages, equations and figures. This table lists commands unique to this house style, not the full universe of usable LaTeX. Standard LaTeX, and whatever the loaded packages provide, is always available too: `\href`, `\cref`, `\texttt`, `\textit`, `\vspace`, `\multicolumn`, `equation`, `align`, `itemize`, `\checkmark`, `physics` macros, `circuitikz`, and so on. Use them as needed.

## 1. Section mapping

| Markdown | `extarticle` (default) | `extreport` |
|---|---|---|
| `# Title` | `\section{Title}` | `\chapter{Title}` |
| `## Title` | `\subsection{Title}` | `\section{Title}` |
| `### Title` | `\subsubsection{Title}` | `\subsection{Title}` |
| `#### Title` | `\textbf{Title:}` run-in label | `\subsubsection{Title}` |

- Use the Markdown heading text exactly as written. Strip a trailing colon if there is one, because the preamble's `\addcolon` already adds a colon to every section title. Never apply manual colour or numbering; title formatting is entirely the preamble's job.
- **The automatic colon** is skipped when the title already ends in `?`, `!`, `.`, `:` or the Bangla danda `।`, so "Why modulate digital data?" never prints as "…?:". Chapters (`extreport` `#`) and `####` run-in labels follow the same idea: the converter writes `\textbf{Title:}` for a run-in label and drops a colon the Markdown already had.
- **When writing content** (Markdown or LaTeX), never end a heading with a colon: `## Results`, not `## Results:`. A heading may end with `?` when it is a real question. A bold lead-in label in body text is different: it is not a heading, so it always carries its own colon (`**Objective:**`, Section 2).
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

**Table hygiene** (verified on rendered pages; the converter does all of this):
- **Tall maths in a cell** (`\dfrac`, `\frac`, `\int`, `\sum`, `\left…\right`, matrices, `\sqrt`, `\overline`, `\boxed`): wrap the cell as `\tallcell{…}`. It pads the cell 3pt above and below, so the formula never touches the row rules. `\tallcell` only works in paragraph-type columns (`x`/`y`/`z`/`C`/`L`/`R`), so a column that holds tall maths never uses plain `l`/`c`/`r`. Don't use `cellspace` or `makecell` for this: the first breaks wrapping in `x{}` columns, the second breaks matrices.
- **The flexible column** is the **maths-heavy** one, if a column is mostly maths, because inline maths can't wrap the way text can. Otherwise it is the column with the longest prose. When the flexible column holds maths, text columns may wrap to 3 lines, capped at 4.4 cm.
- **Minimum width:** no fixed column is narrower than its longest single inline formula.
- **Repeated header:** put `\endhead` right after the header row, so the header repeats when a table continues on the next page.
- **Caption row:** put `\rowcolor{white}` on the line before `\caption{…}`, so the caption row doesn't pick up the banding. Don't use `\hiderowcolors` for this; it breaks the banding of the whole table.
- **Heading with a table:** a heading directly followed by a table (or a figure) gets `\needspace{10\baselineskip}` before it, so the heading never sits alone at a page bottom.
- **Page-break guards:** any other heading directly followed by an equation, a box, a table, a figure or a listing gets `\needspace{7\baselineskip}`, and a lone bold label (`\textbf{Derivation:}` on its own line) followed by one of those gets `\needspace{5\baselineskip}`. Before running text or a list nothing is added, since those break anywhere. `md2tex.py --no-guards` leaves them all out.
- **One item per line:** in a cell listing several items (symbols, steps), separate them with `<br>` in the Markdown, or `\newline` in LaTeX.

**Dense reference sheets** (formula sheets, many-column tables):
- **Font and margins:** use `--fontsize 11pt` and `--margin-x 0.4in` in `build.py`. Pass the matching `--textwidth 18.9` (cm) to `md2tex.py` so it sizes columns for the wider text block.
- **Formula sheet layout:** `Title | Equation | Notation | Reference`.
  - **Notation** is required: define every new symbol in the row, one per line.
  - **Reference** is optional: give the lecture, plus a link to the section of the theory PDF where the formula is derived.

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

**A whole past paper** (every question of an exam, solved) uses the `past-paper` type instead: the paper's questions go in `mainquestion` as a list of sub-parts with their marks, and each sub-part's solution is a `questionblock` (`types/past-paper/guide.md`). The layout below is for a single past-exam question inside other material.

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
