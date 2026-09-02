# Estimation extraction prompt (mirrors the platform extractor)

Use this prompt to **estimate how many Rules a style guide will spawn**. It is the
inclusive extractor the platform actually runs, so applying it (or counting the way it
would) gives a realistic prediction. It deliberately errs on inclusion and does **not**
consolidate restatements — so a guide with a cheat sheet or repeated rules will
estimate high, which is exactly what you want the user to see before choosing a split
strategy.

> This is different from `extraction-prompt.md`, which is an *optional, consolidating*
> prompt you might adopt downstream to reduce counts. For estimation, always use the
> inclusive prompt below.

```
You are a localization quality expert. I will share a translation style guide, and your task is to extract the requirements that translations must satisfy — covering tone, style, register, terminology, formatting, voice, and any other guidance on how the translation should read or feel for its audience. Also extract any examples that illustrate the requirements.
Include any rule the style guide expresses, even subjective or hard-to-measure ones (e.g. "the translation should be funny", "the tone should feel warm"). Err on the side of inclusion.
For each requirement, include all supporting excerpts copied verbatim from the style guide. If the guidance is split across multiple passages, list each as a separate excerpt.
If there are examples in the style guide that illustrate the requirement, include those as well, again copying verbatim all relevant passages. If the example is integrated with the rule text, you can include it as part of the style_guide_excerpt instead of illustrative_examples_excerpt, but make sure to still fill out the requirement field with a concise statement of the requirement. If the example is in the style_guide_excerpt, do not repeat it again in the illustrative_examples_excerpt.
Aim to cover the style guide as thoroughly as possible — extract every rule the guide expresses, but do not invent requirements that are not supported by the text.
The excerpts across requirements must be disjoint: no passage from the style guide may be cited under more than one requirement, and excerpts from different requirements must not overlap (not even partially).
- If a passage covers multiple aspects, assign it to the single requirement it fits best, or split the passage at sentence boundaries so each piece appears under exactly one requirement.
- Before finalizing, check that every excerpt appears in only one requirement and that no two excerpts share any text.
**The requirement statements should be in English.**
```
