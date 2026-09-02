#!/usr/bin/env python3
"""Verify that a RAW style-guide split is lossless and disjoint.

A raw split routes an original style guide into several files without changing any
wording. This script proves two properties:

  * LOSSLESS  — every non-trivial line of the original appears in at least one part.
  * DISJOINT  — no original line appears in more than one part.

Each part file wraps its routed body in shared matter that is replicated across files
(title, legal notice, metadata, change log) and must NOT count toward the check.
Everything above the first line that is exactly '---' (or contains '<!-- BODY -->') is
the header and is ignored; everything at or below a line containing
'<!-- SHARED FOOTER -->' (e.g. the change log) is the footer and is ignored. What
remains is the routed body that must reconstruct the original's rule content.

Usage:
    python verify_split.py --original ORIGINAL.md --parts A.md B.md C.md
    python verify_split.py --original ORIGINAL.md --parts *.md --min-len 8

Exit code is 0 when the split is clean, 1 otherwise, so it can gate a workflow.
"""

import argparse
import sys
from collections import Counter


def normalize(line: str) -> str:
    """Collapse whitespace so trivial reflowing doesn't cause false mismatches."""
    return " ".join(line.strip().split())


def strip_wrapping(text: str) -> str:
    """Return only the routed body: drop the shared header and the shared footer.

    The header is everything up to and including the first line that is exactly '---'
    or contains '<!-- BODY -->'. The footer is everything at or below a line that
    contains '<!-- SHARED FOOTER -->'. Header and footer hold replicated shared matter
    (title, legal notice, metadata, change log) that must not count toward the
    lossless/disjoint check.
    """
    lines = text.split("\n")

    # Cut the footer first (shared matter such as the change log).
    for i, ln in enumerate(lines):
        if "<!-- SHARED FOOTER -->" in ln:
            lines = lines[:i]
            break

    # Then cut the header.
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s == "---" or "<!-- BODY -->" in s:
            return "\n".join(lines[i + 1:])
    # No header delimiter found: treat the remainder as body.
    return "\n".join(lines)


def significant_lines(text: str, min_len: int) -> Counter:
    """Return a multiset of normalized lines worth checking (skips short/boilerplate)."""
    out = Counter()
    for ln in text.split("\n"):
        n = normalize(ln)
        if len(n) < min_len:
            continue
        if set(n) <= set("-|:# *"):  # table rules, dividers, bullet scaffolding
            continue
        out[n] += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--original", required=True, help="Path to the original guide.")
    ap.add_argument("--parts", required=True, nargs="+", help="Paths to the split files.")
    ap.add_argument("--min-len", type=int, default=8,
                    help="Ignore lines shorter than this many characters (default 8).")
    args = ap.parse_args()

    with open(args.original, encoding="utf-8") as f:
        original = significant_lines(f.read(), args.min_len)

    # Count occurrences across all part bodies, and remember which parts hold each
    # line (for reporting). We compare MULTISETS: a line that legitimately appears
    # N times in the original must appear N times total across the parts. That way a
    # recurring boilerplate header (e.g. "### Core rules" in several modules) is fine
    # as long as its total count matches, while a real gap or overlap changes a count.
    combined = Counter()
    where = {line: [] for line in original}
    for path in args.parts:
        with open(path, encoding="utf-8") as f:
            body = significant_lines(strip_wrapping(f.read()), args.min_len)
        for line, c in body.items():
            combined[line] += c
            if line in where:
                where[line].append(path)

    under = [ln for ln, c in original.items() if combined[ln] < c]      # gaps
    over = [ln for ln, c in original.items() if combined[ln] > c]       # overlaps
    # Lines that appear in a part body but not in the original at all (edits/additions).
    foreign = [ln for ln in combined if ln not in original]

    total = sum(original.values())
    print(f"Original significant lines (with repeats): {total}")
    print(f"Parts checked: {len(args.parts)}")
    print(f"UNDER-COUNTED (a gap — original occurrence missing): {len(under)}")
    print(f"OVER-COUNTED (an overlap — occurrence appears too many times): {len(over)}")
    print(f"FOREIGN (in a part but not in the original — reworded/added): {len(foreign)}")

    if under:
        print("\n-- UNDER-COUNTED (gaps) --")
        for ln in under[:50]:
            print(f"  original x{original[ln]} vs parts x{combined[ln]}: {ln[:80]}")
        if len(under) > 50:
            print(f"  ... and {len(under) - 50} more")

    if over:
        print("\n-- OVER-COUNTED (overlaps) --")
        for ln in over[:50]:
            print(f"  original x{original[ln]} vs parts x{combined[ln]} ({', '.join(where[ln])}): {ln[:70]}")
        if len(over) > 50:
            print(f"  ... and {len(over) - 50} more")

    if foreign:
        print("\n-- FOREIGN (not in original) --")
        for ln in foreign[:50]:
            print(f"  {ln[:100]}")
        if len(foreign) > 50:
            print(f"  ... and {len(foreign) - 50} more")

    clean = not under and not over and not foreign
    print("\nRESULT:", "CLEAN — lossless and disjoint." if clean
          else "NOT CLEAN — fix the lines above.")
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
