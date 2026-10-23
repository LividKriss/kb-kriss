#!/usr/bin/env python3
"""Backfill pass 2: fetch the step-4 contacts' messages, plus a sample of Kriss's sent mail for voice.

    fetch_content.py plan    decide from headers what may be fetched -> cache/step4/plan.json (no API calls)
    fetch_content.py fetch   fetch it (resumable) -> cache/content/messages.jsonl

Window: last 12 months for every step-4 person; 3 years for the top 50 (threads Kriss replied in, 3 years).
Fetched per message (messages.get, format=full), so what must not be read is never fetched: whole threads
with an excluded employee matter or a private contact (step4lib.thread_exclusion), and single platform,
noise, unconfirmed-freemail and invoice@ messages (step4lib.message_skip). Bodies are stored as decoded
text/plain and text/html; attachments by name only, never their content.

Run with the venv outside the repo:
  "~/Library/Application Support/kb-kriss/venv/bin/python" scripts/email/fetch_content.py plan
"""
import base64
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step4lib as s4  # noqa: E402

# Paced like fetch_headers.py, but slower: format=full counts far more against the per-minute quota.
BATCH_SIZE = 10
START_RATE = 1.5   # messages per second; full format runs into the per-user quota at ~100/min
MAX_RATE = 1.6


