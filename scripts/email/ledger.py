#!/usr/bin/env python3
"""Thread state and decision ledger for the email assistant (livid-kb AGENTS.md §7a, §8).

Plain Python 3, standard library only, so the cloud run and the Mac use the same script.
Both files are append-only JSON lines in the repo (merge=union, .gitattributes):

  data/threads.jsonl    one distilled line per open thread, written by part A and the brief
  data/decisions.jsonl  every recommendation shown to Kriss and his answer

Threads
  ledger.py thread-set                 read JSON objects (one per line) on stdin and append them
  ledger.py thread-get <id>...         latest merged state per thread (JSON lines)
  ledger.py thread-get --open          every thread whose latest state is not closed
  ledger.py thread-close <id>...       mark threads closed (after `gmail_tool.py done`, a send, a task done)

Decisions
  ledger.py decision-add               read JSON objects on stdin and append them
  ledger.py stats [--days N]           agreement per kind and per confidence level (default 28 days)
  ledger.py repeats [--min N]          (kind, decision_key) pairs decided N+ times (default 2), with counter-cases
  ledger.py uses <doc-path>...         how often recommendations resting on these docs were accepted unchanged

Housekeeping (weekly KB review)
  ledger.py compact                    rewrite threads.jsonl to one line per thread; drop threads closed > 30 days

Thread fields (all optional except thread): thread, last_msg_at, label, who, ask (<=12 words), state,
deadline, draft, handled (evidence it is already settled), kind, rec, conf (H|M|L), grounds, closed, by.
Decision fields: thread, kind, decision_key (short slug, e.g. close-handled, hold-payment, send-draft),
counterpart, rec, conf, answer (agree|changed|rejected|later|none), decision, reason, docs (list of KB
paths the recommendation rested on), by. No email body text in either file.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
THREADS = os.path.join(DATA, "threads.jsonl")
DECISIONS = os.path.join(DATA, "decisions.jsonl")
ANSWERS = {"agree", "changed", "rejected", "later", "none"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read(path: str) -> list[dict]:
    out = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass  # a half-merged line; skip it
    except FileNotFoundError:
        pass
    return out


def append(path: str, rows: list[dict]) -> None:
    os.makedirs(DATA, exist_ok=True)
    with open(path, "a") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def stdin_rows(required: str) -> list[dict]:
    rows = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if required not in r:
            sys.exit(f"missing '{required}': {line[:80]}")
        r.setdefault("at", now())
        rows.append(r)
    return rows


def merged_threads() -> dict[str, dict]:
    state: dict[str, dict] = {}
    for r in sorted(read(THREADS), key=lambda r: r.get("at", "")):
        cur = state.setdefault(r["thread"], {})
        if r.get("closed") is False or (r.get("last_msg_at") and r.get("last_msg_at") > cur.get("last_msg_at", "")):
            cur.pop("closed", None)  # new mail reopens a closed thread
        cur.update({k: v for k, v in r.items() if v is not None})
    return state


def cmd_thread_set(_args):
    rows = stdin_rows("thread")
    append(THREADS, rows)
    print(f"{len(rows)} thread lines written")


def cmd_thread_get(args):
    state = merged_threads()
    if args == ["--open"]:
        sel = [s for s in state.values() if not s.get("closed")]
    else:
        sel = [state[t] for t in args if t in state]
        for t in args:
            if t not in state:
                print(json.dumps({"thread": t, "unknown": True}))
    for s in sel:
        print(json.dumps(s, ensure_ascii=False, sort_keys=True))


def cmd_thread_close(args):
    append(THREADS, [{"thread": t, "closed": True, "at": now()} for t in args])
    print(f"{len(args)} closed")


def cmd_decision_add(_args):
    rows = stdin_rows("kind")
    for r in rows:
        if r.get("answer") and r["answer"] not in ANSWERS:
            sys.exit(f"answer must be one of {sorted(ANSWERS)}")
    append(DECISIONS, rows)
    print(f"{len(rows)} decisions written")


def since(days: int) -> list[dict]:
    cut = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).isoformat()
    return [r for r in read(DECISIONS) if r.get("at", "") >= cut[:19]]


def pct(a: int, n: int) -> str:
    return f"{100 * a // n}%" if n else "-"


def cmd_stats(args):
    days = int(args[1]) if args[:1] == ["--days"] else 28
    rows = [r for r in since(days) if r.get("answer") not in (None, "none", "later")]
    by_kind = collections.defaultdict(list)
    by_conf = collections.defaultdict(list)
    for r in rows:
        by_kind[r["kind"]].append(r)
        by_conf[r.get("conf", "?")].append(r)
    print(f"Decisions answered, last {days} days: {len(rows)}")
    print("By confidence: " + " · ".join(
        f"{c} {pct(sum(x['answer'] == 'agree' for x in v), len(v))} of {len(v)}" for c, v in sorted(by_conf.items())))
    print("kind · n · agree · changed · rejected · first · last")
    for k, v in sorted(by_kind.items(), key=lambda kv: -len(kv[1])):
        c = collections.Counter(x["answer"] for x in v)
        ats = sorted(x["at"][:10] for x in v)
        print(f"{k} · {len(v)} · {pct(c['agree'], len(v))} · {c['changed']} · {c['rejected']} · {ats[0]} · {ats[-1]}")


def cmd_repeats(args):
    m = int(args[1]) if args[:1] == ["--min"] else 2
    groups = collections.defaultdict(list)
    for r in read(DECISIONS):
        if r.get("decision_key") and r.get("answer") in ("agree", "changed"):
            groups[(r["kind"], r["decision_key"])].append(r)
    for (kind, key), v in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(v) < m:
            continue
        against = [x for x in read(DECISIONS) if x.get("kind") == kind and x.get("decision_key") not in (key, None)
                   and x.get("answer") in ("agree", "changed")]
        cases = "; ".join(f"{x['at'][:10]} {x.get('counterpart', '')}".strip() for x in v[-5:])
        print(f"{kind} → {key} · {len(v)}x · against {len(against)} · {cases}")


def cmd_uses(args):
    rows = read(DECISIONS)
    for doc in args:
        used = [r for r in rows if doc in (r.get("docs") or [])]
        c = collections.Counter(r.get("answer") for r in used)
        print(f"{doc} · used {len(used)} · unchanged {c['agree']} · changed {c['changed']} · rejected {c['rejected']}")


def cmd_compact(_args):
    state = merged_threads()
    cut = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).isoformat()[:19]
    keep = [s for s in state.values() if not (s.get("closed") and s.get("at", "") < cut)]
    with open(THREADS, "w") as f:
        for s in sorted(keep, key=lambda s: s.get("at", "")):
            f.write(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"threads: {len(state)} → {len(keep)}")


CMDS = {"thread-set": cmd_thread_set, "thread-get": cmd_thread_get, "thread-close": cmd_thread_close,
        "decision-add": cmd_decision_add, "stats": cmd_stats, "repeats": cmd_repeats, "uses": cmd_uses,
        "compact": cmd_compact}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        sys.exit(__doc__)
    CMDS[sys.argv[1]](sys.argv[2:])
