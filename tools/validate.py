#!/usr/bin/env python3
"""Validate kb-kriss against OKF v0.2 and schema/ (copied from livid-kb, extended).

Hard errors (exit 1) and soft warnings. Run from anywhere:
    python3 tools/validate.py            # errors + warnings
    python3 tools/validate.py --errors   # errors only
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kblib import (KB, RESERVED, area_of, default_tier, iter_docs, load_domains,  # noqa: E402
                   load_types, parse_duration, parse_when, rel, resolve_kb_url,
                   split_frontmatter)

SECRET_PATTERNS = [
    ("11-digit number (personnummer / bank account)", re.compile(r"(?<![\d.])\d{6} ?\d{5}(?![\d])")),
    ("bank account number (xxxx.xx.xxxxx)", re.compile(r"(?<!\d)\d{4}[. ]\d{2}[. ]\d{5}(?!\d)")),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2} ?(?:[A-Z0-9]{4} ?){2,7}[A-Z0-9]{1,4}\b")),
    ("credential assignment", re.compile(
        r"(?i)\b(api[_-]?key|password|passord|secret|client[_-]?secret|access[_-]?token|token)\b\s*[:=]\s*\S+")),
]
PHONE_RE = re.compile(r"(?<![\w/.:#-])(?:\+\d{1,3} ?)?\d{2} ?\d{2} ?\d{2} ?\d{2}(?![\w/.:-])")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
TODO_RE = re.compile(r"TODO\(([^)]+)\)")
DATE_H_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")
ORG_FOLDERS = {"supplier": "suppliers", "customer": "customers", "manufacturer": "manufacturers",
               "advisor": "advisors", "authority": "authorities"}


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, f, msg):
        self.errors.append(f"{f}: {msg}")

    def warn(self, f, msg):
        self.warnings.append(f"{f}: {msg}")


TYPES_CFG = load_types()


def resolve_link(src: Path, target: str):
    if target.startswith("kb://"):
        path, status = resolve_kb_url(target, TYPES_CFG)
        return path if status == "ok" else None  # root not present locally → not checked
    target = target.split("#", 1)[0]
    if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
        return None  # anchor or external URL
    if target.startswith("/"):
        return KB / target.lstrip("/")
    return (src.parent / target).resolve()


def check_index(p: Path, fm, r: Report):
    is_root = p.parent == KB
    if fm is not None:
        if not is_root or set(fm) - {"okf_version"}:
            r.err(rel(p), "index.md must have no frontmatter (root may carry only okf_version)")


def check_log(p: Path, fm, body: str, r: Report):
    if fm is not None:
        r.err(rel(p), "log.md must have no frontmatter")
    dates = []
    for n, line in enumerate(body.splitlines(), 1):
        if line.startswith("## "):
            m = DATE_H_RE.match(line)
            if not m:
                r.err(rel(p), f"line {n}: log headings must be ISO dates '## YYYY-MM-DD'")
                continue
            try:
                dates.append(dt.date.fromisoformat(m.group(1)))
            except ValueError:
                r.err(rel(p), f"line {n}: invalid date {m.group(1)}")
    if dates != sorted(dates, reverse=True):
        r.err(rel(p), "log date headings must be newest first")


def folder_ok(relpath: str, area: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if pat.startswith("*/"):
            sub = relpath[len(area) + 1:] if area and relpath.startswith(area + "/") else relpath
            if sub.startswith(pat[2:] + "/"):
                return True
        elif relpath.startswith(pat + "/"):
            return True
    return False


def main(argv):
    only_errors = "--errors" in argv
    types_cfg, domains = load_types(), load_domains()
    types = types_cfg["types"]
    tiers = types_cfg["tiers"]
    now = dt.datetime.now(dt.timezone.utc)
    r = Report()
    inbound = defaultdict(set)
    concepts = []
    todos = {}
    seen_emails = defaultdict(list)
    no_orphan_check = set()

    for p in iter_docs():
        f = rel(p)
        text = p.read_text(encoding="utf-8")
        fm, body, perr = split_frontmatter(text)

        for label, rx in SECRET_PATTERNS:
            for m in rx.finditer(text):
                if label == "IBAN" and len(m.group(0).replace(" ", "")) < 15:
                    continue  # shorter than any IBAN in use (NO = 15); e.g. EU VAT numbers
                line = text[:m.start()].count("\n") + 1
                r.err(f, f"line {line}: possible {label} — personal data and credentials are not allowed")

        for m in PHONE_RE.finditer(text):
            line = text[:m.start()].count("\n") + 1
            r.warn(f, f"line {line}: looks like a phone number — email address is the only contact detail stored")

        for m in LINK_RE.finditer(body):
            tgt = resolve_link(p, m.group(1))
            if tgt is None:
                continue
            if not tgt.exists():
                r.warn(f, f"broken link: {m.group(1)}")
            elif p.name != "index.md":
                inbound[tgt.resolve()].add(f)

        if p.name == "index.md":
            check_index(p, fm, r)
            continue
        if p.name == "log.md":
            check_log(p, fm, body, r)
            continue

        concepts.append(p)
        if perr:
            r.err(f, perr)
            continue
        if fm is None:
            r.err(f, "missing YAML frontmatter")
            continue
        t = fm.get("type")
        if not t or not str(t).strip():
            r.err(f, "missing or empty `type`")
            continue
        if t not in types:
            r.err(f, f"unknown type {t!r} (allowed: {', '.join(types)})")
            continue
        tcfg = types[t] or {}
        if t in ("Person", "Note"):
            no_orphan_check.add(p.resolve())  # standalone by nature; found via index/search

        required = list(types_cfg["common_required"]) + list(tcfg.get("required", []))
        status = fm.get("status")
        if status == "stable":
            required += types_cfg["stable_required"]
        for k in required:
            if fm.get(k) in (None, "", []):
                r.err(f, f"missing required field `{k}` for type {t}" + (" (status stable)" if k in types_cfg["stable_required"] else ""))

        for field, allowed in (tcfg.get("enums") or {}).items():
            if field in fm and fm[field] not in allowed:
                r.err(f, f"`{field}` must be one of {allowed}")

        if status is not None and status not in types_cfg["statuses"]:
            r.err(f, f"`status` must be one of {types_cfg['statuses']}")

        # area / domain
        kind, area = area_of(f, domains)
        if kind is None:
            r.err(f, f"folder `{area}` is not a registered foundation or domain (see schema/domains.yaml; use tools/new_domain.py)")
        elif kind == "root":
            r.err(f, "concept documents may not sit in the bundle root")
        elif kind == "domain":
            if fm.get("domain") != area:
                r.err(f, f"`domain` must be `{area}` (matches folder), got {fm.get('domain')!r}")
        elif kind == "foundation" and "domain" in fm:
            r.err(f, "shared foundation docs must not carry `domain`")
        if kind in ("domain", "foundation") and not folder_ok(f, area if kind == "domain" else "", tcfg.get("folders", [])):
            r.warn(f, f"type {t} usually lives in {tcfg.get('folders')}")
        if t == "Organization" and fm.get("kind") in ORG_FOLDERS:
            if not f.startswith(f"organizations/{ORG_FOLDERS[fm['kind']]}/"):
                r.warn(f, f"kind {fm['kind']} belongs in organizations/{ORG_FOLDERS[fm['kind']]}/")

        # tier
        tier = fm.get("tier")
        if tier is not None and tier not in tiers:
            r.err(f, f"`tier` must be one of {tiers}")
        elif tier and kind in ("domain", "foundation"):
            dflt = default_tier(kind, area, domains)
            if dflt and tiers.index(tier) < tiers.index(dflt) and not fm.get("tier_reason"):
                r.err(f, f"tier `{tier}` is below default `{dflt}` — add `tier_reason`")

        # autonomy
        if "autonomy" in fm:
            if t != "Process":
                r.err(f, "`autonomy` is only allowed on Process docs")
            elif fm["autonomy"] not in types_cfg["autonomy"]:
                r.err(f, f"`autonomy` must be one of {types_cfg['autonomy']}")

        # provenance (OKF §5)
        gen = fm.get("generated")
        if gen is not None:
            if not isinstance(gen, dict) or not gen.get("by"):
                r.err(f, "`generated` must be a mapping with `by` (and `at`)")
            elif gen.get("at") is not None and parse_when(gen["at"]) is None:
                r.err(f, "`generated.at` is not an ISO 8601 date/time")
        ver = fm.get("verified")
        if ver is not None:
            ver = [ver] if isinstance(ver, dict) else ver
            if not isinstance(ver, list) or not all(isinstance(v, dict) and v.get("by") and v.get("at") for v in ver):
                r.err(f, "`verified` entries need `by` and `at`")
                ver = []
            if status == "stable" and not any(str(v.get("by", "")).startswith("human:") for v in ver):
                r.err(f, "status stable requires a `verified` entry by a `human:` actor")
        # review
        if status == "stable":
            sa = parse_when(fm.get("stale_after"))
            if fm.get("stale_after") and sa is None:
                r.err(f, "`stale_after` is not an ISO 8601 date/time")
            elif sa and now >= sa:
                r.warn(f, f"review overdue (stale_after {fm['stale_after']})")
            elif not sa and ver:
                last = max(parse_when(v["at"]) for v in ver if parse_when(v.get("at")))
                every = parse_duration(tcfg.get("review_every", types_cfg["default_review_every"]))
                r.warn(f, f"suggested stale_after: {(last + every).date().isoformat()}")

        # cross-references (soft)
        owner = fm.get("owner")
        if owner and owner not in types_cfg.get("owners", []):
            r.err(f, f"`owner` must be one of {types_cfg.get('owners')}")
        categories = types_cfg.get("categories", [])
        targets = fm.get("applies_to") or []
        for a in (targets if isinstance(targets, list) else [targets]):
            a = str(a)
            if a == "all" or a in categories:
                continue
            if not (a.startswith("/") or a.startswith("kb://") or a.endswith(".md")):
                r.err(f, f"`applies_to` value {a!r} is not `all`, a category {categories}, or a path")
                continue
            tgt = resolve_link(p, a)
            if a.startswith("kb://") and resolve_kb_url(a, types_cfg)[1] != "ok":
                if resolve_kb_url(a, types_cfg)[1] == "unknown-kb":
                    r.err(f, f"`applies_to` uses an unknown KB: {a}")
                continue
            if tgt is None or not tgt.exists():
                r.warn(f, f"`applies_to` target not found: {a}")
            else:
                inbound[tgt.resolve()].add(f)

        # Person
        if t == "Person":
            if fm.get("category") is not None and fm["category"] not in categories:
                r.err(f, f"`category` must be one of {categories}")
            em = fm.get("emails")
            if em is not None:
                if not isinstance(em, list) or not all(isinstance(e, str) and EMAIL_RE.match(e) for e in em):
                    r.err(f, "`emails` must be a list of email addresses")
                else:
                    for e in em:
                        seen_emails[e.lower()].append(f)
            org = fm.get("organization")
            if org:
                orgs = org if isinstance(org, list) else [org]
                for o in orgs:
                    path, st = resolve_kb_url(str(o), types_cfg)
                    if st == "not-kb":
                        r.err(f, f"`organization` must be a kb:// link, got {o!r}")
                    elif st == "unknown-kb":
                        r.err(f, f"`organization` uses an unknown KB: {o}")
                    elif st == "ok" and not path.exists():
                        r.warn(f, f"`organization` target not found: {o}")
            elif fm.get("category") not in (None, "private", "consumer"):
                r.warn(f, "no `organization` (expected for non-private contacts)")

        n = len(TODO_RE.findall(body))
        if n:
            todos[f] = n

    for e, files in seen_emails.items():
        if len(files) > 1:
            r.err(", ".join(files), f"email {e} is on more than one Person — it is the lookup key and must be unique")

    for p in concepts:
        if p.resolve() not in inbound and p.resolve() not in no_orphan_check:
            r.warn(rel(p), "orphan — no other doc links here (index links don't count)")
    for f, n in todos.items():
        r.warn(f, f"{n} open TODO(...)")

    for e in r.errors:
        print(f"ERROR   {e}")
    if not only_errors:
        for w in r.warnings:
            print(f"WARN    {w}")
    print(f"\n{len(concepts)} concept docs · {len(r.errors)} errors · {len(r.warnings)} warnings")
    return 1 if r.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
