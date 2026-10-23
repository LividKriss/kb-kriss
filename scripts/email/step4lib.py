"""Shared logic for backfill pass 2 (content): who gets a Person note, which threads may be fetched.

Inputs (all outside the repo):
  cache/headers/messages.jsonl   headers from fetch_headers.py
  cache/step3/contacts.csv       contact table from build_contacts.py (step4=yes rows)
  review/corrections.json        Kriss's step 3 review answers
  cache/step4/people.json        step 4 grouping: address merges, role mailboxes, merges to confirm

No addresses or names live in this file; they come from those inputs.
"""
import csv
import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict
from email.utils import getaddresses

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_contacts import (CORRECTIONS, FREEMAIL, INTERNAL_DOMAINS, INVOICE_INBOXES, KNOWN_OWN,  # noqa: E402
                            NOISE_DOMAINS, PLATFORM_DOMAINS, in_list)

APP_DIR = os.path.expanduser("~/Library/Application Support/kb-kriss")
CACHE = os.path.join(APP_DIR, "cache")
MSG_PATH = os.path.join(CACHE, "headers", "messages.jsonl")
CONTACTS = os.path.join(CACHE, "step3", "contacts.csv")
STEP4 = os.path.join(CACHE, "step4")
PEOPLE_JSON = os.path.join(STEP4, "people.json")
PLAN = os.path.join(STEP4, "plan.json")
CONTENT = os.path.join(CACHE, "content")
MESSAGES_JSONL = os.path.join(CONTENT, "messages.jsonl")

TOP_N = 50
# Gmail's per-user units-per-minute quota allows ~3 messages/s. Full content is fetched for each person's
# newest THREAD_CAP threads in their window; older threads are covered by the header-only index.
THREAD_CAP = 100
WINDOW_12M_DAYS = 365
WINDOW_3Y_DAYS = 365 * 3
VOICE_TARGET = 60  # sent messages sampled per recipient category (≈40 left after skipping one-liners)
NO_VOICE = {"private", "private?", "skip", "?", "consumer", "colleague?", "authority?", "advisor?"}

# Subjects that mark an employee matter. Applied to threads among colleagues only (supplier mail about a
# factory holiday is not HR). Such threads are never fetched (AGENTS.md §2.3).
HR_SUBJECT = re.compile(
    r"(\blønn(?!som)|\blonn\b|salary|payslip|lønnsslipp|timeliste|timeføring|timelister|\btimer\b|sykemeld|"
    r"sykmeld|egenmeld|sykefrav|\bsyk\b|permisjon|foreldre|\bferie|oppsigelse|oppsagt|advarsel|arbeidsavtale|"
    r"arbeidskontrakt|ansettelse|ansettelses|sluttavtale|medarbeidersamtale|skattekort|overtid|attest|"
    r"tillitsvalgt|fagforening|personalsak|vaktliste|turnus)", re.I)


def addrs(value):
    return [a.lower().strip() for _, a in getaddresses([value or ""]) if "@" in a]


def domain(a):
    return a.split("@", 1)[1] if "@" in a else ""


def load_corrections():
    return json.load(open(CORRECTIONS)) if os.path.exists(CORRECTIONS) else {}


def load_contacts():
    return {r["address"]: r for r in csv.DictReader(open(CONTACTS))}


def own_addresses(corr):
    return set(KNOWN_OWN) | set(corr.get("own", []))


def build_people(contacts, corr):
    """Group step-4 addresses into persons. Returns (persons, roles, addr_to_person, flags).

    persons: primary address -> {"emails": [...], "rows": [...]} (primary first). Merges come from
    people.json and from review notes "same person as <address>".
    """
    cfg = json.load(open(PEOPLE_JSON))
    roles = set(cfg.get("role", []))
    flags = dict(cfg.get("flag", {}))
    groups = [list(g) for g in cfg.get("merge", [])]
    # Review notes "private address; same person as x@y" (only when x@y is an address).
    for a, fix in corr.get("addresses", {}).items():
        m = re.search(r"same person as (\S+@\S+)", fix.get("note", ""))
        if m:
            target = m.group(1).strip(".,;").lower()
            if not any(a in g for g in groups):
                hit = next((g for g in groups if target in g), None)
                if hit:
                    hit.append(a)
                else:
                    groups.append([target, a])
    addr_to_primary = {}
    for g in groups:
        for a in g:
            addr_to_primary[a] = g[0]

    persons = {}
    for a, r in contacts.items():
        if r["step4"] != "yes" or a in roles:
            continue
        p = addr_to_primary.get(a, a)
        persons.setdefault(p, {"emails": [], "rows": []})
    for g in groups:
        if g[0] in persons:
            persons[g[0]]["emails"] = list(dict.fromkeys(g))
    for p, v in persons.items():
        if not v["emails"]:
            v["emails"] = [p]
        v["rows"] = [contacts[a] for a in v["emails"] if a in contacts]
    # A merged address whose primary isn't step 4 but which is (e.g. a private address over the threshold):
    # the primary becomes a person through the group above, because step4=yes rows map to their primary.
    addr_to_person = {a: p for p, v in persons.items() for a in v["emails"]}
    role_rows = {a: contacts[a] for a in roles if a in contacts and contacts[a]["step4"] == "yes"}
    return persons, role_rows, addr_to_person, flags


