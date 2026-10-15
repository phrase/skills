# Native mode: the workflow without scripts

Use this file only when a script cannot run (see "Script mode and native mode" in SKILL.md). The method stays the same: blind translation, comparison, rules, terminology, test rounds. Only the mechanical steps change. You do them yourself, and you follow the formats below exactly, so the result looks the same as in script mode.

Native mode costs more tokens and is less exact. Keep the work small: one document at a time, and only the changed segments in your notes.

Keep working notes in a `work/` folder in your working directory, as in script mode. They are not delivered. Two notes replace the script data files:

- `work/blind_aligned.md`: the comparison table (see "Compare" below).
- `work/terms.md`: one line per termbase item while you sort the differences, with source term, target term, forms to avoid, note, and status (approved or decide). The terminology files are written from this list.

Each section below names the SKILL.md step it replaces.

## Read and pair the files (SKILL.md step 1; replaces extract.py and pair_files.py)

Read each file with your file tools.

- Plain text, Markdown, HTML, JSON, CSV, XLIFF, PO, SRT, VTT: read them directly. In JSON, take the translatable string values and keep their keys. In XLIFF, take `<source>` and `<target>` per `<trans-unit>` or `<unit>`, and keep the id. In PO, take `msgid` and `msgstr`. In HTML, keep the tags inside each segment.
- PDF: read it with your file tool if it can read PDFs. If it cannot, ask the user for the text.
- DOCX, PPTX, XLSX, and other binary formats: you cannot read them reliably without code. Ask the user to save the file as plain text or to paste the text. Say which file it is.

A segment is one key (keyed formats) or one paragraph (running text). Number the segments in document order.

Pair the files by name: the same base name with a language marker (`_EN`, `-de`, `de-DE`) belongs to one document. A file with `blind` or `rules-v1` in the name is a candidate, not a reference. Show the user the table (document, source, reference, candidate) and ask them to confirm it, as in script mode.

## Estimate the size (SKILL.md step 1; replaces estimate.py)

Count the source words roughly: about 500 words per page. Use the same levels as in SKILL.md: up to about 5,000 words, continue; about 5,000 to 15,000 words, tell the user that the run will take long; more than about 15,000 words, propose a sample and ask first. Native mode reads every comparison in the chat, so be stricter than in script mode: above about 5,000 words, propose a sample of about 2 to 3 pages per document.

A sample is the first pages of each document. Use only these segments in every translation and comparison. Keep the next pages of each document for the final held-out test.

## Get a translation (SKILL.md "Getting a translation" and step 7; replaces translation_job.py)

The isolation rule does not change. Without the job folder, you put the source text into the subagent prompt yourself.

1. Build the prompt from three parts only: the text of `references/translator_brief.md` (the "Your task" section and everything after it), the target locale, and the numbered source segments. In a rules round, add the rules file text and the approved term list (source term and target term per line).
2. Before you send it, check the prompt yourself: it must contain no reference text, no aligned comparison, no analysis, and no earlier candidate. Rule examples are the only exception, and they must be short fragments.
3. Ask the subagent to answer with the numbered target segments, followed by the decisions section described in the brief.
4. Check the answer: the same number of segments, the same numbers, the same HTML tags in the same order. Send any missing or broken segment back to a subagent with the same prompt. Never fix a segment yourself.

Without subagents, use option 2 or 3 of "Getting a translation" in SKILL.md.

## Compare (SKILL.md steps 2 and 3; replaces align.py)

For keyed formats, pair segments by key. For running text, pair by order and content. When one paragraph matches two, write both in one row and mark the row CHECK.

Write `work/blind_aligned.md` in this format. List only the segments with differences:

```
| # | Check | Source | Candidate | Reference |
|---|---|---|---|---|
| 3 |  | Ahead of the tournament, ... | Vor dem Turnier präsentierte ... | Vor dem Turnier stellte ... |
```

Then read each row word by word. Note every difference, also small ones: quotation marks, hyphens, dashes, spaces, number formats. These small differences are easy to miss without a diff tool. Read each changed segment twice.

## Check the rules (SKILL.md step 4; replaces check_rules.py)

