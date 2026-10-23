#!/usr/bin/env python3
"""Small Gmail CLI for the Mac attachment agent (docs/mac-agent.md).

    gmail_tool.py list <query> [--max N]          one JSON line per message (no bodies)
    gmail_tool.py pdfs <msg_id> <dir>             download the PDF attachments, print their paths
    gmail_tool.py text <pdf>                      print a PDF's text (pypdf)
    gmail_tool.py forward <msg_id> <to> [--note F] [--only NAME ...] [--force]
                                                  forward with the original PDFs (or only the named ones);
                                                  note above the quote
    gmail_tool.py label <msg_id> +A -B ...        add/remove labels by name (missing ones are created)

With KB_AGENT_DRY=1 (or --dry), `forward` and `label` print what they would do and change nothing.
The duplicate checks still run, so a dry run shows what a real run would skip.

Guards that live here, not only in the agent's instructions:
  - forward sends only to ALLOWED_TO (the two PowerOffice voucher addresses and Ole Eivind);
  - forward refuses (exit 3) when the message already went to that address: the AI/PO-forwarded
    label for a voucher address, a sent message to it in the same thread, or a sent message to it
    carrying an attachment with the same file name. --force skips the last two, never the allowlist.
  - pdfs refuses a target folder inside a Git repo (raw mail never goes in a repo).

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
import os
import subprocess
import sys
from email.message import EmailMessage
from email.utils import getaddresses
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmail_auth import gmail_service  # noqa: E402

VOUCHER_TO = {"livid@faktura.poweroffice.net", "lividretail@faktura.poweroffice.net"}  # livid-kb systems/poweroffice-go.md
ALLOWED_TO = VOUCHER_TO | {"oleeivind@livid.no"}  # docs/mac-agent.md "Never"
FORWARDED_LABEL = "AI/PO-forwarded"


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
            "link": f"https://mail.google.com/mail/u/0/#all/{msg['threadId']}",
        }, ensure_ascii=False))


def inside_git_repo(folder: Path) -> bool:
    r = subprocess.run(["git", "-C", str(folder), "rev-parse", "--is-inside-work-tree"],
                       capture_output=True, text=True)
    return r.stdout.strip() == "true"


def cmd_pdfs(svc, args):
    folder = Path(args.dir).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    if inside_git_repo(folder):
        sys.exit(f"Refusing to write mail attachments inside a Git repo: {folder}")
    msg = svc.users().messages().get(userId="me", id=args.msg_id).execute()
    for i, p in enumerate(a for a in attachments(msg) if is_pdf(a)):
        name = f"{args.msg_id}_{i}_{Path(p['filename']).name}"
        (folder / name).write_bytes(part_bytes(svc, args.msg_id, p))
        print(folder / name)


def cmd_text(_svc, args):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(Path(args.pdf).read_bytes()))
    print("\n".join(p.extract_text() or "" for p in reader.pages))


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


def cmd_forward(svc, args):
    to = args.to.strip().lower()
    if to not in ALLOWED_TO:
        sys.exit(f"Refusing: {to} is not an allowed recipient ({', '.join(sorted(ALLOWED_TO))})")
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("query"); p.add_argument("--max", type=int, default=100)
    p = sub.add_parser("pdfs"); p.add_argument("msg_id"); p.add_argument("dir")
    p = sub.add_parser("text"); p.add_argument("pdf")
    p = sub.add_parser("forward"); p.add_argument("msg_id"); p.add_argument("to")
    p.add_argument("--note"); p.add_argument("--only", nargs="+", metavar="NAME")
    p.add_argument("--force", action="store_true"); p.add_argument("--dry", action="store_true")
    p = sub.add_parser("label"); p.add_argument("msg_id"); p.add_argument("changes", nargs=argparse.REMAINDER)
    args = ap.parse_args()
    if args.cmd == "label":  # "-A" would read as an option, so the changes are taken verbatim
        args.dry = "--dry" in args.changes
        args.changes = [c for c in args.changes if c != "--dry"]
        if not args.changes:
            ap.error("label needs at least one +LABEL or -LABEL")
    svc = None if args.cmd == "text" else gmail_service()
    {"list": cmd_list, "pdfs": cmd_pdfs, "text": cmd_text, "forward": cmd_forward, "label": cmd_label}[args.cmd](svc, args)


if __name__ == "__main__":
    main()
