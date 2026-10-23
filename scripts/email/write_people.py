#!/usr/bin/env python3
"""Backfill pass 2: write draft Person notes from the readers' output.

    write_people.py [--dry-run]

Reads  cache/step4/plan.json, cache/step4/org_map.json, cache/step4/notes/<primary address>.md
Writes kb/people/<kebab-case-full-name>.md (status draft) and cache/step4/written.json.

Each reader file starts with a meta block, then the note body (Who … Links):
  <!-- meta
  full_name: Jane Doe
  description: One sentence.
  category_check: ok | <suggested category and why>
  org_check: ok | <suggestion>
  unsure: <anything for Kriss, or ->
  -->
Frontmatter (emails, category, organization, provenance) comes from the plan, never from the reader, so
file names, email uniqueness and organization paths are decided in one place.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step4lib as s4  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
PEOPLE = REPO / "kb" / "people"
NOTES_IN = os.path.join(s4.STEP4, "notes")
ORG_MAP = os.path.join(s4.STEP4, "org_map.json")
GENERATED_BY = "claude-code/claude-opus-5-5"


def kebab(s):
    s = unicodedata.normalize("NFKD", s.replace("ø", "o").replace("Ø", "O").replace("æ", "ae")
                              .replace("Æ", "Ae").replace("å", "a").replace("Å", "A").replace("ß", "ss"))
    s = s.encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def parse(path):
    text = open(path).read()
    m = re.match(r"\s*<!--\s*meta\s*\n(.*?)-->\s*\n", text, re.S)
    if not m:
        raise ValueError(f"{path}: no meta block")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():].strip() + "\n"


def organization(v, org_map):
    if v["org"]:
        return v["org"]
    for a in v["emails"]:
        if a in org_map["by_address"]:
            return "kb://livid/organizations/" + org_map["by_address"][a]["path"]
        if a in org_map["none"]:
            return ""
    for a in v["emails"]:
        hit = org_map["by_domain"].get(s4.domain(a))
        if hit:
            return "kb://livid/organizations/" + hit["path"]
    return ""


def org_title(org, org_map):
    """Title for a kb://livid organization: from the livid-kb doc if it exists, else the proposal."""
    rel = org.replace("kb://livid/", "")
    doc = REPO.parent / "livid-kb" / "kb" / rel
    if doc.exists():
        m = re.search(r"^title:\s*(.+)$", doc.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1).strip().strip("'\"")
    for hit in list(org_map["by_domain"].values()) + list(org_map["by_address"].values()):
        if "organizations/" + hit["path"] == rel and hit.get("title"):
            return hit["title"]
    return Path(rel).stem


def resolve_links(body, org, org_map, files, colleague=False):
    """{{organization}} -> org link; [[person:addr|Name]] -> link to that person's note (or plain name)."""
    if org:
        body = body.replace("{{organization}}", f"[{org_title(org, org_map)}]({org})")
    elif colleague:
        body = body.replace("{{organization}}", "Livid (colleague).")
    else:
        body = body.replace("{{organization}}", "No organization (individual).")

    def person(m):
        a, name = m.group(1).strip().lower(), (m.group(2) or "").strip()
        f = files.get(a)
        return f"[{name or a}](/people/{f})" if f else (name or "a contact")
    return re.sub(r"\[\[person:([^|\]]+)(?:\|([^\]]*))?\]\]", person, body)


def yaml_str(s):
    return json.dumps(s, ensure_ascii=False) if re.search(r"[:#\[\]{}&*!|>'\"%@`,]", s) or not s else s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    plan = json.load(open(s4.PLAN))
    org_map = json.load(open(ORG_MAP))
    now = dt.datetime.now().astimezone().replace(microsecond=0).isoformat()

    todo, missing = [], []
    for p, v in plan["persons"].items():
        path = os.path.join(NOTES_IN, p + ".md")
        if not os.path.exists(path):
            missing.append(p)
            continue
        meta, body = parse(path)
        if meta.get("skip"):
            missing.append(p)
            continue
        todo.append((p, v, meta, body))

    # File names: kebab-case full name; same name twice -> add the organization id.
    names = {}
    for p, v, meta, body in todo:
        names.setdefault(kebab(meta["full_name"]), []).append(p)
    bases = {}
    for p, v, meta, body in todo:
        base = kebab(meta["full_name"])
        if len(names[base]) > 1:
            org = organization(v, org_map)
            base += "-" + (Path(org).stem if org else kebab(s4.domain(p).split(".")[0]))
        bases[p] = base
    files = {a: bases[p] + ".md" for p, v, meta, body in todo for a in v["emails"]}
    written = {}
    for p, v, meta, body in todo:
        base = bases[p]
        org = organization(v, org_map)
        body = resolve_links(body, org, org_map, files, v["category"] == "colleague")
        fm = ["---", "type: Person", f"title: {yaml_str(meta['full_name'])}",
              f"description: {yaml_str(meta['description'])}", "owner: kriss", "tier: personal", "status: draft",
              "generated:", f"  by: {GENERATED_BY}", f"  at: {now}",
              "emails: [" + ", ".join(v["emails"]) + "]", f"category: {v['category']}"]
        if org:
            fm.append(f"organization: {org}")
        fm.append("---")
        out = PEOPLE / f"{base}.md"
        written[p] = {"file": str(out.relative_to(REPO)), "name": meta["full_name"], "category": v["category"],
                      "organization": org, "meta": meta}
        if not args.dry_run:
            out.write_text("\n".join(fm) + "\n\n" + body, encoding="utf-8")
    json.dump({"written": written, "missing": missing}, open(os.path.join(s4.STEP4, "written.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"{len(written)} notes {'(dry run)' if args.dry_run else 'written'}; no reader output for {len(missing)}")


if __name__ == "__main__":
    main()
