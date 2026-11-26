---
type: Rule
title: What the assistant does with each kind of email
description: Per label — draft, archive, forward, file, follow up — and the limits on each action.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-10-23T10:00:00+02:00
applies_to: all
---

# Applies to
Every thread the [daily run](/email/daily-run.md) labels.

# Rules
- **AI/Urgent, AI/Reply:** stay in the inbox. Draft a reply as a Gmail draft in the thread (thread + Person note + Voice Profile + relevant livid-kb docs), in the thread's language, ending with Kriss's sign-off. Always a reply **inside the thread with the quoted history** (never a new thread without it — Eplehuset complained, 2026-10). No disclaimer while it is a draft Kriss sends himself; if he asks the assistant to send it, add the reviewed disclaimer first ([signature](/email/signature.md)). No draft when the answer needs a decision only Kriss can make — then the brief says what must be decided.
- **No stray files on drafts** (Kriss, 2026-11-17): drafts never carry files the reply doesn't need: no inline images copied from the quoted message (signature logos, screenshots). Only files Kriss asked for, or that the Process requires, are attached. How: replies on the Mac through `gmail_tool.py reply-draft`, or `gmail_tool.py clean-draft <id>` after a Gmail-connector draft; in the cloud run, `update_draft` (same subject, no attachments) right after each connector reply draft. `send-draft` refuses a draft that still has them.
- **AI/Waiting:** when Kriss's question has had no answer for **3 working days** (**2** for production and payment threads), draft a short polite nudge for his approval and list it in the brief. **Before listing or nudging, read the whole thread up to its latest message** (both sides, incl. Kriss's replies and mail that arrived after the label was set): a thread whose counterpart has replied, or where Kriss has answered that reply, is not overdue, and "asked on" is the date of Kriss's latest question (Kriss, 2026-10-28; the same applies to Urgent and Reply rows in the brief). **Also look outside the thread** (Kriss, 2026-10-29): replies from Outlook and similar often land in a separate Gmail thread, so search for mail from the same sender, or with the same subject prefixed Svar:/Sv:/RE:/Re:, received after Kriss's ask. Found → the question is answered: remove `AI/Waiting` and archive both threads. Example: Konsis "Utsolgt Eplehuset T-skjorte XL", answered 27.10 in a separate thread, still listed as Waiting on 29.10.
- **Archive** always = remove `INBOX` and `UNREAD` from the whole thread ([labels](/email/labels.md)).
- **AI/FYI:** archive; one line in the brief.
- **AI/Noise:** archive; counted in the brief, listed only on request.
- **AI/Action:** stays in the inbox; listed under Needs action with the question "how should this be handled?" until Kriss has given a rule for that kind. Archived when the system shows it resolved (checked before each brief) or Kriss settles it; shown twice without an answer → *Still open* line ([brief format](/email/brief.md)).
- **AI/Task:** per [task triggers](/email/task-triggers.md): prepare the proposal, list it under Tasks, execute after Kriss's approval of that task, then archive.
- **AI/HR:** archived once labelled; count only in the next brief. NAV deadlines are Urgent and stay in the inbox.
- **Invoices and customs documents:** per [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md) — vouchers in an approval batch, customs documents filed. Kriss's own forwards to a PowerOffice voucher address count as done.
- **Only one PDF of an email should go to PowerOffice** (e.g. the receipt, not the invoice) and the email can't be forwarded with that PDF alone: save the PDF to `~/Downloads` (mount the Downloads folder if needed) and send it alone in a new email to the entity's voucher address. Never ask Kriss to do it (Kriss, 2026-10-27; Wispr receipt 2441-0061). Company rule: [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md), decision rules.
- **Collection notices from collection agencies** (inkassovarsel, betalingsoppfordring, inkassokrav — Svea, Intrum, Lowell, Collectio, Alektum, Kredinor and similar): always forwarded to the entity's PowerOffice voucher address, then checked, booked and matched per the [collection-agency rule](kb://livid/finance/bookkeeping/rules/supplier-groups/tax-and-collection-claims.md) (section *Collection agencies — both entities*). Arriving in Digipost or Altinn → download first ([Altinn and Digipost payables](kb://livid/finance/bookkeeping/processes/altinn-digipost-payables.md)). Never left unhandled (Kriss, 2026-10-27/28, supersedes the narrower 27.10 rule).
- **Altinn, Skatteetaten and Digipost notices** (both entities): the assistant downloads every document that needs a payment or action per [Altinn and Digipost payables](kb://livid/finance/bookkeeping/processes/altinn-digipost-payables.md); Kriss logs in (ID-porten/BankID), the assistant does the rest in Chrome (Kriss, 2026-10-27).
- **Carrier exceptions on web orders** (UPS undeliverable / exception notices, and similar from other carriers; Kriss, 2026-11-26): when the shipment belongs to a webshop order (Livid reference `W-…`), forward the notice to help@livid.no with a short Norwegian note: "Dette gjelder nettordre <W-nr> (<customer>, <city>, <item>, <amount>)", what happened (e.g. not delivered after three attempts), why the notice came to Kriss (he is the contact on the carrier account), what the carrier needs and by when, and where instructions go (e.g. ernexpnordics@ups.com). Look up the order in Loom first. The forward follows the send policy (draft, sent on Kriss's approval); after it is sent the thread is closed. Example: W-30890, 26.11.
- **Sending, forwarding, replying:** per the [send policy](/email/send-policy.md): at most `send-after-approval` for most classes (Kriss approves in the brief: "send 1, 3"), `draft` for sensitive ones (he sends himself), system auto-sends only as listed there. After sending, replying or forwarding (by the assistant or by Kriss himself): archive the thread (and mark it read), move the label (Waiting if the text asks a question, makes a request or starts a new thread). The tools do this: `gmail_tool.py send-draft` closes the thread after sending, `done` closes what Kriss settles without a send, and the Mac agent's hourly inbox clean-up closes threads Kriss answered from Gmail or his phone. A voucher forward to PowerOffice is not an answer: the thread keeps its open label. **Drafts:** a draft unsent for more than 5 days is listed under *Drafts going stale* (send / rewrite / drop); "drop" deletes that draft and closes the thread. **Recipient addresses** come from the message itself (get_thread / get_message headers, or the From/To/Cc of the message being replied to), never from search results, which drop the dots in addresses; check any address with dots in the local part before sending (Kriss, 2026-10-29: a reply to Eplehuset bounced, 550 5.4.1, sent to piatalmo@ and matstranvag@ instead of pia.talmo@ and mats.tranvag@).
- **Every session, not only the daily run (Kriss, 2026-10-29):** any agent that processes an email in any chat (forwards it to bilagsmottak, files it, or judges it noise or a duplicate) marks it read and archives it right away. Handled email is never left unread in the inbox. Company rule: [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md).
- **Never:** delete mail, mark spam, unsubscribe, accept invitations, add recipients, or send attachments with financial or personal data without explicit approval of that item.

# Exceptions

# Examples

# Source / history
Kriss, 2026-11-26 (brief): carrier exceptions on web orders go to help@livid.no with a standard explanation.
Kriss, 2026-11-17: exits for HR and Action, close-out by the tools, stale drafts.
Interview with Kriss, step 5 (2026-10-23): FYI archived and listed; follow-up after 3 working days (2 for production/payment) with a drafted nudge.
2026-11-17: no stray files on drafts, after 20 drafts were found carrying quoted signature logos and screenshots as attachments (confirmed by Kriss in chat).
