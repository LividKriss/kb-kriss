---
type: Note
title: How the KB repos, auto-sync and the Gmail access are set up
description: Machinery facts about livid-kb and kb-kriss (auto-sync jobs, Gmail OAuth, Mac agent traps); read when a job fails or a new Mac is set up.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/sonnet-5.5
  at: 2026-11-19T09:10:00+01:00
---

Source: Claude memory notes livid-kb-autosync (2026-10-22), kb-kriss-setup (2026-10-22) and kb-kriss-mac-agent (2026-10-23). The run mechanics are in `docs/mac-agent.md`; the saving rules are in `AGENTS.md` §5.

**Repos.** `~/livid-kb` is github.com/LividKriss/livid-kb and `~/kb-kriss` is github.com/LividKriss/kb-kriss, both private, over SSH, branch main. Cowork wrote the first content; nobody runs Git by hand. `~` itself is also a Git repo (no commits), so any "inside a git repo" check fires for everything under home; the auto-sync script and `gmail_tool.py` guard against a repo whose top level is `$HOME`.

**Auto-sync.** launchd jobs `no.livid.kb-autosync` and `no.livid.kb-kriss-autosync` (the second is a copy of the first with names changed) run `tools/autosync.sh` every 180 s: skip if any file changed in the last minute, `git add -A`, commit with the new `kb/log.md` lines as the message, pull with rebase, push. Logs: `~/Library/Logs/livid-kb-autosync.log` and `~/Library/Logs/kb-kriss-autosync.log`; a macOS notification appears after 30 minutes of failures. Reinstall with `tools/install_autosync.sh`. kb-kriss has a `.gitignore` blocking client secrets, tokens, cache and `.eml` files, because auto-sync does `git add -A`. The validator needs PyYAML, which the system Python lacks: use the kb-kriss venv Python for `build_index.py`, `validate.py` and `kb_find.py`. System Git is 2.23 (no `git init -b`). Validation also runs in GitHub CI on every push to livid-kb.

**Gmail access.** A dedicated Google Cloud project `kb-kriss` in the livid.no organisation, Gmail API enabled, consent screen Internal, a Desktop OAuth client `kb-kriss-local`, with its client JSON (mode 600), the venv and the cache stored outside the repo in `~/Library/Application Support/kb-kriss/`. `scripts/email/gmail_auth.py authorize|check` manages the token, which lives in the macOS Keychain (service `kb-kriss-gmail`, account `oauth-token`). Authorised 2026-10-22 with the read-only scope; scopes were later widened to read, modify and send (`docs/mac-agent.md`). The first `check` returned the CFO's mailbox with 69,854 messages in 35,566 threads. Adding a scope means changing Data Access in the project and re-running `authorize`. Downloading the client JSON in the Cloud console cannot be clicked by the browser extension; Kriss has to do it.

**Mac agent traps** (job `no.livid.kb-kriss-mac-agent`, live since 2026-10-23 22:01, hourly, runs on one Mac only):
- The job calls the standalone `claude` CLI (`~/.local/bin/claude`, logged in via claude.ai); the desktop app's bundled CLI cannot be used from launchd. Log: `~/Library/Logs/kb-kriss-mac-agent.log`. Test with `mac_agent.sh --dry` before touching the live job.
- Claude Code's sandbox cannot read the Google Drive CloudStorage folder ("Operation not permitted"); run `file_customs.py` and Drive checks from a terminal tab.
- The venv is Python 3.9: scripts need `from __future__ import annotations` for `X | None`.
- Forward recipients are hard-coded in `gmail_tool.py` `ALLOWED_TO` (two PowerOffice voucher addresses, Ole Eivind, HK Consulting). Adding one also needs a send-policy change, which takes a second confirmation.
- First live run: 9 PowerOffice forwards and 1 to HK. A dry run caught the `~/.git` guard problem, and an extra Nokas receipt (7, not 6) turned up once the agent was made to read every PDF.
