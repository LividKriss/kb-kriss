#!/usr/bin/env python3
"""Backfill pass 2: the livid-kb proposal batch for Kriss (proposal only; nothing is written to livid-kb).

    build_batch.py

Reads  cache/step4/org_map.json, cache/step4/written.json, cache/step4/facts/*.md,
       cache/step3/proposed_orgs.csv, review/corrections.json, ../livid-kb/kb/organizations/
Writes cache/step4/livid-kb-batch.md, grouped so Kriss can approve per group:
  1 New Organizations (1a linked to step-4 people, 1b the rest of the step-3 proposals)
  2 Changes to existing orgs (email_domains, renames, moves suppliers/ -> manufacturers/ with every link)
  3 Company facts (target doc, one line, source thread)
  4 Ideas
"""
import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step4lib as s4  # noqa: E402
from build_contacts import base_domain  # noqa: E402
from write_people import ORG_MAP, kebab  # noqa: E402

LIVID = Path(__file__).resolve().parents[2].parent / "livid-kb"
OUT = os.path.join(s4.STEP4, "livid-kb-batch.md")
FOLDER = {"supplier": "suppliers", "customer": "customers", "manufacturer": "manufacturers",
          "advisor": "advisors", "authority": "authorities"}
# Person category -> Organization kind (livid-kb has no landlord / 3PL / partner kinds).
KIND = {"supplier": "supplier", "manufacturer": "manufacturer", "wholesale-customer": "customer",
        "3pl-client": "customer", "advisor": "advisor", "authority": "authority", "landlord": "supplier",
        "partner-press": "supplier", "vendor-sales": "supplier", "investor": "advisor"}
# Garment factories filed under suppliers/ (step 3 review, progress.md); target id where it changes.
MOVES = {"stork-texteis": "stork-texteis", "lisama": "lisama", "texgoios": "mill-tex", "afonso": "afonso",
         "dia-exemplar": "dia-exemplar", "officocta": "officocta"}


def domain_paths(org_map):
    """Sender domain -> organization path (from step-4 people, roles and the org map), for facts keyed by domain."""
    out = {d: h["path"] for d, h in org_map["by_domain"].items()}
    plan = json.load(open(s4.PLAN))
    prepared = json.load(open(os.path.join(s4.STEP4, "prepared.json")))
    for p, v in prepared["people"].items():
        if v.get("organization"):
            out.setdefault(s4.domain(p), v["organization"].replace("kb://livid/organizations/", ""))
    for a, r in plan["roles"].items():
        if r["org"]:
            out.setdefault(s4.domain(a), r["org"].replace("kb://livid/organizations/", ""))
    return out


def facts(paths=None):
    paths = paths or {}
    out = []
    for path in sorted(glob.glob(os.path.join(s4.STEP4, "facts", "*.md"))):
        for line in open(path):
            m = re.match(r"\s*-\s*org:\s*(.*?)\s*\|\s*kind:\s*(.*?)\s*\|\s*fact:\s*(.*?)\s*\|\s*source:\s*(\S*)", line)
            if m:
                org, kind, fact, src = m.groups()
                org = org.replace("kb://livid/", "").replace("organizations/", "").strip("`")
                org = paths.get(org) or paths.get(base_domain(org)) or org
                out.append({"org": org, "kind": kind.strip(), "fact": fact, "source": src.strip("`")})
    return out


def link(tid):
    return f"[{tid}](https://mail.google.com/mail/u/0/#all/{tid})" if re.fullmatch(r"[0-9a-f]{12,}", tid) else tid


def refs(org_id, livid_files):
    """livid-kb files that mention the org (its own doc, indexes and the log excluded)."""
    pat = re.compile(rf"\b{re.escape(org_id)}\b")
    own = LIVID / "kb" / "organizations" / "suppliers" / f"{org_id}.md"
    return [str(p.relative_to(LIVID)) for p in livid_files
            if p.name not in ("index.md", "log.md") and p != own and pat.search(p.read_text(encoding="utf-8"))]


