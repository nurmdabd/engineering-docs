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
- **Link targets:** a Markdown link `other.md#anchor` becomes `\href{other.pdf\#sec:<anchor with - → _>}{…}`. Section labels are derived the same way (`sec:` + the heading's id, with `-` → `_`), so both ends agree, with one catch: pandoc's id drops a heading's leading number (`## 1 MOS transistor` is `sec:mos_transistor`, GitHub's anchor is `1-mos-transistor`). A past paper's sub-part headings (`## 2(a) …`) are the exception: their labels follow the GitHub anchor (`sec:2a_elmore_delay`), so a formula sheet or mind map can link to any solution. Link to a numbered heading of another type through a heading without a leading number, or check the target.
- **Check after building:** read each PDF's annotations with pypdf and confirm every internal and cross-file destination exists.
- **Only within one folder:** a link to a PDF in another folder does not work (the link names the file only), so do not write one; the user does not want links across folders. Tell the user the PDFs of one set must stay in one folder.
- **In a pack** (`doc.py bundle`, Section 15.7) the parts' links, and the links from one part into another, are rebuilt to point at pages inside the pack, so they work wherever the pack is kept.
