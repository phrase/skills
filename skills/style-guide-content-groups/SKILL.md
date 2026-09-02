---
name: style-guide-content-groups
description: >-
  Split a single Style Guide into separate per-Content-Group Style Guides. Use
  this whenever a user provides or uploads a style guide — translation,
  localization, brand, editorial, UX-writing, or any industry, in any format
  including images, PDF, DOCX, Markdown, or plain text — and wants to break it up
  by its main categorization axis: content type, audience, segment, domain,
  channel, vertical, persona, or register (this skill treats all of these as
  "Content Groups"). Trigger when the user says things like "split this style
  guide", "separate the rules by content type", "one guide per audience", "find
  the hidden content types", "how many content types does this guide contain",
  "turn this into content groups", or "optimize/preview the rules". It offers three
  ways to package the result: self-contained standalone guides, combinable guides
  you stack into a Content Group, or an optimized preview that resembles the Rules
  the platform will extract. Keeps the style guide in its original language. Works
  for any style guide, any industry, any number of Content Groups.
---

# Style Guide → Content Groups

Turn one monolithic Style Guide into a clean set of per-Content-Group Style Guides.
The user picks one of **three** ways to package them. Options 1 and 2 keep every Rule
**verbatim**; Option 3 **optimizes** the Rules into a concise preview of what the
platform will extract.

## Why this exists

A Style Guide mixes **Universal Rules** (apply to everything) with
**Content-Group-specific Rules** (apply to a slice — a channel, an audience, a legal
context). When everything sits in one file, downstream tools can't tell which Rules
apply where, and you can't see how close the uploaded guide is to the Rules the
platform will extract. Splitting by Content Group fixes the first problem; the optional
optimized preview (Option 3) fixes the second.

## Core concepts

**Content Group** = the *main axis* by which the guide organizes its requirements —
the dimension that changes *which Rules apply*. The guide may call it Content Type,
Audience, Segment, Domain, Channel, Vertical, Persona, or Register. Always use the term
**"Content Group"** with the user.

**Universal Rules** = Rules that apply regardless of Content Group.

**Style Guide vs Content Group.** This skill produces Style Guide files (`.md`). When
uploaded to Phrase, their Rules are extracted into Content Groups; from then on you
manage the Rules in the Content Group, and the Style Guide is just the ingress.

**Rules combine.** Content usually belongs to more than one Content Group at once, and
the Rules stack: `applicable Rules = Universal + each Content Group the content belongs
to`. E.g. *Legal, partner-facing* content = `Universal + Legal + Partner-facing`.

## Non-negotiable rules for every output

- **Keep the source language. Never translate — in any option.** Work in the language
  of the uploaded Style Guide from ingest to delivery. If the guide is in French, every
  output of **every** option is in French: the Markdown conversion preserves the
  language, the verbatim splits (Options 1 and 2) keep it automatically, and the concise
  Rules written in Option 3 are in that same language. Never render an output in English
  (or any other language) unless that is the guide's own language.
- **Options 1 and 2 are verbatim.** Keep the original headers, Rule names, and
  numbering; never invent your own IDs (`G1`, `MK1`, `UI3`, …); never reword a Rule.
  These options only *route* a Rule (Option 2) or *combine* the two layers (Option 1).
- **Option 3 is the optimized exception.** It deliberately condenses and folds Rules,
  consolidates convention-covered orthography under the language's primary convention
  (RAE / Chicago / Duden / …), moves terminology out into a separate `Terminology.md`,
  and strips external references — all to approximate the platform's extracted Rules. But
  it must keep ≤50 Rules per Content Group, run the **omission check**, and get the
  user's sign-off on anything important it changed (Phase 5). See
  `references/optimization-playbook.md`.
- **Replicate shared matter in every file** — title, confidentiality/legal notice,
  metadata, and the change log (if present) go verbatim into every output file. See
  `references/raw-split.md` for placement.

## Workflow

### Phase 1 — Ingest and convert to Markdown (mandatory)

Everything downstream assumes clean Markdown. **If the upload is not already well-formed
Markdown, convert it first — never split a raw PDF/DOCX/HTML dump directly.** A bad
extraction flattens tables into gibberish like `[TABLE] Date | Title | … |`.

