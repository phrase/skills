#!/usr/bin/env python3
"""Check which parts of the rule extractor can run as scripts in this environment.

Usage:
  python3 check_env.py

Prints one line per check and a final line "MODE: script" or "MODE: partial".
If this file cannot run at all (no shell, no Python 3), the deriver uses native mode.

The core scripts (align, pair_files, translation_job, check_rules, make_diff_view,
write_terminology) need only the Python standard library. Only some file formats need
extra libraries or LibreOffice. A missing library affects only those formats.
"""
import importlib
import shutil
import sys

LIBS = [
    ("docx", "python-docx", ".docx (and .doc .odt .rtf after conversion)"),
    ("pptx", "python-pptx", ".pptx (and .ppt .odp after conversion)"),
    ("openpyxl", "openpyxl", ".xlsx"),
    ("pdfplumber", "pdfplumber", ".pdf"),
    ("bs4", "beautifulsoup4", ".html"),
]


def main():
    ok = sys.version_info >= (3, 8)
    print(f"python: {sys.version.split()[0]} ({'OK' if ok else 'too old, need 3.8 or newer'})")
    if not ok:
        print("MODE: native")
        return 1
    missing = []
    for mod, pkg, formats in LIBS:
        try:
            importlib.import_module(mod)
            print(f"{pkg}: OK ({formats})")
        except Exception:
            print(f"{pkg}: MISSING ({formats})")
            missing.append(pkg)
    office = shutil.which("soffice") or shutil.which("libreoffice")
    print(f"libreoffice: {'OK' if office else 'MISSING'} (.doc .odt .rtf .ppt .odp)")
    print("core scripts: OK (standard library only)")
    if missing:
        print("To add the missing formats: pip install " + " ".join(missing) + " --break-system-packages")
        print("MODE: partial")
    else:
        print("MODE: script")
    return 0


if __name__ == "__main__":
    sys.exit(main())
