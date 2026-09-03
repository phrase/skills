#!/usr/bin/env python3
"""Flag Rules that reference a companion file this skill produced.

In Option 3 the optimized Style Guide is applied by an LLM that has no tools — it cannot
open another file at runtime. So a Rule that points at `Terminology.md` (or the verbatim
split, or a sibling Content-Group file) is a broken reference: the term/value it names is
unreachable. Inline what the Rule needs instead (see optimization-playbook.md).

This is the deterministic counterpart to the omission check — a grep-simple gate that
catches every self-reference for free, without an LLM pass.

What it does:
  * Skips each file's header — everything up to and including the first line that is
    exactly `---` (a companion-file mention in the human-facing scope/metadata is fine).
  * In the body, FAIL on any Markdown filename token (e.g. `Terminology.md`,
    "universal.md", optimized/product_copy.md), whether backtick-quoted or not.
  * Prints the offending file, line number, and line — same output shape as
    check_markdown.py.

Usage:
    python check_self_references.py FILE [FILE ...]
Exit code is 0 only if no FAILs across all files.
"""

import re
import sys

# A Markdown filename token: optional path, ends in .md. Matches `Terminology.md`,
# "universal.md", optimized/product_copy.md, etc. A bare ".md" does not match.
MD_REF = re.compile(r"[\w./-]*[\w-]\.md\b", re.IGNORECASE)


def body_lines(text):
    """Yield (lineno, line) for the body — everything after the first '---' line."""
    lines = text.split("\n")
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            start = i + 1
            break
    for i in range(start, len(lines)):
        yield i + 1, lines[i]


def check(path):
    fails = []
    try:
        text = open(path, encoding="utf-8").read()
    except Exception as e:
        return [f"cannot read file: {e}"]
    for lineno, line in body_lines(text):
        m = MD_REF.search(line)
        if m:
            fails.append(
                f"line {lineno}: references companion file {m.group(0)!r} — a Rule can't "
                f"open another file at runtime; inline what it needs instead")
    return fails


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python check_self_references.py FILE [FILE ...]", file=sys.stderr)
        return 2
    any_fail = False
    for path in sys.argv[1:]:
        fails = check(path)
        status = "FAIL" if fails else "PASS"
        print(f"[{status}] {path}")
        for f in fails:
            print(f"    FAIL: {f}")
        any_fail = any_fail or bool(fails)
    print("\nRESULT:", "NOT CLEAN — remove the companion-file references above."
          if any_fail else "clean — no Rule references a companion file.")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
