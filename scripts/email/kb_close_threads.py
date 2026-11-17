#!/usr/bin/env python3
"""Close quiet open threads in Person notes (kb/email/kb-sync.md, step 8).

    kb_close_threads.py [--days 14] [--dry]

An Open threads bullet whose Gmail thread(s) are all archived (not in the inbox) and have had no
mail for --days days is moved to History as
    - <today>: Closed, no mail since <date>: <subject>
(History is newest first, so it goes at the top). Bullets without a thread link are left alone;
an emptied Open threads section becomes "- None.". Changes get one kb/log.md entry.
Run once a day by mac_agent.sh; the Gmail API token is on the Mac, so the cloud run cannot do it.
"""
from __future__ import annotations  # venv is Python 3.9

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmail_auth import gmail_service  # noqa: E402
from gmail_tool import with_backoff  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
PEOPLE = REPO / "kb" / "people"
LOG = REPO / "kb" / "log.md"
LINK = re.compile(r"#all/([0-9a-f]{12,20})")
SECTION = re.compile(r"^# (.+)$", re.M)


def thread_state(svc, tid, cache):
    if tid not in cache:
        try:
            t = with_backoff(svc.users().threads().get(userId="me", id=tid, format="minimal"))
            msgs = [m for m in t.get("messages", []) if "DRAFT" not in m.get("labelIds", [])]
            newest = max((int(m["internalDate"]) for m in msgs), default=0)
            cache[tid] = (dt.datetime.fromtimestamp(newest / 1000).date() if newest else None,
                          any("INBOX" in m.get("labelIds", []) for m in msgs))
        except Exception as e:  # noqa: BLE001
            cache[tid] = ("error", str(e)[:80])
    return cache[tid]


def sections(text):
    """[(title, start, end)] of the # sections, body from start to end."""
    ms = list(SECTION.finditer(text))
    return [(m.group(1).strip(), m.end(), ms[i + 1].start() if i + 1 < len(ms) else len(text))
            for i, m in enumerate(ms)]


def subject_of(bullet: str) -> str:
    s = bullet[2:].strip()
    s = re.sub(r"\(\[thread\]\([^)]*\)\)|\[thread\]\([^)]*\)", "", s).strip(" .")
    parts = re.split(r" — | – | - ", s)
    subj = parts[0]
    if len(parts) > 2 and len(parts[1]) <= 24:  # "Purchase Order — PO-00147 — status": keep the number
        subj += " — " + parts[1]
    return subj[:100]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    dry = args.dry or os.environ.get("KB_AGENT_DRY") == "1"
    today = dt.date.today()
    cutoff = today - dt.timedelta(days=args.days)
    svc = gmail_service()
    cache, changed, closed_total, errors = {}, [], 0, 0
    for path in sorted(PEOPLE.glob("*.md")):
        text = path.read_text()
        secs = {t: (a, b) for t, a, b in sections(text)}
        if "Open threads" not in secs or "History" not in secs:
            continue
        a, b = secs["Open threads"]
        body = text[a:b]
        keep, closed = [], []
        for line in body.splitlines():
            ids = LINK.findall(line) if line.startswith("- ") else []
            if not ids:
                keep.append(line)
                continue
            states = [thread_state(svc, i, cache) for i in ids]
            if any(s[0] == "error" for s in states):
                errors += 1
                keep.append(line)
                continue
            if all(not inbox and last and last <= cutoff for last, inbox in states):
                last = max(s[0] for s in states)
                closed.append(f"- {today.isoformat()}: Closed, no mail since {last.isoformat()}: {subject_of(line)}")
            else:
                keep.append(line)
        if not closed:
            continue
        if not any(l.startswith("- ") for l in keep):
            keep = [l for l in keep if l.strip()] + ["- None."]
        new_open = "\n" + "\n".join(l for l in keep if l.strip()) + "\n\n"
        ha, hb = secs["History"]
        hist = text[ha:hb]
        hlines = hist.strip("\n").splitlines()
        new_hist = "\n" + "\n".join(closed + hlines) + "\n\n"
        # rebuild in document order (History comes before Open threads in the template)
        parts = sorted([(ha, hb, new_hist), (a, b, new_open)])
        out, pos = [], 0
        for s, e, rep in parts:
            out += [text[pos:s], rep]
            pos = e
        out.append(text[pos:])
        new_text = "".join(out)
        closed_total += len(closed)
        changed.append(path.name)
        print(f"{'DRY ' if dry else ''}{path.name}: closed {len(closed)}")
        if not dry:
            path.write_text(new_text)
    if changed and not dry:
        entry = (f"- **Update** {len(changed)} Person notes: moved {closed_total} quiet open threads to History "
                 f"(thread archived, no mail for {args.days}+ days; `scripts/email/kb_close_threads.py`).\n")
        log = LOG.read_text()
        head = f"## {today.isoformat()}\n\n"
        if head in log:
            log = log.replace(head, head + entry, 1)
        else:
            log = log.replace("# Change log\n\n", "# Change log\n\n" + head + entry + "\n", 1)
        LOG.write_text(log)
    print(f"kb_close_threads: {closed_total} closed in {len(changed)} notes"
          + (f", {errors} bullets skipped on Gmail errors" if errors else "") + (" (dry run)" if dry else ""))


if __name__ == "__main__":
    main()
