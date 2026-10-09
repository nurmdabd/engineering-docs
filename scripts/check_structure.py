#!/usr/bin/env python3
"""
check_structure.py -- lightweight, no-compile structural sanity check for
converted LaTeX body content.

Catches the two most common generation mistakes without needing a LaTeX
install:
  1. Unbalanced curly braces {}
  2. Mismatched / unclosed \\begin{...} ... \\end{...} pairs

This is NOT a full LaTeX parser and is NOT a substitute for an actual
compile -- it won't catch undefined commands, bad table column counts,
missing packages, or semantic errors. It's a fast first-pass check to run
before returning output, to catch the kind of typo that's easy to
introduce when hand-assembling nested commands (e.g. \\textbf{\\keyterm{...})
or a table environment.

Usage:
    python3 check_structure.py <file.tex>
    cat snippet.tex | python3 check_structure.py -

Exit code 0 = no issues found. Exit code 1 = issues found (printed to stdout).
"""

import sys
import re

BEGIN_RE = re.compile(r'\\begin\{([a-zA-Z*]+)\}')
END_RE = re.compile(r'\\end\{([a-zA-Z*]+)\}')


def strip_comments(line):
    """Remove a trailing LaTeX comment (unescaped %) from a line."""
    i = 0
    while i < len(line):
        if line[i] == '\\' and i + 1 < len(line):
            i += 2
            continue
        if line[i] == '%':
            return line[:i]
        i += 1
    return line


def check_braces(lines):
    """Track brace depth line-by-line, skipping escaped \\{ and \\}."""
    issues = []
    depth = 0
    depth_at_line_start = []
    for lineno, raw in enumerate(lines, start=1):
        depth_at_line_start.append(depth)
        line = strip_comments(raw)
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == '\\' and i + 1 < len(line):
                i += 2
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth < 0:
                    issues.append(
                        f"line {lineno}: unmatched closing '}}' "
                        f"(no corresponding '{{' open at this point)"
                    )
                    depth = 0
            i += 1
    if depth > 0:
        issues.append(
            f"end of file: {depth} unclosed '{{' brace(s) -- "
            f"a '}}' is missing somewhere"
        )
    return issues


def check_environments(lines):
    """Track \\begin{X}/\\end{X} pairing and nesting order."""
    issues = []
    stack = []  # list of (env_name, lineno)
    for lineno, raw in enumerate(lines, start=1):
        line = strip_comments(raw)
        for m in BEGIN_RE.finditer(line):
            stack.append((m.group(1), lineno))
        for m in END_RE.finditer(line):
            env = m.group(1)
            if not stack:
                issues.append(
                    f"line {lineno}: \\end{{{env}}} with no matching "
                    f"\\begin{{...}} open"
                )
                continue
            open_env, open_lineno = stack[-1]
            if open_env == env:
                stack.pop()
            else:
                # Try to find a matching open further down the stack --
                # if found, everything above it is likely a missing \end.
                found_idx = None
                for idx in range(len(stack) - 1, -1, -1):
                    if stack[idx][0] == env:
                        found_idx = idx
                        break
                if found_idx is not None:
                    unclosed = stack[found_idx + 1:]
                    for uenv, ulineno in unclosed:
                        issues.append(
                            f"line {ulineno}: \\begin{{{uenv}}} appears "
                            f"never closed (found \\end{{{env}}} on line "
                            f"{lineno} before it)"
                        )
                    stack = stack[:found_idx]
                else:
                    issues.append(
                        f"line {lineno}: \\end{{{env}}} does not match "
                        f"the currently open \\begin{{{open_env}}} "
                        f"(opened on line {open_lineno})"
                    )
    for env, lineno in stack:
        issues.append(
            f"line {lineno}: \\begin{{{env}}} is never closed "
            f"(no matching \\end{{{env}}} found)"
        )
    return issues


def main():
    if len(sys.argv) != 2:
        print("Usage: check_structure.py <file.tex>   (or '-' for stdin)")
        sys.exit(2)

    src = sys.argv[1]
    if src == '-':
        text = sys.stdin.read()
    else:
        with open(src, 'r', encoding='utf-8') as f:
            text = f.read()

    lines = text.splitlines()
    issues = check_braces(lines) + check_environments(lines)

    if not issues:
        print("OK: no brace or environment mismatches found.")
        print("(Note: this is a structural check only, not a full compile --")
        print(" it can't catch undefined commands, bad table column counts,")
        print(" or other semantic errors.)")
        sys.exit(0)
    else:
        print(f"Found {len(issues)} issue(s):\n")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)


if __name__ == '__main__':
    main()