Count the characters of each rule. Count every letter, space, and punctuation mark. Count sentence by sentence, write down the count of each sentence, and add them up. This is more reliable than one count over the whole rule. Your count is approximate, so keep each rule at 420 characters or fewer. That gives a safety margin under the 450-character limit. Tell the user that the count is approximate, and that Phrase will reject a rule that is too long when they paste it in.

The AI check prediction does not change in native mode. It needs no script: run it in an isolated subagent, or ask the user to run it in a new chat, as SKILL.md step 4 says. Judge a rule yourself only when neither is possible. Then mark the verdict "self-judged" in the report.

Then check each rule for these words and fix them: "natural", "clear", "appealing", "when possible", "when appropriate", "if necessary", "consistently", "throughout", "on first use", and any file name such as `Terminology.tbx`.

## Show the differences (SKILL.md step 5; replaces make_diff_view.py)

The interactive HTML view needs the script. In native mode, write `<name>_differences.md` instead. Use one table per document:

```
| # | Source | Blind translation | Reference | Type | Explanation |
|---|---|---|---|---|---|
| 3 | the Showtime pack | das ~~Showtime-Pack~~ | die **„Showtime“-Kollektion** | Rule R1 | Collection names always get German quotation marks. |
| 5 | was almost comedic | ~~beinahe~~ komisch | komisch | Reference error | The reference drops the hedge "almost". |
```

Show only the changed words, with a few words of context. Use strikethrough for text only in the blind translation and bold for text only in the reference. When one span holds differences of several types (for example a rule and a termbase item), write one row per type for the same span. Every difference gets a row with a type: Rule (with the rule id), Termbase item, Reference error, One-off, or File handling. Repeat until no difference is left without a type.

Present this file first, as in script mode.

## Write the terminology files (SKILL.md step 4; replaces write_terminology.py)

Write `Terminology.md` in this format:

```
**Terminology.** These are deterministic terms to use or avoid, pulled out for import into the platform's Term Base — not Style Guide Rules.

| Source term (en-US) | Target term (de-DE) | Do not use | Note |
| --- | --- | --- | --- |
| silhouette | Modellreihe | Silhouette | |

**Needs a decision.** The reference translates these source terms in more than one way. Choose one target term for each before you import this file.

| Source term (en-US) | Forms found in the reference | Note |
| --- | --- | --- |
```

Write `Terminology.tbx` from the main table only. Use exactly this structure. Add one `termEntry` per term and number the ids `c1`, `c2`, and so on. Write one target term per entry. Never write a "Do not use" form or a "Needs a decision" term into the TBX file.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<martif type="TBX" xml:lang="en">
  <martifHeader>
    <fileDesc>
      <sourceDesc>
        <p>Terms derived from a reference translation for Term Base import.</p>
      </sourceDesc>
    </fileDesc>
  </martifHeader>
  <text>
    <body>
      <termEntry id="c1">
        <langSet xml:lang="en_us">
          <tig>
            <term>silhouette</term>
            <termNote type="status">Approved</termNote>
          </tig>
        </langSet>
        <langSet xml:lang="de_de">
          <tig>
            <term>Modellreihe</term>
            <termNote type="preferred">True</termNote>
            <termNote type="status">Approved</termNote>
          </tig>
        </langSet>
      </termEntry>
    </body>
  </text>
</martif>
```

Escape `&` as `&amp;`, `<` as `&lt;`, and `>` as `&gt;` inside terms and notes. Add `<note>...</note>` after the status line of the target term, and only when the term has a note. Use the language codes the user's Term Base uses. Phrase style is `en_us` and `de_de`.

After writing, read the file once more and check: every `termEntry` has two `langSet` elements, every target `langSet` has exactly one `tig`, and every tag is closed.

## Test rounds and delivery (SKILL.md steps 7 and 8)

Run the test rounds as in SKILL.md, with "Get a translation" above for each translation and "Compare" for each comparison. Deliver the same files as in script mode (including `Style Guide.md` and the "How to use these files" section in the report), with `<name>_differences.md` in place of the HTML view. At the top of the report, repeat the note you gave the user when you switched modes. Say which steps ran without scripts, that character counts are approximate, and that the difference view is a Markdown table.
