# Mac attachment agent — instructions (part C of the daily email run)

Runs **Claude Code headless on Kriss's Mac, every hour while the Mac is awake** (launchd job `no.livid.kb-kriss-mac-agent`, `claude -p "Follow docs/mac-agent.md in ~/kb-kriss"`). Exists because the cloud Gmail connector can't read attachments; on the Mac, the Gmail API (token in the Keychain, scopes readonly + modify + send) can.

## Each run
1. Read `~/kb-kriss/AGENTS.md`, `~/livid-kb/AGENTS.md`, livid-kb `finance/bookkeeping/processes/invoice-routing.md` (follow it exactly), and the supplier Organization docs it needs (`kb_find.py`).
2. **Invoices:** messages labelled `AI/Invoice` (set by the 06:47 cloud run) and any new unlabelled mail with a PDF from a supplier domain or to invoice@ since the last run. Download the PDFs (`scripts/email/gmail_tool.py`), read them, then per invoice-routing:
   - clear case (step 6) → forward to the entity's PowerOffice voucher address, label `AI/PO-forwarded`, remove `AI/Invoice`;
   - external brand (step 7b) → also forward to Ole Eivind with the Norwegian note + auto-sent disclaimer;
   - not clear → keep `AI/Invoice`, and add a one-line reason to the message's entry in the run log so the brief can show "why not automatic".
3. **Customs:** run `scripts/email/file_customs.py` (it files `AI/Customs` mail into Tolldeklarasjoner/LJAS|LRAS and relabels `AI/Filed`).
4. **Log:** append one line per run to `~/Library/Logs/kb-kriss-mac-agent.log` and, if anything was forwarded or filed, one `kb/log.md` entry (counts, suppliers, entity; no amounts or bodies). Auto-sync pushes it; the morning brief reads it for "Forwarded automatically".
5. Never: reply, delete, unsubscribe, or send to anyone other than the two PowerOffice voucher addresses and Ole Eivind (`oleeivind@livid.no`). Never forward the same message twice (`AI/PO-forwarded` and the Sent check). Raw mail and PDFs only in a temp folder outside the repo, deleted at the end of the run.

## Setup (Claude Code, once)
- Gmail scopes in `scripts/email/gmail_auth.py`: readonly + modify + send; re-authorize.
- `scripts/email/gmail_tool.py`: small CLI over `gmail_service()` — `list <query>`, `pdfs <msg_id> <dir>` (download PDF attachments), `forward <msg_id> <to> [--note file]` (forward with the original attachments, note above the quoted message), `label <msg_id> +A -B`.
- launchd job: hourly (`StartInterval 3600`, `RunAtLoad`), runs `claude -p` in `~/kb-kriss` with only the permissions this needs (Bash for the two scripts and `kb_find.py`, file reads, edits to `kb/log.md`), log to `~/Library/Logs/kb-kriss-mac-agent.log`. Test once with `--dry` behaviour (no forwarding) before enabling.
