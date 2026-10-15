#!/usr/bin/env python3
"""Align source, candidate, and reference segments for one or many documents. No scoring.

Usage, many documents (the normal case):
  python3 align.py --manifest work/pairs.json --label blind --out work/

Usage, one document:
  python3 align.py --src <source> --mt <candidate> --ref <reference> [--doc name] --label blind --out work/

The manifest is written by pair_files.py and checked by you. Format:
  [{"doc": "World Cup article", "src": "en/world_cup.txt", "ref": "de/world_cup.txt",
    "mt": "world_cup_de-DE_blind.txt", "prev": "world_cup_de-DE_rules-v1.txt"}, ...]
An entry may also have "sample": {"start": i, "end": j}, written by estimate.py. Then only the
sampled source segments and their reference counterparts are compared.
"mt" is the candidate of this run. "prev" is optional: the candidate of the previous round. It adds
a column, so you can see per segment what a rule changed. Files may have any format that
extract.py reads, and the three files of one document may even have different formats.

How segments are paired:
  - Keyed formats (CMS JSON, XLIFF, PO, spreadsheets): by key, when the candidate and the
    reference share most keys.
  - Running text (PDF, DOCX, PPTX, HTML, Markdown, plain text), or keys that do not match:
    candidate to reference by content similarity, source to reference by length and by shared
    numbers and names. One paragraph may pair with two (a split or a merge).
  Rows that the aligner is not sure about get "check": true. Read them before you analyze. A wrong
  pairing creates false differences.

Writes to --out:
  <label>_segments.json  all aligned rows in document order, for make_diff_view.py
  <label>_aligned.md     the changed rows, grouped by document, in document order
Prints one summary line per document.
"""
import argparse
import difflib
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import ExtractError, load, split  # noqa: E402

WORD = re.compile(r"\w+", re.UNICODE)
ANCHOR = re.compile(r"\d[\w.,:/-]*|\b[A-Z]{2,}[\w-]*|\b\w*\d\w*\b|https?://\S+")


def parts(path, side):
    keyed, segs = load(path, side)
    return keyed, [(k, p) for k, t in segs for p in split(t)], segs


def sim(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, WORD.findall(a.lower()), WORD.findall(b.lower()), autojunk=False).ratio()


def anchors(t):
    return {x.strip(".,:") for x in ANCHOR.findall(t)}


def dp_align(xs, ys, cost, skip=1.0, merge_pen=0.15, band=40):
    """Align two lists. Moves: 1-1, 1-2, 2-1, 1-0, 0-1. Returns [(x_idx_list, y_idx_list, cost)]."""
    n, m = len(xs), len(ys)
    INF = float("inf")
    D = {(0, 0): (0.0, None)}
    for i in range(n + 1):
        center = i * m / n if n else 0
        lo, hi = max(0, int(center) - band), min(m, int(center) + band)
        for j in range(lo, hi + 1):
            if (i, j) == (0, 0):
                continue
            best = (INF, None)
            for di, dj in ((1, 1), (1, 2), (2, 1), (1, 0), (0, 1)):
                pi, pj = i - di, j - dj
                if pi < 0 or pj < 0 or (pi, pj) not in D:
                    continue
                if di == 0 or dj == 0:
                    c = skip
                else:
                    c = cost(" ".join(xs[pi:i]), " ".join(ys[pj:j]))
                    if di + dj > 2:
                        c += merge_pen
                total = D[(pi, pj)][0] + c
                if total < best[0]:
                    best = (total, (pi, pj, c))
            if best[1]:
                D[(i, j)] = best
    if (n, m) not in D:  # band too narrow: fall back to strict order
        k = min(n, m)
        return [([i], [i], 0.5) for i in range(k)] + [([i], [], skip) for i in range(k, n)] + [([], [j], skip) for j in range(k, m)]
    out, cur = [], (n, m)
    while cur != (0, 0):
        pi, pj, c = D[cur][1]
        out.append((list(range(pi, cur[0])), list(range(pj, cur[1])), c))
        cur = (pi, pj)
    return out[::-1]


def length_ratio(src, tgt):
    s = sum(len(x) for x in src) or 1
    return (sum(len(x) for x in tgt) or 1) / s


def src_cost_fn(ratio):
    def cost(s, r):
        c = abs(math.log((len(r) + 10) / (len(s) * ratio + 10)))
        a, b = anchors(s), anchors(r)
        if a or b:
            c -= 0.6 * len(a & b) / len(a | b)
            if a and b and not (a & b):
                c += 0.3
        return max(c, 0.0)
    return cost


