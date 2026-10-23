#!/usr/bin/env python3
"""Backfill pass 2: turn fetched messages into compact, cleaned text files for reading.

    prepare_content.py

Reads  cache/step4/plan.json, cache/content/messages.jsonl, cache/headers/messages.jsonl
Writes (all outside the repo, deleted with the cache):
  cache/content/people/<primary address>.md   one per step-4 person: thread index (3 years, headers only)
                                               + cleaned messages in the person's window, newest first
  cache/content/roles/<domain>.md             role/shared mailboxes per domain (company facts only)
  cache/content/voice/<category>.md           Kriss's own sent text, sampled per recipient category
  cache/step4/prepared.json                   sizes, counts, windows (for batching and the report)

Per message: date, from, to/cc, subject, body without quoted replies, signatures, disclaimers and HTML,
phone numbers masked, truncated to ~2,000 characters. Attachments by name only.
"""
import datetime as dt
import html
import json
import os
import re
import sys
from collections import defaultdict
from email.utils import getaddresses
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step4lib as s4  # noqa: E402
from write_people import ORG_MAP, organization  # noqa: E402

BODY_MAX = 2000
OLD_BODY_MAX = 700          # when a person's file runs over budget, older bodies are cut harder
BUDGET = 60_000             # characters per person file (top 50: 1.5x)
INDEX_MAX = 80              # header-only index lines per person

OUT_PEOPLE = os.path.join(s4.CONTENT, "people")
OUT_ROLES = os.path.join(s4.CONTENT, "roles")
OUT_VOICE = os.path.join(s4.CONTENT, "voice")

# Where the quoted part of a reply starts (English, Norwegian, Portuguese, Italian, German, French, Outlook).
QUOTE_START = re.compile(
    r"^\s*(On .{5,200}wrote:|Den .{5,200}skrev.{0,40}:|.{0,200} skrev følgende:|Em .{5,200}escreveu:|"
    r"Il giorno .{5,200}ha scritto:|Am .{5,200}schrieb.{0,40}:|Le .{5,200}a écrit\s*:|"
    r"-{2,}\s*(Original Message|Opprinnelig melding|Forwarded message|Videresendt melding|Mensagem original|"
    r"Messaggio originale)\s*-{2,}|_{10,}|"
    r"(From|Fra|De|Da|Von|Van)\s*:\s.+)$", re.I)
OUTLOOK_BLOCK = re.compile(r"^\s*(Sent|Sendt|Enviado|Inviato|Gesendet|Date|Dato)\s*:", re.I)
SIGNOFF = re.compile(
    r"^\s*(all the best|vennlig hilsen|med vennlig hilsen|vennleg helsing|mvh\.?|hilsen|beste hilsen|best regards?|"
    r"kind regards|warm regards|regards|best|cheers|many thanks|tusen takk|cumprimentos|melhores cumprimentos|"
    r"com os melhores cumprimentos|cordiali saluti|distinti saluti|saluti|mit freundlichen grüßen|viele grüße|"
    r"liebe grüße|bien à vous|cordialement|br|kr|rgds)\b", re.I)
THANKS_SIGNOFF = re.compile(r"^\s*(thanks|thank you|takk|obrigad[oa]|grazie)\b[\s,.!]*$", re.I)


def is_signoff(ln, rest):
    """A sign-off line; a bare "Thanks," only when what follows looks like a signature (short lines)."""
    if len(ln.strip()) <= 50 and SIGNOFF.match(ln):
        return True
    tail = [x for x in rest if x.strip()]
    return bool(THANKS_SIGNOFF.match(ln)) and len(tail) <= 12 and all(len(x) <= 80 for x in tail)
SIG_DASH = re.compile(r"^--\s*$")
NOISE_LINE = re.compile(
    r"(sent from my (iphone|ipad|android)|sendt fra min (iphone|ipad)|get outlook for|hentet outlook|"
    r"this (e-?mail|message) (and any attachments )?(is|may be) confidential|denne e-?posten (er|kan)|"
    r"disclaimer|virus-free|superhuman|unsubscribe|please consider the environment|"
    r"conteúdo desta mensagem|questo messaggio|confidentiality notice)", re.I)
PHONE = re.compile(r"(?<![\w/=.-])(\+|00)?\d[\d ().-]{6,}\d(?![\w/=-])")
URL = re.compile(r"https?://\S+")
WS = re.compile(r"[ \t ]+")


class _Text(HTMLParser):
    BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "table", "blockquote"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.quote = [], 0, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("style", "script", "head"):
            self.skip += 1
        elif tag == "blockquote" or "gmail_quote" in (a.get("class") or "") or a.get("id") == "divRplyFwdMsg" \
                or "yahoo_quoted" in (a.get("class") or "") or a.get("id") == "appendonsend":
            self.quote += 1
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("style", "script", "head"):
            self.skip = max(0, self.skip - 1)
        elif tag == "blockquote":
            self.quote = max(0, self.quote - 1)
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip and not self.quote:
            self.out.append(data)


