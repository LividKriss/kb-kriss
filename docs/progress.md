# kb-kriss build — progress and handoff

Companion to [brief.md](brief.md). Read the brief first; this file records what is done, what was decided along the way, and what step 3 needs to know. Update it at the end of every step.

## Status (2026-10-23)

| Step | Status | Where |
|---|---|---|
| 0 Prerequisites | Done | Claude Code |
| 1 Scaffold kb-kriss | Done | Cowork |
| 2 livid-kb changes | Done | Cowork |
| 3 Backfill pass 1 (headers) | Done (3 years fetched and reviewed, 2026-10-23) | Claude Code |
| 4 Backfill pass 2 (content) | Done (2026-10-23; cache deleted) | Claude Code |
| 5 Triage rules and labels | Done (docs drafted, dry run, cloud routine + Cowork brief running; Mac agent being installed) | Cowork |
| 5b Send policy + signature | Done as draft (2026-10-23); stable after Kriss's second confirmation | Cowork |
| 6 Live trial (2 weeks) | **Next**: from Mon 2026-10-26 | Cloud + Cowork + Mac |
| 7 Review and automate | Not started | |

## Decisions made so far (also in the KBs)

- **Hosting (2026-10-23):** daily run = Claude cloud scheduled task (routine), weekdays 06:47 Oslo, repos kb-kriss + livid-kb, Gmail connector; pushes to main at the end. Customs filing = separate scheduled task on the Mac (no Drive connector in the cloud). Runs use the Team plan's normal usage. Superhuman retired at go-live.

- **Signature (2026-10-23):** no "Kjell Odne (AI assistent)" sign-off. Agent-sent mail uses Kriss's own sign-off + the AI disclaimer (reviewed / auto-sent, NO/EN) above his Gmail signature. See brief → Signature.
- **KB sync from all mail (2026-10-23):** the daily run also reads Kriss's **sent** mail (incl. replies he writes himself in Gmail), message-level label `AI/KB-synced`, weekly 8-day sweep; to be written in step 5 as `email/kb-sync.md`.

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

**3-year rebuild (2026-10-23):** all 69,608 messages fetched (2023-10-23 … 2026-10-22, none missing). One more click-through round covered the people and ~20 domains that only appear in older mail (former staff, a former auditor, banks, trade shows, mills). Result: **1,397 contacts kept**, 412 matched to a livid-kb org, 153 proposed new organizations. Every contact with ≥ 2 replied threads has a confirmed category; the 303 left as "?" have 25 replied threads between them. Former staff are `colleague` with a "former staff" note (work context only).

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

**Noise list changes:** paddlersuk.com (Livid Retail supplier), tvstore.fr (rental) and labels-things.com (caps manufacturer) are **not** noise; epsonconnect.com and livid.com (UPS notices) are. Role mailboxes rescued from the drop: profrakt.no, virke.no, nfta.no. Authority robots (Altinn, Skatteetaten, NAV …) are dropped as *contacts* but matter for step 5 urgency rules.

**Threshold for step 4:** a Person note for every contact with **≥ 2 threads Kriss replied in during the last 12 months**, plus **every contact Kriss has written to** in `board-owner`, `landlord`, `advisor`, `3pl-client`. No notes for private, skip, unknown, consumer or shared mailboxes. On the full 3-year data: **235 candidates** (99 supplier, 32 colleague, 27 advisor, 24 wholesale-customer, 19 manufacturer, 19 landlord, 8 3pl-client, 5 board-owner, 2 partner-press); `build_contacts.py` marks them `step4=yes` in `cache/step3/contacts.csv`. Top ~50 extended to 3 years.

**For the step 4 livid-kb batch** (from the review; details in `review/corrections.json`)
- New `email_domains` on existing orgs: milltex.pt → Texgoios (renamed Mill-Tex), videbula.com.pt → Lisama, axm.cz → Axpel Made, amorgado.pt → Albano Morgado, abelfragrance.com → Abel Odor, idegroup.no + printcollect.no → Eplehuset; dht.no → DHT Corporate Finance.
- **Eplehuset** is mainly a **customer** (Livid produces and stores their uniforms; orders arrive through a webshop run by Konsis, as PrintCollect emails) and also a supplier (leased office hardware). livid-kb has it only as a supplier.
- New Organizations (~100 domains): wholesale customers, the 3PL clients, manufacturers, fabric mills/trims, retail-goods suppliers and agents, logistics, systems, landlords (incl. DNB Næringseiendom for Galleriet/Livid Bergen, Prinsens Gate AS, Stavanger, Trondheim), advisors (bank, IP lawyers, investment bank), board/owners.
- **Gap:** only 31 of 209 livid-kb Organizations have `email_domains` (not ~56 as noted above), so most supplier matches are by name. (Fixed: `kb_find.py` now searches `email_domains`.)

