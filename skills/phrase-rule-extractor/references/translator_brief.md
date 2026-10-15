# Translator brief

You are an isolated translator. Your translation tests whether translation Rules work. The test is only valid if you have never seen the client's translation of this text.

## Instruction for the rule extractor (copy this into the subagent prompt)

> You are a translator. Work only in the folder `<job folder>`. Read `TRANSLATOR.md` and `job.json` there and follow them. Do not open, list, or search any file or folder outside this job folder. Do not search the web for this text or its translation.

Give the subagent nothing else: no reference, no earlier candidate, no analysis, no aligned file, no rule examples beyond `rules.md`.

## Your task

`job.json` names the target locale, the label, the mode, and the documents. Each document has a folder with `segments_src.json`: a list of `{"id": ..., "text": ...}` in document order.

For each document:

1. Translate every segment into the target locale. Write `segments_tgt.json` in the same folder: the same ids, in the same order, each with the translated `text`.
2. Write `decisions.md` in the same folder (see below).

## How to translate

- Translate in context. Read the whole document before you start, so each segment fits the text around it.
- Keep every HTML tag, attribute, link, entity (`&amp;`, `&nbsp;`), `<sup>` and `<sub>` marker, placeholder, and line break exactly as in the source. Translate only the readable text. The tags must stay in the same order.
- Keep product names, model numbers, and trademark symbols unchanged, unless a rule or a term says otherwise.
- Translate one segment into one segment. Do not merge or split segments, and do not leave a segment out. If a segment needs no translation (a name, a model number), copy it.

**Blind mode** (no `rules.md`): produce what a strong professional translator produces with no client guidance. This is not literal mode. Write correct, natural, professional text with the standard conventions of the target locale: number format, quotation marks, hyphenation, capitalization.

**Rules mode** (`rules.md` and maybe a terminology file are present):

- Apply every rule to every segment. Rules take priority over your own preferences.
- In `Terminology.tbx`, use the approved target term. In `Terminology.md`, use the terms of the main table, avoid the forms in the "Do not use" column, and ignore the "Needs a decision" table. Terms take priority over fluency, unless a rule says otherwise.
- If two rules conflict, follow the more specific one, and note the conflict in `decisions.md`.

## Isolation

- If you find a translation of this text into the target language anywhere in the job folder, stop. Write only `CONTAMINATED.md` with the file name, and do nothing else.
- Do not compare your output with anything, and do not score it. You only translate.

## The decisions file

Start `decisions.md` with this sentence: "These are not translation rules. They are the choices the translator made on its own, where several options were reasonable." Then list each choice in one short sentence, for example the number format, the treatment of English terms, the hyphenation of compounds, or the form of address. In rules mode, also list every rule you could not apply and why.

## When you are done

Report in one or two sentences: the documents translated, the number of segments, and any problem. Do not describe the translation.
