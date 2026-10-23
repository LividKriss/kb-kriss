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
- `scripts/email/gmail_tool.py`: small CLI over `gmail_service()` — `list <query>` (JSON lines), `pdfs <msg_id> <dir>` (download PDF attachments), `text <pdf>`, `forward <msg_id> <to> [--note file] [--only NAME …]` (forwards the message's PDFs, or only the named voucher PDFs; note above the quoted message, Kriss's Gmail signature after it), `label <msg_id> +A -B`. The recipient allowlist and the duplicate checks (label, Sent in the thread, same file name in Sent) are in the code; exit 3 = skipped as already forwarded. The note for Ole Eivind is an `.html` file in the run's temp folder: the 7b text, then the auto-sent disclaimer from `kb/email/signature.md` in its grey `<p>`.
- `scripts/email/mac_agent.sh [--dry]`: one run. Makes the per-run temp folder (deleted afterwards), passes the last-run time, runs `claude -p` in `dontAsk` mode with only: Read/Glob/Grep, the two scripts, `kb_find.py`, `build_index.py`/`validate.py`, edits to `kb/log.md` (+ `kb/index.md`) and the temp folder. `--dry` sets `KB_AGENT_DRY=1`, which makes `forward`, `label` and `file_customs.py` print instead of act.
- `scripts/email/install_mac_agent.sh`: launchd job `no.livid.kb-kriss-mac-agent`, hourly (`StartInterval 3600`, `RunAtLoad`), log `~/Library/Logs/kb-kriss-mac-agent.log`. Needs the standalone `claude` CLI, logged in. Replaces `install_customs_job.sh` (removes that job if present). Install only after a dry run looked right.
