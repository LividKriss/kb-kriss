#!/usr/bin/env python3
"""Small Gmail CLI for the Mac attachment agent (docs/mac-agent.md).

    gmail_tool.py list <query> [--max N]          one JSON line per message (no bodies)
    gmail_tool.py attachments <msg_id> <dir> [--pdf]
                                                  download all attachments (or only PDFs), print path,
                                                  type and size; `pdfs <msg_id> <dir>` = --pdf
    gmail_tool.py text <file>                     print the text of a PDF, Excel, Word or CSV/text file
    gmail_tool.py fetch <url> <dir>               download a public link (no login): WeTransfer, Google
                                                  Drive/Docs, Dropbox, or a direct file URL; exit 4 if the
                                                  link is a web page or needs a login (nothing saved)
    gmail_tool.py forward <msg_id> <to> [--note F] [--only NAME ...] [--force]
                                                  forward with the original PDFs (or only the named ones);
                                                  note above the quote
    gmail_tool.py label <msg_id> +A -B ...        add/remove labels by name (missing ones are created)
    gmail_tool.py draft <thread_id> <subject> <body-file>
                                                  [Doc] summary draft, no recipient; the thread link is
                                                  appended; replaces an earlier [Doc] draft for the thread
    gmail_tool.py drafts                          list the [Doc] drafts (JSON lines)
    gmail_tool.py delete-draft <draft_id>         delete one [Doc] draft (other drafts are refused)
    gmail_tool.py housekeep [--days 14]           delete docs/<threadId> folders and [Doc] drafts older than
                                                  --days, and [Doc] drafts whose thread is archived

Documents for a thread live in DOCS_DIR/<threadId>/ (outside any repo) until housekeep removes them.
With KB_AGENT_DRY=1 (or --dry), forward, label, draft, delete-draft and housekeep print what they
would do and change nothing.
The duplicate checks still run, so a dry run shows what a real run would skip.

Guards that live here, not only in the agent's instructions:
  - forward sends only to ALLOWED_TO (the two PowerOffice voucher addresses and Ole Eivind),
    and sends nothing while a [STOP-SENDING] draft exists (exit 5; the send policy's kill switch);
  - forward refuses (exit 3) when the message already went to that address: the AI/PO-forwarded
    label for a voucher address, a sent message to it in the same thread, or a sent message to it
    carrying an attachment with the same file name. --force skips the last two, never the allowlist.
  - attachments and fetch refuse a target folder inside a Git repo (raw mail never goes in a repo);
  - fetch is GET-only over https to public hosts and sends no cookies or credentials;
  - delete-draft and housekeep only touch drafts whose subject starts with "[Doc]".

Note file (--note): .html is used as-is, anything else is plain text (paragraphs on blank lines).
Kriss's Gmail signature is appended after the note. The note should already hold the sign-off
and the AI disclaimer (kb/email/signature.md); a forward with no note has no text above the quote.

Run with the venv outside the repo:
  "~/Library/Application Support/kb-kriss/venv/bin/python" scripts/email/gmail_tool.py list "label:AI/Invoice"
"""
from __future__ import annotations  # venv is Python 3.9

import argparse
import base64
import datetime as dt
import html
import io
import json
import ipaddress
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from email.message import EmailMessage
from email.utils import getaddresses
from urllib.parse import parse_qs, unquote, urlparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmail_auth import APP_DIR, gmail_service  # noqa: E402

VOUCHER_TO = {"livid@faktura.poweroffice.net", "lividretail@faktura.poweroffice.net"}  # livid-kb systems/poweroffice-go.md
ALLOWED_TO = VOUCHER_TO | {"oleeivind@livid.no"}  # docs/mac-agent.md "Never"
FORWARDED_LABEL = "AI/PO-forwarded"
DOCS_DIR = Path(APP_DIR) / "docs"
DOC_PREFIX = "[Doc]"
KILL_SWITCH = "[STOP-SENDING]"  # kb/email/send-policy.md: while this draft exists, nothing is forwarded
MAX_FETCH = 200 * 1024 * 1024