def plan():
    corr = s4.load_corrections()
    contacts = s4.load_contacts()
    own = s4.own_addresses(corr)
    persons, roles, addr_to_person, flags = s4.build_people(contacts, corr)
    metas = {p: s4.person_meta(p, v) for p, v in persons.items()}
    top = sorted(metas.values(), key=lambda m: -m["replied_threads"])[:s4.TOP_N]
    top_set = {m["primary"] for m in top}
    merged = set(addr_to_person)
    # Livid's own shared mailboxes are not followed; their threads come in through the people in them.
    roles = {a: r for a, r in roles.items() if not s4.in_list(s4.domain(a), s4.INTERNAL_DOMAINS)}
    tracked = merged | set(roles)
    by_thread = s4.load_threads()
    c12, c3 = s4.cutoff(s4.WINDOW_12M_DAYS), s4.cutoff(s4.WINDOW_3Y_DAYS)

    selected, excluded = {}, Counter()
    excluded_msgs, skipped_msgs = Counter(), Counter()
    fetch_ids = []
    per_person = defaultdict(list)
    for tid, msgs in by_thread.items():
        who = set()
        for m in msgs:
            who |= s4.participants(m) & tracked
        if not who:
            continue
        last = msgs[-1]["internalDate"]
        keys = {addr_to_person.get(a, a) for a in who}
        wanted = [k for k in keys if last >= (c3 if k in top_set else c12)]
        if not wanted:
            continue
        why = s4.thread_exclusion(msgs, contacts, corr, own, merged)
        if why:
            excluded[why] += 1
            excluded_msgs[why] += len(msgs)
            continue
        for k in wanted:
            per_person[k].append(tid)

    # Newest THREAD_CAP threads per person; fetch order round-robin so everyone's recent mail comes first.
    capped_away = 0
    for k, tids in per_person.items():
        tids.sort(key=lambda t: -by_thread[t][-1]["internalDate"])
        capped_away += max(0, len(tids) - s4.THREAD_CAP)
        del tids[s4.THREAD_CAP:]
    for k, tids in per_person.items():
        for t in tids:
            selected.setdefault(t, []).append(k)
    seen = set()
    for rank in range(s4.THREAD_CAP):
        for k in sorted(per_person):
            if rank < len(per_person[k]) and per_person[k][rank] not in seen:
                tid = per_person[k][rank]
                seen.add(tid)
                for m in by_thread[tid]:
                    skip = s4.message_skip(m, contacts, corr, own)
                    if skip:
                        skipped_msgs[skip] += 1
                    else:
                        fetch_ids.append(m["id"])

    # Voice sample: Kriss's sent messages, last 12 months, by recipient category (To first, then Cc).
    sent_by_cat = defaultdict(list)
    for tid, msgs in by_thread.items():
        if tid not in selected and s4.thread_exclusion(msgs, contacts, corr, own, merged):
            continue
        for m in msgs:
            if m["internalDate"] < c12 or not s4.is_sent(m, own) or s4.message_skip(m, contacts, corr, own):
                continue
            to = [a for a in s4.addrs(m["headers"].get("To")) if a not in own]
            cats = [s4.category_of(a, contacts, corr) for a in to] or \
                   [s4.category_of(a, contacts, corr) for a in s4.addrs(m["headers"].get("Cc")) if a not in own]
            cats = [c for c in cats if c and c not in s4.NO_VOICE]
            if cats:
                sent_by_cat[Counter(cats).most_common(1)[0][0]].append((m["id"], tid, tid in selected))
    rnd = random.Random(4)
    voice = {}
    for cat, items in sent_by_cat.items():
        # Prefer messages inside fetched threads (no extra call); top up from other threads.
        inside = [i for i in items if i[2]]
        outside = [i for i in items if not i[2]]
        rnd.shuffle(inside)
        rnd.shuffle(outside)
        pick = (inside + outside)[:s4.VOICE_TARGET]
        voice[cat] = [{"id": i, "threadId": t, "in_thread_fetch": f} for i, t, f in pick]

    out = {
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "persons": {p: {**metas[p], "top50": p in top_set, "threads": per_person.get(p, []),
                        "flag": "; ".join(flags[a] for a in metas[p]["emails"] if a in flags)}
                    for p in metas},
        "roles": {a: {"name": r["name"], "category": r["category"], "org": r["org"], "domain": r["domain"],
                      "threads": per_person.get(a, [])} for a, r in roles.items()},
        "top50": [m["primary"] for m in top],
        "threads": selected,
        "excluded_threads": dict(excluded),
        "excluded_messages": dict(excluded_msgs),
        "skipped_messages": dict(skipped_msgs),
        "thread_cap": s4.THREAD_CAP,
        "threads_over_cap": capped_away,
        "fetch_ids": fetch_ids + [i["id"] for v in voice.values() for i in v if not i["in_thread_fetch"]],
        "voice": voice,
        "voice_available": {c: len(v) for c, v in sent_by_cat.items()},
    }
    os.makedirs(s4.STEP4, exist_ok=True)
    json.dump(out, open(s4.PLAN, "w"), ensure_ascii=False, indent=1)
    extra = sum(1 for v in voice.values() for i in v if not i["in_thread_fetch"])
    print(f"persons {len(metas)}, role mailboxes {len(roles)}, top-50 cut at {top[-1]['replied_threads']} "
          f"replied threads")
    print(f"threads {len(selected)}; messages to fetch {len(fetch_ids)} + {extra} extra voice")
    print("excluded threads:", dict(excluded), "messages:", dict(excluded_msgs))
    print("skipped messages:", dict(skipped_msgs), f"; person-threads over the cap: {capped_away}")
    print("voice available per category (12m):", {c: len(v) for c, v in sorted(sent_by_cat.items())})
    print("no threads:", [p for p in metas if not per_person.get(p)])


def b64(data):
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def walk(part, out):
    mime = part.get("mimeType", "")
    body = part.get("body", {})
    if part.get("filename"):
        out["attachments"].append(part["filename"])  # name only, never content
        return
    if mime == "text/plain" and body.get("data"):
        out["text"] += b64(body["data"])
    elif mime == "text/html" and body.get("data"):
        out["html"] += b64(body["data"])
    for p in part.get("parts", []) or []:
        walk(p, out)


KEEP_HEADERS = ("From", "To", "Cc", "Date", "Subject")


