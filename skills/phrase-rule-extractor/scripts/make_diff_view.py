#!/usr/bin/env python3
"""Build a side-by-side difference view (HTML) of a candidate and a reference translation.

Usage:
  python3 make_diff_view.py --segments work/blind_segments.json --annotations work/annotations.json
      --out diff_view.html [--max-chars 2000]

--segments     output of align.py (<label>_segments.json), one or many documents
--annotations  JSON written by the rule extractor (format below)
--max-chars    maximum characters per side and per document; segments are chosen to cover as
               many rules as possible. With several documents, each one gets its own section.
--list-unclassified  print differences in the excerpt that no annotation explains

An annotation with "scope": "segment" applies to every difference in the segment that contains its
"ref" (or "mt") fragment and has no other annotation. Use it for "the other differences in this
segment are one-off wording choices".

Any annotation may carry "rule": "R4", also a reference error that the rule prevents. The tooltip
then shows the note and the rule text.

Annotations format:
{
  "title": "World Cup 2026 pink boots article",
  "source_locale": "en-US", "target_locale": "de-DE",
  "candidate_label": "Blind translation", "reference_label": "Reference",
  "rules": [{"id": "R1", "category": "Editorial", "text": "Put the names of collections ..."}],
  "annotations": [
    {"type": "rule", "rule": "R1", "mt": "Showtime-Pack", "ref": "„Showtime“-Kollektion"},
    {"type": "termbase", "mt": "Silhouetten", "ref": "Modellreihen", "note": "silhouette -> Modellreihe"},
    {"type": "reference_error", "ref": "erinnern ,", "note": "Space before a comma."},
    {"type": "one_off", "mt": "Weitere", "ref": "Verwandte", "note": "Equally good wording."}
  ]
}
"mt" is a fragment of the candidate text, "ref" a fragment of the reference text. Give at least one.
Optional "doc": the document name from the manifest. The annotation then applies only to that
document. Without "doc", it applies to every document that contains the fragment.
A highlighted difference gets an annotation when it overlaps the position of that fragment in
the same segment.
"""
import argparse
import difflib
import html
import json
import re
import sys

TOKEN = re.compile(r"\w+|\s+|[^\w\s]", re.UNICODE)
TYPE_LABEL = {
    "rule": "Rule",
    "termbase": "Termbase item",
    "reference_error": "Reference error",
    "one_off": "One-off choice",
    "file_handling": "File handling",
}


def tokens_with_spans(text):
    out, pos = [], 0
    for m in TOKEN.finditer(text):
        out.append((m.group(0), m.start(), m.end()))
    return out


def diff_hunks(mt, ref):
    """Return a list of pieces: (kind, mt_text, mt_span, ref_text, ref_span)."""
    a, b = tokens_with_spans(mt), tokens_with_spans(ref)
    sm = difflib.SequenceMatcher(None, [t[0] for t in a], [t[0] for t in b], autojunk=False)
    ops = sm.get_opcodes()
    # Merge changes that are separated only by whitespace, so one change reads as one block.
    merged = []
    for op in ops:
        tag, i1, i2, j1, j2 = op
        if (merged and tag == "equal" and merged[-1][0] != "equal"
                and all(t[0].isspace() for t in a[i1:i2]) and i2 - i1 <= 1):
            merged.append(op)
            continue
        if (len(merged) >= 2 and tag != "equal" and merged[-1][0] == "equal"
                and merged[-2][0] != "equal"
                and all(t[0].isspace() for t in a[merged[-1][1]:merged[-1][2]])
                and merged[-1][2] - merged[-1][1] <= 1):
            ws = merged.pop()
            prev = merged.pop()
            merged.append(("replace", prev[1], i2, prev[3], j2))
            continue
        merged.append(op)
    pieces = []
    for tag, i1, i2, j1, j2 in merged:
        mt_txt = "".join(t[0] for t in a[i1:i2])
        ref_txt = "".join(t[0] for t in b[j1:j2])
        mt_span = (a[i1][1], a[i2 - 1][2]) if i2 > i1 else (a[i1][1] if i1 < len(a) else len(mt),) * 2
        ref_span = (b[j1][1], b[j2 - 1][2]) if j2 > j1 else (b[j1][1] if j1 < len(b) else len(ref),) * 2
        pieces.append(("equal" if tag == "equal" else "change", mt_txt, mt_span, ref_txt, ref_span))
    return pieces


def spans_of(fragment, text):
    if not fragment:
        return []
    out, start = [], 0
    while True:
        k = text.find(fragment, start)
        if k < 0:
            return out
        out.append((k, k + len(fragment)))
        start = k + 1


