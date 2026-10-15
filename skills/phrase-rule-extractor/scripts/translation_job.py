#!/usr/bin/env python3
"""Prepare an isolated translation job for a subagent, and collect its result.

The rule extractor never translates. It uses this script to hand the source text to a translator
subagent that never sees the reference, and to turn the subagent's output into candidate files.

1. Prepare (before you spawn the translator):
   python3 translation_job.py prepare --manifest work/pairs.json --label blind --locale de-DE \
       --jobs work/jobs/ [--rules work/rules_v1.md] [--terms <outputs>/Terminology.tbx]

   Writes work/jobs/<label>/ with only these files:
     <doc>/segments_src.json   [{"id": ..., "text": ...}] in document order, markup kept
     TRANSLATOR.md             the translator brief (copied from references/translator_brief.md)
     job.json                  locale, label, documents
     rules.md, Terminology.tbx only in rules rounds
   No reference text and no earlier candidate is copied. The script checks this.
   If a manifest entry has "sample" (written by estimate.py), only those segments are copied.

2. Spawn one translator subagent per job folder (or per document for large jobs). Give it only
   the job folder path and the instruction in references/translator_brief.md.

3. Collect (after the subagent wrote <doc>/segments_tgt.json and <doc>/decisions.md):
   python3 translation_job.py collect --manifest work/pairs.json --label blind --jobs work/jobs/ --out work/candidates/

   Builds one candidate per document and updates the manifest: "mt" points to the new candidate,
   and "prev" to the candidate of the last round.
     source is CMS or other JSON  -> the same JSON structure with translated values
     other keyed formats (XLIFF, PO, spreadsheets) -> flat JSON {key: translation}
     running text (DOCX, PDF, PPTX, HTML, Markdown, TXT) -> .txt, one segment per line
   It refuses to build a document when an id is missing or unknown, or when the HTML tags of a
   segment differ from the source. Send the listed segments back to the translator to fix.
"""
import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import load  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BRIEF = os.path.join(HERE, "..", "references", "translator_brief.md")
TAG = re.compile(r"<[^>]+>")


def safe(name):
    return re.sub(r"[^\w.-]+", "_", name).strip("_") or "document"


