#!/usr/bin/env python3
"""Write the terminology files from the termbase annotations.

Usage:
  python3 write_terminology.py --annotations work/annotations.json --out <outputs>/Terminology.md
      --tbx <outputs>/Terminology.tbx [--source-lang en_us] [--target-lang de_de]

Terminology.tbx  the import file for the Phrase Term Base. Only approved terms: one source term and
                 one approved target term per entry. Uses <termNote type="status">Approved,
                 <termNote type="preferred">, and <note>. Forbidden forms ("avoid") are never
                 written to the TBX file, because Phrase imports them as extra terms.
Terminology.md   a readable copy for review, plus the "Needs a decision" table. Terms that need a
                 decision are not in the TBX file until the user chooses one form.

Language codes: by default the locales from the annotations are written in Phrase style
(en-US -> en_us). Phrase skips a language that is not configured on the term base, without an
error. If the term base uses plain codes such as "de", pass --target-lang de.

Reads every annotation with "type": "termbase" that has a "source_term". Fields:
  source_term   term in the source language (required)
  target_term   approved target term (required unless status is "decide")
  avoid         list of target forms not to use, optional. Shown only in the "Do not use"
                column of Terminology.md. Never written to the TBX file.
  status        "approved" (default) or "decide" (the reference uses several forms)
  variants      list of the forms found in the reference, for status "decide"
  note          one plain sentence, optional

Entries are merged by source term. Both files are for the Term Base only. No rule may name them.
"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

PREFACE = ("**Terminology.** These are deterministic terms to use or avoid, pulled out for import "
           "into the platform's Term Base — not Style Guide Rules.")


def cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def phrase_lang(locale):
    return (locale or "").strip().lower().replace("-", "_")


def write_tbx(path, approved, src_lang, tgt_lang):
    martif = ET.Element("martif", {"type": "TBX", "xml:lang": src_lang.split("_")[0] or "en"})
    header = ET.SubElement(martif, "martifHeader")
    fd = ET.SubElement(ET.SubElement(header, "fileDesc"), "sourceDesc")
    ET.SubElement(fd, "p").text = "Terms derived from a reference translation for Term Base import."
    body = ET.SubElement(ET.SubElement(martif, "text"), "body")
    for i, (src, t) in enumerate(sorted(approved.items(), key=lambda x: x[0].lower()), 1):
        entry = ET.SubElement(body, "termEntry", {"id": f"c{i}"})
        ls = ET.SubElement(entry, "langSet", {"xml:lang": src_lang})
        tig = ET.SubElement(ls, "tig")
        ET.SubElement(tig, "term").text = src
        ET.SubElement(tig, "termNote", {"type": "status"}).text = "Approved"
        lt = ET.SubElement(entry, "langSet", {"xml:lang": tgt_lang})
        tig = ET.SubElement(lt, "tig")
        ET.SubElement(tig, "term").text = t["target_term"]
        ET.SubElement(tig, "termNote", {"type": "preferred"}).text = "True"
        ET.SubElement(tig, "termNote", {"type": "status"}).text = "Approved"
        if t["notes"]:
            ET.SubElement(tig, "note").text = " ".join(t["notes"])
    xml = minidom.parseString(ET.tostring(martif, encoding="unicode")).toprettyxml(indent="  ", encoding="UTF-8")
    open(path, "wb").write(xml)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotations", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tbx", required=True)
    ap.add_argument("--source-lang")
    ap.add_argument("--target-lang")
    a = ap.parse_args()

    meta = json.load(open(a.annotations, encoding="utf-8"))
    src_loc = meta.get("source_locale", "source")
    tgt_loc = meta.get("target_locale", "target")
    terms = {}
    for ann in meta.get("annotations", []):
        if ann.get("type") != "termbase" or not ann.get("source_term"):
            continue
        key = ann["source_term"].strip()
        t = terms.setdefault(key, {"target_term": "", "avoid": [], "status": "approved",
                                   "variants": [], "notes": []})
        if ann.get("target_term"):
            t["target_term"] = ann["target_term"].strip()
        for x in ann.get("avoid", []):
            if x not in t["avoid"]:
                t["avoid"].append(x)
        if ann.get("status") == "decide":
            t["status"] = "decide"
        for x in ann.get("variants", []):
            if x not in t["variants"]:
                t["variants"].append(x)
        if ann.get("note") and ann["note"] not in t["notes"]:
            t["notes"].append(ann["note"])

    missing = [k for k, t in terms.items() if t["status"] == "approved" and not t["target_term"]]
    if missing:
        sys.exit(f"Approved terms without a target term: {missing}")

    approved = {k: t for k, t in terms.items() if t["status"] == "approved"}
    decide = {k: t for k, t in terms.items() if t["status"] == "decide"}
    lines = [PREFACE, ""]
    lines += [f"| Source term ({src_loc}) | Target term ({tgt_loc}) | Do not use | Note |",
              "| --- | --- | --- | --- |"]
    for k in sorted(approved, key=str.lower):
        t = approved[k]
        lines.append(f"| {cell(k)} | {cell(t['target_term'])} | {cell(', '.join(t['avoid']))} | {cell(' '.join(t['notes']))} |")
    if decide:
        lines += ["", "**Needs a decision.** The reference translates these source terms in more than one way. "
                      "Choose one target term for each before you import this file.", "",
                  f"| Source term ({src_loc}) | Forms found in the reference | Note |", "| --- | --- | --- |"]
        for k in sorted(decide, key=str.lower):
            t = decide[k]
            lines.append(f"| {cell(k)} | {cell(', '.join(t['variants']))} | {cell(' '.join(t['notes']))} |")
    open(a.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    src_lang = a.source_lang or phrase_lang(src_loc)
    tgt_lang = a.target_lang or phrase_lang(tgt_loc)
    write_tbx(a.tbx, approved, src_lang, tgt_lang)
    ET.parse(a.tbx)  # fails loudly if the XML is not well formed
    print(f"Wrote {a.tbx}: {len(approved)} approved terms, languages {src_lang} and {tgt_lang}.")
    print(f"Wrote {a.out}: {len(approved)} approved terms, {len(decide)} terms that need a decision "
          f"(not in the TBX file until the user chooses one form).")


if __name__ == "__main__":
    main()