def person_meta(p, v):
    rows = v["rows"]
    main = next((r for r in rows if r["address"] == p), rows[0])
    cats = [r["category"] for r in rows if r["category"]]
    orgs = [r["org"] for r in rows if r["org"]]
    replied = sum(int(r["replied_threads"]) for r in rows)
    replied_12m = sum(int(r["replied_12m"]) for r in rows)
    return {"primary": p, "emails": v["emails"], "name": main["name"], "category": main["category"] or cats[0],
            "categories": sorted(set(cats)), "org": main["org"] or (orgs[0] if orgs else ""),
            "orgs": sorted(set(orgs)), "domain": main["domain"], "replied_threads": replied,
            "replied_12m": replied_12m, "notes": sorted({r["note"] for r in rows if r["note"]})}


def load_threads():
    by_thread = defaultdict(list)
    for line in open(MSG_PATH):
        if line.strip():
            m = json.loads(line)
            by_thread[m["threadId"]].append(m)
    for v in by_thread.values():
        v.sort(key=lambda m: m["internalDate"])
    return by_thread


def participants(m):
    h = m["headers"]
    return set(addrs(h.get("From")) + addrs(h.get("To")) + addrs(h.get("Cc")))


def category_of(a, contacts, corr):
    """Confirmed category of any address (kept contact or a review answer), '' if unknown."""
    r = contacts.get(a)
    if r:
        return r["category"]
    fix = corr.get("addresses", {}).get(a)
    return fix["category"] if fix else ""


def message_skip(m, contacts, corr, own):
    """Reason this one message must not be fetched, or ''. Decided from headers only.

    Platform and noise messages inside a real conversation (e.g. Superhuman reminders) are skipped, not the
    whole thread. Senders on a freemail address nobody has categorised ('private?') are skipped too.
    """
    h = m["headers"]
    frm = (addrs(h.get("From")) or [""])[0]
    if not frm or frm in own:
        return ""
    noise = NOISE_DOMAINS + corr.get("noise", [])
    if in_list(domain(frm), PLATFORM_DOMAINS) or in_list(domain(frm), noise) or frm.split("@")[0] == "mailer-daemon":
        return "platform or noise sender"
    if category_of(frm, contacts, corr) == "private?":
        return "unconfirmed freemail sender"
    if INVOICE_INBOXES & set(addrs(h.get("To")) + addrs(h.get("Cc"))):
        return "invoice@ traffic"
    return ""


def thread_exclusion(msgs, contacts, corr, own, merged):
    """Reason the whole thread must not be fetched, or ''. Decided from headers only."""
    hr_domains = corr.get("exclude_hr", [])
    people = set()
    for m in msgs:
        people |= participants(m)
    others = {a for a in people if a not in own and a not in INVOICE_INBOXES}
    if any(in_list(domain(a), hr_domains) for a in others):
        return "employee matter (excluded domain)"
    if any(a not in merged and category_of(a, contacts, corr) == "private" for a in others):
        return "private contact in thread"
    colleagues_only = all(in_list(domain(a), INTERNAL_DOMAINS) or category_of(a, contacts, corr) == "colleague"
                          for a in others)
    if colleagues_only and others and any(HR_SUBJECT.search(m["headers"].get("Subject", "")) for m in msgs):
        return "employee matter (subject, colleagues only)"
    if all(message_skip(m, contacts, corr, own) for m in msgs):
        return "only platform/noise/unconfirmed messages"
    return ""


def now_ms():
    return dt.datetime.now().timestamp() * 1000


def cutoff(days):
    return now_ms() - days * 864e5


def is_sent(m, own):
    return "SENT" in m.get("labelIds", []) or (addrs(m["headers"].get("From")) or [""])[0] in own


def is_freemail(a):
    return domain(a) in FREEMAIL
