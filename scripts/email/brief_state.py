#!/usr/bin/env python3
"""Brief state: what the morning brief has shown and what Kriss put off (kb/email/brief.md).

    brief_state.py status <thread_id> ...         one line per thread: full | still-open | hidden <date>
    brief_state.py shown <thread_id> ...          record that these threads were shown as full rows today
    brief_state.py later <thread_id> <YYYY-MM-DD> hide the thread until that date ("later 5 fri")
    brief_state.py reopen <thread_id> ...         forget the thread (it shows as a full row again)
    brief_state.py prune                          drop threads no longer in the inbox, or untouched 30 days

Rules (kb/email/brief.md):
  - hidden: a "later" date in the future, and no new mail in the thread since it was put off;
  - still-open: shown as a full row on two or more earlier days, and no new mail since it was last shown;
  - full: everything else. The brief still shows a still-open item in full when its deadline is two
    days or less away (the brief judges that, not this script).

State lives outside the repo: ~/Library/Application Support/kb-kriss/brief-state.json. Thread ids only,
no subjects or senders.
"""
from __future__ import annotations  # venv is Python 3.9

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmail_auth import APP_DIR, gmail_service  # noqa: E402
from gmail_tool import with_backoff  # noqa: E402

STATE = os.path.join(APP_DIR, "brief-state.json")


def load() -> dict:
    try:
        with open(STATE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(state: dict):
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=1, sort_keys=True)
    os.replace(tmp, STATE)


def latest(svc, tid) -> tuple[int, bool]:
    """(internalDate of the newest non-draft message, thread still in the inbox)."""
    t = with_backoff(svc.users().threads().get(userId="me", id=tid, format="minimal"))
    msgs = [m for m in t.get("messages", []) if "DRAFT" not in m.get("labelIds", [])]
    newest = max((int(m["internalDate"]) for m in msgs), default=0)
    return newest, any("INBOX" in m.get("labelIds", []) for m in msgs)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("status", "shown", "later", "reopen", "prune"):
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    today = dt.date.today().isoformat()
    state = load()
    svc = gmail_service() if cmd in ("status", "shown", "later", "prune") else None

    if cmd == "status":
        for tid in args:
            s = state.get(tid, {})
            newest, _ = latest(svc, tid)
            if s.get("hidden_until", "") > today and newest <= s.get("hidden_at_msg", 0):
                print(f"{tid} hidden {s['hidden_until']}")
            elif len([d for d in s.get("shown", []) if d < today]) >= 2 and newest <= s.get("shown_at_msg", 0):
                print(f"{tid} still-open")
            else:
                print(f"{tid} full")
    elif cmd == "shown":
        for tid in args:
            s = state.setdefault(tid, {})
            newest, _ = latest(svc, tid)
            if newest > s.get("shown_at_msg", 0):
                s["shown"] = []          # new mail: the count starts again
            if today not in s.setdefault("shown", []):
                s["shown"].append(today)
            s["shown_at_msg"] = newest
            s["touched"] = today
        save(state)
        print(f"recorded {len(args)} shown")
    elif cmd == "later":
        if len(args) != 2:
            sys.exit("usage: later <thread_id> <YYYY-MM-DD>")
        tid, until = args
        dt.date.fromisoformat(until)
        newest, _ = latest(svc, tid)
        state.setdefault(tid, {}).update(hidden_until=until, hidden_at_msg=newest, touched=today)
        save(state)
        print(f"{tid} hidden until {until}")
    elif cmd == "reopen":
        for tid in args:
            state.pop(tid, None)
        save(state)
        print(f"reopened {len(args)}")
    elif cmd == "prune":
        cutoff = (dt.date.today() - dt.timedelta(days=30)).isoformat()
        drop = []
        for tid, s in state.items():
            if s.get("touched", "") < cutoff:
                drop.append(tid)
                continue
            try:
                _, inbox = latest(svc, tid)
            except Exception:  # noqa: BLE001 - a deleted thread
                inbox = False
            if not inbox and s.get("hidden_until", "") <= today:
                drop.append(tid)
        for tid in drop:
            state.pop(tid)
        save(state)
        print(f"pruned {len(drop)}, kept {len(state)}")


if __name__ == "__main__":
    main()
