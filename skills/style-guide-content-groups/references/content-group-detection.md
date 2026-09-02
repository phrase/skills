# Content-group detection

A **content group** is the main axis by which a style guide organizes its
requirements — the dimension that changes *which rules apply to a given piece of
content*. Your job is to find that axis (or axes), including the parts the guide
never labeled.

## Alternate names

Guides rarely say "content group." The same concept hides under many labels. Treat
any of these as a content group when it drives which rules apply:

- Content type, content category
- Audience, reader, persona, segment
- Domain, vertical, industry
- Channel, surface, medium, placement
- Register, formality level, tone bucket
- Product line, brand, sub-brand

If two labels describe the same slices of content with the same rules, they are one
axis — don't double-count them.

## What is NOT a content group

- **Universal rules** — apply regardless of slice. They are the shared baseline, not
  a group. (Signal: stated once, near the top, framed as "always" / "across all
  content".)
- **Terminology / glossaries** — approved or forbidden term lists, product-name
  catalogs, abbreviation tables. These are reference data, not a categorization
  axis. (Keep the *rule about* terms — see the optimization playbook.)
- **Brand context** — mission, values, positioning narrative. Informative, yields no
  checkable rule.
- **Cross-cutting dimensions** the guide doesn't tie to distinct rules — e.g. target
  language or region are not content groups *unless* the guide assigns them their
  own tone or rules.

## Two-pass detection

### Pass 1 — explicit groups

Read structurally. The guide usually advertises its main axis through:

- Section and sub-section headers ("UI copy", "Marketing", "Legal", "Email").
- A table or matrix mapping a category to its guidance.
- A table of contents or an index.
- Sentences like "for [category] content, …" used as section openers.

List every category the guide presents as a first-class bucket.

### Pass 2 — hidden groups

Explicit sections miss the groups the guide *applies but never names*. Hunt for
rules that are **conditional on an audience or context**, then cluster the
conditions. Signals:

- Conditional phrasing scattered across other sections: "for partner-facing copy",
  "when writing to travellers", "in legal or compliance contexts", "for internal
  users".
- Tone/register rules that switch by reader ("keep partner copy professional; keep
  traveller copy warm").
- Fixed forms tied to an audience (salutations, sign-offs, disclaimers).
- **Decision trees, flowcharts, matrices, infographics.** These frequently encode
  an entire audience taxonomy the prose never states outright. Transcribe the
  branches and read the leaf conditions as candidate groups.

Each recurring condition that changes the rules is a **hidden content group**. Name
it after its condition (e.g. "Partner-facing") if the guide gives no label.

### Sanity checks

- **Is it really a separate group, or a universal rule with an exception?** If only
  one or two rules ever switch on the condition, it may be cleaner as a noted
  exception inside Universal. Flag the judgment call to the user.
- **Does the axis apply to a language/medium where it collapses?** A gendered
  form-of-address tree is central for gendered languages but mostly inert for
  English. Keep the *taxonomy*, but note where a group's mechanics don't bite.

## Layering and combination

Content groups are often two-dimensional: a **format/purpose** axis (UI, Marketing,
Legal) *and* an **audience** axis (Partner, Traveller). A single piece of content
can belong to one from each. Rules stack:

```
applicable rules = Universal + (format group) + (audience group)
```

When you present the taxonomy, show at least one worked combination so the user
sees they compose small files rather than maintaining one file per combination:

> *Legal, partner-facing content* → apply **Universal + Legal + Partner-facing**.

Make the insight explicit: universal rules combine with specific rules to produce
the full requirement set for any slice.

## Presentation format

```
Content groups I found in your style guide:

Universal (baseline) — applies to all content.
<Group> — <one-line purpose / use-case>.
<Group> — <one-line purpose / use-case>.   [hidden — found in pass 2]

How the rules combine:
- <example slice> → Universal + <Group> + <Group>
```

Then ask the user to confirm, rename, merge, or split before any files are created.
