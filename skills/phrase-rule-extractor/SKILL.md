---
name: "phrase-rule-extractor"
description: "Use this skill to derive translation Rules that also work as Phrase AI checks. Share two sets of documents: the source files and your reference translations. Any common file format works. The skill makes its own blind AI translation and compares it with your reference. From the differences, it writes the Rules and a TBX file for your Term Base. Then it tests and improves the Rules over up to three rounds. Use it also when someone asks to compare a translation with a reference or to create or reverse-engineer a style guide."
---

# Rule extractor

Find the Rules that turn a default translation into the client's preferred translation.

The method: a translator that has never seen the reference produces a candidate. You compare the candidate with the reference. The differences show what the reference translator does beyond a good default translation. Repeated differences become rules. Then an isolated translator translates again with the rules, and you check, rule by rule, whether the differences are gone.

This skill uses no scores such as chrF, BLEU, or TER. The evidence is the differences themselves: which ones a rule explains, and which ones disappear in the next round.

More documents give better rules. A pattern that appears in three documents is a rule. A pattern that appears in one sentence of one document is often a one-off.

**Recommendation: use three or more documents per content group.** A content group is one kind of content, for example case studies, product pages, or UI strings. With one or two documents, most rules rest on one or two examples. The rules are then less reliable, and two runs on the same files can give very different rule sets. Four or more documents are best: three to derive the rules, and one more to test them (see step 7).

## Script mode and native mode

The skill has Python scripts for the mechanical work: reading file formats, pairing segments, preparing isolated translation jobs, counting characters, building the difference view, and writing the TBX file. Scripts are faster, cheaper in tokens, and give the same result on every run. Always try them first.

**At the start of every run, check the environment once:**

```bash
python3 scripts/check_env.py
```

Choose the mode from the result:

- **MODE: script.** Use the scripts as described in this file. Say nothing about the mode to the user.
- **MODE: partial.** Python works, but some format libraries are missing. Try to install them with the `pip install` command the check prints. If the install fails, use the scripts for everything else, and read only the affected file formats in native mode (section "Read and pair the files" in `references/native_mode.md`).
- **The check cannot run** (no shell tool, no Python 3, or the command fails), or it prints **MODE: native.** Use native mode for the whole run. Follow `references/native_mode.md` for every step that names a script.

**A script can also fail later**, for example with an error on one file. Read the error first. Fix the cause if it is simple (a wrong path, a missing argument) and run the script again once. If it fails again, do that step in native mode and continue with the scripts for the other steps.

**Tell the user every time you leave script mode.** Do it once, at the moment you switch, in two or three plain sentences: what does not work, which steps you now do without scripts, and what changes for them. Example: "Python is not available in this environment, so I will do the comparison and the terminology files myself. The result is the same, but it takes longer, character counts are approximate, and the difference view is a Markdown table instead of an interactive page." Repeat the note in the report.

Native mode keeps the method and the two rules below unchanged. In particular, you still never translate. The blind and rules translations still come from an isolated subagent or from the user.

## Two rules you must never break

**You never translate.** You have seen the reference, so any translation you produce drifts toward it. That would make the test meaningless. Every candidate translation must come from an isolated translator: a session or subagent that has received only the source file, the target locale, the rules file, and optional termbase entries.

**The reference never leaves your side.** When you hand work to a translator, send the source, the locale, the rules file, and the termbase entries. Never send the reference, the aligned comparison, or the analysis. Rule examples are the one exception: they may quote a few words from the reference, because a rule needs a concrete example. Keep each example to a short fragment (a number, a term, a compound). Never quote a whole sentence, because that leaks the reference into the test.

## Inputs

The user may give one document or many. Each document has up to three files:

- Source file (any language), target locale.
- Reference translation: the canonical target the client wants.
- Candidate translation: a blind translation from an isolated translator. It is optional. When subagents are available, the skill produces it itself (see "Getting a translation"). Then the user needs to give only the source files and the reference files.