def by_key(ref_keyed, mt_keyed, src_keyed, prev_keyed):
    """Pair by key. Each argument is a dict key -> original string, or None."""
    rows = []
    for key, rtext in ref_keyed.items():
        if key not in mt_keyed:
            continue
        r_parts, m_parts = split(rtext), split(mt_keyed[key])
        s_parts = split(src_keyed[key]) if src_keyed and key in src_keyed else []
        p_parts = split(prev_keyed[key]) if prev_keyed and key in prev_keyed else []
        if len(r_parts) != len(m_parts):
            r_parts, m_parts = [" ".join(r_parts)], [" ".join(m_parts)]
            s_parts = [" ".join(s_parts)] if s_parts else []
            p_parts = [" ".join(p_parts)] if p_parts else []
        if len(s_parts) != len(r_parts):
            s_parts = [" ".join(s_parts)] if len(r_parts) == 1 and s_parts else [""] * len(r_parts)
        if len(p_parts) != len(r_parts):
            p_parts = [" ".join(p_parts)] if len(r_parts) == 1 and p_parts else [""] * len(r_parts)
        for s, m, r, p in zip(s_parts, m_parts, r_parts, p_parts):
            rows.append({"field": key, "src": s, "mt": m, "ref": r, "prev": p,
                         "check": bool(s_parts and not s and r)})
    return rows


def by_content(ref, mt, src, prev):
    """Pair running text. ref, mt, src, prev are lists of segment strings (src/prev may be empty)."""
    def tgt_cost(a, b):
        return 1.0 - sim(a, b)
    mt_al = dp_align(mt, ref, tgt_cost, skip=0.85)
    ref_to_mt, ref_cost = {}, {}
    rows = []
    for mi, ri, c in mt_al:
        if not ri:  # candidate text with no reference: keep it visible
            rows.append({"ref_idx": None, "mt": " ".join(mt[i] for i in mi), "ref": "", "check": True})
            continue
        rows.append({"ref_idx": ri, "mt": " ".join(mt[i] for i in mi), "ref": " ".join(ref[i] for i in ri),
                     "check": (not mi) or c > 0.75 or len(mi) + len(ri) > 2})
    def attach(other, name, cost, skip, merge_pen):
        if not other:
            for r in rows:
                r[name] = ""
            return
        al = dp_align(other, ref, cost, skip=skip, merge_pen=merge_pen)
        owner = {}
        for oi, ri, c in al:
            for k in ri:
                owner[k] = (oi, c, len(oi) + len(ri) > 2)
        for r in rows:
            if r["ref_idx"] is None:
                r[name] = ""
                continue
            got, flag = [], False
            for k in r["ref_idx"]:
                oi, c, merged = owner.get(k, ([], 9, True))
                for i in oi:
                    if i not in got:
                        got.append(i)
                flag |= (not oi) or merged or c > 0.9
            r[name] = " ".join(other[i] for i in got)
            if name == "src":
                r["check"] |= flag
    attach(src, "src", src_cost_fn(length_ratio(src, ref)) if src else None, 1.2, 0.45)
    attach(prev, "prev", lambda a, b: 1.0 - sim(a, b), 0.85, 0.15)
    for r in rows:
        r.pop("ref_idx", None)
        r["field"] = "text"
    return rows


