# kb-kriss build — progress and handoff

Companion to [brief.md](brief.md). Read the brief first; this file records what is done, what was decided along the way, and what step 3 needs to know. Update it at the end of every step.

## Status (2026-10-22)

| Step | Status | Where |
|---|---|---|
| 0 Prerequisites | Done | Claude Code |
| 1 Scaffold kb-kriss | Done | Cowork |
| 2 livid-kb changes | Done | Cowork |
| 3 Backfill pass 1 (headers) | **Reviewed on 12 months; 3-year refresh pending** (fetch running) | Claude Code |
| 4–7 | Not started | |

## Decisions made so far (also in the KBs)

- **Scope** (kb-kriss `kb/notes/email-assistant-scope.md`): work Gmail only; headers 3 years; content 12 months (3 years for key contacts); KB in English, drafts in the thread's language.
- **Person notes** written by an agent start as `status: draft` until Kriss has reviewed them (bulk confirmation is fine).
- **kb-router** is one skill, uploaded to Kriss's Claude account (`anthropic-skills:kb-router`), used by both Cowork and Claude Code. No symlink. After any edit to `livid-kb/.claude/skills/kb-router/SKILL.md` it must be re-uploaded — tell Kriss.
- **Finding docs:** `python3 ~/livid-kb/tools/kb_find.py [--kb company|personal|both] [--type T] <terms>` — frontmatter/path/email search, never bodies.
- **livid-kb schema:** Organization has optional `email_domains` (sender domains, never shared platforms) and `invoice_channels` (`ehf | email | portal`). As of 2026-10-22: `invoice_channels` on 54 orgs, `email_domains` on 31 (EHF-only suppliers often have none). `kb_find.py <domain>` searches both since 2026-10-22.
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

## Step 3 — what was done and decided (2026-10-22)

**Tooling** (`scripts/email/`, run with the venv; nothing written to either `kb/`)
- `fetch_headers.py`: `format=metadata`, resumable, output in `cache/headers/`. 69,608 messages in the 3-year window (almost the whole mailbox). Besides From/To/Cc/Date/Subject it reads the list/auto headers (`List-Unsubscribe`, `List-Id`, `Precedence`, `Auto-Submitted`, `X-Autoreply`) for the noise pass. **Quota:** the binding limit is Gmail's per-user units-per-minute quota (403 "Quota exceeded … per minute per user"), not concurrency; the script paces itself at ~4 msgs/s, so 3 years takes ~5 h. Raise the quota in the `kb-kriss` GCP project to go faster.
- `build_contacts.py [--months N]`: contact table, noise drop, org match, step-4 flag. Output in `cache/step3[-Nm]/`.
- `report_html.py [--months N]`: one local HTML page of the five deliverables (`cache/step3[-Nm]/report.html`); open it locally, never upload it.
- **Kriss's review answers** live in `~/Library/Application Support/kb-kriss/review/corrections.json` (domain/address → category, org, note), outside the cache so they survive its deletion. `build_contacts.py` applies them. They hold third-party and private details, so they stay out of the repo; delete them once step 4 has written the Person notes and the org batch is decided.
- PyYAML is not in the system `python3` on this Mac; it is installed in the kb-kriss venv. Run `kb_find.py` with the venv's python.

**Review was done on a 12-month preview** (28.7k messages), in rounds of click-through questions; the 3-year rebuild applies the same corrections. Result: 843 contacts kept, 275 matched to a livid-kb org, "?" down to 99 contacts that Kriss never replied to.

**Category enum (Person `category`)**
- Keep the brief's list, plus **`3pl-client`** (brands Livid does warehouse fulfilment for). Second confirmation given; added to `schema/types.yaml` and logged (2026-10-22).
- `vendor-sales` stays (for triage), though cold outreach is mostly dropped as noise.
- **manufacturer** = garment factories and production agents. **supplier** = fabric mills, trims, logistics, systems/SaaS, retail goods for Livid Retail (external brands and their agents), services. The sub-type (production / fabrics-trims / logistics / system / retail goods) belongs on the **Organization in livid-kb**, not on the Person.
- Several livid-kb `suppliers/` docs are garment factories (Stork Texteis, Lisama, Texgoios = now **Mill-Tex**, Afonso, Dia Exemplar, Officocta); their people get `manufacturer`. Propose moving or reclassifying the orgs in the step 4 batch.
- Livid store/workshop Gmail accounts and the Gorgias customer-service mailbox = `colleague`, **no Person note**. Colleagues' private addresses are merged into the same Person as their work address.
- Store staff on private addresses = `colleague`, work context only (their salary/timesheet threads stay out).
- Private-address contacts: Kriss is asked per person, but only above the step-4 threshold.
- Kriss's own private Gmail is treated as one of his own addresses.

**Employee matters:** mail involving the union and an individual employee's private address about an employee case is excluded entirely (29 messages): no rows, no notes, no proposals (AGENTS.md §2.3).

**Shared-platform list, additions confirmed by Kriss** (never a contact, never an org match): vismaonline.com, faktura.poweroffice.net (incl. Livid's own voucher inboxes), gorgias.com/.io (Livid's support desk: its internal mailbox stays a colleague), intercom-mail.eu/.com, zendesk.com, insight.ly, joor.com, judge.me, post.dearsystems.com, microsoftonline.com, docusign.net.

**Noise list changes:** paddlersuk.com (Livid Retail supplier) and tvstore.fr (rental) are **not** noise; epsonconnect.com and livid.com (UPS notices) are. Role mailboxes rescued from the drop: profrakt.no, virke.no, nfta.no. Authority robots (Altinn, Skatteetaten, NAV …) are dropped as *contacts* but matter for step 5 urgency rules.

**Threshold for step 4:** a Person note for every contact with **≥ 2 threads Kriss replied in during the last 12 months**, plus **every contact Kriss has written to** in `board-owner`, `landlord`, `advisor`, `3pl-client`. No notes for private, skip, unknown, consumer or shared mailboxes. On the 12-month preview: **221 candidates** (98 supplier, 31 colleague, 24 wholesale-customer, 19 manufacturer, 18 advisor, 16 landlord, 8 3pl-client, 5 board-owner, 2 partner-press). Top ~50 extended to 3 years.

**For the step 4 livid-kb batch** (from the review; details in `review/corrections.json`)
- New `email_domains` on existing orgs: milltex.pt → Texgoios (renamed Mill-Tex), videbula.com.pt → Lisama, axm.cz → Axpel Made, amorgado.pt → Albano Morgado, abelfragrance.com → Abel Odor, idegroup.no + printcollect.no → Eplehuset; dht.no → DHT Corporate Finance.
- **Eplehuset** is mainly a **customer** (Livid produces and stores their uniforms; orders arrive through a webshop run by Konsis, as PrintCollect emails) and also a supplier (leased office hardware). livid-kb has it only as a supplier.
- New Organizations (~100 domains): wholesale customers, the 3PL clients, manufacturers, fabric mills/trims, retail-goods suppliers and agents, logistics, systems, landlords (incl. DNB Næringseiendom for Galleriet/Livid Bergen, Prinsens Gate AS, Stavanger, Trondheim), advisors (bank, IP lawyers, investment bank), board/owners.
- **Gap:** only 31 of 209 livid-kb Organizations have `email_domains` (not ~56 as noted above), so most supplier matches are by name. (Fixed: `kb_find.py` now searches `email_domains`.)

**Workflow idea (later):** Eplehuset uniform orders arrive as PrintCollect emails → create the order in Loom. Candidate for a livid-kb process / step 5 triage rule.