The files can have any format that `scripts/extract.py` reads: CMS JSON and other JSON, XLIFF (.xliff, .xlf, .mxliff, .sdlxliff), PO, CSV, TSV, XLSX, DOCX, DOC, ODT, RTF, PPTX, PPT, PDF, HTML, Markdown, TXT, SRT, and VTT. Other files are read as plain text. The three files of one document do not need the same format. For example, the source can be a DOCX file and the reference a PDF file. A bilingual XLIFF or PO file can serve as source and reference at the same time: list it in both places.
- Optional: the translator's decisions file (`*_translator-decisions.md`). It lists the choices the translator made on its own. Use it to find differences faster: each listed choice that differs from the reference is a likely rule candidate. It is not a set of rules.
- Optional: existing rules, existing termbase entries, the client's category table.
- Recommended: three or more documents from the same content group, and ideally a fourth one that you do not use to derive rules. You use it only for the final test (see step 7).

## Getting a translation

Pick the first option that is available:

1. **Subagents available (Cowork, Claude Code): automatic.** You prepare an isolated job folder, and a subagent translates it. The user does nothing.
   ```bash
   python3 scripts/translation_job.py prepare --manifest work/pairs.json --label blind --locale <de-DE> --jobs work/jobs/
   ```
   For a rules round, add `--rules work/rules_vN.md --terms <outputs>/Terminology.tbx` and use the label `rules-vN`. The job folder holds only the source segments, the translator brief, and (in rules rounds) the rules and the terms. The script stops if any reference text ends up in the folder.

   Then spawn one subagent for the job folder. For more than about 300 segments, spawn one subagent per document folder, in parallel. Give each subagent only the instruction from `references/translator_brief.md`, with the folder path filled in. Do not add anything from the reference, the analysis, or an earlier candidate. Do not translate any segment yourself, also not to fix a gap: send it back to the subagent.

   When the subagents are done, build the candidates:
   ```bash
   python3 scripts/translation_job.py collect --manifest work/pairs.json --label blind --jobs work/jobs/ --out work/candidates/
   ```
   This writes one candidate per document, copies each decisions file next to it, and updates `work/pairs.json` ("mt" is the new candidate, "prev" the last one). If it reports missing ids or changed HTML tags, send those segments back to a subagent with the same instruction. If a subagent wrote `CONTAMINATED.md`, stop and tell the user.
2. **Phrase:** the user loads the rules into the content group and runs AI translation. This is the best test, because it is where the rules will run in production.
3. **Claude.ai chat without subagents:** tell the user to open a new chat, upload only the source files and the rules file, ask for a translation of every file into the locale in its original format, and upload the results here. Ask the user to rename files so a new upload does not overwrite an existing one with the same name (for example, add `_EN`, `_REF`, `_blind`, `_rules-v1`).

With options 2 and 3, translate all source files in the same run and with the same rules version. The candidate file name must contain the run label (`blind`, `rules-v1`, `rules-v2`), so `pair_files.py` can tell it apart from the reference.

To check whether subagents are available, look at your tools. If you have a tool that starts a subagent or a task (for example "Task" or "Agent"), use option 1. If you do not, say so to the user and offer options 2 and 3.

## Workflow

### 1. Check and pair the inputs

Copy all uploads to `work/in/`. Then let the script propose which files belong together:

```bash
python3 scripts/pair_files.py work/in/ --source-lang <en> --target-lang <de> --out work/pairs.json
```

It reads every file, finds its language from the content and the file name, and groups the files into documents by file name (`world_cup_EN.txt`, `world_cup-de.txt`, and `world_cup_de-DE_blind.txt` become one document). Files with unrelated names are paired by shared numbers, model names, and URLs. It prints a reason for every guess and lists the problems: duplicate uploads, an unclear language, a document with two possible references, a scanned PDF with no text.

Show the user the proposed documents in a short table (document, source, reference, candidate) and ask them to confirm it.