def dry_mode(args) -> bool:
    return getattr(args, "dry", False) or os.environ.get("KB_AGENT_DRY") == "1"


def headers(msg) -> dict:
    return {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}


def walk(payload):
    stack = [payload]
    while stack:
        p = stack.pop(0)
        yield p
        stack += p.get("parts", []) or []


def attachments(msg):
    """Parts that are files (have a file name), in message order."""
    return [p for p in walk(msg["payload"]) if p.get("filename")]


def is_pdf(part) -> bool:
    return part["filename"].lower().endswith(".pdf") or part.get("mimeType") == "application/pdf"


def part_bytes(svc, msg_id, part) -> bytes:
    body = part.get("body", {})
    data = body.get("data")
    if not data and body.get("attachmentId"):
        data = svc.users().messages().attachments().get(
            userId="me", messageId=msg_id, id=body["attachmentId"]).execute()["data"]
    return base64.urlsafe_b64decode(data or "")


def body_text(svc, msg_id, msg, mime) -> str:
    for p in walk(msg["payload"]):
        if p.get("mimeType") == mime and not p.get("filename"):
            return part_bytes(svc, msg_id, p).decode("utf-8", errors="replace")
    return ""


def label_map(svc) -> dict:
    return {l["name"]: l["id"] for l in svc.users().labels().list(userId="me").execute()["labels"]}


def cmd_list(svc, args):
    names = {v: k for k, v in label_map(svc).items()}
    resp = svc.users().messages().list(userId="me", q=args.query, maxResults=args.max).execute()
    for ref in resp.get("messages", []):
        msg = svc.users().messages().get(userId="me", id=ref["id"]).execute()
        h = headers(msg)
        print(json.dumps({
            "id": msg["id"], "thread": msg["threadId"],
            "date": dt.datetime.fromtimestamp(int(msg["internalDate"]) / 1000).isoformat(timespec="minutes"),
            "from": h.get("from", ""), "to": h.get("to", ""), "subject": h.get("subject", ""),
            "labels": sorted(names.get(i, i) for i in msg.get("labelIds", [])),
            "pdfs": [p["filename"] for p in attachments(msg) if is_pdf(p)],
            "files": [p["filename"] for p in attachments(msg) if not is_pdf(p)],
            "link": f"https://mail.google.com/mail/u/0/#all/{msg['threadId']}",
        }, ensure_ascii=False))


