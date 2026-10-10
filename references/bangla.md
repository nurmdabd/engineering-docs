# Bangla documents (Section 14)

Part of the engineering-docs rules; SKILL.md has the workflow, `references/latex-rules.md` the general LaTeX rules.

## 14. Bangla (বাংলা) documents

Use this for notes translated into Bangla, where technical terms stay in English.

- **Converter:** run `md2tex.py --bangla`. It wraps every run of Bangla text (outside maths and `\label`/`\ref` keys) as `\bn{…}`.
- **Build:** run `build.py --bangla`. It loads the Bangla font: Noto Serif Bengali (install `fonts-noto-core` on Linux), else **Nirmala UI**, else **Vrinda**, so the same build folder compiles on Windows MikTeX. It also wraps the Bangla parts of the title, header and cover fields, and sets `\emergencystretch` so lines never overflow.
- **Why explicit `\bn{}` wrapping:** automatic switching with `ucharclasses` breaks at group boundaries (bold labels, table headers), so Latin letters vanish. Explicit wrapping is robust.
- **Never span hyphens or dashes in a `\bn{}` run:** LaTeX writes the em-dash as `---`, and inside the Bangla font that prints literally.
- **What to keep in English while translating:**
  - all technical terms (carrier, bandwidth, quantization noise, …), plus "Lecture N" and "self-check" (the self-check box is detected by that word);
  - maths, numbers, figure paths and callout markers (⚠ 🎯 📌).
- **What translates freely:** bold lead-in labels end with "।" and are still recognised as labels. Example boxes may start with "উদাহরণ".
- **Check after translating:** compare the translation with the source mechanically. Display and inline maths must be identical, and the counts of figures, headings, table rows, callouts, numbered items and bullets must match.
- **Column widths:** table widths count only base letters, not vowel signs or hasanta. Every column is at least as wide as its longest word, because Bangla is not hyphenated.