Check the number of documents per content group. If the documents look like different kinds of content (for example case studies and product pages), ask the user whether they belong to one content group. Rules are derived per content group. If a content group has fewer than three documents, tell the user once, in two or three plain sentences: the rules will rest on few examples, they will be less reliable, and a new run can give a different rule set. Ask whether more documents from the same content group are available. If not, continue with what you have. Do not stop the run for this. Fix `work/pairs.json` by hand when a guess is wrong. If two uploads have the same name, the second overwrote the first: ask for a re-upload with a new name. If a PDF has no text layer, ask for an OCR version or for the original file.

To check what the script reads from a single file, run `python3 scripts/extract.py <file> --side src|tgt`.

**Estimate the size of the run.** Every round translates and compares the full text, so the cost grows with the size of the files. After the user confirms the pairing, run:

```bash
python3 scripts/estimate.py --manifest work/pairs.json
```

It prints the words and pages per document, an estimate of tokens and time for a full run, and a size level. Act on the level:

- **SIZE: OK** (up to about 5,000 source words, or 10 pages): continue without comment.
- **SIZE: NOTE** (about 5,000 to 15,000 words): show the user the estimate in one or two sentences, then continue.
- **SIZE: LARGE** (more than about 15,000 words, or a comparison too large to read well in one chat): stop and tell the user, in plain words, that processing everything will use a large part of their usage limit and take a long time. Explain that rules come from repeated patterns, not from volume, so a sample gives almost the same rules. Propose a sample of about 2,500 words (5 pages) per document, and ask before you continue.

When the user agrees to a sample, run:

```bash
python3 scripts/estimate.py --manifest work/pairs.json --sample 2500 --holdout work/holdout.json
```

This writes the sample into `work/pairs.json`: one block of consecutive segments from the start of each document. `translation_job.py` and `align.py` then use only these segments. It also writes `work/holdout.json`: the next block of each document, for the final held-out test in step 7. If the user wants a different part of a document, change its `"sample"` range by hand. With `--clear-sample`, the full documents are used again. Name the sample size in the report.


If a document has no candidate and subagents are available, get the blind translation now with option 1 of "Getting a translation". Do this before you read any reference text in detail.

### 2. Align

```bash
python3 scripts/align.py --manifest work/pairs.json --label blind --out work/
```

This writes `work/blind_segments.json` (all documents, for the difference view in step 5) and `work/blind_aligned.md` (only the segments with differences, grouped by document, in document order). For a single document you can also use `--src`, `--mt`, `--ref`, and `--doc` instead of a manifest.

Keyed formats (CMS JSON, XLIFF, PO, spreadsheets) are paired by key. Running text (PDF, DOCX, PPTX, HTML, Markdown, TXT) is paired by content and order. One paragraph may pair with two, because translators split and join paragraphs. Rows marked CHECK are pairings the script is not sure about. Read them first. A wrong pairing creates false differences. If a document has many CHECK rows, look at the extracted text with `extract.py` and fix the cause, for example a PDF whose paragraphs were rebuilt wrongly.

Read the aligned file document by document. Note in which documents each difference appears. A difference that repeats across documents is strong evidence for a rule. Small systematic differences (number format, hyphens, symbols) also count, even when the rest of the segment is the same.

### 3. List and sort every difference

For each difference, note the segment, the source text, the candidate text, and the reference text. Sort it into one group:

- **Rule candidate:** a pattern that repeats, or one clear convention (a number format, a date format, a placeholder treatment).
- **Termbase item:** a term that is always translated the same way: a single term choice, a fixed UI, navigation, or menu label. It goes into the terminology files (`Terminology.tbx` for import, `Terminology.md` for review), never into a rule (see the Terminology section in `references/rule_categories.md`). The form the reference does not use goes into `avoid`. It appears only in `Terminology.md`, never in the TBX file.
- **Reference error:** a grammar mistake, a dropped hedge, a misplaced symbol, a spacing error, an encoding artifact. Never encode these.
- **One-off:** a different but equally good wording with no pattern. Ignore.
- **File handling:** line endings, encoding. Report only.

