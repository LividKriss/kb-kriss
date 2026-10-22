#!/usr/bin/env python3
"""Render the step 3 checkpoint as one local HTML page, from the CSVs build_contacts.py wrote.

    report_html.py [--months N] [--top 150]

Writes cache/step3[-<N>m]/report.html (outside the repo). Open it in a browser; nothing is uploaded.
"""
import argparse
import csv
import html
import os
from collections import defaultdict

APP_DIR = os.path.expanduser("~/Library/Application Support/kb-kriss")

CSS = """
:root{--bg:#fff;--fg:#1d1d1f;--muted:#6e6e73;--line:#e5e5ea;--head:#f5f5f7;--hl:#fff7d6}
@media (prefers-color-scheme:dark){:root{--bg:#1c1c1e;--fg:#f2f2f7;--muted:#a1a1a6;--line:#38383a;--head:#2c2c2e;--hl:#3a3420}}
body{background:var(--bg);color:var(--fg);font:13px/1.45 -apple-system,system-ui,sans-serif;margin:0;padding:16px 24px}
h1{font-size:20px}h2{font-size:16px;margin-top:32px}p,li{color:var(--muted);max-width:900px}
table{border-collapse:collapse;width:100%;margin:8px 0}th,td{border-bottom:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
th{background:var(--head);position:sticky;top:0;cursor:pointer;white-space:nowrap}td.n{text-align:right;font-variant-numeric:tabular-nums}
tr.q td.cat{background:var(--hl)}.wrap{overflow-x:auto}
"""
JS = """
document.querySelectorAll('table.sort th').forEach((th,i)=>th.onclick=()=>{
 const tb=th.closest('table').tBodies[0],rows=[...tb.rows],asc=th.dataset.asc!=='1';th.dataset.asc=asc?'1':'0';
 rows.sort((a,b)=>{const x=a.cells[i].innerText,y=b.cells[i].innerText,nx=parseFloat(x),ny=parseFloat(y);
  const c=(!isNaN(nx)&&!isNaN(ny))?nx-ny:x.localeCompare(y);return asc?c:-c});rows.forEach(r=>tb.appendChild(r))});
"""


