#!/usr/bin/env python3
"""Backfill pass 1: build the contact table from the headers fetched by fetch_headers.py.

    build_contacts.py [--top 150] [--months N]

--months N limits the table to the last N months (output in cache/step3-<N>m/), e.g. for a preview
while the 3-year fetch is still running.

Reads  cache/headers/messages.jsonl and the Organization docs in ../livid-kb/kb/organizations/.
Writes cache/step3/ (outside the repo, never committed):
  contacts.csv        every kept contact
  top.md              the top N contacts as a table for review
  dropped.csv         dropped noise, per domain and rule
  invoice_traffic.csv senders of mail addressed to invoice@ (excluded from the table)
  proposed_orgs.csv   unmatched business domains with real traffic
  summary.md          summary by category, dropped noise, threshold options

Run with the venv outside the repo:
  "~/Library/Application Support/kb-kriss/venv/bin/python" scripts/email/build_contacts.py
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
from collections import Counter, defaultdict
from email.utils import getaddresses
from pathlib import Path

APP_DIR = os.path.expanduser("~/Library/Application Support/kb-kriss")
MSG_PATH = os.path.join(APP_DIR, "cache", "headers", "messages.jsonl")
OUT_DIR = os.path.join(APP_DIR, "cache", "step3")
LIVID_KB = Path(__file__).resolve().parents[2].parent / "livid-kb"

sys.path.insert(0, str(LIVID_KB / "tools"))
from kblib import split_frontmatter  # noqa: E402

KNOWN_OWN = {"kristoffer@livid.no", "kristoffer@lividjeans.com"}
INTERNAL_DOMAINS = {"livid.no", "lividjeans.com"}
INVOICE_INBOXES = {"invoice@lividjeans.com", "invoice@livid.no"}

# Shared platforms send on behalf of many companies: never a contact, never an org match (progress.md).
PLATFORM_DOMAINS = ["xero.com", "via.tripletex.no", "fiken.no", "xledger.net", "e-conomic.com",
                    "delivery.payex.com", "traede.com", "stripe.com", "mail.poweroffice.net",
                    "equity.credit", "equity.no", "fortnox.se", "exact.com", "superhuman.com"]
# Further platforms found in step 3 (proposed for the list above): they send on behalf of other companies,
# so a sender there is kept as a contact but never matched to an organization.
NO_ORG_MATCH = ["vismaonline.com", "microsoftonline.com", "insight.ly", "faktura.poweroffice.net",
                "gorgias.com", "zendesk.com", "freshdesk.com", "hubspot.com", "docusign.net", "visma.com"]
NOISE_DOMAINS = ["news.modeinfo.com", "paddlersuk.com", "email.kinto-europe.com", "labels-things.com",
                 "later.com", "mail.adobe.com", "hs-send.com", "tvstore.fr", "123lyd.no", "123lyd.com"]
FREEMAIL = {"gmail.com", "googlemail.com", "hotmail.com", "hotmail.no", "outlook.com", "live.com",
            "live.no", "icloud.com", "me.com", "mac.com", "yahoo.com", "yahoo.no", "online.no",
            "msn.com", "aol.com", "protonmail.com", "proton.me", "gmx.com", "gmx.de", "hotmail.co.uk",
            "qq.com", "163.com", "126.com", "naver.com", "libero.it", "sapo.pt", "yahoo.co.jp"}
AUTOMATED_LOCAL = re.compile(
    r"(^|[._-])(no-?reply|do-?not-?reply|donotreply|noreply|notifications?|notify|alerts?|mailer-daemon|"
    r"postmaster|bounces?|newsletters?|news|marketing|nyhetsbrev|automated|system|calendar-notification|"
    r"invitations?|updates?|digest|mailer|hello|info|support|service|kundeservice|team)([._+-]|$)")
MULTI_PART_TLDS = {"co.uk", "com.au", "co.jp", "com.br", "co.nz", "com.tr", "co.kr", "com.cn",
                   "com.hk", "co.in", "com.pt", "com.es", "co.za", "com.sg", "com.tw", "com.mx"}
# Heuristic categories for unmatched domains; always shown with "?" for Kriss to confirm.
AUTHORITY_HINTS = ["skatteetaten.no", "brreg.no", "toll.no", "tolletaten.no", "nav.no", "altinn.no",
                   "kommune.no", "oslo.kommune.no", "regjeringen.no", "politiet.no", "datatilsynet.no",
                   "arbeidstilsynet.no", "ssb.no", "domstol.no", "innkreving.no", "ehf.no"]
ADVISOR_HINTS = ["dnb.no", "nordea.no", "nordea.com", "handelsbanken.no", "sparebank1.no", "danskebank.no",
                 "seb.no", "kpmg.no", "pwc.com", "ey.com", "deloitte.no", "bdo.no", "wiersholm.no",
                 "thommessen.no", "schjodt.com", "wikborg.no", "kvale.no", "grette.no", "simonsen.no",
                 "advokat", "revisjon", "regnskap"]


def base_domain(domain):
    parts = domain.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in MULTI_PART_TLDS:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def in_list(domain, lst):
    return any(domain == d or domain.endswith("." + d) or base_domain(domain) == d for d in lst)


LEGAL = r"\b(as|asa|ab|aps|a/s|ltd|limited|gmbh|srl|s\.r\.l|spa|s\.p\.a|sa|inc|llc|bv|oy|kk|co)\b"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", re.sub(LEGAL, "", s.lower()))


def load_orgs():
    orgs = []
    for p in sorted((LIVID_KB / "kb" / "organizations").rglob("*.md")):
        if p.name == "index.md":
            continue
        fm, _, _ = split_frontmatter(p.read_text(encoding="utf-8"))
        if not fm or fm.get("type") != "Organization":
            continue
        orgs.append({"addr": "kb://livid/" + str(p.relative_to(LIVID_KB / "kb")),
                     "title": fm.get("title", ""), "kind": fm.get("kind", ""),
                     "domains": [d.lower() for d in fm.get("email_domains") or []],
                     "slug": norm(p.stem), "ntitle": norm(fm.get("title", "")),
                     "first": p.stem.split("-")[0]})
    return orgs


def words(s):
    return " " + " ".join(re.findall(r"[a-z0-9]+", norm_spaced(s))) + " "


def norm_spaced(s):
    return re.sub(LEGAL, " ", s.lower())


def match_org(domain, names, orgs):
    if in_list(domain, NO_ORG_MATCH):
        return None, ""
    for o in orgs:
        if in_list(domain, o["domains"]):
            return o, "domain"
    stem = norm(base_domain(domain).split(".")[0])
    if domain not in FREEMAIL and len(stem) >= 3:
        for o in orgs:
            if ((len(stem) >= 4 and stem in (o["slug"], o["ntitle"]))
                    or (len(stem) >= 4 and len(o["slug"]) >= 5 and o["slug"] in stem)
                    or (len(stem) >= 6 and o["slug"].startswith(stem))
                    or stem == o["first"]):  # dht.no -> dht-corporate-finance
                return o, "name"
    # Display name, e.g. "Helena - STORKTEXTEIS": the org title (6+ letters) as whole words inside it.
    for n in names:
        wn = words(n)
        for o in orgs:
            wt = words(o["title"])
            if len(wt.replace(" ", "")) >= 6 and wt in wn:
                return o, "display name"
    return None, ""


def addrs(value):
    return [a.lower().strip() for _, a in getaddresses([value or ""]) if "@" in a]


def is_bulk(h):
    prec = h.get("Precedence", "").lower()
    auto = h.get("Auto-Submitted", "").lower()
    return bool(h.get("List-Unsubscribe") or h.get("List-Id") or prec in ("bulk", "list", "junk")
                or (auto and auto != "no") or h.get("X-Autoreply") or h.get("X-Autorespond"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=150)
    ap.add_argument("--months", type=int, default=0, help="only the last N months (default: everything)")
    args = ap.parse_args()
    global OUT_DIR
    if args.months:
        OUT_DIR += f"-{args.months}m"
    os.makedirs(OUT_DIR, exist_ok=True)

    msgs = [json.loads(line) for line in open(MSG_PATH) if line.strip()]
    if args.months:
        since = (dt.datetime.now() - dt.timedelta(days=round(args.months * 30.44))).timestamp() * 1000
        msgs = [m for m in msgs if m["internalDate"] >= since]
    print(f"{len(msgs)} messages")

    # Kriss's own addresses: the known two plus any Livid From address on 5+ SENT messages (send-as aliases).
    sent_from = Counter(a for m in msgs if "SENT" in m["labelIds"] for a in addrs(m["headers"].get("From")))
    own = KNOWN_OWN | {a for a, n in sent_from.items() if n >= 5 and in_list(a.split("@")[1], INTERNAL_DOMAINS)}

    names = defaultdict(Counter)
    for m in msgs:
        h = m["headers"]
        for field in ("From", "To", "Cc"):
            for name, a in getaddresses([h.get(field) or ""]):
                if "@" in a and name.strip().strip("'\""):
                    names[a.lower().strip()][name.strip().strip("'\"")] += 1

    # Per contact counters.
    c = defaultdict(lambda: {"in": 0, "out": 0, "bulk_in": 0, "threads": set(), "first": None, "last": None,
                             "replied": set(), "replied_12m": set()})
    invoice_traffic = Counter()
    platform = Counter()
    by_thread = defaultdict(list)
    for m in msgs:
        h = m["headers"]
        frm = (addrs(h.get("From")) or [""])[0]
        rcpt = addrs(h.get("To")) + addrs(h.get("Cc"))
        out = "SENT" in m["labelIds"] or frm in own
        if not out and INVOICE_INBOXES & set(rcpt):
            invoice_traffic[frm] += 1
            continue
        targets = [a for a in rcpt if a not in own] if out else ([frm] if frm and frm not in own else [])
        when = dt.datetime.fromtimestamp(m["internalDate"] / 1000)
        for a in targets:
            dom = a.split("@")[1]
            if in_list(dom, PLATFORM_DOMAINS) or a.split("@")[0] == "mailer-daemon":
                platform[a] += 1
                continue
            r = c[a]
            r["out" if out else "in"] += 1
            if not out and is_bulk(h):
                r["bulk_in"] += 1
            r["threads"].add(m["threadId"])
            r["first"] = min(r["first"] or when, when)
            r["last"] = max(r["last"] or when, when)
        by_thread[m["threadId"]].append((m["internalDate"], out, frm))

    # Kriss replied = a SENT message in the thread after a message from that contact.
    cutoff_12m = (dt.datetime.now() - dt.timedelta(days=365)).timestamp() * 1000
    for tid, items in by_thread.items():
        items.sort()
        seen = set()
        for ts, out, frm in items:
            if out:
                for a in seen:
                    if a in c:
                        c[a]["replied"].add(tid)
                        if ts >= cutoff_12m:
                            c[a]["replied_12m"].add(tid)
            elif frm:
                seen.add(frm)

    orgs = load_orgs()
    colleague_names = {norm(names[a].most_common(1)[0][0]) for a in c
                       if in_list(a.split("@")[1], INTERNAL_DOMAINS) and names[a]}
    kept, dropped = [], defaultdict(lambda: {"contacts": 0, "msgs": 0, "examples": set()})
    for a, r in c.items():
        local, dom = a.split("@", 1)
        engaged = r["out"] > 0 or r["replied"]
        wrote_to = r["out"] > 0  # a forward of their mail sets "replied" but is not engagement with a robot
        internal = in_list(dom, INTERNAL_DOMAINS)
        rule = None
        if internal:
            pass  # colleagues and shared Livid mailboxes are never noise
        elif AUTOMATED_LOCAL.search(local) and not wrote_to:
            rule = "automated sender (local part)"
        elif in_list(dom, NOISE_DOMAINS) and not engaged:
            rule = "known noise domain"
        elif not wrote_to and r["bulk_in"] >= max(1, r["in"] / 2):
            rule = "bulk/list/auto headers, never answered"
        elif not engaged and r["in"] <= 2:
            rule = "one-off, never answered"
        if rule:
            d = dropped[(dom, rule)]
            d["contacts"] += 1
            d["msgs"] += r["in"] + r["out"]
            if len(d["examples"]) < 2:
                d["examples"].add(local)
            continue

        org, how = (None, "") if internal else match_org(dom, names[a], orgs)
        if internal:
            cat = "colleague"
        elif dom in FREEMAIL and ("livid" in local or "past" in local
                                  or norm((names[a].most_common(1) or [("", 0)])[0][0]) in colleague_names):
            cat = "colleague?"  # store/workshop mailboxes, or a colleague's private address
        elif org:
            cat = org["kind"] or "?"
        elif in_list(dom, AUTHORITY_HINTS) or dom.endswith(".kommune.no"):
            cat = "authority?"
        elif any(h in dom for h in ADVISOR_HINTS):
            cat = "advisor?"
        elif dom in FREEMAIL:
            cat = "private?"
        else:
            cat = "?"
        kept.append({
            "address": a, "name": (names[a].most_common(1) or [("", 0)])[0][0], "domain": dom,
            "org": org["addr"] if org else "", "org_match": how, "in": r["in"], "out": r["out"],
            "threads": len(r["threads"]), "replied_threads": len(r["replied"]),
            "replied_12m": len(r["replied_12m"]), "first": r["first"].date().isoformat(),
            "last": r["last"].date().isoformat(), "category": cat,
            "note": "never answered" if not engaged else "",
        })
    kept.sort(key=lambda k: (-k["replied_threads"], -k["out"], -k["in"]))

    fields = list(kept[0].keys())
    with open(os.path.join(OUT_DIR, "contacts.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(kept)

    with open(os.path.join(OUT_DIR, "top.md"), "w") as f:
        f.write("| # | address | name | org (match) | in | out | replied thr (12m) | first–last | category |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for i, k in enumerate(kept[:args.top], 1):
            org = f"{k['org'].replace('kb://livid/organizations/', '')} ({k['org_match']})" if k["org"] else ""
            name = k["name"].replace("|", "/")
            f.write(f"| {i} | {k['address']} | {name} | {org} | {k['in']} | {k['out']} | "
                    f"{k['replied_threads']} ({k['replied_12m']}) | {k['first']}–{k['last']} | {k['category']} |\n")

    drows = sorted(({"domain": d, "rule": rule, "contacts": v["contacts"], "msgs": v["msgs"],
                     "examples": " ".join(sorted(v["examples"]))} for (d, rule), v in dropped.items()),
                   key=lambda x: -x["msgs"])
    with open(os.path.join(OUT_DIR, "dropped.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, ["domain", "rule", "contacts", "msgs", "examples"])
        w.writeheader()
        w.writerows(drows)
    with open(os.path.join(OUT_DIR, "invoice_traffic.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sender", "msgs"])
        w.writerows(invoice_traffic.most_common())

    # Proposed organizations: unmatched, non-freemail, non-internal domains with real traffic.
    pd = defaultdict(lambda: {"contacts": 0, "in": 0, "out": 0, "replied": 0, "names": Counter(), "cats": Counter()})
    for k in kept:
        if (k["org"] or k["category"] in ("colleague", "colleague?") or k["domain"] in FREEMAIL
                or in_list(k["domain"], NO_ORG_MATCH)):
            continue
        b = base_domain(k["domain"])
        p = pd[b]
        p["contacts"] += 1
        p["in"] += k["in"]
        p["out"] += k["out"]
        p["replied"] += k["replied_threads"]
        p["names"][k["name"]] += 1
        p["cats"][k["category"]] += 1
    prop = sorted(({"domain": d, "contacts": v["contacts"], "in": v["in"], "out": v["out"],
                    "replied_threads": v["replied"], "hint": v["cats"].most_common(1)[0][0],
                    "names": "; ".join(n for n, _ in v["names"].most_common(3) if n)}
                   for d, v in pd.items() if v["replied"] >= 1 or v["out"] >= 2),
                  key=lambda x: (-x["replied_threads"], -x["out"]))
    with open(os.path.join(OUT_DIR, "proposed_orgs.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, ["domain", "contacts", "in", "out", "replied_threads", "hint", "names"])
        w.writeheader()
        w.writerows(prop)

    # Summary by category.
    s = defaultdict(lambda: [0, 0, 0, 0])
    for k in kept:
        row = s[k["category"]]
        row[0] += 1
        row[1] += k["in"]
        row[2] += k["out"]
        row[3] += k["replied_threads"]
    with open(os.path.join(OUT_DIR, "summary.md"), "w") as f:
        f.write(f"Messages: {len(msgs)}; own addresses: {', '.join(sorted(own))}\n\n")
        f.write("| category | contacts | in | out | replied threads |\n|---|---|---|---|---|\n")
        for cat, (n, i, o, rt) in sorted(s.items(), key=lambda x: -x[1][0]):
            f.write(f"| {cat} | {n} | {i} | {o} | {rt} |\n")
        f.write(f"\nKept contacts: {len(kept)}; matched to an org: {sum(1 for k in kept if k['org'])} "
                f"(domain {sum(1 for k in kept if k['org_match'] == 'domain')}, "
                f"name {sum(1 for k in kept if k['org_match'] == 'name')})\n")
        f.write(f"Platform-sender messages dropped: {sum(platform.values())} from {len(platform)} addresses\n")
        f.write(f"Invoice@ traffic excluded: {sum(invoice_traffic.values())} messages from "
                f"{len(invoice_traffic)} senders\n")
        rules = Counter()
        for d in drows:
            rules[d["rule"]] += d["contacts"]
        f.write("Dropped contacts by rule: " + ", ".join(f"{r}: {n}" for r, n in rules.most_common()) + "\n\n")
        f.write("Threshold options (replied threads in the last 12 months / ever):\n")
        for t in (1, 2, 3, 5):
            f.write(f"- >= {t}: {sum(1 for k in kept if k['replied_12m'] >= t)} contacts (12m), "
                    f"{sum(1 for k in kept if k['replied_threads'] >= t)} (3y)\n")
        orgs_with_domains = sum(1 for o in orgs if o["domains"])
        f.write(f"\nlivid-kb Organizations: {len(orgs)}, with email_domains: {orgs_with_domains}\n")
        f.write(f"Proposed organizations: {len(prop)}\n")
    print(open(os.path.join(OUT_DIR, "summary.md")).read())


if __name__ == "__main__":
    main()
