# Writing rules that work as Rules and as AI checks

The same rule text is used twice:

1. **During translation.** The translation agent reads all rules together and applies them.
2. **As an AI check.** A judge sees one source segment, one target segment, and this one rule. Nothing else: no other rules, no termbase, no translation memory, no document context, no information about where the string appears in the UI.

A rule is good only if it works in both places. Phrase runs an eligibility check when a rule is created. The prompt it uses is in `eligibility_prompt.md`. If the rule cannot give the same pass/fail verdict every time from a single segment pair, Phrase omits it as an AI check.

## Hard requirements

- **450 characters or fewer.** Count with `scripts/check_rules.py`. Do not estimate.
- **Written as a translation instruction.** Say what to do: "Write...", "Keep...", "Do not use...". Never "Flag a segment if...". Translation does not flag anything.
- **One theme per rule.** Several related conditions are fine (three sentence types, two separators). Unrelated requirements go into separate rules.
- **At least one concrete example**, in quotation marks, ideally with the wrong form next to the right form ("„Showtime“-Kollektion", not "Showtime-Kollektion").
- **No external references** the model cannot see: no "approved materials", "the style guide", "project instructions", "other rules", and no file names such as `Terminology.tbx`.
- **No term pairs.** "Always translate X as Y" is a termbase entry, not a rule. It goes into the terminology files.
- **Plain English.** One idea per sentence. Short, direct sentences. Keep technical terms. No idioms or slang.
- **The rules file format:** one rule per paragraph, paragraphs separated by one empty line, no headers, no numbers, no character counts.

## Make the trigger visible

The check can only verify what it can see in the two segments. Trigger rules on:

- **Grammar and form:** "an imperative", "a question that ends with a question mark", "a number with four or more digits", "a number followed by p or i".
- **Symbols and markup:** ®, ™, `<sup>` markers, placeholders, brackets.
- **The source itself:** "that the source writes in full", "that the source does not have", "as in the source". Source-relative rules are the most reliable.

Do not trigger rules on:

- **Intent or purpose:** "phrases that ask the reader to act", "to make the reader act".
- **Vague classes:** "short phrases", "technical terms", "headlines" (unless defined by a visible pattern).
- **UI location:** "button text", "error messages", "tooltips". Describe the text pattern instead ("a phrase with no ending punctuation").
- **Hedged conditions:** "when possible", "when appropriate", "unless important", "if necessary".
- **Quality judgments:** "natural", "clear", "appealing", "sufficiently non-technical".
- **Document position:** "on first use", "in the previous sentence". Use "in the same sentence" instead.
- **Consistency across segments:** "translate the same term the same way throughout", "use one form consistently". The judge sees one segment and cannot compare it with others. Move the consistency to the termbase, or name the required form in the rule.

## Real omission reasons and the fixes that worked

**Audience rule, omitted.** The rule asked to add a plain-language explanation for every technical term and to expand every abbreviation. Reason: deciding what is a "technical term" and whether wording is "sufficiently non-technical" needs judgment; whether all abbreviations should be expanded needs context. Fix that passed: remove the explanation requirement; make the abbreviation part source-relative; make slang concrete with categories and examples; keep the audience sentence as context only.

> Readers are older US adults with little technical background. Do not use internet slang, gaming slang, or trendy business expressions, for example "game-changer," "level up," "hack," "next-level," or "FOMO." Do not shorten a word or phrase that the source writes in full into an abbreviation or acronym, for example "two-factor authentication" into "2FA" or "information" into "info."

**Content type rule, omitted.** The rule depended on identifying marketing intent and on distinguishing short phrases from full sentences. Reason: intent and phrase length are subjective. Fix that passed: trigger only on grammatical sentence type with a visible marker for each case.

> This is marketing content. Keep the sentence type of the source in the target. Translate an imperative as an imperative that starts with a verb, for example "Start your free trial," not "A free trial is available." Translate a question as a question that ends with a question mark. Translate an exclamation as an exclamation that ends with an exclamation mark. Do not turn any of these into a statement.

**Patterns from Phrase's own eligibility results:**

- "Use active voice unless the actor is not important." Omitted: "not important" is a judgment.
- "Use a placeholder name when possible." Omitted: "when possible" and several acceptable rewrites.
- "Never translate a brand name." Omitted: the check does not know which words are brands. Route brand lists to the termbase. But "Never add a trademark symbol the source does not have" passed, because it checks a visible symbol.
- "Follow Chicago Manual of Style, with exceptions for em dashes, ampersands..." Omitted: the exceptions are not visible to the check. "Follow Chicago Manual of Style punctuation and capitalization" passed.

## Good rules derived from a reference (en-US → de-DE, sports article)

These come from the example in `references/example/`. All four were predicted suitable as AI checks and worked in the first test round.

> Put the names of collections and colors in German quotation marks every time they appear, also when the source writes them without quotation marks, for example "„Showtime“-Kollektion," not "Showtime-Kollektion." Join a German noun that follows the name with a hyphen after the closing mark, as in "„Breakout“-Kollektion."

> When the source puts a year before the name of a product collection, write the year in parentheses after the name, for example "„Tricks“-Kollektion (2014)" for "2014 Tricks collection." Do not write "aus dem Jahr 2014" or "von 2014" after the name.

> Do not form a genitive with "-s" from a brand name. Use "von" and the brand name after the noun, for example "die legendäre Kollektion von Puma," not "Pumas legendäre Kollektion."

> Do not use the English loanwords "Look," "Statement," "Twist," and "Highlight" in the target, also not when the source has the English word. Use "Erscheinungsbild," "Aussage," "Note," and "Höhepunkt." Keep English words that are part of a product, collection, or color name, for example "Poison Pink."

## Do not overfit

A rule must describe a pattern that will repeat in other documents of the same content group. It must not describe one sentence. Test: would this rule still make sense on a different page from the same client? If not, it is a one-off or a termbase item. The best protection is a test on a second document that was not used to derive the rules.

## Do not encode reference errors

A rule that copies a reference error brings the translation closer to the reference, but it makes the translation worse. When the reference does something inconsistent (two forms of the same thing) or clearly wrong, ask the user which form the rule should follow, or follow the majority pattern and say so.
