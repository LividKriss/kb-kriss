# Brief: Personal knowledge base (`kb-kriss`) and email assistant

You are helping Kriss (CFO, Livid) build his **personal** knowledge base and an email assistant on top of it.
It complements the company KB `livid-kb` (at `/Users/kristoffer/livid-kb`) and reuses its format, tooling and conventions.
Read `livid-kb/AGENTS.md` first. Everything there applies unless this brief says otherwise.

## Goal

An assistant for Kriss's work email (Gmail) that:
1. knows who people are and the history of each relationship,
2. writes replies in Kriss's voice, adjusted to the type of contact,
3. flags what is urgent and what needs a reply,
4. routes incoming invoices to the right PowerOffice voucher address,
5. remembers things Kriss tells it, and gets better from his corrections.

The assistant is **Kjell Odne**, Kriss's AI assistant. It may send email on its own, but only where the send policy allows it (see "Sending email"). Superhuman is retired once this works; Gmail is the system of record, and archiving in Gmail marks an email as done.

## Scope decisions (confirm at step 1)

- **Mailbox:** Kriss's work Gmail only. Private email accounts are out of scope.
- **History:** headers for 3 years; full content for the last 12 months, extended to 3 years for key contacts only.
- **Language:** KB in English (as `livid-kb`); drafts in whatever language the thread uses.

## Ground rules (in addition to livid-kb AGENTS.md)

1. **No raw email in any repo.** Only distilled notes. Raw messages fetched for processing live in a local cache outside the repo (`~/Library/Application Support/kb-kriss/cache/`) and are deleted after each pass.
2. **Minimal notes about third parties.** Only what helps work: role, relationship, history, open threads, how to communicate. Never health, family, private life, opinions about the person's character, or anything you wouldn't be comfortable showing them.
3. **Employees:** work context only. Nothing HR-related (performance, absence, salary, conflicts). That stays out entirely.
4. **Email address is the only contact detail stored.** It's the lookup key. No phone numbers, home addresses etc.
5. **Personal vs company:** every new fact is either personal (→ `kb-kriss`) or company knowledge (→ proposed for `livid-kb` via its feedback protocol, written only after Kriss confirms). E.g. "SSENSE is a wholesale customer of Livid Jeans AS" is company; "Kriss and SSENSE's AP contact settle disputes by phone" is personal.
6. **Sending is governed by `email/send-policy.md`.** Nothing is sent, forwarded or deleted outside what that policy allows. When in doubt: draft, don't send.

## Different from livid-kb: update rules

- Person notes, voice examples and notes may be **created and updated without asking**. They are private and low-risk. Every change gets a `log.md` entry, and Kriss gets a **daily digest** of what changed.
- Voice profiles, triage rules and anything with `autonomy` still follow livid-kb's confirmation rules (show change → confirm → write).
- Kriss can say "forget X" → delete the line/doc and log it as **Removal**.

## Repo

```
kb-kriss/                         (private GitHub repo, local clone /Users/kristoffer/kb-kriss)
├── AGENTS.md                     # personal rules (this brief's rules), points to livid-kb/AGENTS.md for the rest
├── CLAUDE.md                     # @AGENTS.md
├── schema/types.yaml             # personal types (below), same structure as livid-kb
├── schema/domains.yaml           # foundations: people, voice, email, areas, notes; owner kriss; tier personal
├── templates/
├── tools/                        # copied from livid-kb (kblib, validate, build_index, autosync)
├── scripts/email/                # backfill + daily scripts (Gmail API), see steps 3-4
├── .claude/skills/
│   └── email-assistant/SKILL.md  # thin wrapper
└── kb/                           # OKF v0.2 bundle
    ├── index.md
    ├── log.md
    ├── people/                   # type: Person — one per contact
    ├── voice/                    # type: Voice Profile — general.md + one per contact category
    ├── email/                    # type: Rule / Process — triage, labels, actions, daily run
    ├── areas/                    # type: Area — Kriss's ongoing responsibilities and projects
    └── notes/                    # type: Note — things to remember; type: Decision — decisions and why
```

## Schema

Same common fields as livid-kb (`type, title, description, owner, tier, status, generated`, plus `verified`/`stale_after` when stable). Differences:
- `owner: kriss` (a person, because this KB *is* personal), `tier: personal` (new tier, readable by the owner only).
- Cross-repo links use the stable address `kb://livid/<path>` (e.g. `kb://livid/organizations/suppliers/ups.md`). The validator resolves these against `../livid-kb/kb/` when present, and warns if they're broken.