def read(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def table(headers, rows, numeric=(), cls="sort", row_class=None):
    e = html.escape
    out = [f'<div class="wrap"><table class="{cls}"><thead><tr>']
    out += [f"<th>{e(h)}</th>" for h in headers]
    out.append("</tr></thead><tbody>")
    for r in rows:
        rc = f' class="{row_class(r)}"' if row_class else ""
        out.append(f"<tr{rc}>")
        for h, v in zip(headers, r):
            c = ' class="n"' if h in numeric else (' class="cat"' if h == "category" else "")
            out.append(f"<td{c}>{e(str(v))}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=0)
    ap.add_argument("--top", type=int, default=150)
    args = ap.parse_args()
    d = os.path.join(APP_DIR, "cache", "step3" + (f"-{args.months}m" if args.months else ""))
    contacts = read(os.path.join(d, "contacts.csv"))
    dropped = read(os.path.join(d, "dropped.csv"))
    proposed = read(os.path.join(d, "proposed_orgs.csv"))
    invoice = read(os.path.join(d, "invoice_traffic.csv"))
    window = f"last {args.months} months" if args.months else "3 years"

    # 1. Summary by category.
    s = defaultdict(lambda: [0, 0, 0, 0, 0])
    for c in contacts:
        r = s[c["category"]]
        r[0] += 1
        r[1] += int(c["in"])
        r[2] += int(c["out"])
        r[3] += int(c["replied_threads"])
        r[4] += int(c["org"] != "")
    summary = [(k, *v) for k, v in sorted(s.items(), key=lambda x: -x[1][0])]

    # 2. Top contacts.
    top = [(i, c["address"], c["name"], c["org"].replace("kb://livid/organizations/", ""), c["org_match"],
            c["in"], c["out"], c["replied_threads"], c["replied_12m"], c["first"], c["last"], c["category"])
           for i, c in enumerate(contacts[:args.top], 1)]

    # 3. Dropped noise, per base domain.
    dd = defaultdict(lambda: {"contacts": 0, "msgs": 0, "rules": set(), "examples": set()})
    for r in dropped:
        dom = r["domain"]
        x = dd[dom]
        x["contacts"] += int(r["contacts"])
        x["msgs"] += int(r["msgs"])
        x["rules"].add(r["rule"])
        x["examples"].update(r["examples"].split())
    drop_rows = sorted(((dom, v["msgs"], v["contacts"], "; ".join(sorted(v["rules"])),
                         " ".join(sorted(v["examples"])[:3])) for dom, v in dd.items()), key=lambda x: -x[1])
    by_rule = defaultdict(lambda: [0, 0, 0])
    for r in dropped:
        b = by_rule[r["rule"]]
        b[0] += 1
        b[1] += int(r["contacts"])
        b[2] += int(r["msgs"])

    # 5. Threshold options.
    thr = []
    for t in (1, 2, 3, 4, 5):
        thr.append((f">= {t}", sum(1 for c in contacts if int(c["replied_12m"]) >= t),
                    sum(1 for c in contacts if int(c["replied_threads"]) >= t)))

    parts = [f"<!doctype html><meta charset=utf-8><title>Step 3 checkpoint</title><style>{CSS}</style>",
             f"<h1>Backfill pass 1, contact table ({window})</h1>",
             f"<p>{len(contacts)} contacts kept. Headers only. Categories ending in “?” and “?” alone are guesses "
             "for you to correct. Click a column header to sort.</p>",
             "<h2>1. Summary by category</h2>",
             table(["category", "contacts", "msgs in", "msgs out", "replied threads", "matched to org"], summary,
                   numeric={"contacts", "msgs in", "msgs out", "replied threads", "matched to org"}),
             f"<h2>2. Top {args.top} contacts</h2><p>Ranked by threads where Kriss replied, then messages out, "
             "then in. Org match: domain = via email_domains, name / display name = guessed from the name.</p>",
             table(["#", "address", "name", "org", "match", "in", "out", "replied", "replied 12m", "first", "last",
                    "category"], top, numeric={"#", "in", "out", "replied", "replied 12m"},
                   row_class=lambda r: "q" if "?" in r[-1] else ""),
             "<h2>3. Dropped noise</h2>",
             table(["rule", "domains", "contacts", "messages"], [(k, *v) for k, v in by_rule.items()],
                   numeric={"domains", "contacts", "messages"}),
             f"<p>Mail addressed to invoice@ excluded as invoice traffic: "
             f"{sum(int(r['msgs']) for r in invoice)} messages from {len(invoice)} senders.</p>",
             table(["domain", "messages", "contacts", "rule", "example local parts"], drop_rows[:200],
                   numeric={"messages", "contacts"}),
             "<h2>4. Proposed new Organizations / email_domains</h2><p>Unmatched business domains with at least "
             "one reply from Kriss or two messages out. Freemail and Livid domains excluded.</p>",
             table(["domain", "contacts", "in", "out", "replied threads", "hint", "names"],
                   [(p["domain"], p["contacts"], p["in"], p["out"], p["replied_threads"], p["hint"], p["names"])
                    for p in proposed], numeric={"contacts", "in", "out", "replied threads"}),
             "<h2>5. Threshold for step 4</h2>",
             table(["replied threads", "contacts (last 12 months)", f"contacts ({window})"], thr, cls="",
                   numeric={"contacts (last 12 months)", f"contacts ({window})"}),
             f"<script>{JS}</script>"]
    path = os.path.join(d, "report.html")
    with open(path, "w") as f:
        f.write("".join(parts))
    print(path)


if __name__ == "__main__":
    main()