def html_to_text(s):
    p = _Text()
    try:
        p.feed(s)
        return "".join(p.out)
    except Exception:
        return re.sub(r"<[^>]+>", " ", html.unescape(s))


def clean_body(m, keep_signoff=True):
    text = m.get("text") or ""
    if not text.strip() and m.get("html"):
        text = html_to_text(m["html"])
    lines = [WS.sub(" ", ln).rstrip() for ln in text.replace("\r", "").split("\n")]
    out = []
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith(">"):
            break
        if QUOTE_START.match(ln):
            # "From: x" alone is a quote header only when Outlook's Sent/Date line follows.
            if re.match(r"^\s*(From|Fra|De|Da|Von|Van)\s*:", ln, re.I):
                nxt = " ".join(lines[i + 1:i + 4])
                if not OUTLOOK_BLOCK.search("\n".join(lines[i + 1:i + 4])) and "Sent:" not in nxt:
                    out.append(ln)
                    continue
            break
        if SIG_DASH.match(ln):
            break
        if NOISE_LINE.search(ln):
            continue
        out.append(ln)
        if is_signoff(ln, lines[i + 1:]):
            # keep the sign-off and the name under it, drop the signature block
            for nxt in lines[i + 1:i + 4]:
                if nxt.strip():
                    if keep_signoff and len(nxt.strip()) < 40:
                        out.append(nxt.strip())
                    break
            break
    body = "\n".join(out)
    body = URL.sub("[link]", body)
    body = PHONE.sub("[phone]", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body


def short(body, n):
    return body if len(body) <= n else body[:n].rsplit(" ", 1)[0] + " …[truncated]"


def names_of(value):
    out = []
    for name, a in getaddresses([value or ""]):
        if "@" in a:
            name = name.strip().strip("'\"")
            out.append(f"{name} <{a.lower()}>" if name else a.lower())
    return ", ".join(out)


def day(ms):
    return dt.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")


def fmt_msg(m, own, body_max):
    h = m["headers"]
    who = "KRISS" if s4.is_sent(m, own) else names_of(h.get("From"))
    lines = [f"--- {day(m['internalDate'])} | from: {who}",
             f"to: {names_of(h.get('To'))}" + (f" | cc: {names_of(h.get('Cc'))}" if h.get("Cc") else "")]
    if m.get("attachments"):
        lines.append("attachments: " + "; ".join(m["attachments"][:8]))
    body = clean_body(m)
    lines.append(short(body, body_max) if body else "(no text)")
    return "\n".join(lines) + "\n"


def header_index(emails, by_addr, by_thread_hdr, own, c3):
    """Header-only list of the person's threads in 3 years (date, subject, messages, Kriss replied)."""
    rows = []
    for tid in set().union(*(by_addr.get(a, set()) for a in emails)):
        msgs = by_thread_hdr[tid]
        if msgs[-1]["internalDate"] < c3:
            continue
        sent = any(s4.is_sent(m, own) for m in msgs)
        rows.append((msgs[-1]["internalDate"], msgs[0]["internalDate"], tid,
                     msgs[0]["headers"].get("Subject", "")[:90], len(msgs), sent))
    rows.sort(reverse=True)
    return rows


def main():
    plan = json.load(open(s4.PLAN))
    corr = s4.load_corrections()
    own = s4.own_addresses(corr)
    for d in (OUT_PEOPLE, OUT_ROLES, OUT_VOICE):
        os.makedirs(d, exist_ok=True)
    msgs = {}
    with open(s4.MESSAGES_JSONL) as f:
        for line in f:
            if line.strip():
                m = json.loads(line)
                msgs[m["id"]] = m
    by_thread = defaultdict(list)
    for m in msgs.values():
        by_thread[m["threadId"]].append(m)
    for v in by_thread.values():
        v.sort(key=lambda m: m["internalDate"])
    by_thread_hdr = s4.load_threads()
    contacts = s4.load_contacts()
    merged = {a for v in plan["persons"].values() for a in v["emails"]}
    # Excluded threads (employee matters, private contacts) never appear, not even by subject.
    tracked = merged | set(plan["roles"])
    by_addr = defaultdict(set)
    for t, ms in by_thread_hdr.items():
        for m in ms:
            for a in s4.participants(m) & tracked:
                by_addr[a].add(t)
    hidden = {t for ts in by_addr.values() for t in ts
              if t not in plan["threads"] and s4.thread_exclusion(by_thread_hdr[t], contacts, corr, own, merged)}
    c12, c3 = s4.cutoff(s4.WINDOW_12M_DAYS), s4.cutoff(s4.WINDOW_3Y_DAYS)

    def write_file(path, head, emails, tids, since, budget):
        parts = [head]
        idx = [r for r in header_index(emails, by_addr, by_thread_hdr, own, c3) if r[2] not in hidden]
        parts.append(f"## Thread index (headers only, 3 years; {len(idx)} threads, newest first)\n")
        parts.append("last | first | messages | Kriss wrote | subject | threadId\n")
        for last, first, tid, subj, n, sent in idx[:INDEX_MAX]:
            parts.append(f"{day(last)} | {day(first)} | {n} | {'yes' if sent else 'no'} | {subj} | {tid}\n")
        if len(idx) > INDEX_MAX:
            parts.append(f"(+{len(idx) - INDEX_MAX} older threads not listed)\n")
        parts.append("\n## Messages (cleaned, newest thread first)\n")
        size = sum(len(p) for p in parts)
        threads = [t for _, t in sorted(((ms[-1]["internalDate"], t) for t in tids
                                          for ms in [by_thread.get(t)] if ms), reverse=True)]
        shown = omitted = 0
        for tid in threads:
            ms = [m for m in by_thread[tid] if m["internalDate"] >= since]
            if not ms:
                continue
            # Long threads are kept with shorter bodies rather than dropped (a 30-message thread can matter most).
            block = ""
            for body_max in (BODY_MAX if size < budget * 0.6 else OLD_BODY_MAX, 400, 160):
                block = (f"\n### {ms[0]['headers'].get('Subject', '(no subject)')[:120]} — thread {tid}\n"
                         + "".join(fmt_msg(m, own, body_max) for m in ms))
                if len(block) <= budget * 0.3 and size + len(block) <= budget:
                    break
            if size + len(block) > budget:
                omitted += 1
                continue
            parts.append(block)
            size += len(block)
            shown += 1
        if omitted:
            parts.append(f"\n({omitted} older threads in the window left out for length; see the index)\n")
        text = "".join(parts)
        open(path, "w").write(text)
        return {"chars": len(text), "threads_shown": shown, "threads_omitted": omitted, "index": len(idx)}

    org_map = json.load(open(ORG_MAP))
    prepared = {"people": {}, "roles": {}, "voice": {}}
    for p, v in plan["persons"].items():
        org = organization(v, org_map)
        since = c3 if v["top50"] else c12
        head = (f"# {v['name'] or p}\n"
                f"emails: {', '.join(v['emails'])}\ncategory: {v['category']}"
                f"{' (also ' + ', '.join(c for c in v['categories'] if c != v['category']) + ')' if len(v['categories']) > 1 else ''}\n"
                f"organization: {org or '(none)'}{'' if v['org'] or not org else ' (proposed, not yet in livid-kb)'}\n"
                f"review notes: {'; '.join(v['notes']) or '-'}\n"
                f"window: {'3 years (top 50)' if v['top50'] else '12 months'}; today {dt.date.today()}\n"
                f"threads Kriss replied in (3y / 12m): {v['replied_threads']} / {v['replied_12m']}\n\n")
        budget = int(BUDGET * 1.5) if v["top50"] else BUDGET
        path = os.path.join(OUT_PEOPLE, p + ".md")
        prepared["people"][p] = {"file": path, "organization": org, "top50": v["top50"], **write_file(path, head, v["emails"], v["threads"], since, budget)}

    by_dom = defaultdict(list)
    for a, r in plan["roles"].items():
        by_dom[r["domain"]].append(a)
    for dom, roles in by_dom.items():
        tids = sorted({t for a in roles for t in plan["roles"][a]["threads"]})
        r0 = plan["roles"][roles[0]]
        head = (f"# Role mailboxes at {dom}: {', '.join(roles)}\ncategory: {r0['category']}\n"
                f"organization (step 3 match): {r0['org'] or '(none)'}\nwindow: 12 months\n"
                f"Read for company facts only (no Person note).\n\n")
        path = os.path.join(OUT_ROLES, dom + ".md")
        prepared["roles"][dom] = {"file": path, "addresses": roles,
                                  **write_file(path, head, roles, tids, c12, BUDGET // 2)}

    for cat, items in plan["voice"].items():
        parts = [f"# Kriss's sent mail to `{cat}` contacts (12 months, his own text only)\n\n"]
        kept = 0
        for it in items:
            m = msgs.get(it["id"])
            if not m:
                continue
            body = clean_body(m)
            subj = m["headers"].get("Subject", "")
            if len(body) < 40 or (re.match(r"^\s*(fwd?|vs|videresend)\s*:", subj, re.I) and len(body) < 80):
                continue  # one-word replies and forwards without text
            first_in_thread = by_thread[m["threadId"]][0]["id"] == m["id"]
            parts.append(f"--- {day(m['internalDate'])} | {'new thread' if first_in_thread else 'reply'} | "
                         f"subject: {subj[:100]}\n{short(body, 1500)}\n\n")
            kept += 1
        path = os.path.join(OUT_VOICE, cat + ".md")
        open(path, "w").write("".join(parts))
        prepared["voice"][cat] = {"file": path, "messages": kept}

    json.dump(prepared, open(os.path.join(s4.STEP4, "prepared.json"), "w"), indent=1)
    sizes = sorted((v["chars"], p) for p, v in prepared["people"].items())
    print(f"people files: {len(sizes)}, total {sum(s for s, _ in sizes) // 1000}k chars, "
          f"largest {sizes[-1][0] // 1000}k")
    print("voice samples kept:", {c: v["messages"] for c, v in prepared["voice"].items()})


if __name__ == "__main__":
    main()
