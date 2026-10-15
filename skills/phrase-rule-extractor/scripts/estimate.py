#!/usr/bin/env python3
"""Estimate the size, token use, and time of a run, and write a sample for large sets.

Usage:
  python3 estimate.py --manifest work/pairs.json
  python3 estimate.py --manifest work/pairs.json --sample 2500 [--holdout work/holdout.json]
  python3 estimate.py --manifest work/pairs.json --clear-sample

Without options: prints the size of every document, an estimate for the whole run, and a
size level: OK, NOTE, or LARGE.

--sample N    keeps about N source words per document: one block of consecutive segments from the
              start of the document. Writes "sample": {"start": i, "end": j} into each manifest
              entry. translation_job.py and align.py then use only these segments. The estimate is
              printed again for the sample.
--holdout F   with --sample: writes a second manifest to F. It holds the next block of the same
              size from each document, for the final held-out test (SKILL.md step 7).
--clear-sample  removes all samples from the manifest.

The numbers are rough. They assume about 4 characters per token in the source, a target about
1.3 times as long in tokens, one translation subagent per document, a blind round plus three rules
rounds, and a fixed cost for instructions, rule writing, and the AI check prediction. Use them to
decide whether to sample, not as a price.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import ExtractError, load  # noqa: E402

WORDS_PER_PAGE = 500
NOTE_WORDS = 5000        # above this, show the estimate before you continue
LARGE_WORDS = 15000      # above this, propose a sample
CONTEXT_LIMIT = 60000    # tokens of one comparison file that the main chat can still read well
SUBAGENT_OVERHEAD = 35000
FIXED = 400000           # instructions, sorting, rule writing, eligibility checks, report
ROUNDS = 4               # blind + up to three rules rounds
OUT_TOKENS_PER_MIN = 3000


def size(segs):
    text = " ".join(t for _, t in segs)
    return len(text.split()), len(text)


def cut(segs, sample):
    return segs[sample["start"]:sample["end"]] if sample else segs


def estimate(docs):
    """docs: list of (name, words, chars)."""
    src = [c / 4 for _, _, c in docs]
    tgt = [s * 1.3 for s in src]
    S, T = sum(src), sum(tgt)
    translate = ROUNDS * (len(docs) * SUBAGENT_OVERHEAD + S + 1.2 * T)
    compare_first = S + 2 * T
    compare_rest = (ROUNDS - 1) * (S + 3 * T)
    total = translate + compare_first + compare_rest + FIXED
    longest = max(tgt) if tgt else 0
    minutes = ROUNDS * (1.2 * longest / OUT_TOKENS_PER_MIN + 2) + (compare_first + compare_rest) / 15000 + 15
    return total, minutes, compare_rest / (ROUNDS - 1) if ROUNDS > 1 else compare_first


def fmt_tokens(n):
    return f"{n / 1e6:.1f} million" if n >= 1e6 else f"{round(n / 1000, -1):.0f} thousand"


def report(rows, title):
    words = sum(w for _, w, _ in rows)
    total, minutes, compare = estimate(rows)
    print(f"\n{title}")
    for name, w, _ in rows:
        print(f"  {name}: {w} words, about {max(1, round(w / WORDS_PER_PAGE))} pages")
    print(f"  Total: {words} source words, about {max(1, round(words / WORDS_PER_PAGE))} pages")
    print(f"  Estimate for a full run: about {fmt_tokens(total)} tokens and {int(math.ceil(minutes / 5) * 5)} minutes")
    if words > LARGE_WORDS or compare > CONTEXT_LIMIT:
        level = "LARGE"
    elif words > NOTE_WORDS:
        level = "NOTE"
    else:
        level = "OK"
    print(f"  SIZE: {level}")
    if compare > CONTEXT_LIMIT:
        print(f"  The comparison file would be about {fmt_tokens(compare)} tokens. That is too much to read well in one chat.")
    return level


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--sample", type=int, help="source words to keep per document")
    ap.add_argument("--holdout", help="write a held-out manifest to this file (with --sample)")
    ap.add_argument("--clear-sample", action="store_true")
    a = ap.parse_args()
    manifest = json.load(open(a.manifest, encoding="utf-8"))

    if a.clear_sample:
        for e in manifest:
            e.pop("sample", None)
        json.dump(manifest, open(a.manifest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("Removed all samples.")

    loaded, full = [], []
    for e in manifest:
        if not e.get("src"):
            continue
        try:
            _, segs = load(e["src"], "src")
        except ExtractError as err:
            print(f"Skipped {e.get('doc')}: {err}")
            continue
        loaded.append((e, segs))
        full.append((e["doc"], *size(segs)))
    if not loaded:
        sys.exit("No source files could be read.")
    level = report(full, "All documents")

    if a.sample:
        held = []
        for e, segs in loaded:
            words, end = 0, 0
            while end < len(segs) and words < a.sample:
                words += len(segs[end][1].split())
                end += 1
            e["sample"] = {"start": 0, "end": end}
            if a.holdout and end < len(segs):
                words2, end2 = 0, end
                while end2 < len(segs) and words2 < a.sample:
                    words2 += len(segs[end2][1].split())
                    end2 += 1
                h = {k: v for k, v in e.items() if k not in ("mt", "prev", "sample")}
                h["doc"] = f"{e['doc']} (held out)"
                h["sample"] = {"start": end, "end": end2}
                held.append(h)
        json.dump(manifest, open(a.manifest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        rows = [(e["doc"], *size(cut(segs, e["sample"]))) for e, segs in loaded]
        report(rows, f"Sample (about {a.sample} words per document, written to {a.manifest})")
        if a.holdout:
            if held:
                json.dump(held, open(a.holdout, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(f"\nWrote {a.holdout}: {len(held)} held-out blocks for the final test.")
            else:
                print("\nNo text is left after the sample, so no held-out blocks were written.")
    elif level == "LARGE":
        print("\nPropose a sample to the user, for example: --sample 2500 --holdout work/holdout.json")


if __name__ == "__main__":
    main()
