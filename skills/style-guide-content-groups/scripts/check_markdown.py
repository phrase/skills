#!/usr/bin/env python3
"""Flag conversion 'gibberish' in a Markdown file.

Run this after converting an uploaded document to Markdown (input gate) and on every
file the split produces (output gate). It catches the failure the screenshot showed:
a source table flattened into a run-on paragraph of pipes, e.g.
`[TABLE] Date | Title | Description 22/12/2017 | N/A | Original published ...`.

Checks:
  * FAIL  literal table markers: [TABLE], [/TABLE], [TABLE], etc.
  * FAIL  flattened table: a single line with many ' | ' separators that is NOT part
          of a real Markdown table (no header separator row of dashes).
  * FAIL  malformed table: a block of pipe-rows with no '| --- |' separator after the
          header.
  * FAIL  raw HTML table markup (<table>, <tr>, <td>, <th>, <colgroup>, <col ...>, etc.)
          — a table left as HTML instead of converted to a Markdown table.
  * WARN  image references (<img ...> or ![](...)) — an LLM called via API can't see
          them; transcribe with vision or remove.
  * WARN  stray leftover HTML markup (<div>, <span>, <font>, Office <o:p>/<w:...> tags).
  * WARN  stray HTML comment artifacts other than the intended markers
          (<!-- BODY -->, <!-- SHARED FOOTER -->).
  * FAIL  effectively empty file.

Usage:
    python check_markdown.py FILE [FILE ...]
Exit code is 0 only if no FAILs across all files.
"""

import re
import sys

ALLOWED_COMMENTS = {"<!-- BODY -->", "<!-- SHARED FOOTER -->"}
PIPES_FLATTENED = 5          # ' | ' occurrences in one line to suspect a flattened table
LONG_LINE = 1200             # chars; run-on lines are a conversion smell

# Raw HTML table structure left over from a failed conversion (should be a Markdown table).
HTML_TABLE_TAG = re.compile(r"</?(?:table|thead|tbody|tfoot|colgroup|col|tr|td|th)\b", re.IGNORECASE)
# Image references the model can't see (HTML <img> or Markdown ![alt](path)).
IMG_TAG = re.compile(r"<img\b", re.IGNORECASE)
MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
# Leftover block/Office markup that a clean Markdown conversion would not emit.
STRAY_HTML_TAG = re.compile(r"</?(?:div|span|font|o:p|w:[A-Za-z]+|v:[A-Za-z]+|m:[A-Za-z]+)\b", re.IGNORECASE)


def is_table_separator(line: str) -> bool:
    s = line.strip()
    return bool(re.match(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?$", s))


def check(path: str):
    fails, warns = [], []
    try:
        text = open(path, encoding="utf-8").read()
    except Exception as e:
        return [f"cannot read file: {e}"], []

    lines = text.split("\n")
    non_trivial = [l for l in lines if len(l.strip()) >= 3]
    if len("".join(non_trivial).strip()) < 20:
        fails.append("file is effectively empty after conversion")

    # Literal table markers anywhere.
    for m in re.finditer(r"\[/?TABLE\]", text, re.IGNORECASE):
        fails.append(f"literal table marker {m.group(0)!r} — table was not converted")
        break

    # Raw HTML table markup: a table left as HTML instead of converted to Markdown.
    html_tbl = [i for i, line in enumerate(lines, 1) if HTML_TABLE_TAG.search(line)]
    if html_tbl:
        shown = ", ".join(map(str, html_tbl[:5])) + (" …" if len(html_tbl) > 5 else "")
        fails.append(
            f"raw HTML table markup on line(s) {shown} — a table was left as HTML, not "
            f"converted to a Markdown table")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Flattened table: many pipes in one physical line, not a real table row/sep.
        pipe_groups = stripped.count(" | ")
        if pipe_groups >= PIPES_FLATTENED:
            prev = lines[i - 2].strip() if i >= 2 else ""
            nxt = lines[i].strip() if i < len(lines) else ""
            in_real_table = is_table_separator(prev) or is_table_separator(nxt) \
                or is_table_separator(line)
            if not in_real_table:
                fails.append(
                    f"line {i}: {pipe_groups} '|'-separated cells on one line with no "
                    f"table separator row — looks like a flattened table")

        # Image references — an LLM called via API can't see them.
        if IMG_TAG.search(line) or MD_IMAGE.search(line):
            warns.append(f"line {i}: image reference — an API LLM can't see it; "
                         f"transcribe with vision or remove")

        # Leftover block / Office HTML markup a clean conversion wouldn't emit.
        if STRAY_HTML_TAG.search(line):
            warns.append(f"line {i}: stray HTML markup — leftover from conversion")

        # Stray comment artifacts.
        for c in re.findall(r"<!--.*?-->", line):
            if c.strip() not in ALLOWED_COMMENTS:
                warns.append(f"line {i}: stray HTML comment {c.strip()!r}")

        if len(line) > LONG_LINE:
            warns.append(f"line {i}: very long line ({len(line)} chars) — possible run-on conversion")

    # Malformed Markdown tables: a table's HEADER row (a pipe-row that starts a table
    # block — i.e. the previous line is not itself a pipe-row) must be followed by a
    # '| --- |' separator. Interior data rows are consecutive pipe-rows and are fine,
    # so only the block-opening row is checked.
    def is_pipe_row(s: str) -> bool:
        return s.startswith("|") and s.count("|") >= 2 and not is_table_separator(s)

    for i, line in enumerate(lines):
        cur = line.strip()
        prev = lines[i - 1].strip() if i > 0 else ""
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        starts_table = is_pipe_row(cur) and not is_pipe_row(prev) and not is_table_separator(prev)
        if starts_table and not is_table_separator(nxt):
            warns.append(f"line {i+1}: table header row with no '| --- |' separator on the next line")

    return fails, warns


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python check_markdown.py FILE [FILE ...]", file=sys.stderr)
        return 2
    any_fail = False
    for path in sys.argv[1:]:
        fails, warns = check(path)
        status = "FAIL" if fails else ("WARN" if warns else "PASS")
        print(f"[{status}] {path}")
        for f in fails:
            print(f"    FAIL: {f}")
        for w in warns[:20]:
            print(f"    warn: {w}")
        any_fail = any_fail or bool(fails)
    print("\nRESULT:", "NOT CLEAN — fix the FAILs above before using this file."
          if any_fail else "clean enough — no gibberish detected.")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