def overlaps(span, spans):
    s, e = span
    for fs, fe in spans:
        if s == e:  # pure insertion point on this side
            if fs <= s <= fe:
                return True
        elif s < fe and fs < e:
            return True
    return False


def in_doc(ann, seg):
    return not ann.get("doc") or ann["doc"] == seg.get("doc")


def annotate(seg, anns):
    pieces = diff_hunks(seg["mt"], seg["ref"])
    hunks = []
    fallback = [i for i, ann in enumerate(anns) if ann.get("scope") == "segment" and in_doc(ann, seg)
                and ((ann.get("ref") and ann["ref"] in seg["ref"]) or (ann.get("mt") and ann["mt"] in seg["mt"]))]
    for kind, mt_txt, mt_span, ref_txt, ref_span in pieces:
        ids = []
        if kind == "change":
            for idx, ann in enumerate(anns):
                if ann.get("scope") == "segment" or not in_doc(ann, seg):
                    continue
                # Match only on a side where text actually changed, so an empty insertion point
                # never pulls in an annotation that belongs to neighbouring text.
                hit_mt = bool(mt_txt) and overlaps(mt_span, spans_of(ann.get("mt", ""), seg["mt"]))
                hit_ref = bool(ref_txt) and overlaps(ref_span, spans_of(ann.get("ref", ""), seg["ref"]))
                if hit_mt or hit_ref:
                    ids.append(idx)
            if not ids:
                ids = list(fallback)
        hunks.append({"kind": kind, "mt": mt_txt, "ref": ref_txt, "anns": ids})
    return hunks


def choose(segments, anns, max_chars):
    changed = [s for s in segments if s["mt"] != s["ref"]]
    info = []
    for s in changed:
        hunks = annotate(s, anns)
        found = {i for h in hunks for i in h["anns"]}
        info.append((s, hunks, found))
    chosen, covered, used_total = [], set(), 0
    docs = []
    for item in info:
        if item[0].get("doc") not in docs:
            docs.append(item[0].get("doc"))
    for doc in docs:
      used = 0
      pool = [x for x in info if x[0].get("doc") == doc]
      while pool:
        def gain(item):
            s, h, found = item
            new = found - covered
            rules_new = len({anns[i]["rule"] for i in new if anns[i].get("rule")} - {anns[i]["rule"] for i in covered if anns[i].get("rule")})
            unclassified = sum(1 for x in h if x["kind"] == "change" and not x["anns"])
            return (rules_new, len(new), -unclassified, -max(len(s["mt"]), len(s["ref"])))
        pool.sort(key=gain, reverse=True)
        s, h, found = pool.pop(0)
        size = max(len(s["mt"]), len(s["ref"]))
        if used + size > max_chars:
            continue
        chosen.append((s, h))
        covered |= found
        used += size
      used_total = max(used_total, used)
    chosen.sort(key=lambda x: x[0]["order"])
    return chosen, used_total, len(changed), covered


def esc(t):
    return html.escape(t, quote=True)


def render_side(hunks, side):
    out = []
    for n, h in enumerate(hunks):
        txt = h[side]
        if h["kind"] == "equal":
            out.append(esc(txt))
            continue
        if not txt:
            continue
        cls = "del" if side == "mt" else "ins"
        types = sorted({h_type for h_type in h.get("types", [])})
        extra = " is-flag" if "reference_error" in types else ""
        extra += "" if h["anns"] else " is-unknown"
        out.append(
            f'<mark class="hunk {cls}{extra}" tabindex="0" data-hunk="{h["hid"]}" '
            f'data-anns="{",".join(map(str, h["anns"]))}">{esc(txt)}</mark>')
    return "".join(out)


