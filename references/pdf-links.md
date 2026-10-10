# Links between PDFs (Section 13)

Part of the engineering-docs rules; SKILL.md has the workflow.

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
