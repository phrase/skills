# Optimization playbook — Option 3 only

Option 3 produces a **preview of the Rules the platform will extract** from the uploaded
Style Guide. The goal is to get each Content Group's file as close as possible to that
final extracted set, so there are no surprises between what the user uploads and what
the platform turns it into.

Start from the **verbatim Combinable split** (Option 2) and optimize each file toward
`../assets/extraction-prompt.md` — the concise, deduplicated shape the extractor aims
for. Keep the verbatim split; it is the ground truth for the omission check.

**Language:** write every optimized Rule in the **source language** of the Style Guide.
If the guide is French, the Rules are French. Never translate.

**The reader is a tool-less LLM.** The optimized Style Guide is consumed by an LLM called
via API that *applies* the Rules. It has **no tools** — it cannot browse, search, open a
link, fetch a file, see an image, or look up an external document. So every surviving Rule
must be **checkable from the text of the guide alone**, plus what the model already knows
from training (e.g. a major published language convention). If a Rule would require the
model to go find, verify, or look at something, either rewrite it so the requirement is
stated inline, or drop it (see *Strip external references*).

## Target

- **≤ 50 Rules per Content Group.** That is the platform cap; the optimized file must
  land under it. Use `rule-count-estimation.md` to track the count as you go.
- **A file over ~30 Rules gets the consolidation pass first.** Above roughly 30 Rules —
  most often the Universal file — apply *Consolidate under the primary language
  convention* (below) before the other levers. It is the single biggest reducer for a
  bloated Universal file.
- Each Rule reads as one concise, checkable requirement — the way an extracted Rule
  reads, not the way a prose paragraph reads.

## Levers (use all of them)

1. **Consolidate under the primary language convention** — for any file over ~30 Rules.
   See below.
2. **Move terminology to a separate `Terminology.md`** — extract it, don't silently drop
   it. See below.
3. **Strip external references** so every Rule is self-sufficient. See below.
4. **Fold overlaps.** Merge Rules that say the same thing (a rule restated in a cheat
   sheet, a summary, or across sections) into one. Merge closely related sub-points into
   a single Rule where the extractor would.
5. **State concisely.** Rewrite each surviving Rule as a short, direct requirement. Drop
   preamble, motivation, and repetition. This is the one place the skill *does* reword —
   because the target itself (an extracted Rule) is a concise restatement.
6. **Relocate audience-conditional Rules** into their own Content Group (that is already
   what the split does; make sure none are left as un-checkable conditionals in
   Universal).
7. **Keep the examples that illustrate a surviving Rule** — they ride along with it and
   don't add to the count. (Examples that are really *term choices* are terminology —
   see lever 2.)

### Consolidate under the primary language convention (>30 Rules)

When a file exceeds ~30 Rules — usually Universal — many of those Rules just restate the
standard orthography and punctuation of the language, which any professional in that
language already follows.

**This works for every language, not a fixed list.** Each language has an authoritative,
widely published convention — find the one for the guide's language and name it. Examples:
**RAE** (Spanish); **The Chicago Manual of Style** or **Merriam-Webster** (American
English); **Duden** (German); the **Internetová jazyková příručka / Pravidla českého
pravopisu** of the Institute for the Czech Language (Czech); **Le Bon Usage / Académie
française** (French); **Accademia della Crusca** (Italian); and the equivalent national
authority for any other language. If you are unsure what the recognized authority is for
the guide's language, do **not** invent one — keep the Rules spelled out instead.

Consolidate only under a convention the model **reliably knows from training** — the guide
is applied by an LLM that **cannot look anything up**, so a reference it can't reproduce
from memory is useless. So folding is a judgment call, not automatic:

- **Fold** the well-known *basics* the model can reproduce cold — e.g. Spanish `¿? ¡!`
  pairing, English serial-comma / quotation basics — into a single reference Rule.
- **Keep spelled out** (do *not* fold) three kinds of Rule, even when they technically
  fall under the convention:
  1. **House-style departures** — anything the guide does *differently from* or *on top
     of* the convention (a brand capitalization, "don't use semicolons").
  2. **Specific or mechanical typography** — exact spacing and number, currency, phone,
     date, time, and range formats (e.g. "space on both sides of the colon in a ratio",
     "group phone digits in threes", "DD.MM.YYYY"). A bare "follow the convention" rarely
     reproduces these exactly, so stating them keeps each Rule checkable from the text
     alone.
  3. **Lower-resource languages** — when the model is unlikely to recall the language's
     detailed typographic rules precisely, keep the specifics explicit and let the
     convention cover only the rest.

  When in doubt, keep the Rule separate; the omission check catches over-consolidation.

**Always state precedence explicitly — in words, never merely implied.** However you
reference the convention, the specific Rules in the guide must win over it, and the
convention reference Rule must say so. Use whichever framing matches what you did, but keep
the precedence sentence in both:

- *Fold framing* — you replaced many basics with one reference:
  > *"Follow <AUTHORITY> orthography and punctuation conventions (paired
  > question/exclamation marks, comma placement, quotation marks, etc.) unless prompted
  > otherwise. Any requirement in this Style Guide that contradicts <AUTHORITY> takes
  > precedence."*
- *Fallback framing* — you kept many specific Rules and use the convention only for the
  rest:
  > *"For <language> spelling, grammar, and punctuation not covered by a specific
  > rule in this guide, follow <AUTHORITY>. Where this guide gives a specific rule,
  > that rule takes precedence, and a runtime prompt may override either."*

Replace `<AUTHORITY>` and `<language>` with the guide's own. This convention reference is
the **one allowed external reference** (see *Strip external references* below).

### Move terminology to a separate `Terminology.md`

Terminology does not belong in the Rules — the platform's Term Bases handle it. But don't
silently delete it: **extract it into a single `Terminology.md`** delivered alongside the
optimized set.

- **Omit from the Style Guide** any Rule whose content is a **specific term to use or
  avoid** — concrete examples, substitutions, approved/forbidden word lists, product-name
  catalogs, "say X not Y" pairs, flagged terms.
- **Keep in the Style Guide** any Rule that states a **general principle** rather than a
  specific term. Example to keep: *"For non-binary individuals, use the pronouns
  'they/them.'"* — a general rule, not a term-list entry.
- **Collect** every omitted term into `Terminology.md` so nothing is lost, noting the
  Content Group it came from where that matters. Start the file with a short preface:

  > **Terminology.** These are terms to use or avoid, pulled out of the Style Guide.
  > Terminology should be handled separately, in Term Bases — not as Style Guide Rules.

Keep the *rule about* terminology (e.g. "follow the approved termbase", precedence
between terminology and fluency) in the Style Guide — that is a principle, not a term.

### Strip external references

Every Rule must be **self-sufficient** — checkable on its own by an LLM that reads only
the text of this Style Guide. The guide is consumed by an **LLM called via API: it cannot
open a link, fetch a page, see an image, or look anything up.** Any Rule that leans on
external material or on markup the model can't act on is uncheckable, so remove that part
during optimization:

- Remove process/escalation pointers: *"When in doubt, ask your Project Manager"*,
  *"check online"*, *"confirm with the client"*, *"search for the latest guidance"*.
- Remove links to external sources and web pages. Example to omit: *"Use the official
  Spanish translation published at apple.com/la."*
- Remove **image and media references** — the model can't see them. Examples to omit: an
  `<img src="/media/image2c.png" …>` tag, a Markdown image like `![logo](media/image1.png)`,
  or a Rule that says *"match the example shown in the screenshot above."*
- Remove **leftover conversion markup and raw HTML** — it's noise, not a requirement.
  Examples to strip: stray table scaffolding like
  `<table> <colgroup> <col style="width: 20%" /> <col style="width: 18%" /> <col style="width: 60%" /> </colgroup> <tbody> <tr class="odd"> <td><strong>Project Folder</strong></td> …`,
  orphan `<td>` / `<tr>` / `<div>` / `<span>` tags, and stray HTML entities. If a real
  requirement is trapped inside such markup, rewrite it as a plain-text Rule; if it's pure
  scaffolding, delete it. (The ingest gate `check_markdown.py` catches the worst flattened
  tables, but strip anything that slips through here.)
- If a Rule's only content is an external pointer or leftover markup, drop the Rule. If a
  Rule carries a real requirement *plus* an external pointer, keep the requirement and cut
  the pointer.

The **one exception** is the primary language convention (RAE / Chicago / Duden / …)
introduced by the consolidation pass — the model already knows these conventions from
training (it is not being asked to look them up), so that reference is allowed.

## Do not lose meaning

Concise is not the same as incomplete. Every distinct requirement in the verbatim source
must still be represented — folded, shortened, consolidated under a convention, or moved
to `Terminology.md`, but never simply gone. Anything that changes facts, legal meaning,
conditions, or the user's action must survive as a Rule. Whatever you are unsure about,
keep; the omission check (`diff-eval-agent.md`) exists to catch the calls you got wrong,
and the user gets the final say.

## After optimizing

1. Confirm each Content Group's optimized file is **≤ 50 Rules** (and that any file you
   took through the consolidation pass is genuinely smaller, not just relabeled).
2. Run the **omission check** (`references/diff-eval-agent.md`) against the verbatim
   split, present any important omissions, and ask the user to restore or proceed. The
   check also confirms convention-consolidated Rules really are covered by the named
   convention, and that everything routed to `Terminology.md` is genuinely term-level.
3. Deliver `Terminology.md` alongside the optimized set. Deliver the verbatim split
   **only when the user asks for it** — it is always built and kept as the ground truth
   for the omission check, but it ships only on request.