CSS = """
:root{
  --page:#fafafa;--card:#ffffff;--recessed:#f3f3f3;--border:#dfdfdf;
  --text:#181818;--text2:#505050;--muted:#8c8c8c;--click:#1080fc;--click-bg:#f1f9ff;
  --del-bg:#fcf4f3;--del-fg:#bd2c17;--del-mark:#f6cfc8;
  --ins-bg:#f1fef6;--ins-fg:#039754;--ins-mark:#bdf0d4;
  --flag:#de6006;--flag-bg:#fff7ed;
  --shadow:0 0 2px 0 #1818181a,0 1px 16px 0 #1818181a;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){:root{
  --page:#141414;--card:#1e1e1e;--recessed:#262626;--border:#383838;
  --text:#f3f3f3;--text2:#c2c2c2;--muted:#8c8c8c;--click:#4da3ff;--click-bg:#0f2540;
  --del-bg:#2a1714;--del-fg:#ff9a8a;--del-mark:#5a231b;
  --ins-bg:#10261a;--ins-fg:#6ee7a8;--ins-mark:#17492e;
  --flag:#fb923c;--flag-bg:#33200e;
  --shadow:0 0 2px 0 #00000066,0 1px 16px 0 #00000066;
  color-scheme:dark;
}}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--text);font:14px/20px Inter,Helvetica,Arial,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:32px 24px 64px}
h1{font-size:24px;line-height:32px;font-weight:700;margin:0 0 4px}
.sub{color:var(--text2);margin:0 0 16px}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}
.stat{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;color:var(--text2)}
.stat b{color:var(--text);font-weight:700}
.bar{display:flex;flex-wrap:wrap;align-items:center;gap:16px;margin:0 0 16px;color:var(--text2)}
.key{display:inline-flex;align-items:center;gap:6px}
.sw{display:inline-block;width:28px;height:16px;border-radius:4px}
.sw.del{background:var(--del-mark)}.sw.ins{background:var(--ins-mark)}
.sw.flag{background:transparent;border-bottom:2px dashed var(--flag);border-radius:0;height:12px}
label.toggle{margin-left:auto;display:inline-flex;gap:6px;align-items:center;cursor:pointer}
.grid{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.head,.row{display:grid;grid-template-columns:1fr 1fr}
.head div{padding:10px 16px;font-weight:700;border-bottom:1px solid var(--border);background:var(--recessed)}
.head div:first-child,.row .cell:first-child{border-right:1px solid var(--border)}
.row{border-bottom:1px solid var(--border)}
.row:last-child{border-bottom:0}
.doc{padding:8px 16px;font-weight:700;background:var(--recessed);border-bottom:1px solid var(--border)}
.src{grid-column:1/-1;padding:8px 16px 0;color:var(--muted);font-size:12px;line-height:16px;display:none}
.show-src .src{display:block}
.cell{padding:12px 16px;white-space:pre-wrap;overflow-wrap:anywhere}
.cell.mt{background:linear-gradient(var(--del-bg),var(--del-bg)) left/4px 100% no-repeat}
.cell.ref{background:linear-gradient(var(--ins-bg),var(--ins-bg)) left/4px 100% no-repeat}
mark.hunk{color:inherit;border-radius:3px;padding:0 1px;cursor:help;outline:0;transition:box-shadow .12s}
mark.del{background:var(--del-mark)}
mark.ins{background:var(--ins-mark)}
mark.is-flag{box-shadow:inset 0 -2px 0 var(--flag)}
mark.is-unknown{opacity:.75}
mark.lit,mark:focus-visible{box-shadow:0 0 0 2px var(--click)}
mark.spot{box-shadow:0 0 0 2px var(--click);background:var(--click-bg)}
.tip{position:fixed;z-index:10;max-width:380px;background:var(--card);color:var(--text);
  border:1px solid var(--border);border-radius:12px;box-shadow:var(--shadow);padding:12px 14px;
  pointer-events:none;opacity:0;transform:translateY(4px);transition:opacity .12s,transform .12s}
.tip.on{opacity:1;transform:none}
.tip .item+.item{margin-top:10px;padding-top:10px;border-top:1px solid var(--border)}
.badge{display:inline-block;border-radius:4px;padding:2px 8px;font-size:12px;line-height:16px;font-weight:500;margin-right:6px}
.b-rule{background:var(--click-bg);color:var(--click)}
.b-termbase,.b-one_off,.b-file_handling,.b-none{background:var(--recessed);color:var(--text2)}
.b-reference_error{background:var(--flag-bg);color:var(--flag)}
.cat{color:var(--muted);font-size:12px}
.tip p{margin:6px 0 0}
.pair{margin-top:6px;font-size:12px;color:var(--text2)}
h2{font-size:20px;line-height:28px;margin:32px 0 8px}
.hint{color:var(--text2);margin:0 0 12px}
.rules{display:grid;gap:8px}
.rule{text-align:left;font:inherit;color:inherit;background:var(--card);border:1px solid var(--border);
  border-radius:12px;padding:12px 16px;cursor:pointer;display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:start}
.rule:hover{border-color:var(--click)}
.rule[aria-pressed=true]{border-color:var(--click);box-shadow:0 0 0 1px var(--click)}
.rule .id{font-weight:700;color:var(--click)}
.rule .n{color:var(--muted);white-space:nowrap}
.foot{color:var(--muted);margin-top:16px;font-size:12px}
@media (max-width:760px){.head,.row{grid-template-columns:1fr}
  .head div:first-child,.row .cell:first-child{border-right:0;border-bottom:1px dashed var(--border)}
  .head div:last-child{display:none}.cell.mt::before{content:attr(data-label);display:block;color:var(--muted);font-size:12px}
  .cell.ref::before{content:attr(data-label);display:block;color:var(--muted);font-size:12px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = """
const ANN = __ANN__, RULES = __RULES__, LABEL = __LABEL__;
const tip = document.getElementById('tip');
const esc = s => s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function content(ids){
  if(!ids.length) return '<div class="item"><span class="badge b-none">Not classified</span><p>No rule, termbase item, or reference error was linked to this difference.</p></div>';
  return ids.map(i => {
    const a = ANN[i]; let body = '';
    if(a.rule && RULES[a.rule]){
      const r = RULES[a.rule];
      body = `<span class="cat">${esc(a.rule)}, ${esc(r.category)}</span><p>${esc(r.text)}</p>`;
    }
    if(a.type === 'termbase' && a.source_term){
      const tgt = a.target_term || (a.variants||[]).join(' or ');
      body += `<p>${esc(a.source_term)} → ${esc(tgt)}</p><p class="cat">${a.status === 'decide' ? 'Needs a decision before it goes into Terminology.tbx.' : 'Saved to Terminology.tbx for the Term Base. Not a rule.'}</p>`;
    }
    if(a.note) body += `<p>${esc(a.note)}</p>`;
    const pair = (a.mt||a.ref) ? `<div class="pair">${a.mt?'Blind: '+esc(a.mt):''}${a.mt&&a.ref?'<br>':''}${a.ref?'Reference: '+esc(a.ref):''}</div>` : '';
    return `<div class="item"><span class="badge b-${a.type}">${LABEL[a.type]||a.type}</span>${body}${pair}</div>`;
  }).join('');
}
function place(el){
  const r = el.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
  let x = Math.min(Math.max(8, r.left), innerWidth - w - 8);
  let y = r.bottom + 8; if(y + h > innerHeight - 8) y = Math.max(8, r.top - h - 8);
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}
function show(el){
  const ids = el.dataset.anns ? el.dataset.anns.split(',').map(Number) : [];
  tip.innerHTML = content(ids); tip.classList.add('on'); place(el);
  document.querySelectorAll(`mark[data-hunk="${el.dataset.hunk}"]`).forEach(m => m.classList.add('lit'));
}
function hide(el){
  tip.classList.remove('on');
  document.querySelectorAll('mark.lit').forEach(m => m.classList.remove('lit'));
}
document.querySelectorAll('mark.hunk').forEach(m => {
  m.addEventListener('mouseenter', () => show(m)); m.addEventListener('mouseleave', () => hide(m));
  m.addEventListener('focus', () => show(m)); m.addEventListener('blur', () => hide(m));
});
addEventListener('scroll', () => tip.classList.remove('on'), {passive:true});
document.getElementById('src').addEventListener('change', e => document.body.classList.toggle('show-src', e.target.checked));
document.querySelectorAll('button.rule').forEach(b => b.addEventListener('click', () => {
  const on = b.getAttribute('aria-pressed') !== 'true';
  document.querySelectorAll('button.rule').forEach(x => x.setAttribute('aria-pressed','false'));
  document.querySelectorAll('mark.spot').forEach(m => m.classList.remove('spot'));
  if(!on) return;
  b.setAttribute('aria-pressed','true');
  const idx = ANN.map((a,i) => a.rule === b.dataset.rule ? i : -1).filter(i => i >= 0);
  const marks = [...document.querySelectorAll('mark.hunk')].filter(m => m.dataset.anns && m.dataset.anns.split(',').some(i => idx.includes(+i)));
  marks.forEach(m => m.classList.add('spot'));
  if(marks[0]) marks[0].scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block:'center'});
}));
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", required=True)
    ap.add_argument("--annotations", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-chars", type=int, default=2000)
    ap.add_argument("--list-unclassified", action="store_true",
                    help="print the differences in the excerpt that no annotation explains")
    a = ap.parse_args()

    segs = json.load(open(a.segments, encoding="utf-8"))
    meta = json.load(open(a.annotations, encoding="utf-8"))
    anns = meta.get("annotations", [])
    rules = {r["id"]: r for r in meta.get("rules", [])}
    for ann in anns:
        if ann.get("type") == "rule" and not ann.get("rule"):
            sys.exit("An annotation of type 'rule' needs a rule id.")
        if ann.get("rule") and ann.get("rule") not in rules:
            sys.exit(f"Annotation points to unknown rule id: {ann.get('rule')}")

    chosen, used, total_changed, covered = choose(segs, anns, a.max_chars)
    hid = 0
    rows = []
    n_docs = len({s.get("doc") for s in segs})
    last_doc = object()
    for s, hunks in chosen:
        if n_docs > 1 and s.get("doc") != last_doc:
            last_doc = s.get("doc")
            rows.append(f'<div class="doc">{esc(str(last_doc or "Document"))}</div>')
        for h in hunks:
            h["hid"] = hid
            h["types"] = [anns[i]["type"] for i in h["anns"]]
            hid += 1
        rows.append(
            f'<div class="row"><div class="src">{esc(s.get("src", ""))}</div>'
            f'<div class="cell mt" data-label="{esc(meta.get("candidate_label", "Blind translation"))}">{render_side(hunks, "mt")}</div>'
            f'<div class="cell ref" data-label="{esc(meta.get("reference_label", "Reference"))}">{render_side(hunks, "ref")}</div></div>')

    shown_rules = {anns[i]["rule"] for i in covered if anns[i].get("rule")}
    counts = {}
    for i in covered:
        counts[anns[i]["type"]] = counts.get(anns[i]["type"], 0) + 1

    stats = []
    if n_docs > 1:
        stats.append(f'<span class="stat">Documents <b>{n_docs}</b></span>')
    stats += [f'<span class="stat">Rules shown <b>{len(shown_rules)} of {len(rules)}</b></span>',
              f'<span class="stat">Changed segments shown <b>{len(chosen)} of {total_changed}</b></span>']

    rule_items = []
    for rid, r in rules.items():
        n = sum(1 for s, hunks in chosen for h in hunks
                if any(anns[i].get("rule") == rid for i in h["anns"]))
        where = f"{n} highlighted" if n else "not in this excerpt"
        rule_items.append(
            f'<button class="rule" type="button" aria-pressed="false" data-rule="{esc(rid)}">'
            f'<span class="id">{esc(rid)}</span><span><span class="cat">{esc(r["category"])}</span><br>{esc(r["text"])}</span>'
            f'<span class="n">{where}</span></button>')

    title = meta.get("title", "Translation differences")
    locales = " to ".join(x for x in (meta.get("source_locale"), meta.get("target_locale")) if x)
    js = (JS.replace("__ANN__", json.dumps(anns, ensure_ascii=False))
            .replace("__RULES__", json.dumps(rules, ensure_ascii=False))
            .replace("__LABEL__", json.dumps(TYPE_LABEL)))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}: differences</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>{esc(title)}</h1>