def prepare(a):
    manifest = json.load(open(a.manifest, encoding="utf-8"))
    root = os.path.join(a.jobs, a.label)
    if os.path.exists(root):
        shutil.rmtree(root)
    os.makedirs(root)
    ref_texts = set()
    docs = []
    for e in manifest:
        if not e.get("src"):
            print(f"Skipped {e.get('doc')}: no source file.")
            continue
        keyed, segs = load(e["src"], "src")
        if e.get("sample"):  # written by estimate.py --sample
            segs = segs[e["sample"]["start"]:e["sample"]["end"]]
        d = safe(e["doc"])
        os.makedirs(os.path.join(root, d))
        items = [{"id": k, "text": t} for k, t in segs]
        json.dump(items, open(os.path.join(root, d, "segments_src.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        docs.append({"doc": e["doc"], "folder": d, "segments": len(items)})
        if e.get("ref"):
            ref_texts |= {t.strip() for _, t in load(e["ref"], "tgt")[1] if len(t.strip()) > 40}
    shutil.copy(BRIEF, os.path.join(root, "TRANSLATOR.md"))
    if a.rules:
        shutil.copy(a.rules, os.path.join(root, "rules.md"))
    if a.terms:
        shutil.copy(a.terms, os.path.join(root, os.path.basename(a.terms)))
    job = {"locale": a.locale, "label": a.label, "mode": "rules" if a.rules else "blind",
           "rules": "rules.md" if a.rules else None,
           "terms": os.path.basename(a.terms) if a.terms else None, "documents": docs}
    json.dump(job, open(os.path.join(root, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # Isolation check: no reference sentence may appear anywhere in the job folder.
    leaked = []
    for dirpath, _, names in os.walk(root):
        for n in names:
            text = open(os.path.join(dirpath, n), encoding="utf-8", errors="ignore").read()
            leaked += [n for r in ref_texts if r in text]
    if leaked:
        shutil.rmtree(root)
        sys.exit(f"Stopped: reference text found in the job folder ({sorted(set(leaked))}). The job was deleted.")
    total = sum(d["segments"] for d in docs)
    print(f"Prepared {root}: {len(docs)} documents, {total} segments, mode {job['mode']}, locale {a.locale}.")
    print("Isolation check passed: the job folder contains no reference text.")


def set_path(data, path, value):
    keys = path.split("/")
    node = data
    for k in keys[:-1]:
        node = node[int(k)] if isinstance(node, list) else node[k]
    last = keys[-1]
    if isinstance(node, list):
        node[int(last)] = value
    else:
        node[last] = value


def collect(a):
    manifest = json.load(open(a.manifest, encoding="utf-8"))
    root = os.path.join(a.jobs, a.label)
    job = json.load(open(os.path.join(root, "job.json"), encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    by_doc = {d["doc"]: d for d in job["documents"]}
    failed = 0
    for e in manifest:
        d = by_doc.get(e.get("doc"))
        if not d:
            continue
        folder = os.path.join(root, d["folder"])
        src = json.load(open(os.path.join(folder, "segments_src.json"), encoding="utf-8"))
        tgt_path = os.path.join(folder, "segments_tgt.json")
        if not os.path.exists(tgt_path):
            print(f"{e['doc']}: no segments_tgt.json yet.")
            failed += 1
            continue
        tgt = {x["id"]: x["text"] for x in json.load(open(tgt_path, encoding="utf-8"))}
        problems = []
        for s in src:
            if s["id"] not in tgt:
                problems.append(f"missing id {s['id']}")
            elif TAG.findall(s["text"]) != TAG.findall(tgt[s["id"]]):
                problems.append(f"HTML tags differ in {s['id']}")
        unknown = set(tgt) - {s["id"] for s in src}
        problems += [f"unknown id {k}" for k in sorted(unknown)]
        if problems:
            failed += 1
            print(f"{e['doc']}: not built. {len(problems)} problems, e.g. " + "; ".join(problems[:5]))
            continue
        keyed, _ = load(e["src"], "src")
        ext = os.path.splitext(e["src"])[1].lower()
        base = f"{safe(e['doc'])}_{job['locale']}_{a.label}"
        if ext == ".json":
            data = json.load(open(e["src"], encoding="utf-8-sig"))
            for s in src:
                set_path(data, s["id"], tgt[s["id"]])
            out = os.path.join(a.out, base + ".json")
            json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False)
        elif keyed:
            out = os.path.join(a.out, base + ".json")
            json.dump({s["id"]: tgt[s["id"]] for s in src}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        else:
            out = os.path.join(a.out, base + ".txt")
            open(out, "w", encoding="utf-8").write("\n".join(re.sub(r"\s*\n\s*", " ", tgt[s["id"]]) for s in src) + "\n")
        dec = os.path.join(folder, "decisions.md")
        if os.path.exists(dec):
            shutil.copy(dec, os.path.join(a.out, base + "_translator-decisions.md"))
        if e.get("mt") and os.path.abspath(e["mt"]) != os.path.abspath(out):
            e["prev"] = e["mt"]
        e["mt"] = out
        print(f"{e['doc']}: built {out}")
    json.dump(manifest, open(a.manifest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Updated {a.manifest}." + (f" {failed} documents still need work." if failed else ""))
    sys.exit(1 if failed else 0)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--manifest", required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--locale", required=True)
    p.add_argument("--jobs", default="work/jobs")
    p.add_argument("--rules")
    p.add_argument("--terms")
    c = sub.add_parser("collect")
    c.add_argument("--manifest", required=True)
    c.add_argument("--label", required=True)
    c.add_argument("--jobs", default="work/jobs")
    c.add_argument("--out", default="work/candidates")
    a = ap.parse_args()
    prepare(a) if a.cmd == "prepare" else collect(a)


if __name__ == "__main__":
    main()
