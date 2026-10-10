# Custom commands: the registry and adding new ones

Every custom command or environment of the house style is recorded in a registry, at one of three levels:

| Level | LaTeX lives in | Registry | Loaded |
|---|---|---|---|
| **core** | `template/main-tex-preamble.tex` | `template/commands.yaml` | every document |
| **type** | `types/NAME/preamble.tex` | `types/NAME/commands.yaml` | documents of that type |
| **document** | a `.tex` file next to the Markdown, named in its front matter (`preamble: my-commands.tex`) | the `.yaml` with the same name (`my-commands.yaml`) | that document only |

```bash
python3 <skill>/scripts/commands.py list [--type T]          # everything registered, and how Markdown writes it
python3 <skill>/scripts/commands.py check NAME [--type T]    # is the name free?
```

## Using a registered command from Markdown

Each registry entry says how Markdown produces it (`markdown:`):

| `markdown:` | Markdown | LaTeX |
|---|---|---|
| `span` | `[text]{.note}`, `[jump back]{.golink label="sec:x"}` | `\note{text}`, `\golink{sec:x}{jump back}`: the text is the last argument, the others come from attributes named like the arguments |
| `div` | `::: {.repocard title="OpenLane repo"}` … `:::` | `\begin{repocard}{OpenLane repo}` … `\end{repocard}`; an optional argument is an attribute too (`::: {.notebox title="…"}` → `\begin{notebox}[…]`) |
| `auto` | ordinary Markdown (bold, `> ⚠`, `#### N1`, …) | made by the converter (`references/authoring.md`) |
| `none` | not from Markdown | LaTeX only, and only when the user asks for it |

- **Attribute values** are Markdown, so `&` and maths are handled; `label`, `width`, `url` and `path` pass through untouched.
- **A div box** takes any number of paragraphs, lists or equations, which a `> ⚠` or `**Example:**` callout cannot.
- **The linter** warns about a `:::` or `{.class}` that is not registered (it would print as plain text) and reports a missing required attribute.

## Adding a command

Only when nothing registered fits. Never define a command inside a body `.tex` file.

1. **Choose the level.** Core only if every kind of document will use it; a type if one kind of document needs it (most cases); document level for a one-off.
2. **Propose it to the user** before adding: the name, the LaTeX definition, the Markdown syntax, and an example of where the document would use it. Add it only once they agree.
3. **Check the name** with `commands.py check NAME --type T`. It must not be registered, not defined in any preamble, and not defined by LaTeX or a loaded package (the check compiles a page to find out).
4. **Add it:**
   ```bash
   python3 <skill>/scripts/commands.py add marksnote --kind command --level type --type past-paper \
       --latex '\newcommand{\marksnote}[1]{\hfill\textit{#1}}' --args text --markdown span \
       --use "a marks remark at the right margin, [5 marks]{.marksnote}"
   ```
   `--latex` is the definition or a file holding it. `add` writes the definition into the level's preamble and the entry into its registry, then compiles a test page that uses the command (or `--example "…"`); if that page does not compile cleanly, both files are restored and nothing changes. For `--level document`, pass `--preamble path/to/my-commands.tex` and put `preamble: my-commands.tex` in the document's front matter.
5. **Document it:** for a type command, add a line to the type's `guide.md` saying when to use it. Then run `tests/run_tests.py --build` and commit to the skill repo.

**Promotion:** when a type or document command turns out to be needed by a second type, move it to the core level (definition into the house preamble, entry into `template/commands.yaml`) and remove it from the type.

**Never** redefine an existing command (`\renewcommand` of a core or LaTeX command) to suit one document; add a new name instead.
