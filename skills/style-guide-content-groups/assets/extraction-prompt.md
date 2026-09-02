# Concise extraction target (what Option 3 aims to resemble)

Option 3 optimizes each Content Group toward the shape below — a concise, deduplicated
set of Rules, the way the platform's extraction produces them. Use it as the target when
optimizing, and as a downstream prompt if a tool needs to generate the Rules directly.

Two properties keep it lean: it consolidates restatements into one Rule, and it excludes
terminology (the termbase handles it). It stays in the **source language** of the guide.

```
You are a localization quality expert. I will share a style guide. Extract the
requirements that content must satisfy — tone, style, register, formatting, voice, and
any other guidance on how the text should read or feel for its audience. Also extract
any examples that illustrate the requirements.

Prefer fewer, broader requirements. Include every distinct rule the guide expresses,
even subjective ones (e.g. "the tone should feel warm"). But when the same underlying
instruction appears in multiple passages, sections, or a summary/cheat-sheet recap,
consolidate them into ONE requirement and list each passage as a separate excerpt.
Section location alone does not justify a separate requirement.

Do not extract terminology or glossary lookups — specific approved or forbidden terms,
product- or feature-name lists, abbreviation catalogs — the termbase handles these. Do
extract rules ABOUT terminology usage (e.g. "keep approved product names exactly as
approved", or precedence between terminology and fluency).

For each requirement, include all supporting excerpts copied verbatim from the guide. If
an example illustrates it, include that too. Aim to cover the guide thoroughly — extract
every distinct rule, but do not invent requirements the text does not support.

Return no more than 50 requirements. If you would exceed this, consolidate the most
similar requirements rather than dropping distinct rules.

Write the requirement statements in the SAME LANGUAGE as the style guide. Do not
translate.
```