<p class="sub">Blind translation compared with the reference{(", " + esc(locales)) if locales else ""}. Hover over or tab to a highlighted difference to see the rule behind it.</p>
<div class="stats">{"".join(stats)}</div>
<div class="bar"><span class="key"><span class="sw del"></span>Only in the blind translation</span>
<span class="key"><span class="sw ins"></span>Only in the reference</span>
<span class="key"><span class="sw flag"></span>Error in the reference</span>
<label class="toggle"><input type="checkbox" id="src"> Show source text</label></div>
<div class="grid"><div class="head"><div>{esc(meta.get("candidate_label", "Blind translation"))}</div><div>{esc(meta.get("reference_label", "Reference"))}</div></div>
{"".join(rows)}</div>
<h2>Rules</h2><p class="hint">Select a rule to mark every difference it explains.</p>
<div class="rules">{"".join(rule_items)}</div>
<p class="foot">Excerpt of up to {used} characters per side{" and per document" if n_docs > 1 else ""}, chosen to show as many rules as possible. Footnote markers are hidden.</p>
</div><div class="tip" id="tip" role="tooltip"></div><script>{js}</script></body></html>"""
    open(a.out, "w", encoding="utf-8").write(page)
    unknown = sum(1 for s, hunks in chosen for h in hunks if h["kind"] == "change" and not h["anns"])
    if a.list_unclassified:
        for s, hunks in chosen:
            for h in hunks:
                if h["kind"] == "change" and not h["anns"]:
                    print(f'  blind: {h["mt"]!r}  reference: {h["ref"]!r}  in: {s["ref"][:60]!r}')
    print(f"Wrote {a.out}: {len(chosen)} segments, {used} characters per side, "
          f"{len(shown_rules)} of {len(rules)} rules visible, {unknown} unclassified differences.")


if __name__ == "__main__":
    main()