Note where the reference is inconsistent with itself (for example, a menu label translated in one footnote and left in English in another, or two translations of the same term). With several documents, also compare the documents with each other: the references may come from different translators. These are questions for the user.

For each rule candidate, count the documents in which it appears. Report this count with the rule. A rule candidate that appears in only one document of several is weak evidence. Say so, and ask the user before you keep it.

### 4. Write rules per category

Read `references/rule_categories.md` and `references/rule_writing.md` before writing. Go through every category. Create a rule only when the differences give evidence for it. For each skipped category, write one sentence on why.

Write each rule to work both as a translation instruction and as an AI check: visible triggers, source-relative where possible, concrete examples, no judge instructions, 450 characters or fewer, plain English. Then lint:

```bash
python3 scripts/check_rules.py work/rules_v1.md
```

Fix every rule that is over the limit. Rewrite every warning unless you can explain why it is a false positive (for example, "natural" inside a quoted example).

Then write the terminology file. Add `source_term` and `target_term` (and optionally `avoid` and `note`) to every termbase annotation in `work/annotations.json` (see step 5). If the reference uses more than one form for the same source term with no clear majority, set `"status": "decide"` and list the forms in `variants`. If one form is used in most places and another only once, use the majority form as `target_term` and mention the other form in the `note`. Then run:

```bash
python3 scripts/write_terminology.py --annotations work/annotations.json --tbx <outputs>/Terminology.tbx --out <outputs>/Terminology.md
```

This writes two files from the same data:

- `Terminology.tbx` is the import file for the Phrase Term Base. It contains only approved terms: one source term and one approved target term per entry, with status Approved, the preferred flag, and the note. It never contains forbidden forms. Phrase imports every term in a TBX file as a separate term, so a forbidden form in the TBX file shows up as an extra approved translation.
- `Terminology.md` is a readable copy for review. It starts with a fixed preface that says it contains no rules. Its "Do not use" column lists the forms from `avoid`. It also holds the "Needs a decision" table. Terms that need a decision stay out of the TBX file until the user chooses one form. Then set `target_term`, remove `"status": "decide"`, and run the script again.

Then remove any forbidden forms that are still in the TBX file. Older versions of `write_terminology.py` wrote them. Run this every time after the script:

```bash
python3 -c "import sys,xml.etree.ElementTree as E;p=sys.argv[1];t=E.parse(p);[ls.remove(g) for ls in t.getroot().iter('langSet') for g in list(ls.findall('tig')) if any(n.get('type')=='forbidden' for n in g.findall('termNote'))];t.write(p,encoding='UTF-8',xml_declaration=True)" <outputs>/Terminology.tbx
```

Then check that every target language set in the TBX file holds exactly one term. If not, fix it before delivery.

Language codes are written in Phrase style (`en_us`, `de_de`) from the locales in the annotations. Phrase skips a language that is not configured on the term base, without an error. Ask the user which codes the term base uses if it is not clear, and pass `--source-lang` and `--target-lang` when they differ (for example `--target-lang de`). Check that no rule repeats a term from these files, and that no rule names them.

Write `avoid` forms with care. A form in `avoid` must never match part of a correct word. For example, do not put "Schuh" in `avoid` for "boot" when "Fußballschuh" is the correct term. A translator may then avoid the correct compound as well.

Then predict the AI check verdict with `references/eligibility_prompt.md`. This is the prompt Phrase uses. Run it in isolation, never in your own context:

- **Subagents available:** spawn one subagent per rule with only the prompt and the rule text.
- **Claude.ai:** ask the user to open a new chat, paste the prompt, and paste the rules with the instruction "Judge each rule separately." The user brings back the verdicts.

