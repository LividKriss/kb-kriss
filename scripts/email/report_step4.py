#!/usr/bin/env python3
"""Render the step 4 checkpoint as one local HTML page (never uploaded).

    report_step4.py [--seed N]

Reads cache/step4/ (plan, prepared, written, people.json, org_map, voice drafts, batch, unsure.md) and the
written kb/people notes. Writes cache/step4/report.html. Open it in a browser.
"""
import argparse
import glob
import html
import json
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step4lib as s4  # noqa: E402
from report_html import CSS, JS, table  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXTRA_CSS = """
.md{border:1px solid var(--line);border-radius:6px;padding:4px 16px;margin:12px 0;max-width:980px}
.md h1{font-size:15px}.md h2,.md h3,.md h4{font-size:13px;margin:14px 0 4px}.md p,.md li{color:var(--fg)}
.md blockquote{border-left:3px solid var(--line);margin:6px 0;padding:2px 10px;color:var(--muted)}
.md code{background:var(--head);padding:0 3px;border-radius:3px}.fm{color:var(--muted);font-size:12px}
details{margin:6px 0}summary{cursor:pointer;font-weight:600}nav a{margin-right:14px}
"""


def inline(s):
    e = html.escape(s)
    e = re.sub(r"`([^`]+)`", r"<code>\1</code>", e)
    e = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", e)
    return re.sub(r"\[([^\]]+)\]\((https://mail\.google\.com[^)\s]+)\)", r'<a href="\2" target="_blank">\1</a>', e)