**Workflow idea (later):** Eplehuset uniform orders arrive as PrintCollect emails → create the order in Loom. Candidate for a livid-kb process / step 5 triage rule.

## Step 4 — what was done and decided (2026-10-23)

**Tooling** (`scripts/email/`, venv; raw mail only in the local cache)
- `fetch_content.py plan|fetch`: decides from headers what may be fetched, then `messages.get(format=full)` per message (not whole threads), so excluded material is never fetched: threads with employee matters or confirmed private contacts, and single platform/noise, unconfirmed-freemail and invoice@ messages. Gmail's per-user quota allows only ~1.5 msgs/s for full format; the script paces itself and retries on network drops.
- **What "3 years for the top 50" became:** full content for each person's **newest 100 threads** in their window (12 months; 3 years for the top 50 by threads Kriss replied in); older threads appear only as a header index (dates, subjects). 14.7k messages fetched.
- `prepare_content.py` (cleaned per-person files, quotes/signatures stripped, phones masked, ~2,000 chars per body), `write_people.py` (frontmatter from the plan, bodies from readers), `build_batch.py`, `report_step4.py`. Readers were parallel subagents with a fixed brief.

**kb-kriss**
- 185 Person notes (`draft`). 13 tagged `former` (kept as history, `tags: [former]` + a line in Who). Role/shared mailboxes and 3 contacts (a private matter, an HR-adjacent recruitment fee, an unnamed address) have no note; 3 notes deleted at Kriss's request (automated senders).
- New contact category **`sales-agent`** (Standard Agency, John Webb); second confirmation given.
- **Voice Profiles** (`draft`) in `voice/`: general + 8 categories. Sign-off rule (Kriss): "All the best," / "Vennlig hilsen," + "Kristoffer"; casual mail just "Kristoffer". Setting them `stable` needs Kriss's second confirmation. Messages signed "Kjell Odne" were excluded from the samples.
- **Contacts exception** recorded in AGENTS.md §1: a business contact's name, role and work email may be in both KBs.
- Kriss's corrections that are rules went into the notes/config: former contacts kept, hired-in freelancers (e.g. a photographer) are `supplier`, not `colleague` (now in AGENTS.md §2.3).

**livid-kb** (all with log entries, 0 validator errors)
- AGENTS.md §1 rule 4 + Organization template: **business contacts by name** in a `# Contacts` section (second confirmation given); backfilled on all org docs that step-4 people link to.
- ~100 new Organization docs (first `customers/` and `manufacturers/` docs), 72 existing docs updated, 14 production partners moved to `manufacturers/` (Texgoios → Mill-Tex), Eplehuset → `customers/`, HK Consulting → `advisors/`, new entity `company/entities/livid-jeans-unipessoal.md`. Many open questions are `TODO(cfo)` in the docs (entity per supplier, legal names, invoice channels).

**What step 5 needs**
- `docs/step4-pending-facts.md`: Livid-internal facts (store routines, Loom/Sitoo/Cin7 flows, intercompany, year-end items) and ideas grouped in 7 themes — the most frequent is auto-forwarding emailed supplier invoices to PowerOffice (~15 senders), then payment/due-date tracking (UPS suspended 5× in 2026, Kowa, Quickship, rent reminders), orders typed in by hand (PrintCollect/Eplehuset, wholesale restocks), system-sync monitoring, mail routing, checklists (offboarding, 3PL onboarding, year-end, bank deadlines).
- **Urgency signals seen:** UPS Collections (suspension → debt collection deadlines), bank KYC deadlines (account blocked if missed), Eksfin/credit-line renewals, landlord rent reminders, Altinn/NAV/SSB notices, auditor reminders, debt-collection notices from creditors.
- **Send policy (5b):** replies signed "Kjell Odne (AI assistent)" were already sent on 2026-10-10 and 2026-10-15 (Eplehuset, Rangel, Frameless) before any send policy exists.
- **invoice@ gap:** messages addressed to invoice@ were not fetched; some supplier threads that copy invoice@ have gaps.
- The cache and `review/corrections.json` were deleted on 2026-10-23 (Kriss's yes). Person notes and org docs can now only be edited, not regenerated together with the step 3 review rounds (`review/round*.json`), so no raw or review data is left outside the repos. A new backfill would start from `fetch_headers.py` again.