def slim(msg):
    payload = msg.get("payload", {})
    hdrs = {}
    for h in payload.get("headers", []):
        if h["name"] in KEEP_HEADERS:
            hdrs[h["name"]] = hdrs[h["name"]] + ", " + h["value"] if h["name"] in hdrs else h["value"]
    out = {"id": msg["id"], "threadId": msg["threadId"], "internalDate": int(msg["internalDate"]),
           "labelIds": msg.get("labelIds", []), "headers": hdrs, "text": "", "html": "", "attachments": []}
    walk(payload, out)
    return out


def done_ids(path, key):
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        return {json.loads(line)[key] for line in f if line.strip()}


def fetch_all(svc, ids, path, log):
    """messages.get(format=full) in paced batches, one slimmed message per line in path."""
    from googleapiclient.errors import HttpError
    from fetch_headers import call
    pending = list(ids)
    rate, clean, retries, n = START_RATE, 0, 0, 0
    with open(path, "a") as out:
        while pending:
            started = time.time()
            chunk, pending = pending[:BATCH_SIZE], pending[BATCH_SIZE:]
            got, retry, why = [], [], []

            def cb(request_id, response, exception):
                if exception is None:
                    got.append(response)
                elif isinstance(exception, HttpError) and exception.resp.status == 404:
                    pass
                else:
                    retry.append(request_id)
                    content = getattr(exception, "content", b"") or b""
                    why.append(f"{getattr(exception, 'resp', {}).get('status', '?')} "
                               f"{content.decode('utf-8', 'replace')[:160]}".replace("\n", " "))

            batch = svc.new_batch_http_request(callback=cb)
            for i in chunk:
                batch.add(svc.users().messages().get(userId="me", id=i, format="full"), request_id=i)
            for attempt in range(10):
                try:
                    call(batch)
                    break
                except (OSError, TimeoutError) as e:  # network drop (Wi-Fi, sleep): wait and resend the batch
                    got.clear(), retry.clear(), why.clear()
                    log(f"messages {n}: network error ({e}); retrying in {min(300, 15 * 2 ** attempt)} s")
                    time.sleep(min(300, 15 * 2 ** attempt))
            else:
                sys.exit("Network still down after 10 tries; re-run to resume.")
            for r in got:
                out.write(json.dumps(slim(r), ensure_ascii=False) + "\n")
            out.flush()
            n += len(got)
            if retry:
                pending = retry + pending
                retries += len(retry)
                # Per-minute quota: wait the minute out and slow down. Concurrency/backend errors: short pause.
                per_minute = any("per minute" in w or "Quota exceeded" in w for w in why)
                rate = max(1.0, rate * (0.9 if per_minute else 0.95))
                clean = 0
                wait = 60 if per_minute else 15
                log(f"messages {n}: {len(retry)} to retry ({retries} so far), waiting {wait} s, rate {rate:.1f}/s; {why[0]}")
                time.sleep(wait)
                continue
            clean += len(got)
            if clean >= 500:
                rate, clean = min(MAX_RATE, rate * 1.1), 0
                log(f"messages {n}/{n + len(pending)}, rate {rate:.1f}/s")
            time.sleep(max(0.0, len(chunk) / rate - (time.time() - started)))
    return n


def fetch():
    from gmail_auth import gmail_service
    p = json.load(open(s4.PLAN))
    os.makedirs(s4.CONTENT, exist_ok=True)
    svc = gmail_service()
    t0 = time.time()

    def log(text):
        print(f"{time.strftime('%H:%M:%S')} ({(time.time() - t0) / 60:.0f} min) {text}", flush=True)

    ids = list(dict.fromkeys(p["fetch_ids"]))
    done = done_ids(s4.MESSAGES_JSONL, "id")
    todo = [i for i in ids if i not in done]
    log(f"messages: {len(ids)} planned, {len(todo)} to go")
    fetch_all(svc, todo, s4.MESSAGES_JSONL, log)
    log("done")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "plan":
        plan()
    elif cmd == "fetch":
        fetch()
    else:
        sys.exit(__doc__)
