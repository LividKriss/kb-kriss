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
- **AI/Urgent, AI/Reply:** stay in the inbox. Draft a reply as a Gmail draft in the thread (thread + Person note + Voice Profile + relevant livid-kb docs), in the thread's language, ending with Kriss's sign-off. Always a reply **inside the thread with the quoted history** (never a new thread without it — Eplehuset complained, 2026-10). No disclaimer: Kriss reviews every draft before it goes out ([signature](/email/signature.md)). No draft when the answer needs a decision only Kriss can make — then the brief says what must be decided.
- **AI/Waiting:** when Kriss's question has had no answer for **3 working days** (**2** for production and payment threads), draft a short polite nudge for his approval and list it in the brief. **Before listing or nudging, read the whole thread up to its latest message** (both sides, incl. Kriss's replies and mail that arrived after the label was set): a thread whose counterpart has replied, or where Kriss has answered that reply, is not overdue, and "asked on" is the date of Kriss's latest question (Kriss, 2026-10-28; the same applies to Urgent and Reply rows in the brief).
- **Archive** always = remove `INBOX` and `UNREAD` from the whole thread ([labels](/email/labels.md)).
- **AI/FYI:** archive; one line in the brief.
- **AI/Noise:** archive; counted in the brief, listed only on request.
- **AI/Action:** stays in the inbox; listed under Needs action with the question "how should this be handled?" until Kriss has given a rule for that kind.
- **AI/Task:** per [task triggers](/email/task-triggers.md): prepare the proposal, list it under Tasks, execute after Kriss's approval of that task, then archive.
- **AI/HR:** stays in the inbox; count only in the brief.
- **Invoices and customs documents:** per [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md) — vouchers in an approval batch, customs documents filed. Kriss's own forwards to a PowerOffice voucher address count as done.
- **Sending, forwarding, replying:** per the [send policy](/email/send-policy.md): at most `send-after-approval` for most classes (Kriss approves in the brief: "send 1, 3"), `draft` for sensitive ones (he sends himself), system auto-sends only as listed there. After sending, replying or forwarding (by the assistant or by Kriss himself): archive the thread (and mark it read), move the label (Waiting if a question was asked).
- **Every session, not only the daily run (Kriss, 2026-10-29):** any agent that processes an email in any chat (forwards it to bilagsmottak, files it, or judges it noise or a duplicate) marks it read and archives it right away. Handled email is never left unread in the inbox. Company rule: [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md).
- **Never:** delete mail, mark spam, unsubscribe, accept invitations, add recipients, or send attachments with financial or personal data without explicit approval of that item.

# Exceptions

# Examples

# Source / history
Interview with Kriss, step 5 (2026-10-23): FYI archived and listed; follow-up after 3 working days (2 for production/payment) with a drafted nudge.
