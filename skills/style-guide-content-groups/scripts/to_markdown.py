#!/usr/bin/env python3
"""Convert an uploaded document to clean Markdown before it is split.

Everything in this skill assumes well-formed Markdown. A raw PDF/DOCX/HTML text dump
flattens tables into gibberish like `[TABLE] a | b | c ...`, and that gibberish then
propagates into every split file. So convert first, always.

Strategy (first available wins), all targeting GitHub-Flavored Markdown so tables
stay real Markdown tables:
  1. markitdown  (pip install markitdown) — best at docx/pdf/pptx/xlsx/html tables
  2. pandoc      (system binary) — solid for docx/html/rtf
Images/scans are NOT handled here — a converter can't OCR them reliably. Transcribe
those visually into Markdown instead (see references/ingest-to-markdown.md).

Usage:
    python to_markdown.py INPUT [-o OUTPUT.md]

Prints the output path (or the Markdown to stdout if no -o). Exits non-zero with an
actionable message if no converter is available or conversion fails.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PASSTHROUGH = {".md", ".markdown", ".mdown", ".txt"}
CONVERTIBLE = {".docx", ".doc", ".pdf", ".html", ".htm", ".pptx", ".xlsx", ".rtf", ".odt", ".epub"}


def via_markitdown(path: Path):
    """Try the markitdown Python package, then its CLI. Return Markdown or None."""
    try:
        from markitdown import MarkItDown  # type: ignore
        return MarkItDown().convert(str(path)).text_content
    except ImportError:
        pass
    except Exception as e:  # library present but failed on this file
        print(f"  markitdown (library) failed: {e}", file=sys.stderr)
    if shutil.which("markitdown"):
        try:
            return subprocess.run(["markitdown", str(path)], capture_output=True,
                                  text=True, check=True).stdout
        except subprocess.CalledProcessError as e:
            print(f"  markitdown (cli) failed: {e.stderr.strip()}", file=sys.stderr)
    return None


def via_pandoc(path: Path):
    """Try pandoc → GitHub-Flavored Markdown. Return Markdown or None."""
    if not shutil.which("pandoc"):
        return None
    try:
        return subprocess.run(
            ["pandoc", str(path), "-t", "gfm", "--wrap=none"],
            capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        print(f"  pandoc failed: {e.stderr.strip()}", file=sys.stderr)
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--output", help="Write Markdown here instead of stdout.")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"ERROR: no such file: {src}", file=sys.stderr)
        return 2

    ext = src.suffix.lower()

    if ext in PASSTHROUGH:
        md = src.read_text(encoding="utf-8", errors="replace")
        note = "already Markdown/plain text — passed through (still run check_markdown.py)"
    elif ext in CONVERTIBLE or ext == "":
        md = via_markitdown(src) or via_pandoc(src)
        if md is None:
            print(
                "ERROR: no working converter found.\n"
                "  Install one, then retry:\n"
                "    pip install markitdown        # recommended, best table handling\n"
                "    # or install pandoc: https://pandoc.org/installing.html\n"
                f"  (input was {src.name}, type {ext or 'unknown'})",
                file=sys.stderr)
            return 3
        note = "converted to Markdown"
    else:
        print(f"ERROR: unsupported type {ext!r}. If this is an image or scan, "
              "transcribe it to Markdown visually instead — a converter can't OCR it.",
              file=sys.stderr)
        return 4

    if args.output:
        out = Path(args.output)
        out.write_text(md, encoding="utf-8")
        print(f"{note}: wrote {out}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
