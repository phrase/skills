# Ingest → Markdown (mandatory first step)

The whole workflow operates on Markdown. If you split a raw PDF/DOCX/HTML text dump,
tables collapse into gibberish — e.g. a revision-history table becomes one run-on line
`[TABLE] Date | Title | Description 22/12/2017 | N/A | Original published …` — and that
gibberish is copied into every output file. So the upload is **always** converted to
clean Markdown and gated before anything else happens.

## 0. Prerequisite — a converter must be installed (non-Markdown uploads)

`.docx/.pdf/.pptx/.xlsx/.html/.rtf` uploads need `markitdown` (recommended) or `pandoc`.
`.md`/`.txt` and images (handled by vision) need neither. **Before converting, check that
one is present** — `python3 -c "import markitdown"` or `command -v pandoc`. If neither is,
**tell the user the exact install command for their OS and offer to run it** rather than
proceeding into a failing conversion:

- Recommended, any OS: `pip install -U markitdown` (needs Python 3.10+; the `-U` avoids a
  stale build — an older `markitdown` can import without the converter class and fail).
- pandoc — macOS: `brew install pandoc` · Debian/Ubuntu: `sudo apt install pandoc` ·
  Windows: `winget install --id JohnMacFarlane.Pandoc` (or the installer at pandoc.org).

## 1. Convert

Run the bundled converter:

```bash
python scripts/to_markdown.py <upload> -o working.md
```

It tries, in order, and targets GitHub-Flavored Markdown so tables stay real tables:

1. **markitdown** — `pip install -U markitdown` (Python 3.10+). Best at
   `.docx/.pdf/.pptx/.xlsx/.html` tables. Recommended.
2. **pandoc** — system binary (`https://pandoc.org/installing.html`). Good for
   `.docx/.html/.rtf`.

`.md`/`.markdown`/`.txt` pass through untouched (still gate them — step 3).

If neither converter is installed, `to_markdown.py` exits with install instructions.
Install markitdown and re-run; don't hand-transcribe a long document you could convert.

### Images, screenshots, scans, diagrams

A converter cannot OCR these. **Transcribe them into Markdown yourself using vision:**
rebuild any table as a real Markdown table, and read the logic of decision trees,
flowcharts, and infographics into prose or a list — guides frequently hide real rules
(audience taxonomies, form-of-address logic) in diagrams, and those must not be lost.

## 2. Gate the conversion

```bash
python scripts/check_markdown.py working.md
```

It reports:

- **FAIL** — literal `[TABLE]`/`[/TABLE]` markers, a flattened table (many `|`-cells
  on one line with no `| --- |` separator), **raw HTML table markup** (`<table>`, `<tr>`,
  `<td>`, `<colgroup>`, `<col …>`, etc. — a table left as HTML instead of Markdown), or an
  effectively empty file. The conversion is broken.
- **WARN** — a table header row with no separator on the next line, **image references**
  (`<img …>` or `![](…)` — an LLM called via API can't see them, so transcribe with vision
  or remove), **stray leftover HTML markup** (`<div>`, `<span>`, Office `<o:p>`/`<w:…>`
  tags), stray HTML comments, or very long run-on lines. Usually worth a look but not fatal.
- **PASS** — no gibberish detected.

**On FAIL:** re-run `to_markdown.py` with the other converter, or open `working.md` and
fix the affected tables by hand (put each row on its own line, add the `| --- |`
separator), then re-check. Do not start the split until the source passes — a gibberish
source can only produce gibberish splits.

## 3. Assemble

If the guide arrived as several files or images, assemble one working Markdown document
so you can reason over all of it at once. Note whether it contains a **change log /
revision history**; it is shared matter you will replicate into every output file
(see `raw-split.md`).

## Same gate on the way out

`check_markdown.py` is also the **output** gate: in Phase 6, run it on every file you
produce (raw, optimized, combined) and fix any FAIL before delivering, so a formatting
problem never reaches the user.
