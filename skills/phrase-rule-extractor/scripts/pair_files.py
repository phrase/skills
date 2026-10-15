#!/usr/bin/env python3
"""Propose which source, reference, and candidate files belong to the same document.

Usage:
  python3 pair_files.py <files or folders ...> --source-lang en --target-lang de --out work/pairs.json

It reads every file (any format extract.py supports), guesses its role, and groups files into
documents:
  src   source language                           (language from the name or the content)
  ref   target language, the canonical translation
  mt    target language, a candidate: the name contains "blind", "mt", "candidate", or "rules-vN"
Files named *_translator-decisions.md are listed as decisions files, not as documents.

Grouping uses the file name without language and role tokens ("world_cup_EN.txt" and "world_cup-de.txt"
become "world_cup"). Files whose names do not match are paired by shared numbers, model names, and URLs.
Every guess is printed with a reason. Check the result with the user before you align. Edit
pairs.json by hand when a guess is wrong.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import ExtractError, load  # noqa: E402

STOP = {
    "en": "the and of to is in for with that this are on as be it by from or an".split(),
    "de": "der die das und ist nicht mit für von den dem ein eine zu auf sich auch im des".split(),
    "fr": "le la les et des est pour une dans du que qui sur pas avec au".split(),
    "es": "el la los las y de que es en para una por con del se al".split(),
    "it": "il la di che e per una sono con del della non gli le".split(),
    "nl": "de het een en van is dat op te voor met zijn niet aan".split(),
    "pt": "o a os as de que e em para um uma com do da não".split(),
    "pl": "i w na z do się nie jest to że od dla jak po".split(),
    "sv": "och att det som en på är av för med till den inte".split(),
}
CANDIDATE = re.compile(r"(^|[_\-. ])(blind|mt|candidate|cand|rules[-_]?v\d+|round\d+)($|[_\-. ])", re.I)
ROLE_SRC = re.compile(r"(^|[_\-. ])(src|source|orig|original)($|[_\-. ])", re.I)
ROLE_REF = re.compile(r"(^|[_\-. ])(ref|reference|target|tgt|canonical|final)($|[_\-. ])", re.I)
ANCHOR = re.compile(r"\d[\w.,/-]*\d|\b[A-Z]{2,}\d*[\w-]*|https?://\S+")
EXTS = {".json", ".xliff", ".xlf", ".mxliff", ".sdlxliff", ".po", ".csv", ".tsv", ".xlsx", ".xlsm", ".xls",
        ".docx", ".doc", ".odt", ".rtf", ".pptx", ".ppt", ".odp", ".pdf", ".html", ".htm", ".md",
        ".markdown", ".txt", ".srt", ".vtt"}


def lang_tokens(lang):
    lang = lang.lower()
    base = lang.split("-")[0].split("_")[0]
    return {lang, base, lang.replace("-", "_"), lang.replace("_", "-")} | {f"{base}-{x}" for x in ("us", "gb", "de", "at", "ch", "fr", "es", "mx", "br", "pt", "it", "nl", "be")} | {f"{base}_{x}" for x in ("us", "gb", "de", "at", "ch", "fr", "es", "mx", "br", "pt", "it", "nl", "be")}


def stem_of(name, langs):
    s = os.path.splitext(os.path.basename(name))[0].lower()
    s = CANDIDATE.sub(" ", s)
    s = ROLE_SRC.sub(" ", s)
    s = ROLE_REF.sub(" ", s)
    toks = [t for t in re.split(r"[_\-. ()\[\]]+", s) if t]
    toks = [t for t in toks if t not in langs]
    return " ".join(toks)


def name_lang(name, src_tokens, tgt_tokens):
    toks = set(t.lower() for t in re.split(r"[_\-. ()\[\]]+", os.path.splitext(os.path.basename(name))[0]) if t)
    joined = os.path.basename(name).lower()
    s = bool(toks & src_tokens) or any(f"{a}" in joined for a in src_tokens if len(a) > 2)
    t = bool(toks & tgt_tokens) or any(f"{a}" in joined for a in tgt_tokens if len(a) > 2)
    return "src" if s and not t else "tgt" if t and not s else None


def content_lang(text, src, tgt):
    words = re.findall(r"[^\W\d_]+", text.lower())[:4000]
    if not words:
        return None, 0
    def score(lang):
        st = set(STOP.get(lang, []))
        return sum(w in st for w in words) / len(words)
    s, t = score(src), score(tgt)
    if max(s, t) < 0.02:
        return None, 0
    return ("src" if s > t else "tgt"), abs(s - t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--source-lang", required=True)
    ap.add_argument("--target-lang", required=True)
    ap.add_argument("--out", default="work/pairs.json")
    a = ap.parse_args()

    files = []
    for p in a.paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                files += [os.path.join(root, n) for n in sorted(names)]
        else:
            files.append(p)
    src_tok, tgt_tok = lang_tokens(a.source_lang), lang_tokens(a.target_lang)
    sb, tb = a.source_lang.lower()[:2], a.target_lang.lower()[:2]

    decisions, items, problems, seen = [], [], [], {}
    for f in files:
        base = os.path.basename(f)
        if base.lower().endswith("translator-decisions.md"):
            decisions.append(f)
            continue
        if os.path.splitext(f)[1].lower() not in EXTS:
            problems.append(f"{base}: unknown format, read as plain text.")
        try:
            _, segs = load(f, "tgt")
        except ExtractError as e:
            problems.append(f"{base}: {e}")
            continue
        text = " ".join(t for _, t in segs)
        if not text.strip():
            problems.append(f"{base}: no text found.")
            continue
        digest = hash(text)
        if digest in seen:
            problems.append(f"{base}: same text as {seen[digest]}. Ignored as a duplicate.")
            continue
        seen[digest] = base
        by_name = name_lang(f, src_tok, tgt_tok)
        by_text, margin = content_lang(text, sb, tb)
        lang = by_text if by_text and margin > 0.01 else by_name or by_text
        why = f"language from {'content' if lang == by_text and by_text else 'file name'}"
        if by_name and by_text and by_name != by_text:
            why += f" (the file name suggests {by_name}; check this)"
        role = "src" if lang == "src" else None
        if lang == "tgt":
            if CANDIDATE.search(os.path.splitext(base)[0]):
                role = "mt"
            else:
                role = "ref"
                if not ROLE_REF.search(base):
                    why += "; no candidate marker in the name, so treated as reference"
        if lang is None:
            problems.append(f"{base}: language unclear. Ask the user.")
            continue
        items.append({"file": f, "role": role, "stem": stem_of(f, src_tok | tgt_tok), "why": why,
                      "anchors": set(x.strip(".,") for x in ANCHOR.findall(text))})

    docs = {}
    for it in items:
        docs.setdefault(it["stem"], {}).setdefault(it["role"], []).append(it)

    # Pair leftovers whose names differ (for example "Broschüre DE.pdf" and "Brochure EN.pdf").
    lone_src = [d for d in docs if set(docs[d]) == {"src"}]
    lone_tgt = [d for d in docs if "src" not in docs[d]]
    for s in list(lone_src):
        best, score = None, 0.0
        sa = docs[s]["src"][0]["anchors"]
        for t in lone_tgt:
            ta = set().union(*(i["anchors"] for r in docs[t].values() for i in r))
            j = len(sa & ta) / max(len(sa | ta), 1)
            if j > score:
                best, score = t, j
        if best and score >= 0.2:
            for r, its in docs.pop(best).items():
                for it in its:
                    it["why"] += f"; paired by shared numbers and names ({score:.0%} overlap), check this"
                docs[s].setdefault(r, []).extend(its)
            lone_tgt.remove(best)

    manifest = []
    print(f"Proposed documents ({a.source_lang} to {a.target_lang}):")
    for stem, roles in sorted(docs.items()):
        entry = {"doc": stem or "document"}
        for r in ("src", "ref", "mt"):
            if r in roles:
                if len(roles[r]) > 1:
                    problems.append(f"{stem}: {len(roles[r])} files look like '{r}': "
                                    + ", ".join(os.path.basename(i['file']) for i in roles[r]) + ". Ask the user.")
                entry[r] = roles[r][0]["file"]
        manifest.append(entry)
        print(f"- {entry['doc']}")
        for r in ("src", "ref", "mt"):
            if r in roles:
                for it in roles[r]:
                    print(f"    {r}: {os.path.basename(it['file'])}  [{it['why']}]")
            else:
                print(f"    {r}: missing")
    for d in decisions:
        print(f"Decisions file: {os.path.basename(d)}")
    for p in problems:
        print(f"Problem: {p}")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(manifest, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Wrote {a.out}: {len(manifest)} documents. Check it with the user before you align.")


if __name__ == "__main__":
    main()
