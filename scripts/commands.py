#!/usr/bin/env python3
"""
commands.py -- the custom-command registry (references/commands.md).

    python3 commands.py list  [--type T]                 # every registered command and how Markdown writes it
    python3 commands.py check NAME [--type T] [--kind environment]
                                                         # is NAME free: not registered, not in a preamble, not in LaTeX?
    python3 commands.py add NAME --kind command|environment --level core|type --type T|document --preamble FILE.tex
                         --latex DEFINITION.tex --use "when to use it"
                         [--args a,b] [--optional o] [--markdown span|div|none] [--example "LaTeX that uses it"]

`add` refuses a name that is taken, appends the definition to the right preamble and the entry to the matching
commands.yaml, then compiles a test page that uses the command; if that fails, both files are restored.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CORE_PRE = SKILL / "template" / "main-tex-preamble.tex"
CORE_REG = SKILL / "template" / "commands.yaml"
DEFINE = re.compile(r"\\(?:newcommand|renewcommand|providecommand|NewDocumentCommand|RenewDocumentCommand|"
                    r"DeclareRobustCommand|newtcbox|DeclareUrlCommand|def)\*?\s*\{?\\([A-Za-z]+)"
                    r"|\\(?:newenvironment|NewDocumentEnvironment|newtcolorbox|DeclareTColorBox)\*?\s*\{([A-Za-z]+)\}")


def _yaml(path):
    import yaml
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path and path.exists() else {}


def registry(kind=None, doc_reg=None):
    """name -> entry (with 'level'), core first, then the type's, then the document's."""
    reg = {}
    for level, path in (("core", CORE_REG), (f"type {kind}", SKILL / "types" / kind / "commands.yaml" if kind else None),
                        ("document", doc_reg)):
        for name, e in _yaml(path).items():
            reg[name] = dict(e or {}, level=level)
    return reg


def encode(reg):
    """The span/div entries as one string for house.lua: name|kind|arg,arg|optional;..."""
    return ";".join(f"{n}|{e['kind']}|{','.join(e.get('args') or [])}|{e.get('optional') or ''}"
                    for n, e in reg.items() if e.get("markdown") in ("span", "div"))


def preamble_names(paths):
    names = set()
    for p in paths:
        if p and Path(p).exists():
            for m in DEFINE.finditer(Path(p).read_text(encoding="utf-8")):
                names.add(m.group(1) or m.group(2))
    return names


def syntax(name, e):
    args, opt = e.get("args") or [], e.get("optional")
    attrs = "".join(f' {a}="…"' for a in (args[:-1] if e["kind"] == "command" else args)) + (f' {opt}="…"' if opt else "")
    if e.get("markdown") == "span":
        return f"[{args[-1] if args else 'text'}]{{.{name}{attrs}}}"
    if e.get("markdown") == "div":
        return f"::: {{.{name}{attrs}}} … :::"
    return {"auto": "(automatic)", "none": "(LaTeX only)"}.get(e.get("markdown"), "")


def probe(name, kind, type_name=None, extra_pre=None):
    """Compile a page with the full preamble and ask LaTeX whether NAME is already defined."""
    test = (f"\\ifcsname {name}\\endcsname\\typeout{{@@TAKEN@@}}\\fi\n"
            + (f"\\ifcsname end{name}\\endcsname\\typeout{{@@TAKEN@@}}\\fi\n" if kind == "environment" else "")
            + "probe\n")
    return "@@TAKEN@@" in compile_page(test, type_name, extra_pre)[1]


def compile_page(body_tex, type_name=None, extra_pre=None):
    with tempfile.TemporaryDirectory() as tmp:
        body = Path(tmp) / "probe.tex"
        body.write_text(body_tex, encoding="utf-8")
        cmd = [sys.executable, str(SKILL / "scripts" / "build.py"), str(body), "--out", f"{tmp}/probe.pdf",
               "--build-dir", f"{tmp}/b", "--no-toc"]
        if type_name:
            cmd += ["--type", type_name]
        if extra_pre:
            cmd += ["--type-preamble", str(extra_pre)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        log = (Path(tmp) / "b" / "main.log")
        return r, log.read_text(errors="replace") if log.exists() else r.stdout + r.stderr


def is_free(name, kind, type_name=None, doc_reg=None, extra_pre=None):
    """Return why NAME is taken, or None if it is free."""
    reg = registry(type_name, doc_reg)
    if name in reg:
        return f"already registered ({reg[name]['level']}): {reg[name].get('use', '')}"
    pres = [CORE_PRE] + list((SKILL / "types").glob("*/preamble.tex")) + ([extra_pre] if extra_pre else [])
    if name in preamble_names(pres):
        return "already defined in a preamble (core or a type), though not registered"
    if probe(name, kind, type_name, extra_pre):
        return "already defined by LaTeX or a loaded package"
    return None


def cmd_list(a):
    reg = registry(a.type)
    width = max(len(n) for n in reg)
    for n, e in reg.items():
        print(f"{n:{width}}  {e['kind'][:3]}  {e['level']:<14} {syntax(n, e):<42} {e.get('use', '')}")


def cmd_check(a):
    why = is_free(a.name, a.kind, a.type)
    print(f"'{a.name}' is taken: {why}" if why else f"'{a.name}' is free")
    sys.exit(1 if why else 0)


def cmd_add(a):
    if not re.fullmatch(r"[A-Za-z]+", a.name):
        sys.exit("a LaTeX command name has letters only")
    if a.level == "core":
        pre, reg_path = CORE_PRE, CORE_REG
    elif a.level == "type":
        if not a.type or not (SKILL / "types" / a.type / "type.json").exists():
            sys.exit("--level type needs --type NAME of an existing type")
        pre, reg_path = SKILL / "types" / a.type / "preamble.tex", SKILL / "types" / a.type / "commands.yaml"
    else:
        if not a.preamble:
            sys.exit("--level document needs --preamble FILE.tex (the document's own commands, next to its Markdown)")
        pre = Path(a.preamble).resolve()
        reg_path = pre.with_suffix(".yaml")
    why = is_free(a.name, a.kind, a.type, reg_path if a.level == "document" else None,
                  pre if a.level == "document" else None)
    if why:
        sys.exit(f"'{a.name}' is taken: {why}. Choose another name.")
    definition = Path(a.latex).read_text(encoding="utf-8").strip() if Path(a.latex).exists() else a.latex.strip()
    if a.name not in preamble_names([]) and not DEFINE.search(definition):
        sys.exit("the definition must use \\newcommand, \\NewDocumentCommand, \\newenvironment, \\newtcolorbox, ...")
    if a.name not in {m.group(1) or m.group(2) for m in DEFINE.finditer(definition)}:
        sys.exit(f"the definition does not define '{a.name}'")

    backups = {p: p.read_text(encoding="utf-8") if p.exists() else None for p in (pre, reg_path)}
    header = {"core": "", "type": f"% Commands of the {a.type} type, loaded after the house preamble.\n",
              "document": "% This document's own commands, loaded after the house preamble.\n"}[a.level]
    old = backups[pre] if backups[pre] is not None else header
    marker = "% ---------- Registered custom commands (scripts/commands.py add) ----------"
    if marker not in old:
        old = old.rstrip() + "\n\n" + marker + "\n"
    pre.write_text(old.rstrip() + f"\n\n% {a.name}: {a.use}\n{definition}\n", encoding="utf-8")

    args = [x for x in (a.args or "").split(",") if x]
    entry = f"\n{a.name}:\n  kind: {a.kind}\n"
    entry += f"  args: [{', '.join(args)}]\n" if args else ""
    entry += f"  optional: {a.optional}\n" if a.optional else ""
    entry += f"  markdown: {a.markdown}\n  use: {json.dumps(a.use, ensure_ascii=False)}\n"
    reg_old = backups[reg_path] if backups[reg_path] is not None else "# Format: template/commands.yaml in the engineering-docs skill.\n"
    reg_path.write_text(reg_old.rstrip() + "\n" + entry, encoding="utf-8")

    example = a.example or (f"\\begin{{{a.name}}}" + "".join("{x}" for _ in args) + "\ntest\n\\end{" + a.name + "}"
                            if a.kind == "environment" else f"\\{a.name}" + "".join("{x}" for _ in args) + " test")
    r, log = compile_page(example + "\n", a.type if a.level == "type" else None, pre if a.level == "document" else None)
    if r.returncode or "Log clean" not in r.stdout:
        for p, text in backups.items():
            if text is None:
                p.unlink(missing_ok=True)
            else:
                p.write_text(text, encoding="utf-8")
        sys.exit("the test page did not compile cleanly, so nothing was changed:\n" + (r.stdout + r.stderr).strip())
    print(f"added '{a.name}' to {pre.relative_to(SKILL) if a.level != 'document' else pre}"
          f" and {reg_path.relative_to(SKILL) if a.level != 'document' else reg_path}; the test page compiled clean.")
    if a.markdown in ("span", "div"):
        print("Markdown: " + syntax(a.name, {"kind": a.kind, "args": args, "optional": a.optional, "markdown": a.markdown}))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--type")
    p = sub.add_parser("check"); p.add_argument("name"); p.add_argument("--type")
    p.add_argument("--kind", default="command", choices=["command", "environment"])
    p = sub.add_parser("add"); p.add_argument("name")
    p.add_argument("--kind", required=True, choices=["command", "environment"])
    p.add_argument("--level", required=True, choices=["core", "type", "document"])
    p.add_argument("--type"); p.add_argument("--preamble"); p.add_argument("--latex", required=True)
    p.add_argument("--use", required=True); p.add_argument("--args"); p.add_argument("--optional")
    p.add_argument("--markdown", default="none", choices=["span", "div", "none"]); p.add_argument("--example")
    a = ap.parse_args()
    {"list": cmd_list, "check": cmd_check, "add": cmd_add}[a.cmd](a)


if __name__ == "__main__":
    main()
