#!/usr/bin/env python3
"""Backfill pass 1: fetch message headers (no bodies) from Kriss's work Gmail.

    fetch_headers.py [--years 3]

Uses format=metadata only. Output goes to the cache outside the repo:
  ~/Library/Application Support/kb-kriss/cache/headers/ids.txt        message ids in the window
  ~/Library/Application Support/kb-kriss/cache/headers/messages.jsonl one line per message

Resumable: ids already in messages.jsonl are skipped, so a re-run continues where it stopped.

Run with the venv outside the repo:
  "~/Library/Application Support/kb-kriss/venv/bin/python" scripts/email/fetch_headers.py
"""
import argparse
import datetime as dt
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmail_auth import APP_DIR, gmail_service  # noqa: E402

from googleapiclient.errors import HttpError  # noqa: E402

OUT_DIR = os.path.join(APP_DIR, "cache", "headers")
IDS_PATH = os.path.join(OUT_DIR, "ids.txt")
MSG_PATH = os.path.join(OUT_DIR, "messages.jsonl")

# Headers only. The list/auto headers are what make the noise pass reliable.
HEADERS = ["From", "To", "Cc", "Reply-To", "Date", "Subject", "List-Unsubscribe", "List-Id",
           "Precedence", "Auto-Submitted", "X-Autoreply", "X-Autorespond"]
BATCH_SIZE = 50


def list_ids(svc, after):
    ids, token = [], None
    while True:
        resp = call(svc.users().messages().list(userId="me", q=f"after:{after}", maxResults=500,
                                                pageToken=token))
        ids += [m["id"] for m in resp.get("messages", [])]
        token = resp.get("nextPageToken")
        print(f"\rlisted {len(ids)}", end="", flush=True)
        if not token:
            print()
            return ids


def call(req, tries=8):
    for i in range(tries):
        try:
            return req.execute()
        except HttpError as e:
            if e.resp.status in (429, 500, 503) or (e.resp.status == 403 and b"ateLimit" in e.content):
                time.sleep(min(64, 2 ** i) + random.random())
                continue
            raise
    sys.exit("Gave up after repeated rate-limit errors; re-run to resume.")


def slim(msg):
    hdrs = {}
    for h in msg.get("payload", {}).get("headers", []):
        name = h["name"]
        hdrs[name] = hdrs[name] + ", " + h["value"] if name in hdrs and name in ("To", "Cc") else h["value"]
    return {"id": msg["id"], "threadId": msg["threadId"], "internalDate": int(msg["internalDate"]),
            "labelIds": msg.get("labelIds", []), "headers": hdrs}


def fetch(svc, ids, out):
    pending = list(ids)
    delay = 0.0
    while pending:
        chunk, pending = pending[:BATCH_SIZE], pending[BATCH_SIZE:]
        got, retry = [], []

        def cb(request_id, response, exception):
            if exception is None:
                got.append(slim(response))
            elif isinstance(exception, HttpError) and exception.resp.status == 404:
                pass  # deleted since listing
            else:
                retry.append(request_id)

        batch = svc.new_batch_http_request(callback=cb)
        for mid in chunk:
            batch.add(svc.users().messages().get(userId="me", id=mid, format="metadata",
                                                 metadataHeaders=HEADERS), request_id=mid)
        batch.execute()
        for m in got:
            out.write(json.dumps(m, ensure_ascii=False) + "\n")
        out.flush()
        if retry:
            pending = retry + pending
            delay = min(30.0, delay * 2 or 1.0)
        else:
            delay = max(0.0, delay / 2 - 0.1)
        yield len(got)
        time.sleep(delay)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=3)
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    svc = gmail_service()

    if not os.path.exists(IDS_PATH):
        after = (dt.date.today() - dt.timedelta(days=365 * args.years)).strftime("%Y/%m/%d")
        ids = list_ids(svc, after)
        with open(IDS_PATH, "w") as f:
            f.write("\n".join(ids) + "\n")
    with open(IDS_PATH) as f:
        ids = [line.strip() for line in f if line.strip()]

    done = set()
    if os.path.exists(MSG_PATH):
        with open(MSG_PATH) as f:
            done = {json.loads(line)["id"] for line in f if line.strip()}
    todo = [i for i in ids if i not in done]
    print(f"{len(ids)} in window, {len(done)} already fetched, {len(todo)} to go")

    n, t0 = 0, time.time()
    with open(MSG_PATH, "a") as out:
        for got in fetch(svc, todo, out):
            n += got
            if n % 1000 < BATCH_SIZE:
                rate = n / max(1, time.time() - t0)
                print(f"{n}/{len(todo)} ({rate:.0f}/s)", flush=True)
    print(f"Done: {n} fetched this run")


if __name__ == "__main__":
    main()