def inside_git_repo(folder: Path) -> bool:
    """True inside a project repo. A repo at $HOME itself (Kriss's Mac has ~/.git) doesn't count."""
    r = subprocess.run(["git", "-C", str(folder), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    top = r.stdout.strip()
    return bool(top) and Path(top).resolve() != Path.home().resolve()


def target_dir(path: str) -> Path:
    folder = Path(path).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    if inside_git_repo(folder):
        sys.exit(f"Refusing to write mail attachments inside a Git repo: {folder}")
    return folder


def safe_name(name: str) -> str:
    return re.sub(r"[/\\\x00]", "_", Path(name).name) or "file"


def cmd_attachments(svc, args):
    folder = target_dir(args.dir)
    msg = svc.users().messages().get(userId="me", id=args.msg_id).execute()
    for i, p in enumerate(a for a in attachments(msg) if is_pdf(a) or not args.pdf):
        name = f"{args.msg_id}_{i}_{safe_name(p['filename'])}"
        data = part_bytes(svc, args.msg_id, p)
        (folder / name).write_bytes(data)
        inline = any(h["name"].lower() == "content-id" for h in p.get("headers", []))
        print(f"{folder / name}\t{p.get('mimeType', '')}\t{len(data)} bytes{chr(9) + 'inline' if inline else ''}")


def cmd_text(_svc, args):
    path = Path(args.file)
    ext = path.suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        print("\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(path.read_bytes())).pages))
    elif ext in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True)
        for ws in wb.worksheets:
            print(f"## sheet: {ws.title}")
            for row in ws.iter_rows(values_only=True):
                if any(v is not None for v in row):
                    print("\t".join("" if v is None else str(v) for v in row))
    elif ext == ".docx":
        from docx import Document
        doc = Document(str(path))
        for para in doc.paragraphs:
            if para.text.strip():
                print(para.text)
        for t in doc.tables:
            for row in t.rows:
                print("\t".join(c.text.strip() for c in row.cells))
    elif ext in (".csv", ".txt", ".tsv"):
        print(path.read_text(errors="replace"))
    else:
        sys.exit(f"No text reader for {ext}; open images with Read instead")


def public_host(host: str) -> bool:
    try:
        return all(ipaddress.ip_address(a[4][0]).is_global for a in socket.getaddrinfo(host, 443))
    except (socket.gaierror, ValueError):
        return False


def resolve_link(url: str, session) -> str:
    """Turn a share link into a direct download URL where the service allows it without a login."""
    u = urlparse(url)
    host = u.netloc.lower()
    if host in ("we.tl", "wetransfer.com") or host.endswith(".wetransfer.com"):
        page = session.get(url, timeout=30, allow_redirects=True).url  # we.tl/t-… → …/downloads/<id>/[<rcpt>/]<hash>
        parts = [x for x in urlparse(page).path.split("/") if x]
        if "downloads" not in parts:
            raise RuntimeError("not a WeTransfer download link")
        rest = parts[parts.index("downloads") + 1:]
        body = {"security_hash": rest[-1], "intent": "entire_transfer"}
        if len(rest) == 3:
            body["recipient_id"] = rest[1]
        r = session.post(f"https://wetransfer.com/api/v4/transfers/{rest[0]}/download", json=body, timeout=30)
        link = r.json().get("direct_link") if r.ok else None
        if not link:
            raise RuntimeError(f"WeTransfer gave no download link ({r.status_code}; expired or needs a login)")
        return link
    m = re.search(r"/(?:file/d|open\?id=|uc\?id=)/?([\w-]{20,})", url) or re.search(r"[?&]id=([\w-]{20,})", url)
    if host == "drive.google.com" and m:
        return f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t"
    m = re.search(r"docs\.google\.com/(spreadsheets|document|presentation)/d/([\w-]+)", url)
    if m:
        fmt = {"spreadsheets": "xlsx", "document": "docx", "presentation": "pptx"}[m.group(1)]
        return f"https://docs.google.com/{m.group(1)}/d/{m.group(2)}/export?format={fmt}"
    if host.endswith("dropbox.com"):
        q = parse_qs(u.query)
        q["dl"] = ["1"]
        return u._replace(query="&".join(f"{k}={v[0]}" for k, v in q.items())).geturl()
    return url


def cmd_fetch(_svc, args):
    import requests
    if urlparse(args.url).scheme != "https":
        sys.exit("Refusing: only https links")
    folder = target_dir(args.dir)
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (Macintosh) kb-kriss-mac-agent"
    try:
        url = resolve_link(args.url, session)
    except Exception as e:  # noqa: BLE001 - any failure means "can't get it without a login"
        print(f"NOFILE {args.url}: {e}")
        sys.exit(4)
    host = urlparse(url).hostname or ""
    if not public_host(host):
        sys.exit(f"Refusing: {host} is not a public host")
    with session.get(url, stream=True, timeout=60, allow_redirects=True) as r:
        ctype = r.headers.get("content-type", "").split(";")[0].strip()
        if not r.ok or ctype == "text/html":
            title = re.search(r"<title>(.*?)</title>", r.text[:20000], re.S | re.I) if r.ok else None
            print(f"NOFILE {args.url}: HTTP {r.status_code}, {ctype or 'no type'}"
                  f"{' - page: ' + title.group(1).strip() if title else ''} (a web page or a login, nothing saved)")
            sys.exit(4)
        cd = r.headers.get("content-disposition", "")
        m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="?([^";]+)"?', cd)
        name = safe_name(unquote(m.group(1)) if m else Path(urlparse(r.url).path).name)
        target = folder / name
        size = 0
        with open(target, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                size += len(chunk)
                if size > MAX_FETCH:
                    f.close(); target.unlink()
                    sys.exit(f"Refusing: {args.url} is larger than {MAX_FETCH >> 20} MB")
                f.write(chunk)
    print(f"{target}\t{ctype}\t{size} bytes")


def already_sent(svc, msg, to, files) -> str:
    """Why this message must not go to `to` again, or '' if it may."""
    thread = svc.users().threads().get(userId="me", id=msg["threadId"], format="metadata",
                                       metadataHeaders=["To", "Cc", "Bcc"]).execute()
    for m in thread["messages"]:
        if "SENT" in m.get("labelIds", []):
            h = headers(m)
            rcpts = {a.lower() for _, a in getaddresses([h.get("to", ""), h.get("cc", ""), h.get("bcc", "")])}
            if to in rcpts:
                return f"a sent message to {to} is already in this thread"
    for p in files:
        q = f'in:sent to:{to} filename:"{p["filename"]}"'
        if svc.users().messages().list(userId="me", q=q, maxResults=1).execute().get("messages"):
            return f"{p['filename']} was already sent to {to}"
    return ""


def signature(svc) -> str:
    for s in svc.users().settings().sendAs().list(userId="me").execute().get("sendAs", []):
        if s.get("isDefault"):
            return s.get("signature", "")
    return ""


def note_html(path: str) -> str:
    text = Path(path).read_text()
    if path.lower().endswith(".html"):
        return text
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>" for p in paras)


def kill_switch_on(svc) -> bool:
    resp = svc.users().drafts().list(userId="me", q='subject:"STOP-SENDING"', maxResults=20).execute()
    for d in resp.get("drafts", []):
        m = svc.users().drafts().get(userId="me", id=d["id"], format="metadata").execute()["message"]
        if headers(m).get("subject", "").strip().startswith(KILL_SWITCH):
            return True
    return False


def cmd_forward(svc, args):
    to = args.to.strip().lower()
    if to not in ALLOWED_TO:
        sys.exit(f"Refusing: {to} is not an allowed recipient ({', '.join(sorted(ALLOWED_TO))})")
    if kill_switch_on(svc):
        print(f"STOP {args.msg_id}: a {KILL_SWITCH} draft exists (kb/email/send-policy.md), nothing forwarded")
        sys.exit(5)
    msg = svc.users().messages().get(userId="me", id=args.msg_id).execute()
    h = headers(msg)
    labels = label_map(svc)
    if to in VOUCHER_TO and labels.get(FORWARDED_LABEL) in msg.get("labelIds", []):
        print(f"SKIP {args.msg_id}: already labelled {FORWARDED_LABEL}")
        sys.exit(3)
    files = [p for p in attachments(msg) if is_pdf(p) and (not args.only or p["filename"] in args.only)]
    missing = set(args.only or []) - {p["filename"] for p in files}
    if missing or not files:
        sys.exit(f"No such PDF attachment(s) on {args.msg_id}: {sorted(missing) or 'none at all'}")
    if not args.force:
        why = already_sent(svc, msg, to, files)
        if why:
            print(f"SKIP {args.msg_id}: {why}")
            sys.exit(3)

    subject = h.get("subject", "")
    fwd = EmailMessage()
    fwd["To"] = to
    fwd["Subject"] = subject if subject.lower().startswith(("fwd:", "fw:")) else f"Fwd: {subject}"
    if h.get("message-id"):
        fwd["In-Reply-To"] = h["message-id"]
        fwd["References"] = (h.get("references", "") + " " + h["message-id"]).strip()

    quote_head = [("From", h.get("from", "")), ("Date", h.get("date", "")),
                  ("Subject", subject), ("To", h.get("to", ""))]
    orig_text = body_text(svc, args.msg_id, msg, "text/plain")
    orig_html = body_text(svc, args.msg_id, msg, "text/html") or f"<pre>{html.escape(orig_text)}</pre>"
    top_html = note_html(args.note) + signature(svc) if args.note else ""
    top_text = Path(args.note).read_text() if args.note and not args.note.lower().endswith(".html") else ""

    plain = (top_text + "\n\n" if top_text else "") + "---------- Forwarded message ---------\n" + \
        "".join(f"{k}: {v}\n" for k, v in quote_head) + "\n" + orig_text
    rich = top_html + "<br><div>---------- Forwarded message ---------<br>" + \
        "".join(f"{k}: {html.escape(v)}<br>" for k, v in quote_head) + "<br></div>" + orig_html
    fwd.set_content(plain)
    fwd.add_alternative(rich, subtype="html")

    for p in files:
        maintype, _, subtype = (p.get("mimeType") or "application/octet-stream").partition("/")
        fwd.add_attachment(part_bytes(svc, args.msg_id, p), maintype=maintype,
                           subtype=subtype or "octet-stream", filename=p["filename"])

    names = ", ".join(p["filename"] for p in files)
    if dry_mode(args):
        print(f"DRY would forward {args.msg_id} to {to}: {fwd['Subject']} | attachments: {names}"
              f" | note: {'yes' if args.note else 'no'}")
        return
    raw = base64.urlsafe_b64encode(fwd.as_bytes()).decode()
    sent = svc.users().messages().send(userId="me", body={"raw": raw, "threadId": msg["threadId"]}).execute()
    print(f"SENT {args.msg_id} to {to} as {sent['id']}: {fwd['Subject']} | attachments: {names}")


def cmd_label(svc, args):
    labels = label_map(svc)
    add = [c[1:] for c in args.changes if c.startswith("+")]
    remove = [c[1:] for c in args.changes if c.startswith("-")]
    bad = [c for c in args.changes if c[:1] not in "+-"]
    if bad:
        sys.exit(f"Label changes must start with + or -: {bad}")
    if dry_mode(args):
        print(f"DRY would label {args.msg_id}: +{add} -{remove}")
        return
    for name in add:
        if name not in labels:
            labels[name] = svc.users().labels().create(userId="me", body={"name": name}).execute()["id"]
    body = {"addLabelIds": [labels[n] for n in add],
            "removeLabelIds": [labels[n] for n in remove if n in labels]}
    svc.users().messages().modify(userId="me", id=args.msg_id, body=body).execute()
    print(f"labelled {args.msg_id}: +{add} -{remove}")


def doc_drafts(svc):
    """[Doc] drafts with their thread id (from X-KB-Thread, else the thread link in the body)."""
    out, token = [], None
    while True:
        resp = svc.users().drafts().list(userId="me", q='subject:"Doc"', pageToken=token, maxResults=100).execute()
        for d in resp.get("drafts", []):
            full = svc.users().drafts().get(userId="me", id=d["id"], format="full").execute()
            msg = full["message"]
            h = headers(msg)
            if not h.get("subject", "").startswith(DOC_PREFIX):
                continue
            thread = h.get("x-kb-thread", "")
            if not thread:
                m = re.search(r"#all/([0-9a-f]+)", body_text(svc, msg["id"], msg, "text/plain"))
                thread = m.group(1) if m else ""
            created = dt.datetime.fromtimestamp(int(msg["internalDate"]) / 1000)
            out.append({"id": d["id"], "subject": h["subject"], "thread": thread,
                        "date": created.isoformat(timespec="minutes")})
        token = resp.get("nextPageToken")
        if not token:
            return out


def cmd_draft(svc, args):
    subject = args.subject if args.subject.startswith(DOC_PREFIX) else f"{DOC_PREFIX} {args.subject}"
    body = Path(args.body_file).read_text().rstrip() + \
        f"\n\nGmail: https://mail.google.com/mail/u/0/#all/{args.thread_id}\n"
    old = [d for d in doc_drafts(svc) if d["thread"] == args.thread_id]
    if dry_mode(args):
        print(f"DRY would write draft '{subject}'" + (f" (replacing {len(old)} earlier)" if old else "") +
              "\n" + "\n".join("    " + line for line in body.splitlines()))
        return
    m = EmailMessage()
    m["Subject"] = subject
    m["X-KB-Thread"] = args.thread_id
    m.set_content(body)
    raw = base64.urlsafe_b64encode(m.as_bytes()).decode()
    new = svc.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    for d in old:
        svc.users().drafts().delete(userId="me", id=d["id"]).execute()
    print(f"drafted {new['id']}: {subject}" + (f" (replaced {len(old)})" if old else ""))


def cmd_drafts(svc, _args):
    for d in doc_drafts(svc):
        print(json.dumps(d, ensure_ascii=False))


def delete_doc_draft(svc, draft_id, why, dry):
    d = svc.users().drafts().get(userId="me", id=draft_id, format="metadata").execute()
    subject = headers(d["message"]).get("subject", "")
    if not subject.startswith(DOC_PREFIX):
        sys.exit(f"Refusing: draft {draft_id} is not a {DOC_PREFIX} draft ({subject!r})")
    if dry:
        print(f"DRY would delete draft {draft_id} '{subject}' ({why})")
        return
    svc.users().drafts().delete(userId="me", id=draft_id).execute()
    print(f"deleted draft {draft_id} '{subject}' ({why})")


def cmd_delete_draft(svc, args):
    delete_doc_draft(svc, args.draft_id, "on request", dry_mode(args))


def thread_archived(svc, thread_id) -> bool:
    try:
        t = svc.users().threads().get(userId="me", id=thread_id, format="minimal").execute()
    except Exception:  # noqa: BLE001 - a deleted thread counts as archived
        return True
    return not any("INBOX" in m.get("labelIds", []) for m in t.get("messages", []))


def cmd_housekeep(svc, args):
    dry = dry_mode(args)
    cutoff = time.time() - args.days * 86400
    if DOCS_DIR.is_dir():
        for folder in sorted(DOCS_DIR.iterdir()):
            if folder.is_dir() and folder.stat().st_mtime < cutoff:
                print(f"{'DRY would delete' if dry else 'deleted'} {folder.name}/ (older than {args.days} days)")
                if not dry:
                    shutil.rmtree(folder)
    for d in doc_drafts(svc):
        old = dt.datetime.fromisoformat(d["date"]).timestamp() < cutoff
        if old or not d["thread"] or thread_archived(svc, d["thread"]):
            why = f"older than {args.days} days" if old else "thread archived" if d["thread"] else "no thread"
            delete_doc_draft(svc, d["id"], why, dry)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("query"); p.add_argument("--max", type=int, default=100)
    p = sub.add_parser("attachments"); p.add_argument("msg_id"); p.add_argument("dir")
    p.add_argument("--pdf", action="store_true")
    p = sub.add_parser("pdfs"); p.add_argument("msg_id"); p.add_argument("dir")
    p.set_defaults(pdf=True)
    p = sub.add_parser("text"); p.add_argument("file")
    p = sub.add_parser("fetch"); p.add_argument("url"); p.add_argument("dir")
    p = sub.add_parser("forward"); p.add_argument("msg_id"); p.add_argument("to")
    p.add_argument("--note"); p.add_argument("--only", nargs="+", metavar="NAME")
    p.add_argument("--force", action="store_true"); p.add_argument("--dry", action="store_true")
    p = sub.add_parser("label"); p.add_argument("msg_id"); p.add_argument("changes", nargs=argparse.REMAINDER)
    p = sub.add_parser("draft"); p.add_argument("thread_id"); p.add_argument("subject"); p.add_argument("body_file")
    p.add_argument("--dry", action="store_true")
    sub.add_parser("drafts")
    p = sub.add_parser("delete-draft"); p.add_argument("draft_id"); p.add_argument("--dry", action="store_true")
    p = sub.add_parser("housekeep"); p.add_argument("--days", type=int, default=14)
    p.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    if args.cmd == "label":  # "-A" would read as an option, so the changes are taken verbatim
        args.dry = "--dry" in args.changes
        args.changes = [c for c in args.changes if c != "--dry"]
        if not args.changes:
            ap.error("label needs at least one +LABEL or -LABEL")
    svc = None if args.cmd in ("text", "fetch") else gmail_service()
    {"list": cmd_list, "attachments": cmd_attachments, "pdfs": cmd_attachments, "text": cmd_text,
     "fetch": cmd_fetch, "forward": cmd_forward, "label": cmd_label, "draft": cmd_draft,
     "drafts": cmd_drafts, "delete-draft": cmd_delete_draft, "housekeep": cmd_housekeep}[args.cmd](svc, args)


if __name__ == "__main__":
    main()
