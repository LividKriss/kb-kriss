# kb-kriss build — progress and handoff

Companion to [brief.md](brief.md). Read the brief first; this file records what is done, what was decided along the way, and what step 3 needs to know. Update it at the end of every step.

## Status (2026-10-22)

| Step | Status | Where |
|---|---|---|
| 0 Prerequisites | Done | Claude Code |
| 1 Scaffold kb-kriss | Done | Cowork |
| 2 livid-kb changes | Done | Cowork |
| 3 Backfill pass 1 (headers) | **Next** | Claude Code |
| 4–7 | Not started | |

## Decisions made so far (also in the KBs)

- **Scope** (kb-kriss `kb/notes/email-assistant-scope.md`): work Gmail only; headers 3 years; content 12 months (3 years for key contacts); KB in English, drafts in the thread's language.
- **Person notes** written by an agent start as `status: draft` until Kriss has reviewed them (bulk confirmation is fine).
- **kb-router** is one skill, uploaded to Kriss's Claude account (`anthropic-skills:kb-router`), used by both Cowork and Claude Code. No symlink. After any edit to `livid-kb/.claude/skills/kb-router/SKILL.md` it must be re-uploaded — tell Kriss.
- **Finding docs:** `python3 ~/livid-kb/tools/kb_find.py [--kb company|personal|both] [--type T] <terms>` — frontmatter/path/email search, never bodies.
- **livid-kb schema:** Organization has optional `email_domains` (sender domains, never shared platforms) and `invoice_channels` (`ehf | email | portal`). Filled for ~56 suppliers (top 50 by 2026 voucher count + 14 new docs).
- **Invoice routing** (livid-kb `finance/bookkeeping/processes/invoice-routing.md`, draft): invoices/credit notes/receipts → entity's PowerOffice voucher address after batch approval; customs documents → Google Drive `My Drive/test/REGNSKAP/Tolldeklarasjoner/LJAS|LRAS`, never PowerOffice. Used in steps 5–6, not in step 3.

## What step 3 needs to know

**Mail facts found in step 2**
- invoice@lividjeans.com (one.com) has forwarded into Kriss's Gmail only since about **2026-10-11**. Older invoice@ mail exists only in the one.com mailbox — not in scope for the backfill. In Gmail, treat mail addressed to invoice@ as **invoice traffic, not relationships** (exclude it from the contact table, or mark it).
- Many suppliers send invoices to kristoffer@ directly (Texgoios, Kuroki via Blue.Men, Nilorn, Stork, Afonso, Passamar, Japan Blue, Rangel …). Those people are also real relationships — keep them.
- **Shared platform senders — never a contact, never an organization match:** xero.com / post.xero.com, via.tripletex.no, fiken.no, xledger.net, e-conomic.com, delivery.payex.com, traede.com, stripe.com, mail.poweroffice.net (also sends Kriss's payslips), equity.credit / equity.no, fortnox.se, exact.com, superhuman.com (reminders/sharing), mailer-daemon.
- **Noise seen:** news.modeinfo.com, paddlersuk.com (mostly), email.kinto-europe.com, labels-things.com, later.com, mail.adobe.com, *.hs-send.com, tvstore.fr, 123lyd.
- Internal domains: livid.no, lividjeans.com → category `colleague` (work context only, nothing HR).

**Organization matching**
- Match sender domains against livid-kb Organization `email_domains` first (read frontmatter with PyYAML or `kb_find.py <domain>`), then by name.
- Kuroki's invoices come from its agent Blue.Men (bluemens.com, bluemen.it); Welcome AB and Abel Odor via platforms. Don't infer organizations from platform senders.
- Unmatched domains with real business traffic → list as **proposed Organizations** (customers, manufacturers, advisors) for Kriss to confirm in a batch at the step 4 checkpoint. Do not write to livid-kb in step 3.

**Rules that apply (brief + AGENTS.md of both repos)**
- Gmail API, scope `gmail.readonly`, `format=metadata` only (headers: From, To, Cc, Date, Subject; plus threadId and labelIds). **No bodies in step 3.**
- Use the venv and `gmail_service()` from `scripts/email/gmail_auth.py`. Batch requests; respect quota (back off on 429).
- Raw output lives only in `~/Library/Application Support/kb-kriss/cache/`, never in the repo. Scripts go in `scripts/email/` (committed); their output does not.
- "Kriss replied" = a message in the thread with label `SENT` (or From kristoffer@livid.no / kristoffer@lividjeans.com) after a message from that contact.
- Contact categories (brief) are a **proposal** at this step: confirm/adjust the enum with Kriss in the summary.

**Deliverable for the ⏸ checkpoint**
1. Summary by category: number of contacts, messages in/out, threads with a reply from Kriss.
2. Top ~150 contacts (address, name, domain, matched org, in/out, replied threads, first/last contact, suggested category) as a local CSV in the cache folder plus a readable table for Kriss.
3. List of dropped noise (domains + counts) so Kriss can rescue anything wrongly dropped.
4. Proposed new Organizations and `email_domains` for livid-kb (one batch).
5. Proposed threshold for step 4 content reading (brief: ≥3 threads with a reply from Kriss in the last 12 months) with the resulting contact count.

After Kriss's corrections: update this file (status + decisions), and add a `kb/log.md` entry in kb-kriss for anything written.