def align_doc(entry):
    doc = entry.get("doc") or os.path.splitext(os.path.basename(entry["ref"]))[0]
    r_keyed, r_parts, r_raw = parts(entry["ref"], "tgt")
    m_keyed, m_parts, m_raw = parts(entry["mt"], "tgt")
    s_keyed, s_parts, s_raw = parts(entry["src"], "src") if entry.get("src") else (False, [], [])
    p_keyed, p_parts, p_raw = parts(entry["prev"], "tgt") if entry.get("prev") else (False, [], [])
    sample = entry.get("sample")
    if sample and s_keyed:  # keyed formats: keep only the keys of the sampled source segments
        keep = {k for k, _ in load(entry["src"], "src")[1][sample["start"]:sample["end"]]}
        if keep & {k for k, _ in r_raw}:
            r_raw = [(k, t) for k, t in r_raw if k in keep]
            m_raw = [(k, t) for k, t in m_raw if k in keep]
            p_raw = [(k, t) for k, t in p_raw if k in keep]
            s_raw = [(k, t) for k, t in s_raw if k in keep]
    rd, md = dict(r_raw), dict(m_raw)
    shared = len(set(rd) & set(md)) / max(len(rd), 1)
    if r_keyed and m_keyed and shared >= 0.6:
        sd = dict(s_raw) if s_keyed and len(set(dict(s_raw)) & set(rd)) / max(len(rd), 1) >= 0.6 else None
        pd = dict(p_raw) if p_keyed else None
        rows = by_key(rd, md, sd, pd)
        method = "by key"
        if sd is None and s_parts:  # source keys differ: pair the source by content
            for r in rows:
                r["src"] = ""
            filler = by_content([r["ref"] for r in rows], [r["mt"] for r in rows], [p for _, p in s_parts], [])
            for r, f in zip(rows, filler):
                r["src"], r["check"] = f["src"], f["check"]
            method = "by key, source by content"
        missing = [k for k in rd if k not in md]
        if missing:
            print(f"  Warning: {doc}: {len(missing)} reference fields have no candidate text, e.g. {missing[:3]}")
    else:
        if sample and s_raw:  # running text: compare only the matching part of the reference
            before = sum(len(split(t)) for _, t in s_raw[:sample["start"]])
            s_sel = [(k, p) for k, t in s_raw[sample["start"]:sample["end"]] for p in split(t)]
            ratio = len(r_parts) / max(len(s_parts), 1)
            margin = max(3, len(s_sel) // 5)
            r0 = max(0, int(before * ratio) - margin)
            r1 = min(len(r_parts), int((before + len(s_sel)) * ratio) + margin)
            r_parts, s_parts = r_parts[r0:r1], s_sel
            # Narrow the window: the first candidate paragraph marks the start, the last one the end.
            if m_parts and len(r_parts) > 2:
                texts = [p for _, p in r_parts]
                half = len(texts) // 2
                j0 = max(range(0, half + 1), key=lambda j: sim(m_parts[0][1], texts[j]))
                j1 = max(range(half, len(texts)), key=lambda j: sim(m_parts[-1][1], texts[j]))
                if j0 <= j1:
                    r_parts = r_parts[j0:j1 + 1]
        rows = by_content([p for _, p in r_parts], [p for _, p in m_parts],
                          [p for _, p in s_parts], [p for _, p in p_parts])
        method = "by content"
    if sample and method == "by content":  # running text: drop reference paragraphs outside the sample
        rows = [r for r in rows if r["mt"]]
    out = []
    for r in rows:
        if r["mt"] == r["ref"] == r["src"] and r["mt"]:
            continue  # untranslated identical strings such as model names
        r["doc"] = doc
        r["changed"] = r["mt"] != r["ref"]
        out.append(r)
    return doc, method, out


def esc(t):
    return (t or "").replace("|", "\\|").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest")
    ap.add_argument("--src")
    ap.add_argument("--mt")
    ap.add_argument("--ref")
    ap.add_argument("--prev")
    ap.add_argument("--doc")
    ap.add_argument("--label", default="run")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    if a.manifest:
        entries = json.load(open(a.manifest, encoding="utf-8"))
    elif a.mt and a.ref:
        entries = [{"doc": a.doc, "src": a.src, "mt": a.mt, "ref": a.ref, "prev": a.prev}]
    else:
        sys.exit("Give --manifest, or --mt and --ref (and --src).")

    all_rows, sections = [], []
    for e in entries:
        if not e.get("mt") or not e.get("ref"):
            print(f"Skipped {e.get('doc')}: it needs both a candidate (mt) and a reference (ref).")
            continue
        try:
            doc, method, rows = align_doc(e)
        except ExtractError as err:
            print(f"Skipped {e.get('doc')}: {err}")
            continue
        changed = sum(r["changed"] for r in rows)
        checks = sum(r["check"] for r in rows)
        print(f"{doc}: {len(rows)} segments aligned {method}, {changed} with differences, "
              f"{len(rows) - changed} identical, {checks} to check.")
        all_rows += rows
        sections.append((doc, method, rows))

    for i, r in enumerate(all_rows):
        r["order"] = i
    os.makedirs(a.out, exist_ok=True)
    json.dump(all_rows, open(os.path.join(a.out, f"{a.label}_segments.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    has_prev = any(r.get("prev") for r in all_rows)
    lines = [f"# Aligned segments: {a.label}", "",
             "Only segments with differences are listed, in document order. "
             "CHECK marks a pairing the aligner is not sure about.", ""]
    for doc, method, rows in sections:
        lines += [f"## {doc}", "", f"Aligned {method}. {sum(not r['changed'] for r in rows)} identical segments are not listed.", ""]
        head = "| # | Check | Source | " + ("Previous candidate | " if has_prev else "") + "Candidate | Reference |"
        lines += [head, "|" + "---|" * (head.count("|") - 1)]
        for r in rows:
            if not r["changed"]:
                continue
            prev = f"{esc(r.get('prev'))} | " if has_prev else ""
            lines.append(f"| {r['order']} | {'CHECK' if r['check'] else ''} | {esc(r['src'])} | {prev}{esc(r['mt'])} | {esc(r['ref'])} |")
        lines.append("")
    open(os.path.join(a.out, f"{a.label}_aligned.md"), "w", encoding="utf-8").write("\n".join(lines))
    print(f"Wrote {a.label}_segments.json and {a.label}_aligned.md: {len(sections)} documents, {len(all_rows)} segments.")


if __name__ == "__main__":
    main()
