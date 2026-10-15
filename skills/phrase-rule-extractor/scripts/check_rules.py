#!/usr/bin/env python3
"""Lint a rules file: one rule per paragraph, paragraphs separated by an empty line.

Usage: python3 check_rules.py <rules.md>

Checks each rule for the 450-character limit and for wording that made Phrase
omit rules as AI checks (judge instructions, hedges, intent and quality words,
external references, term pairs that belong in Terminology.md). Exit code 1 if any rule is over the
limit or names a file such as Terminology.md.
"""
import re
import sys

LIMIT = 450
WARN = {
    "judge instruction (rules must also guide translation)": r"\bflag\b|\bflagged\b|\bmark the segment\b|\btreat a segment as\b",
    "hedge that needs a judgment": r"\bwhen possible\b|\bwhere possible\b|\bwhen appropriate\b|\bif necessary\b|\bwhen needed\b|\bwhere relevant\b|\bas needed\b",
    "quality or intent word that a check cannot verify": r"\bnatural(ly)?\b|\bsound(s)? \b|\bclear(ly)?\b|\bappealing\b|\bengaging\b|\bpurpose\b|\bintent\b|\bappropriate\b|\bsuitable\b|\bfriendly\b|\bempath",
    "depends on other segments or document order": r"\bconsistent(ly)?\b|\bthroughout\b|\bsame way\b|\bfirst (use|mention|occurrence)\b|\bearlier\b|\blater in\b|\bsubsequent\b|\bacross (segments|the document)\b",
    "looks like a term pair (move it to the terminology files, not into a rule)": r"\balways (translate|render|use)\b|\btranslate [\"'\w][^.]{0,40} as [\"']|→|->",
    "reference to something the check cannot see": r"\bstyle guide\b|\bglossary\b|\btermbase\b|\bapproved materials?\b|\bproject instructions\b|\bother rules\b|\bprevious segment\b|\btranslation memory\b|\bbutton\b|\btooltip\b|\btoast\b|\bheading\b",
}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    text = open(sys.argv[1], encoding="utf-8").read().strip()
    rules = [r.strip() for r in re.split(r"\n\s*\n", text) if r.strip()]
    over = 0
    fails = 0
    for i, rule in enumerate(rules, 1):
        ref = re.search(r"[\w./-]*[\w-]\.(md|csv|tbx|xlsx|json)\b", rule, re.I)
        if ref:
            fails += 1
            print(f"Rule {i}: FAIL, names the file {ref.group(0)!r}. A rule cannot open files. Inline what it needs.")
        n = len(rule)
        status = "OK" if n <= LIMIT else "OVER LIMIT"
        over += n > LIMIT
        print(f"Rule {i}: {n} characters, {status}. Starts: {rule[:60]}...")
        if "\n" in rule:
            print("  warning: line break inside the rule; keep each rule on one line")
        if not re.search(r'"[^"]+"', rule):
            print("  warning: no quoted example; add at least one concrete example")
        for label, pat in WARN.items():
            hits = sorted(set(m.group(0).lower() for m in re.finditer(pat, rule, re.I)))
            if hits:
                print(f"  warning: {label}: {', '.join(hits)}")
    print(f"{len(rules)} rules, {over} over the {LIMIT}-character limit, {fails} naming a file.")
    sys.exit(1 if over or fails else 0)


if __name__ == "__main__":
    main()