For every rule judged not suitable, read the explanation, then rewrite the rule with the fixes in `references/rule_writing.md` and judge it again. If a rule cannot pass but is still useful for translation (for example, "termbase terms take precedence over fluency"), keep it as **Rule only, AI check off**, and say why in the report.

### 5. Show the differences first

Before you show the rules, show the user where they come from. Build an interactive side-by-side view of the blind translation and the reference: differences are highlighted as on GitHub (red for text only in the blind translation, green for text only in the reference), and hovering over a difference shows the rule, termbase item, or reference error behind it.

1. Write `work/annotations.json`. It links each difference to its explanation. With several documents, add `"doc": "<document name from pairs.json>"` to an annotation that belongs to one document only. The format is described at the top of `scripts/make_diff_view.py`, and `references/example_annotations.json` is a complete example from the sports article in `references/example/`. In short: a list of rules (`id`, `category`, `text`) and a list of annotations. Each annotation has a `type` (`rule`, `termbase`, `reference_error`, `one_off`, `file_handling`), termbase annotations also have the term fields from step 4, a short fragment of the blind text (`mt`) and/or of the reference text (`ref`), and a `note` in one plain sentence. Add `"rule": "R4"` to any annotation that a rule explains, also to a reference error that the rule prevents.
2. Generate the view and list what is still unexplained:
   ```bash
   python3 scripts/make_diff_view.py --segments work/blind_segments.json --annotations work/annotations.json --out <outputs>/<name>_diff_view.html --list-unclassified
   ```
   The script picks segments up to 2,000 characters per side for each document, preferring segments that show rules not shown yet. With several documents, each document gets its own section.
3. Label every listed difference. For segments with many small wording differences, add one annotation with `"scope": "segment"` and a fragment that identifies the segment, for example: "Other differences in this segment are one-off wording choices." Repeat until the script reports 0 unclassified differences.
4. Present the HTML file first. Then present the rules, the terminology files, the reference errors, and the questions.

### 6. Ask only what decides a rule's direction

Before the first test round, present a short list: the draft rules (with category and character count), the termbase items, the reference errors, and the open questions. Ask only the questions where the answer changes a rule (for example, "The reference hyphenates English names two ways. Should the rule follow the majority?"). Then hand off the next translation.

### 7. Test rounds (up to three)

For each round N:

1. Write the rules to `work/rules_vN.md` in the final file format: one rule per paragraph, an empty line between rules, no headers, no numbers, no character counts.
2. Get a translation of every source file with these rules from an isolated translator (see "Getting a translation"). Send `Terminology.tbx` along as the termbase entries (in Phrase: import it into the term base of the project), because in production the Term Base runs together with the rules. Label it `rules-vN`.
3. With option 1, `collect` already updated `work/pairs.json`. Otherwise, set `"mt"` to the new file and `"prev"` to the candidate of the last round. Then align again:
   ```bash
   python3 scripts/align.py --manifest work/pairs.json --label rules-vN --out work/
   ```
   The aligned file now has a "Previous candidate" column. It shows per segment what changed since the last round.
4. Check every rule against the differences it was written for, in every document. Mark each rule as **worked** (the differences are gone), **partly worked** (some are gone, or only in some documents), **no effect**, or **caused a regression** (a segment that was right before and is now wrong).
5. Tune: make "no effect" rules more concrete (a better example, a clearer trigger), split rules that only partly worked, and remove or narrow rules that caused regressions. Lint again, and run the eligibility check again for every changed rule.

If the translator is automatic (subagent), run the rounds without asking in between, but ask the questions from step 6 before the first round. If the user must run the translator by hand, show the changes after each round and ask whether to continue.

Stop when one of these is true:

- All remaining differences are termbase items, reference errors, or one-offs.
- No rule changed from "no effect" or "partly worked" to "worked" compared with the previous round.
- Three rounds are done.

