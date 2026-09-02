# Omission check (Option 3 only)

After optimizing (Option 3), you must confirm the concise set didn't quietly drop or
weaken an important requirement. This is the user's explicit safeguard: optimization is
allowed to fold and shorten, but not to lose meaning. Prefer the read-only
`style-guide-content-groups-diff-reviewer` agent for fresh eyes; otherwise run the brief
below inline, once per Content Group, starting with Universal.

## What to compare

For each Content Group, compare the **optimized file** against its **verbatim source**
(the Option 2 split, which is the ground truth). Work in the source language.

## Subagent brief

```
You are auditing an OPTIMIZED style guide file against its VERBATIM source, to catch
requirements that were dropped or weakened during optimization. You are read-only.

Inputs:
- VERBATIM source for one Content Group: <path>
- OPTIMIZED file for the same Content Group: <path>
- The shared Terminology.md produced by the optimization: <path>

Task:
1. List every distinct requirement in the VERBATIM source.
2. For each, decide whether the OPTIMIZED file still enforces it — explicitly, folded
   into a broader concise Rule, or legitimately transformed. These transformations are
   EXPECTED and are NOT losses:
   - Terminology (specific terms to use/avoid, examples, substitutions) removed from the
     Rules and moved to Terminology.md — check it landed there.
   - Orthography/punctuation Rules consolidated into a single reference to the language's
     primary convention (RAE / Chicago / Duden / …) — but only if the requirement is
     genuinely part of that convention (see step 4).
   - External pointers removed ("ask your PM", "check online", links to outside sources)
     — unless a real, checkable requirement was lost along with the pointer.
   Only the rule ABOUT terminology (follow the termbase, precedence) must still survive
   as a Rule.
3. Report only the requirements that are MISSING or WEAKENED, each as:
   | Requirement (from source) | Missing / Weakened | Impact | One-line note |
   - Impact = High   — changes facts, legal meaning, conditions, or the user's required action.
   - Impact = Medium — a real requirement lost or weakened, but low-stakes (a qualifier, a
     nuance, a non-critical detail).
   - Impact = Low    — phrasing or tone only; barely changes what is enforced.
4. Flag anything the OPTIMIZED file states that the source does not support. A reference
   to the primary language convention is allowed — but verify each Rule folded under it
   is genuinely covered by that convention; flag any that are house style the convention
   does not dictate (over-consolidation), and any specific term left in the Rules that
   belongs in Terminology.md. Count each over-consolidation as a High-impact omission — it
   silently drops a real requirement. If the file references a language convention, confirm
   the reference states precedence explicitly (the guide's specific Rules override the
   convention); flag it (Medium) if that precedence line is missing.
5. Compute a CONFIDENCE SCORE (0–100) for how faithfully the OPTIMIZED set preserves the
   source. Start at 100 and subtract for each MISSING/WEAKENED item (step 3) and each
   over-consolidation (step 4):  High −15, Medium −5, Low −1.  Floor the score at 0.
   Do NOT penalize the by-design transformations in step 2 (terminology → Terminology.md,
   convention consolidation, external-reference/image/markup stripping). Report the
   overall score, the per-Content-Group score, the deductions that produced it, and the
   band:  90–100 → ship as-is · 70–89 → review the flagged items · <70 → restore before
   shipping.

Keep everything in the source language. Do not rewrite the files; only report.
```

## Then ask the user

Lead with the **confidence score and band**, then present the High-impact omissions
first. Ask plainly: **restore these, or proceed as-is?** For each item the user wants
back, add it to the optimized file (concise, in the source language). Restoring items
raises the effective confidence — recompute and report the new score. If restoring pushes a Content Group back over 50 Rules, tell the
user and fold or trim elsewhere with their agreement. Then deliver.

## Common false positive

A requirement can look "missing" because it was correctly folded into a broader Rule,
relocated to another Content Group, moved to `Terminology.md`, or consolidated under the
primary language convention. Check the whole optimized set (and `Terminology.md`) before
flagging, and don't report terminology that was intentionally extracted.
