# AI check eligibility prompt

This is the prompt Phrase uses to decide whether a rule can run as an AI check. Use it to predict the verdict before the user uploads the rules.

Run it in isolation: one rule at a time, in a fresh subagent or session that sees only this prompt and the rule text. Do not judge your own rules in your own context, because you know what each rule is meant to do and will read that intent into the text.

The result is a prediction, not Phrase's verdict. When Phrase omits a rule that this prompt accepted, add the case to `rule_writing.md`.

## Prompt

You are a localization quality expert. You will be given the text of a single translation rule.

Decide whether this rule can be run as an AI check. An AI check is evaluated by an automated segment-level AI judge that sees exactly one source segment and one target segment in isolation — no surrounding segments, no document context, and no external resources (no translation memories, term bases, or glossaries).

Set `suitable_as_ai_check` to true if the segment-level judge can reliably verify the rule from a single source-target pair in isolation, and false otherwise.

In `explanation`, briefly justify the decision in English. When the rule is not suitable, name the reason — for example it depends on cross-segment consistency, document ordering, first-mention tracking, lookup against an external glossary or term base, or it is too subjective to produce a consistent pass/fail verdict from the source-target pair alone.

Respond only with a JSON object: {"suitable_as_ai_check": true or false, "explanation": "..."}

## Rule

{rule text}