**Overfitting check.** If you used a sample, run the final test on the held-out blocks in `work/holdout.json`: prepare, translate, and align them with `--manifest work/holdout.json` and the final rules. Otherwise, keep one document out of the analysis when the user gives four or more, so at least three remain for deriving the rules. With three or fewer, ask the user whether one more document is available. Run one final translation of the held-out document with the final rules and compare it with its reference. List which rules worked there too. If a rule helped the analyzed documents but not the held-out one, it probably describes a sentence, not a pattern. Name it.

### 8. Deliver

Phrase takes Rules from a style guide: the user uploads a file in the Style Guide section of a content group, and Phrase extracts one Rule per paragraph. So the final Rules are delivered as a style guide file. The file holds the Rules and nothing else. Never add a title, an instruction, or a note to it, because Phrase would extract that text as one more Rule. Upload instructions go into the report and into your final message.

Create five files in the outputs folder and present all of them, the difference view first:

- `<name>_diff_view.html`: the difference view from step 5, regenerated with the final rule texts, so the tooltips show the rules as delivered.
- `Style Guide.md`: the final Rules, ready for upload in the Style Guide section. One rule per paragraph, an empty line between rules, no headers, no numbers, no character counts, no other text.
- `Terminology.tbx`: every approved term and nothing else, ready for import into the Phrase Term Base, regenerated from the final annotations. One approved target term per entry. No forbidden forms.
- `Terminology.md`: the readable copy with the "Do not use" column and the "Needs a decision" table. Tell the user that the "Needs a decision" terms are not in the TBX file yet, and offer to regenerate it once they choose.
- `rules_<locale>_report.md`: the report. Start it with a short section "How to use these files", in this form:

  > Phrase takes Rules from a style guide, so the Rules are delivered as a style guide file.
  > 1. Upload `Style Guide.md` in the Style Guide section and link it to the content group. Phrase extracts each paragraph as one Rule.
  > 2. Import `Terminology.tbx` into the Term Base of the project.
  > 3. Review the "Needs a decision" table in `Terminology.md`. These terms are not in the TBX file yet.

  Then list the documents used (and the held-out document), a note if a content group had fewer than three documents, each rule with its category, character count, the number of documents it appears in, predicted AI check verdict, and test result per round, the categories with no rule and why, the number of terms in `Terminology.tbx`, the language codes used, the terms that need a decision, the reference errors, and the remaining gaps.

Write the report in plain English: one idea per sentence, short sentences, technical terms kept, no idioms.

End your final message with the same three upload steps, in short form.

## Example of the difference analysis

A complete worked example is in `references/example/`: an English article (`world_cup_2026_en.txt`), the client's German reference (`world_cup_2026_de.txt`), the final style guide file (`Style Guide.md`), the terminology, and the annotations. Some differences from it:

Source: "the Showtime pack"
Candidate: "das Showtime-Pack"
Reference: "die „Showtime“-Kollektion"
Group: rule candidate (Editorial). The reference puts collection names in German quotation marks every time, also where the source has none. "Pack" to "Kollektion" is a separate termbase item.
Rule: "Put the names of collections and colors in German quotation marks every time they appear, also when the source writes them without quotation marks, for example "„Showtime“-Kollektion," not "Showtime-Kollektion.""

Source: "a modern, high-energy twist" / "cultural statements" / "signature look"
Candidate: "Twist" / "Statements" / "Look"
Reference: "Note" / "Aussagen" / "Erscheinungsbild"
Group: rule candidate (Fluency). The pattern repeats four times: the reference never uses these English loanwords.

Source: "was almost comedic"
Candidate: "war beinahe komisch"
Reference: "war komisch"
Group: reference error (dropped hedge). Do not encode.

Source: "the Future, Ultra, and King silhouettes"
Candidate: "Silhouetten"
Reference: "Modellreihen"
Group: termbase item. "Modellreihe" goes into the TBX file. "Silhouette" goes into `avoid`, so it appears only in the "Do not use" column of `Terminology.md`.
