# Rule categories

Go through every category for every analysis. For each one, decide: is there evidence in the differences between the candidate and the reference? Create a rule only when there is. When there is no evidence, write one sentence in the report saying why no rule was created (for example, "The source never addresses the reader, so there is no Formality rule.").

All Rules work together during translation. Each AI check works alone, on one segment, and cannot see other rules, the termbase, or the translation memory. So a rule must not depend on another rule, and terminology does not belong in rules.

## Content type

What kind of text this is (product page, case study, UI strings, marketing, legal footnotes) and what translation behavior follows from that. A label alone ("This is marketing content") does nothing. The rule must name a behavior that follows from the type and that is visible in the text, for example keeping the sentence type of the source (imperative, question, exclamation), keeping placeholders, or keeping ending punctuation. Do not trigger on intent ("phrases that ask the reader to act") or on vague length classes ("short phrases").

## Editorial

Spelling, punctuation, capitalization, number, date and unit formats, hyphenation and compounds, symbols and footnote markers, placeholders such as "TBD". A known convention can be referenced by name when the model knows it natively (for example "standard US spelling according to Merriam-Webster", "Chicago Manual of Style punctuation"). Do not reference conventions with custom exceptions that the check cannot see. Editorial rules are usually the most reliable AI checks.

## Fluency

Naturalness of the target. "Sounds natural" cannot be checked. Turn it into concrete patterns the check can find, for example a list of stiff connectors to avoid ("notwithstanding", "heretofore") with their plain replacements.

## Formality

Form of address (du/Sie, tu/vous), active vs. passive voice, personal pronouns vs. impersonal nouns, plain words vs. jargon. Trigger the rule on what the source does ("when the source uses 'you'...") so the check compares two visible things. Skip this category if the source never addresses the reader.

## Audience

What the reader already knows, and therefore what must not be explained, simplified, added, or removed. This is the one thing no other category controls. Describe the reader in one specific sentence, then give concrete instructions with examples (for example, "do not shorten a word the source writes in full into an abbreviation"). Keep the audience sentence as context only: no instruction may depend on judging what suits the audience.

## Cultural nuances

Adapting or not adapting references, idioms, examples, measurement units, holidays. Make the rule source-relative: "do not add a cultural reference that the source does not contain", "convert units only when ...". Skip if no reference was adapted.

## Accuracy

Meaning, facts, scope, conditions, qualifiers, amounts, hedges ("can", "may", "helps"). Do not strengthen or weaken claims beyond the source. Reference translations often violate accuracy (for example, by dropping "can"). Report those as reference errors. Do not encode them.

## Terminology

Terminology never goes into rules. It goes into `Terminology.tbx`, the import file for the Term Base (with `Terminology.md` as a readable copy). The reason is capacity: a content group can hold at most 50 rules, but a client can have hundreds or thousands of terms. The Term Base is built for that, and its QA check catches term errors more reliably than an AI check.

The deciding question: **is the term always translated the same way, or does it depend on context?**

- **Strict terms** are always translated the same way: approved terms (forbidden alternatives go only into the "Do not use" column of `Terminology.md`, never into the TBX file), product names, fixed UI and navigation labels, menu labels. Put every one of them into the terminology files. Do not write a rule for them, and do not use them as the main content of a rule.
- **Conditional terms** depend on the meaning of the segment, so a Term Base cannot express them (for example, one English word that needs two different German words in two meanings). Only these may stay inline in a rule, with the terms the rule needs. This is rare. Say in the report why the term is conditional.

A rule may state a general principle about terminology, for example "termbase terms take precedence over fluency". Such a rule cannot be an AI check, because AI checks do not see the Term Base. Mark it as Rule only, AI check off.

**Never name a terminology file in a rule.** The model that applies the rules cannot open files. "Use the terms in Terminology.tbx" is as broken as an external link. `scripts/check_rules.py` fails any rule that names a file.

When the reference translates the same source term in more than one way, do not choose silently. The term goes into the "Needs a decision" table of `Terminology.md`, with the forms found. It stays out of the TBX file until the user chooses.

## Style

Sentence structure, nominal vs. verbal style, literalness, sentence length, headline forms. Only create a style rule when the pattern appears several times and can be described as a visible pattern. If following the reference would make the German (or other target) clearly worse, ask the user before encoding it.

## Transcreation

Creative rewriting beyond translation (new slogans, changed metaphors, restructured headlines). Create a rule only if the reference visibly transcreates, and state the limits (what may change and what must stay, for example numbers and product names).

## Other

If a repeated pattern fits no category above, create a rule under a new, plainly named category. Examples: line-break handling, treatment of English UI menu labels, treatment of internal placeholders.

## What is not a rule

- **Termbase items:** single term pairs, forbidden alternatives, fixed UI, navigation, and menu labels. They go into the terminology files.
- **Reference errors:** grammar mistakes, dropped hedges, misplaced symbols, spacing errors, encoding artifacts such as `&amp;` in plain text.
- **One-off choices:** a different but equally good wording that appears once and shows no pattern.
- **File handling:** line endings, encoding, whitespace that the CMS or import settings control.