| Type | Folder | Extra required fields |
|---|---|---|
| Person | people/ | `emails` (list), `category`, `organization` (kb:// link, optional for private) |
| Voice Profile | voice/ | `applies_to` (category or `all`) |
| Rule | email/ | `applies_to` |
| Process | email/ | `autonomy` |
| Area | areas/ | — |
| Note | notes/ | — |
| Decision | notes/ | — |

**Contact categories** (enum on Person; confirm/adjust with Kriss at step 3):
`colleague`, `board-owner`, `manufacturer`, `supplier`, `wholesale-customer`, `consumer` (customer service escalations), `advisor` (accountant, auditor, lawyer, bank), `authority`, `landlord`, `investor`, `partner-press` (agencies, media, collaborations), `vendor-sales` (cold outreach), `private`.

**Person body:** Who · Relationship · How Kriss communicates with them (overrides the category voice if different) · History (dated bullets, newest first, short) · Open threads (with Gmail thread links) · Links (organization, areas).

## Changes needed in livid-kb (do in step 2, with confirmations)

1. **Organization type: add optional `email_domains`** (list) to `schema/types.yaml`. Needed to match a sender to a company. Schema change = second confirmation.
2. **Organization docs: fill "Channels"** with how invoices arrive (EHF / email PDF / both / portal). Today every profile says "Not recorded yet". The invoice routing needs this to avoid **duplicates** (a supplier that sends EHF *and* a PDF copy by email must not be forwarded).
3. **New process `finance/bookkeeping/processes/invoice-routing.md`**. This resolves the TODO in `systems/invoice-inbox.md`:
   - Identify a voucher email (PDF attachment + invoice/credit note/receipt signals; not quotes, order confirmations, statements, reminders, unless Kriss decides otherwise).
   - Entity: supplier register (`finance/reference/suppliers-*.md`) + `email_domains`, else the addressee on the document. Unclear → flag.
   - Skip if the supplier's channel is EHF, if already forwarded (Gmail label `AI/PO-forwarded`), or if it's a private invoice.
   - Forward to the entity's voucher address (see `systems/poweroffice-go.md`), label, log.
   - Autonomy: `execute-with-approval` (batch list Kriss approves). Per-supplier move to `execute` later, once a supplier has a clean track record.
4. **Fix:** `.claude/skills/bilagsmottak/SKILL.md` says "never posts" / "Never post", but the processes are `execute-with-approval` and agents have posted after approval. Make the skill defer to each Process's `autonomy`.
5. **customers/ and manufacturers/ are empty.** The backfill will discover wholesale customers and manufacturers; propose these as Organization docs in a batch for Kriss to confirm.

## Gmail access

- **Bulk backfill (steps 3–4):** Python scripts using the Gmail API (OAuth client in Livid's Google Cloud project, scope `gmail.readonly`). Run by Claude Code on Kriss's Mac. The chat connectors are too slow for tens of thousands of messages.
- **Daily use (steps 5–6):** the Gmail connector in Cowork/Claude (search, read, label, create draft, send, forward, archive). Sending is only used within the send policy.
- The invoice inbox (`invoice@`, one.com) already forwards to Kriss's Gmail, so Gmail is the single place to route from. Verify this at step 2.

## Steps (⏸ = stop for Kriss)

### Step 0: Prerequisites (Kriss, in Claude Code, once)
- Create private repo `kb-kriss`, clone to `/Users/kristoffer/kb-kriss`, install auto-sync (separate launchd label `no.livid.kb-kriss-autosync`).
- Create the Gmail API OAuth client (readonly for now) and authorise it locally. Token stored in the macOS Keychain, never in a repo.

### Step 1: Scaffold `kb-kriss` (Cowork) ⏸
Copy tools from livid-kb, create schema/templates/AGENTS.md/skill per this brief, run the validator. Confirm scope decisions with Kriss.

### Step 2: livid-kb changes (Cowork, in livid-kb) ⏸
Items 1–4 under "Changes needed in livid-kb". Fill Channels + `email_domains` for the ~50 most frequent suppliers first; the rest are filled by the backfill as proposals.

### Step 3: Backfill pass 1, headers only (Claude Code) ⏸
- Fetch metadata for 3 years: from, to, cc, date, subject, thread id, labels, whether Kriss replied. No bodies.
- Build a contact table: address, display name, domain, matched livid-kb organization, messages in/out, threads where Kriss replied, first/last contact, suggested category.
- Drop noise: newsletters, notifications, no-reply senders, one-off cold outreach.
- Show Kriss a **summary by category** (not person by person) and the top ~150 contacts for quick review of categories and organization matches. Kriss corrects in bulk.
- Output stays local (cache); only confirmed categories carry forward.

### Step 4: Backfill pass 2, content (Claude Code) ⏸
- For contacts above a threshold (e.g. ≥3 threads with a reply from Kriss in the last 12 months), read their threads and write **Person** notes. Extend to 3 years for the top ~50 contacts.
- From Kriss's **sent mail**, sample per category and draft **Voice Profiles**: language, formality, length, greetings, sign-off, typical phrasing, what he never does, 3–5 short real examples (Kriss's own words only, other people's names and details removed).
- Propose new Organizations (customers, manufacturers, advisors) and `email_domains` for livid-kb as one batch.
- **Checkpoint:** Kriss reviews the voice profiles carefully (they drive every draft) and spot-checks 10 person notes. Delete the local cache.

### Step 5: Triage rules and labels (Cowork) ⏸
- Interview Kriss: what's urgent (senders, topics, deadlines, money at risk, authorities, the board), what can wait, what he never wants to see.
- Write `email/urgency.md`, `email/labels.md`, `email/actions.md`, `email/daily-run.md` (Process).
- Labels (keep it small): status `AI/Urgent`, `AI/Reply`, `AI/Waiting`, `AI/FYI`, `AI/PO-forwarded`; category labels = contact categories (prefix `C/`).
- **Dry run** on the last 2 weeks of inbox: produce the labels and priority list as a report only. Kriss corrects; corrections go into the rules.

### Step 5b: Send policy and signature (Cowork) ⏸
Write `email/send-policy.md` and `email/signature.md` per "Sending email". All email classes start at `draft` or `send-after-approval`; nothing starts at `auto-send`. Second confirmation required.

### Step 6: Live trial, 2 weeks (Cowork, daily) ⏸
Morning run (`email/daily-run.md`):
1. Label new mail; route invoices (batch for approval).
2. Priority list: urgent first, then replies needed, each with one line on why.
3. Draft replies as **Gmail drafts**, using thread + person note + voice profile + relevant livid-kb docs. Kriss approves in batch ("send 1, 3, 4"); approved drafts are sent with the *reviewed* disclaimer, then archived. No auto-send during the trial.
4. After Kriss sends: compare draft vs sent. Meaningful edits → update the voice profile (with confirmation) or person note (automatic).
5. Update person notes and open threads; daily digest of KB changes.
Track: share of drafts sent with light edits, urgent items missed, invoice routing errors.

### Step 7: Review and automate (Kriss + Claude)
Based on the trial: which steps run on a schedule (Claude Code Routine or Managed Agent), which email classes are promoted towards `auto-send` (per the track-record rules), which invoice senders move to `execute`, and when Superhuman can be retired.
Before running unattended in Anthropic's cloud: note in the records of processing that work email is processed by Anthropic (US transfer), and set transcript deletion for Managed Agents.

## Sending email

### Email classes
Every outgoing email is classified before anything is sent. Classes live in `email/send-policy.md`, e.g.: acknowledgement/receipt, scheduling, information request answered from the KB, document/forwarding request, routine supplier follow-up, invoice/payment query, customer escalation, negotiation/pricing/terms, legal/contract, HR/employee matter, board/owner, authority, private.

### Autonomy per class (`email/send-policy.md`)
| Level | Meaning |
|---|---|
| `draft` | Gmail draft only; Kriss sends himself |
| `send-after-approval` | Agent sends once Kriss approves that specific email (chat or morning brief) |
| `auto-send` | Agent sends on its own, within the guardrails below |

The policy is a table: class × contact category → maximum level. Each email gets the **lowest** level any rule gives it.

**Never `auto-send`** (hard blocks, regardless of track record):
- authorities, board/owners, auditor, accountant, lawyers, bank
- anything that commits money, prices, terms, deadlines, deliveries or legal positions, or that Kriss hasn't already decided
- contracts, disputes, complaints, negative news, HR or employee matters
- first contact with a new person, or new recipients added to a thread
- attachments with financial or personal data
- anything the agent is unsure about (class, facts, tone), or where the KB doc it relies on is `draft`

### Earning autonomy
- A class can move up one level only after a track record: e.g. ≥20 drafts in that class sent by Kriss with no or trivial edits over ≥2 weeks. The agent measures this by comparing draft vs sent.
- The agent **proposes** promotions in the weekly review; Kriss approves with a second confirmation. The change and its evidence go in `log.md`.
- **Automatic demotion** one level for that class when Kriss materially edits, retracts, or corrects an auto-sent email, or a recipient reacts badly. Logged, and flagged in the next brief.

### Guardrails on auto-send
- Send delay: auto-sent email is scheduled 15 minutes ahead and listed in the brief; Kriss can cancel.
- Limits: max N auto-sends per day, max 1 per recipient per thread per day; no auto-send outside 07–20 Oslo time.
- Kill switch: "stop sending" sets every class to `draft` until Kriss lifts it.
- Every sent email is logged (class, level, rule, recipient domain, thread link). No body text in the log.

### Signature (`email/signature.md`)
**Changed 2026-10-23 (Kriss): no "Kjell Odne" sign-off.** An email the agent sends ends like Kriss's own mail — his usual sign-off from the voice profile ("All the best," / "Vennlig hilsen," + "Kristoffer") — followed by an AI disclaimer in small grey text, then Kriss's existing Gmail signature, which stays. Language follows the email.

| | Reviewed by Kriss (`send-after-approval`) | Sent automatically (`auto-send`) |
|---|---|---|
| Norwegian | Denne e-posten ble generert av Kristoffer sin AI assistent. Kristoffer har sett over og godkjent innholdet. | Denne e-posten ble generert av Kristoffer sin AI assistent. Innholdet er sendt ut automatisk basert på regler og ikke gjennomgått. |
| English | This message was prepared by Kristoffer's AI assistant and reviewed by him before sending. | This message was prepared by Kristoffer's AI assistant. It was automatically sent without human review based on automation rules. |

Drafts that Kriss sends himself from Gmail (`draft` level) carry no disclaimer; they go out as his own email.

## Which knowledge base (routing)

Every agent session can see both KBs. Make this work everywhere:
- **Claude Code:** add a user-level `~/.claude/CLAUDE.md` that points to both KBs' AGENTS.md and the routing rules below. It loads in every session, whatever project is open.
- **Cowork:** grant access to both folders, and install a `kb-router` skill (same text) as a personal skill.
- **Later:** the KB server replaces this; one connection with `search(scope: company | personal | both)`.

**Reading:**
- Business processes, rules, systems, organizations → `livid-kb`.
- People, relationships, voice, Kriss's preferences, his areas and notes → `kb-kriss`.
- When unsure, search both. Company rules always win over personal notes for how work is done.

**Writing — one test:** *Would a colleague doing this task need it if Kriss were away?*
- Yes → company (`livid-kb`, confirmation required).
- No, it's about Kriss's own relationships, preferences or work → personal (`kb-kriss`).
- About an organization → company. About an individual person → personal.
- Ambiguous → ask with a one-line choice.

Every save proposal names its destination ("Save to Livid KB: `finance/bookkeeping/rules/suppliers/ups.md`" / "Save to your notes: `people/…`"), so a wrong destination is easy to catch.

### Build: `kb-router` skill + `kb_find.py` (part of step 1)
- **Skill source** lives in `livid-kb/.claude/skills/kb-router/SKILL.md` (draft provided separately). It's company-wide; the personal KB path becomes per-user once others join.
- **`livid-kb/tools/kb_find.py`:** searches frontmatter (title, description, type, tags) and file paths in one or both KBs. Returns a compact list (`kb://` address, title, description, status), never bodies. Options: `--kb company|personal|both`, `--type`, `--status`, `--limit` (default 10). This is the main token saver: agents locate the 2–3 docs they need instead of reading folders.
- **Install (Kriss, once, in Claude Code):**
  - Claude Code: symlink the skill into `~/.claude/skills/kb-router` (always up to date), and add one line to `~/.claude/CLAUDE.md`: "For any Livid or personal-work task, use the kb-router skill."
  - Cowork: upload the skill as a personal skill. Re-upload when it changes; the weekly maintenance report flags drift.
- **Test:** five sample prompts (a supplier coding question, "who is X", "draft a reply to Y", "remember that…", "UPS changed invoicing to EHF") each route, find and propose saves to the right KB.

## Skill (`.claude/skills/email-assistant/SKILL.md`)
Thin wrapper: triggers ("go through my email", "triage inbox", "draft replies", "morning run"); read `kb-kriss/AGENTS.md`, `livid-kb/AGENTS.md`; follow `kb/email/daily-run.md`; required capabilities: Gmail search/read/label/draft/forward, read both KBs. No rules in the skill.
