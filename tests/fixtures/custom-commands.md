---
title: "Custom Commands: Test Notes"
preamble: custom-commands-preamble.tex
---

## Registered boxes from Markdown

::: {.repocard title="OpenLane & PDK repos"}
**Public Repository:** [openlane/](https://github.com/The-OpenROAD-Project/OpenLane)
:::

::: {.notebox title="A note over two paragraphs"}
The first paragraph of the note.

The second paragraph, still inside the same box.
:::

::: examplebox
An example box with its default title.
:::

## Registered spans

The [carrier]{.keyterm} sits at $f_c$, the deviation is small [for NBFM]{.note}, and [jump back]{.golink label="sec:registered_boxes_from_markdown"} works.

## This document's own command

The [peak deviation]{.defterm} is defined here, by a command only this document has.

::: {.unregistered}
A div with an unknown class keeps its content as plain text.
:::