def md(text):
    """Small Markdown subset: frontmatter, headings, bullets, tables, quotes, paragraphs."""
    out, lines, i = [], text.splitlines(), 0
    if lines and lines[0] == "---":
        j = lines.index("---", 1)
        out.append('<pre class="fm">' + html.escape("\n".join(lines[1:j])) + "</pre>")
        i = j + 1
    in_list = False
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-| :]+\|$", lines[i + 1]):
            head = [c.strip() for c in ln.strip("|").split("|")]
            rows = []
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(h)}</th>" for h in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
                       + "</tbody></table>")
            continue
        m = re.match(r"^(\s*)[-*] (.*)", ln)
        if m:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(m.group(2))}</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            h = re.match(r"^(#{1,4}) (.*)", ln)
            if h:
                out.append(f"<h{len(h.group(1))}>{inline(h.group(2))}</h{len(h.group(1))}>")
            elif ln.startswith(">"):
                out.append(f"<blockquote>{inline(ln.lstrip('> '))}</blockquote>")
            elif ln.strip():
                out.append(f"<p>{inline(ln)}</p>")
        i += 1
    if in_list:
        out.append("</ul>")
    return '<div class="md">' + "".join(out) + "</div>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=23)
    args = ap.parse_args()
    plan = json.load(open(s4.PLAN))
    prepared = json.load(open(os.path.join(s4.STEP4, "prepared.json")))
    w = json.load(open(os.path.join(s4.STEP4, "written.json")))
    written, missing = w["written"], w["missing"]
    e = html.escape
    H = [f"<!doctype html><meta charset='utf-8'><title>Step 4 checkpoint</title><style>{CSS}{EXTRA_CSS}</style>",
         "<h1>kb-kriss step 4 — checkpoint (local, never uploaded)</h1>",
         "<nav><a href='#s1'>1 Counts</a><a href='#s2'>2 Voice drafts</a><a href='#s3'>3 Spot-check</a>"
         "<a href='#s4'>4 livid-kb batch</a><a href='#s5'>5 Unsure</a><a href='#s6'>Top 50</a></nav>"]

    # 1. Counts.
    by_cat = Counter(x["category"] for x in written.values())
    waits = [x for x in written.values() if x["organization"] and not (
        REPO.parent / "livid-kb" / "kb" / x["organization"].replace("kb://livid/", "")).exists()]
    no_org = [x for x in written.values() if not x["organization"]]
    H.append("<h2 id='s1'>1. Counts</h2>")
    H.append(f"<p>Person notes written: <b>{len(written)}</b> (all <code>draft</code>) from 235 step-4 addresses "
             f"→ {len(plan['persons'])} persons after merging addresses + {len(plan['roles'])} role mailboxes.</p>")
    H.append(table(["category", "notes"], sorted(by_cat.items(), key=lambda x: -x[1]), numeric=("notes",)))
    skipped = [(a, "role / shared mailbox — no Person note, read for company facts", r["category"])
               for a, r in plan["roles"].items()]
    cfg = json.load(open(s4.PEOPLE_JSON))
    skipped += [(a, "Livid shared mailbox — no Person note", "colleague") for a in cfg["role"]
                if a not in plan["roles"]]
    skipped += [(p, "no reader output (" + (written.get(p, {}).get("meta", {}).get("skip") or
                 ("no threads in window" if not plan["persons"][p]["threads"] else "see unsure")) + ")",
                 plan["persons"][p]["category"]) for p in missing]
    H.append(f"<p>Contacts without a note: {len(skipped)}</p>")
    H.append(table(["address", "why", "category"], skipped))
    H.append(f"<p>Notes whose <code>organization</code> waits for the livid-kb batch: <b>{len(waits)}</b>; "
             f"notes without an organization (individuals, shareholders on private addresses): {len(no_org)}.</p>")
    H.append(table(["note", "category", "organization (proposed)"],
                   sorted((x["file"], x["category"], x["organization"].replace("kb://livid/organizations/", ""))
                          for x in waits)))
    ex = plan["excluded_threads"]
    H.append("<p>Never fetched (decided from headers): " + "; ".join(
        f"{k}: {v} threads / {plan['excluded_messages'][k]} messages" for k, v in ex.items())
        + ". Single messages skipped: " + "; ".join(f"{k}: {v}" for k, v in plan["skipped_messages"].items())
        + f". Full content capped at the newest {plan['thread_cap']} threads per person "
        f"({plan['threads_over_cap']} person-threads beyond it are covered by the header-only index).</p>")

    # 2. Voice drafts.
    H.append("<h2 id='s2'>2. Voice profile drafts — review carefully (not written to kb/voice yet)</h2>")
    vs = {c: v["messages"] for c, v in prepared["voice"].items()}
    H.append("<p>Usable sent messages per recipient category (12 months): "
             + ", ".join(f"{e(c)} {n}" for c, n in sorted(vs.items(), key=lambda x: -x[1])) + "</p>")
    order = ["general"] + sorted(Path(p).stem for p in glob.glob(os.path.join(s4.STEP4, "voice", "*.md"))
                                 if Path(p).stem != "general")
    for c in order:
        p = os.path.join(s4.STEP4, "voice", c + ".md")
        if os.path.exists(p):
            H.append(f"<details open><summary>{e(c)}</summary>{md(open(p).read())}</details>")

    # 3. Spot-check: 10 notes, spread over categories.
    rnd = random.Random(args.seed)
    pool = list(written.values())
    rnd.shuffle(pool)
    pick, need = [], [("colleague", 2), (("supplier", "manufacturer"), 2), (("advisor", "board-owner"), 1)]
    for cats, n in need:
        cats = (cats,) if isinstance(cats, str) else cats
        pick += [x for x in pool if x["category"] in cats and x not in pick][:n]
    seen_cats = Counter(x["category"] for x in pick)
    for x in pool:
        if len(pick) >= 10:
            break
        if x not in pick and seen_cats[x["category"]] < 2:
            pick.append(x)
            seen_cats[x["category"]] += 1
    H.append("<h2 id='s3'>3. Ten Person notes for spot-check</h2>")
    for x in pick:
        H.append(f"<details open><summary>{e(x['file'])} — {e(x['category'])}</summary>"
                 f"{md((REPO / x['file']).read_text(encoding='utf-8'))}</details>")

    # 4. Batch.
    H.append("<h2 id='s4'>4. livid-kb batch (proposal; file: cache/step4/livid-kb-batch.md)</h2>")
    H.append(md(open(os.path.join(s4.STEP4, "livid-kb-batch.md")).read()))

    # 5. Unsure.
    H.append("<h2 id='s5'>5. Unsure — please decide</h2>")
    up = os.path.join(s4.STEP4, "unsure.md")
    if os.path.exists(up):
        H.append(md(open(up).read()))
    rows = []
    for x in written.values():
        m = x["meta"]
        for k in ("category_check", "org_check", "same_person", "unsure"):
            v = (m.get(k) or "").strip()
            if v and v not in ("ok", "-", "—", "none", "None"):
                rows.append((x["file"], x["category"], k, v))
    H.append(f"<p>Reader notes per Person note ({len(rows)}):</p>")
    H.append(table(["note", "category", "kind", "note from reader"], rows))

    # Top 50.
    H.append("<h2 id='s6'>Top 50 (3-year window), ranked by threads Kriss replied in over 3 years</h2>")
    tr = []
    for i, p in enumerate(plan["top50"], 1):
        v = plan["persons"][p]
        tr.append((i, written.get(p, {}).get("file", p), v["category"], v["replied_threads"], v["replied_12m"]))
    H.append(table(["#", "note", "category", "replied 3y", "replied 12m"], tr, numeric=("#", "replied 3y", "replied 12m")))
    H.append(f"<script>{JS}</script>")
    out = os.path.join(s4.STEP4, "report.html")
    open(out, "w").write("\n".join(H))
    print(out)


if __name__ == "__main__":
    main()