def main():
    org_map = json.load(open(ORG_MAP))
    written = json.load(open(os.path.join(s4.STEP4, "written.json")))["written"]
    corr = s4.load_corrections()
    fs = facts(domain_paths(org_map))
    by_org = defaultdict(list)
    for f in fs:
        by_org[f["org"]].append(f)
    livid_files = [p for p in (LIVID / "kb").rglob("*.md")] + [p for p in (LIVID / ".claude").rglob("*.md")]
    people_by_org = defaultdict(list)
    for w in written.values():
        if w["organization"]:
            people_by_org[w["organization"].replace("kb://livid/organizations/", "")].append(w)

    L = ["# livid-kb batch — step 4 proposal (2026-10-23)", "",
         "Proposal only: nothing has been written to livid-kb. Approve per group (e.g. \"1a ok except X\", \"2 ok\").",
         "On approval each group is written per livid-kb AGENTS.md (template, `draft`, a log entry per group, "
         "`build_index.py`, `validate.py`). A move = rename + update every link; deleting or changing a type "
         "needs a second confirmation there.",
         "Facts below are as the readers wrote them and still name individual contacts; livid-kb records roles, not "
         "people (AGENTS.md §1.4), so names become roles when written. Bank details, passwords and personal data were "
         "left out; amounts are business figures only.", ""]

    # 1a: new orgs linked to step-4 people.
    new = {}
    for key, hit in list(org_map["by_domain"].items()) + list(org_map["by_address"].items()):
        if hit.get("new"):
            e = new.setdefault(hit["path"], {"title": hit.get("title", ""), "kind": hit.get("kind", ""),
                                              "domains": set(), "flags": set()})
            e["title"] = e["title"] or hit.get("title", "")
            e["kind"] = e["kind"] or hit.get("kind", "")
            if "@" not in key and key not in s4.FREEMAIL and "no email_domains" not in hit.get("flag", ""):
                e["domains"].add(key)
            if hit.get("flag"):
                e["flags"].add(hit["flag"])
    linked = {p: e for p, e in new.items() if people_by_org.get(p) or any(
        r["org"] == p for r in [])}
    L += [f"## 1. New Organizations", "", f"### 1a. Linked to step-4 people ({len(linked)})", "",
          "Needed for the Person notes' `organization` links (the validator warns until these exist). "
          "Customers and 3PL clients go in `customers/`, factories and production agents in `manufacturers/`, "
          "landlords and other vendors in `suppliers/` (livid-kb has no landlord kind).", ""]
    for path in sorted(linked):
        e = linked[path]
        kind = e["kind"] or Path(path).parts[0].rstrip("s")
        ppl = people_by_org.get(path, [])
        L.append(f"#### `organizations/{path}` — {e['title']}")
        L.append(f"- kind: `{kind}` · email_domains: {', '.join(sorted(e['domains'])) or '—'}")
        L.append(f"- Person notes linking here: {len(ppl)} ({', '.join(sorted({w['category'] for w in ppl}))})")
        for f in by_org.get(path, []) + [f for d in e["domains"] for f in by_org.get(d, [])]:
            if f["kind"] in ("new-org-info", "company-fact"):
                L.append(f"- {f['fact']} ({link(f['source'])})")
        for fl in sorted(e["flags"]):
            L.append(f"- **Unsure:** {fl}")
        L.append("")

    # 1b: the rest of the step-3 proposals.
    known = {d for d in org_map["by_domain"]} | {base_domain(d) for d in org_map["by_domain"]}
    rest = [r for r in csv.DictReader(open(os.path.join(s4.CACHE, "step3", "proposed_orgs.csv")))
            if r["domain"] not in known and base_domain(r["domain"]) not in known]
    fix = corr.get("domains", {})
    L += [f"### 1b. Other step-3 proposals ({len(rest)})", "",
          "Unmatched business domains with real traffic, no step-4 Person note. Path guessed from the domain and "
          "the category from the step-3 review; name and details to be filled from the org's own mail when written. "
          "Strike any that aren't worth a doc.", "",
          "| proposed path | kind | email_domains | category (review) | people seen | note |", "|---|---|---|---|---|---|"]
    for r in rest:
        f = fix.get(r["domain"]) or fix.get(base_domain(r["domain"])) or {}
        cat = f.get("category") or r["hint"]
        kind = KIND.get(cat.strip("?"), "")
        stem = kebab(base_domain(r["domain"]).split(".")[0])
        path = f"{FOLDER.get(kind, '?')}/{stem}.md" if kind else "?"
        note = (f.get("note") or "").replace("|", "/")
        L.append(f"| `{path}` | {kind or '?'} | {r['domain']} | {cat} | {r['contacts']} | {note} |")
    L.append("")

    # 2: changes to existing orgs.
    L += ["## 2. Changes to existing organizations", "", "### 2a. New `email_domains`", "",
          "| organization | add | why |", "|---|---|---|"]
    for d, f in sorted(fix.items()):
        org = (f.get("org") or "").replace("kb://livid/organizations/", "")
        doc = LIVID / "kb" / "organizations" / org if org else None
        if doc and doc.exists():
            have = re.search(r"^email_domains:\s*\[(.*?)\]", doc.read_text(encoding="utf-8"), re.M)
            have = {x.strip() for x in have.group(1).split(",")} if have else set()
            if d not in have and d not in s4.FREEMAIL:
                L.append(f"| `{org}` | {d} | {(f.get('note') or 'step 3 review').replace('|', '/')} |")
    for d, hit in sorted(org_map["by_domain"].items()):
        if not hit.get("new") and "flag" not in hit:
            L.append(f"| `{hit['path']}` | {d} | step 4: sender domain of its people |")
        elif not hit.get("new") and "email_domains" in hit.get("flag", ""):
            L.append(f"| `{hit['path']}` | {d} | **unsure:** {hit['flag']} |")
    L.append("")

    L += ["### 2b. Garment factories: `suppliers/` → `manufacturers/` (kind `manufacturer`)", "",
          "Step 3 review: their people are `manufacturer`. Texgoios is renamed **Mill-Tex** in the same move "
          "(new title, `email_domains` + milltex.pt). Links that must change:", ""]
    for old, new_id in MOVES.items():
        files = refs(old, livid_files)
        kriss = [w["file"] for w in written.values() if w["organization"].endswith(f"suppliers/{old}.md")]
        L.append(f"- `suppliers/{old}.md` → `manufacturers/{new_id}.md`"
                 + (" (rename: Texgoios → Mill-Tex)" if old != new_id else ""))
        L.append(f"  - livid-kb: {', '.join(f'`{x}`' for x in files) or 'no other links'}")
        L.append(f"  - kb-kriss Person notes (`organization`): {len(kriss)}")
    others = ["zhejiang-springair", "forever-ind", "goldfine-asia", "pro-trading", "primeboots", "dibella-india",
              "jose-magalhaes", "outfit21"]
    L += ["", "**Unsure:** these are also in the production-partners coding rule but were not on the move list; "
          "move them too? " + ", ".join(f"`suppliers/{o}.md`" for o in others)
          + ". (Petter Korseth is the production agent for Springair/Bellanza.)", ""]

    L += ["### 2c. Eplehuset: customer as well as supplier", "",
          "`suppliers/eplehuset.md` has kind `supplier` (leased office hardware). It is mainly a **customer**: Livid "
          "produces and stores their uniforms; orders arrive through a webshop run by Konsis as PrintCollect emails. "
          "An Organization has one `kind`. Options: (a) keep it in `suppliers/` and add a \"Customer relationship\" "
          "section; (b) move to `customers/eplehuset.md` (kind customer) with a \"Also a supplier\" section — links: "
          + ", ".join(f"`{x}`" for x in refs("eplehuset", livid_files)) + ". Recommendation: (b), since most "
          "traffic is the uniform business.", ""]

    # Additions decided with Kriss at the checkpoint (cache/step4/batch_extra.md), after group 2.
    extra = os.path.join(s4.STEP4, "batch_extra.md")
    if os.path.exists(extra):
        L += open(extra).read().splitlines() + [""]

    # 3 and 4.
    L += ["## 3. Company facts found while reading", "",
          "For existing docs; one line each with the source thread. New-org facts are listed under 1a.", ""]
    existing = defaultdict(list)
    for f in fs:
        if f["kind"] == "company-fact" and f["org"] not in new:
            existing[f["org"]].append(f)
    for org in sorted(existing):
        L.append(f"- **`{org}`**")
        for f in existing[org]:
            L.append(f"  - {f['fact']} ({link(f['source'])})")
    L += ["", "## 4. Ideas (for a later livid-kb process or step 5 triage rule)", ""]
    for f in fs:
        if f["kind"] == "idea":
            L.append(f"- {f['fact']} — `{f['org']}` ({link(f['source'])})")
    open(OUT, "w").write("\n".join(L) + "\n")
    print(f"wrote {OUT}: 1a {len(linked)}, 1b {len(rest)}, facts {len(fs)}")


if __name__ == "__main__":
    main()