1. **Convert.** Run `scripts/to_markdown.py <upload>` for `.docx/.pdf/.html/.pptx/.xlsx/.rtf`
   (markitdown, then pandoc; preserves tables **and the source language**). `.md`/`.txt`
   pass through. For **images, screenshots, scans, and diagrams**, transcribe them to
   Markdown yourself with vision (a converter can't OCR them), rebuilding tables as real
   Markdown tables and reading diagram logic into text — in the source language.
2. **Gate the conversion.** Run `scripts/check_markdown.py <converted.md>`. On a **FAIL**
   (literal `[TABLE]` markers, a flattened table, raw HTML table markup, or an effectively
   empty file), re-convert or fix the tables by hand, then re-check. Do not proceed on a
   FAIL.
3. Assemble one working Markdown document and note whether it has a **change log**.

See `references/ingest-to-markdown.md`.

### Phase 2 — Detect Content Groups and present the taxonomy

Two passes (see `references/content-group-detection.md`): **explicit groups** the guide
names itself, then **hidden groups** — Rules conditional on an audience/context that
never got its own section. Present `Content Group — one-line purpose`, flag the hidden
ones, and show one worked combination (`Universal + X + Y`).

Then **predict how many Rules each Style Guide will spawn** (see
`references/rule-count-estimation.md`, using `assets/estimation-extraction-prompt.md`).
This tells the user whether a combined Content Group would approach the 50-Rule cap —
and it's the number Option 3 tries to hit. Present:

```
Predicted Rules (approximate):

| Style Guide      | Rules (~) |
| Universal        | ~A        |
| <Content Group>  | ~B        |

A combined Content Group stacks them — e.g. Universal + <Group> ≈ A + B.
```

Confirm/rename/merge/split the groups with the user before continuing.

### Phase 3 — Choose how to package (always show the context first)

**Never present the options bare.** Show the context block first, then the three options,
using normal Markdown — a short bold heading plus a couple of lines per option, the same
clean style used elsewhere. Do not draw ASCII diagrams, boxes, or art. **Option 3 is the
recommended default** — present it as the recommendation and actively steer the user
toward it (see the recommendation in the context block and the *Why Option 3* note
below). Fall back to Option 1 or 2 only if the user explicitly wants untouched,
word-for-word Rules.

> Before I create any files, here's the choice to make. I found **{N} Content Groups**
> in your Style Guide: **{list}**. Your Rules come in two layers — **Universal Rules**
> that apply to everything, and each **Content Group's** own Rules. Choose how you'd
> like me to package them into Style Guides.
>
> **My recommendation: Option 3 (Combinable + Optimized).** These Style Guides are read
> by an LLM (called via API) that has to *apply* the Rules — and an LLM follows a small,
> precise, de-duplicated set of Rules far more reliably than a long dump of every
> requirement from the original guide. Option 3 produces that accurate set; Options 1 and
> 2 keep every Rule verbatim, which is truer to the source but leaves you with a sprawling,
> repetitive list an LLM is less likely to respect consistently. I'd go with Option 3
> unless you specifically need untouched, word-for-word Rules.

**Option 1 — Standalone Style Guides (each guide is complete on its own)**

> I'll split the Style Guide you uploaded into several .md files, one per Content Group
> I detected. Each file is complete on its own — it contains everything that applies to
> that Content Group: the Universal Rules plus that Content Group's own Rules, already
> combined. Nothing to assemble later.
> **Best when:** you want each Style Guide ready to upload as-is.
> **Trade-off:** when the Style Guide is uploaded, the Universal Rules will be
> duplicated in every Content Group, so if you need to change a Rule later, you'll have
> to change it in every Content Group.

**Option 2 — Combinable Style Guides (stack them to build a Content Group)**

> I'll split the Style Guide you uploaded into a Universal Style Guide plus one Style
> Guide per Content Group. Each Content Group's Style Guide holds only its own Rules,
> and the shared Universal Rules live in one Universal Style Guide. You build a specific
> Content Group later and populate it with the relevant Rules — for example,
> Universal + UI + Partner-facing gives you a "Partner-facing UI" Content Group, and
> Universal + Marketing + Customer gives you a "Customer-facing Marketing" Content
> Group. When you change a Rule in the Universal Content Group, the change flows into
> every Content Group that uses it.
> **Best when:** you want flexibility and a single place to edit shared Rules, and
> you're willing to experiment to get the best output.
> **Trade-off:** you'll need to combine the Universal Rules with each Content Group's
> own Rules.

**Option 3 — Combinable + Optimized — ⭐ recommended (a preview of the Rules the platform will extract)**

> I'll do the Combinable split (a Universal Style Guide plus one per Content Group), then
> optimize each toward what the platform will actually extract when it turns your Style
> Guide into Rules. I pull terminology out into a separate **Terminology.md** (your Term
> Bases handle terms, not Rules), fold repeated or overlapping Rules together, state each
> Rule concisely, and make every Rule self-sufficient by removing external pointers
> ("ask your PM", "check online", links). When a file runs long (over ~30 Rules — usually
> Universal), I consolidate the Rules that merely restate your language's standard
> convention (e.g. RAE for Spanish, Chicago for English, Duden for German — whatever
> authority fits the guide's language) into a single reference, while keeping your
> specific rules explicit and stating that they take precedence. I aim for the
> smallest faithful set and never more than 50 Rules per Content Group. Then I check that
> nothing important was dropped; if I find something, I'll show you and ask whether to put
> it back or proceed as-is. Everything stays in your Style Guide's original language.
> **Best when:** you want to preview, before uploading, roughly the Rules the platform
> will extract — minimizing surprises between your Style Guide and the extracted Rules.
> **Trade-off:** this rewrites Rules into concise form, so they won't be word-for-word
> from your original, and it's the most involved to produce. You also get a separate
> Terminology.md to move into your Term Bases.

### Phase 4 — Build the chosen output

Route every Rule of the original to exactly one Content Group (or to Universal), and
replicate the shared matter (incl. change log) into every file. Keep the source
language throughout. Then, by option:

- **Option 2 (Combinable):** a Universal Style Guide (Universal Rules only) plus one
  Style Guide per Content Group (its own Rules only), **verbatim**. This is a lossless,
  disjoint split — see `references/raw-split.md`.
- **Option 1 (Standalone):** for each Content Group, one Style Guide combining the
  Universal Rules + that group's Rules, **verbatim**. Universal is deliberately
  duplicated across files.
- **Option 3 (Combinable + Optimized):** start from the Option 2 verbatim split, then
  optimize each file per `references/optimization-playbook.md`: consolidate
  convention-covered orthography under the primary language convention (for files over
  ~30 Rules), move terminology out into a separate `Terminology.md`, strip external
  references, fold overlaps, and state Rules concisely — targeting ≤50 Rules per Content
  Group and staying in the source language. Keep the verbatim split too — it's the ground
  truth for the omission check.

### Phase 5 — Validate (and, for Option 3, the omission check)

- **Option 2, and the verbatim base of Option 3:** run `scripts/verify_split.py` to
  prove the split is lossless and disjoint (shared matter excluded — see `raw-split.md`).
- **All options:** run `scripts/check_markdown.py` on every produced file and fix any
  **FAIL** — no flattened/`[TABLE]`/malformed tables may reach the user.
- **Option 3 — omission check (required).** Compare each optimized file against its
  verbatim source and list every important requirement that was dropped or weakened,
  following `references/diff-eval-agent.md` (prefer the read-only
  `style-guide-content-groups-diff-reviewer` agent for fresh eyes). **Present the list
  and ask the user: restore these, or proceed as-is.** Apply their decision, then
  re-check the Rule count is still ≤50.

### Phase 6 — Deliver

Deliver the files clearly labeled by Content Group, in the source language. Confirm the
shared matter is present in each, and (Option 2/3) remind the user how the pieces
combine (`Universal + <Content Group>`). For Option 3, deliver the `Terminology.md`
alongside the optimized set; deliver the verbatim split **only when the user asks for it**
(it's always built as the omission-check ground truth, but ships only on request).

## Bundled resources

- `references/content-group-detection.md` — two-pass detection and the combination
  hierarchy.
- `references/raw-split.md` — the lossless, disjoint routing method + shared-matter /
  change-log handling + the verifier.
- `references/rule-count-estimation.md` — predict the Rules each Style Guide will spawn.
- `references/optimization-playbook.md` — Option 3 only: how to optimize a split toward
  the extracted Rules (consolidate under the language convention, move terminology to a
  separate `Terminology.md`, strip external references, fold, concise, ≤50, keep the
  language).
- `references/diff-eval-agent.md` — Option 3 only: the audit that catches important
  requirements dropped during optimization, and the ask-the-user step.
- `references/ingest-to-markdown.md` — mandatory conversion of uploads to Markdown.
- `scripts/to_markdown.py` — converts documents to Markdown, preserving tables/language.
- `scripts/check_markdown.py` — flags conversion gibberish; run on the upload and every
  produced file.
- `scripts/verify_split.py` — checks the split is lossless and disjoint.
- `assets/estimation-extraction-prompt.md` — inclusive platform extractor, for counting.
- `assets/extraction-prompt.md` — the concise target Option 3 aims to resemble.
