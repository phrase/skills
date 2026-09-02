# Raw (lossless) split

The split only *routes* content into files; it never edits it — every Rule stays
verbatim. This method underlies both options: the Combinable split (Option 2), and the
per-group content that Standalone (Option 1) combines with Universal. Exactness matters
more than elegance.

## Shared matter vs. rule content

Split the original into two kinds of content:

- **Shared matter** — the parts that *identify the document* rather than state a rule:
  the title, any confidentiality/legal notice, the metadata block (language, owners,
  dates), and the **change log**. Shared matter is **replicated verbatim into every
  output file** (both the Standalone and Combinable outputs). It is deliberately
  duplicated, so it is **excluded from the lossless/disjoint check**.
- **Rule content** — everything that states a rule. This is what gets **routed** so
  each passage lands in exactly one file, and it is what the lossless check covers.

Placement in each file so the verifier can tell them apart:

```
# <Original Title> — <Content group>        ← header (shared matter): title,
<legal notice>                                 legal notice, metadata, scope
<metadata block>
<one-line scope note>

---                                          ← first '---' ends the header

<routed rule content for this file>          ← body: unique, disjoint

<!-- SHARED FOOTER -->                        ← everything below is shared matter
## Change log                                  (the change log), replicated in
<original change log, verbatim>                every file
```

The verifier ignores everything above the first `---` (the header) and everything at
or below `<!-- SHARED FOOTER -->` (the footer). So the change log can appear in every
file without being counted as an overlap, and the check applies purely to the routed
rule content.

## Rules of the raw split

1. **One destination per rule-content passage.** Every routed rule, sentence, table
   row, and example lands in exactly one file. No routed passage appears twice.
2. **No rewording.** Copy routed passages verbatim; keep original headers and
   numbering. (This skill never optimizes — trimming Rules is the platform's later job.)
3. **Rule content reconstructs the original.** Concatenating the routed bodies of all
   files reproduces the original's rule content — no gaps, no overlaps.
4. **Shared matter is replicated, not routed.** Put it in the header and the shared
   footer of every file.

## Routing procedure

1. Assign each rule-content section to **Universal** (applies to all) or a specific
   **content group**.
2. Content that a group *inherits* rather than owns goes in **Universal only** — don't
   copy it into each group file. (This keeps the Combinable split (Option 2) free of
   overlaps; the Standalone files (Option 1) deliberately duplicate Universal, which is
   that option's accepted trade-off.)
3. Keep original wording, headers, numbering, and example tables in whichever single
   file the rule lands in.
4. Add the shared header and the shared `<!-- SHARED FOOTER -->` change-log block to
   every file.

## Verify

Prove the raw split is lossless and disjoint. Give the verifier the original's **rule
content** (the original with its own shared matter — front-matter and change log —
excluded) and the part files:

```bash
python scripts/verify_split.py --original <original_rule_content.md> --parts <universal.md> <groupA.md> ...
```

It compares the original and the parts as **multisets of lines** (so a heading that
legitimately recurs across modules is fine as long as totals match), after stripping
each part's header (above the first `---`) and shared footer (at/after
`<!-- SHARED FOOTER -->`). It reports:

- **UNDER-COUNTED** — a rule-content line occurs fewer times across the parts than in
  the original (a gap).
- **OVER-COUNTED** — a line occurs more times than in the original (an overlap).
- **FOREIGN** — a line appears in a part but not in the original (a reword or
  addition — not allowed in the raw split).

A clean run (zero under, zero over, zero foreign) means the Combinable split reproduces
the original's rule content exactly. Fix any reported line before delivering.
