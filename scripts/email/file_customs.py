#!/usr/bin/env python3
"""File customs documents from Gmail into the Tolldeklarasjoner folders on Kriss's Mac.

Runs unattended (launchd, see install_customs_job.sh), whenever the Mac is awake.
Process: kb-kriss/kb/email/daily-run.md (step 4) and livid-kb invoice-routing (step 8).

    file_customs.py           file everything labelled AI/Customs (not yet AI/Filed)
    file_customs.py --dry     show what would happen, change nothing (also when KB_AGENT_DRY=1)
    file_customs.py --test F  parse one local PDF and print the result

For each message labelled AI/Customs: download the PDF attachment(s), read the entity
(Livid Jeans AS -> LJAS, Livid Retail AS -> LRAS) from the declaration, save it as
YYYY-MM-DD_<Carrier>_<Type>_<Ref>.pdf in that folder's root, then relabel the message
AI/Customs -> AI/Filed. If the entity is unclear, the PDF goes to _Usikker/ and the
message gets AI/Action, so the morning brief asks Kriss. Never overwrites a file.
Needs the gmail.modify scope (re-run gmail_auth.py authorize once after adding it).
"""
from __future__ import annotations  # venv is Python 3.9

import base64
import datetime as dt
import io
import os
import re
import sys
from pathlib import Path

ROOT = Path.home() / "Library/CloudStorage/GoogleDrive-kristoffer@livid.no/My Drive/test/REGNSKAP/Tolldeklarasjoner"
FOLDER = {"jeans": "LJAS", "retail": "LRAS"}
QUERY = "label:AI/Customs -label:AI/Filed newer_than:60d"

RETAIL = re.compile(r"RETAIL\s+AS|913\s?818\s?822")
JEANS = re.compile(r"LIVID\s+JEANS\s+AS\b|999\s?174\s?930")


def pdf_text(data: bytes) -> str:
    from pypdf import PdfReader
    return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)


def carrier_of(sender: str, text: str) -> str:
    names = (("ups", "UPS"), ("dhl", "DHL"), ("fedex", "FedEx"), ("cargolinea", "CargoLinea"))
    for key, name in names:                       # the sender's domain decides first
        if re.search(rf"[@.]{key}\b", sender.lower()):
            return name
    for key, name in names:                       # then the document itself, whole words only
        if re.search(rf"\b{key}\b", text[:3000].lower()):
            return name
    return "Toll"


def parse(text: str, sender: str = "", subject: str = "", filename: str = "", email_date: str = "") -> dict:
    """Return entity, carrier, doc type, date, ref and the target file name."""
    retail = bool(RETAIL.search(text))
    jeans = bool(JEANS.search(text))
    entity = "retail" if retail and not jeans else "jeans" if jeans and not retail else None

    tollid = re.search(r"\b(44[26]0\d{12})\b", text) or re.search(r"\b(44[26]0\d{12})\b", subject + filename)
    tollid = tollid.group(1) if tollid else ""
    carrier = carrier_of(sender, text)
    if carrier == "UPS":
        doctype = "Utforsel" if tollid.startswith("4420") or "Utførsel" in subject else "Innforsel"
        ref = re.search(r"Ref:\s*(\w+)", subject)
        ref = ref.group(1) if ref else Path(filename).stem.split("_")[0]
    elif carrier == "DHL":
        doctype, ref = "Tolldeklaration", (re.search(r"(\d{10})", filename) or re.search(r"(\d{10})", subject) or [None, tollid])[1]
    elif carrier == "FedEx":
        doctype, ref = "Tolldeklarasjon", tollid or Path(filename).stem
    elif carrier == "CargoLinea":
        doctype = "Tollkvittering"
        m = re.search(r"TK,\s*([\d-]+)", subject)
        ref = m.group(1) if m else tollid or Path(filename).stem
    else:
        doctype, ref = "Tolldokument", tollid or Path(filename).stem

    m = re.search(r"Tolldato:\s*(\d{2})\.(\d{2})\.(\d{4})", text)
    if m:
        date = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    else:
        m = re.search(r"\b(20\d{2})(\d{2})(\d{2})\b", text)
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else (email_date or dt.date.today().isoformat())
    ref = re.sub(r"[^\w.-]", "_", str(ref))
    return {"entity": entity, "carrier": carrier, "type": doctype, "date": date, "ref": ref,
            "name": f"{date}_{carrier}_{doctype}_{ref}.pdf"}


def save(data: bytes, folder: Path, name: str) -> Path | None:
    """Write without overwriting. Returns the path, or None if an identical file exists."""
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    n = 1
    while target.exists():
        if target.read_bytes() == data:
            return None
        target = folder / f"{Path(name).stem}_{n}.pdf"
        n += 1
    target.write_bytes(data)
    return target


def label_ids(svc, names):
    labels = {l["name"]: l["id"] for l in svc.users().labels().list(userId="me").execute()["labels"]}
    return [labels[n] for n in names if n in labels]


def run(dry: bool):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gmail_auth import gmail_service
    svc = gmail_service()
    customs, filed, action = (label_ids(svc, [n]) for n in ("AI/Customs", "AI/Filed", "AI/Action"))
    msgs = svc.users().messages().list(userId="me", q=QUERY, maxResults=200).execute().get("messages", [])
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"{stamp} {len(msgs)} message(s) to file")
    for ref in msgs:
        msg = svc.users().messages().get(userId="me", id=ref["id"]).execute()
        hdr = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        email_date = dt.datetime.fromtimestamp(int(msg["internalDate"]) / 1000).date().isoformat()
        parts, stack = [], [msg["payload"]]
        while stack:
            p = stack.pop()
            stack += p.get("parts", []) or []
            if p.get("filename", "").lower().endswith(".pdf") and p.get("body", {}).get("attachmentId"):
                parts.append(p)
        if not parts:
            print(f"  {ref['id']}: no PDF attachment, left for the brief")
            if not dry:
                svc.users().messages().modify(userId="me", id=ref["id"], body={"addLabelIds": action}).execute()
            continue
        unclear = False
        for p in parts:
            att = svc.users().messages().attachments().get(
                userId="me", messageId=ref["id"], id=p["body"]["attachmentId"]).execute()
            data = base64.urlsafe_b64decode(att["data"])
            info = parse(pdf_text(data), hdr.get("from", ""), hdr.get("subject", ""), p["filename"], email_date)
            folder = ROOT / (FOLDER[info["entity"]] if info["entity"] else "_Usikker")
            unclear |= info["entity"] is None
            if dry:
                print(f"  would save {folder.name}/{info['name']}")
                continue
            out = save(data, folder, info["name"])
            print(f"  {'saved ' + str(out.relative_to(ROOT)) if out else 'already filed: ' + info['name']}")
        if not dry:
            body = {"addLabelIds": filed + (action if unclear else []), "removeLabelIds": [] if unclear else customs}
            svc.users().messages().modify(userId="me", id=ref["id"], body=body).execute()


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--test":
        f = Path(sys.argv[2])
        print(parse(pdf_text(f.read_bytes()), filename=f.name, subject=f.name))
    else:
        if not ROOT.is_dir():
            sys.exit(f"Customs folder not found (Google Drive not mounted?): {ROOT}")
        run(dry="--dry" in sys.argv or os.environ.get("KB_AGENT_DRY") == "1")
