---
type: Rule
title: Send policy
description: When the assistant may send email for Kriss — email classes, the maximum level per class and contact category, hard blocks, system auto-sends, guardrails, the kill switch, and how autonomy is earned and lost.
owner: kriss
tier: personal
status: stable
generated:
  by: claude/opus-5.5
  at: 2026-10-23T22:00:00+02:00
applies_to: all
verified:
  - by: human:kriss
    at: 2026-10-23T22:30:00+02:00
stale_after: 2027-01-21
---

# Applies to
Every email the assistant sends, replies to or forwards from Kriss's work Gmail — in the morning brief, the cloud run, the Mac agent or any other chat. Nothing is sent, forwarded or deleted outside this policy. When in doubt: draft, don't send.

# Levels
| Level | Meaning | Disclaimer ([signature](/email/signature.md)) |
|---|---|---|
| `draft` | Gmail draft only; Kriss sends it himself from Gmail | reviewed (Kriss, 2026-10-26) |
| `send-after-approval` | the assistant sends after Kriss approves that specific email in the brief chat or another chat | reviewed |
| `auto-send` | the assistant sends on its own, within the guardrails below | auto-sent |

# Email classes and maximum level
Classify every outgoing email first. Each email gets the **lowest** level any applicable rule gives it.

| Class | Max level now |
|---|---|
| Acknowledgement / receipt confirmation | send-after-approval |
| Scheduling (meeting times, calls) | send-after-approval |
| Information request answered from the KB | send-after-approval |
| Document / forwarding request | send-after-approval |
| Routine supplier or manufacturer follow-up (status, ETA, missing document) | send-after-approval |
| Invoice / payment query (no new commitment) | send-after-approval |
| Follow-up nudge on an unanswered question | send-after-approval |
| Customer escalation | send-after-approval |
| Negotiation, prices, terms | **draft** |
| Legal, contracts, disputes, complaints | **draft** |
| HR or employee matter | **draft** |
| Board / owners | **draft** |
| Authorities | **draft** |
| Private | **draft** |

Contact category overrides (Person note `category`): `board-owner`, `authority`, `advisor` (auditor, accountant, lawyers, bank) → **draft** whatever the class. `private` → draft.

No class starts at `auto-send`.

# Hard blocks — never auto-send, regardless of track record
- Authorities, board/owners, auditor, accountant, lawyers, bank.
- Anything that commits money, prices, terms, deadlines, deliveries or a legal position, or that Kriss hasn't already decided.
- Contracts, disputes, complaints, negative news, HR or employee matters.
- First contact with a new person, or new recipients added to a thread.
- Attachments with financial or personal data.
- Anything the agent is unsure about (class, facts or tone), or where a KB doc it relies on is `draft`.

# System auto-sends (approved by Kriss, 2026-10-23)
Fixed-recipient system messages, sent without approval by the Mac agent (`docs/mac-agent.md`) per [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md). Not replies; outside the class table and the track-record rules; not counted in the daily cap; stopped by the kill switch; every one logged.
1. Clear-case vouchers forwarded to the entity's PowerOffice voucher address.
2. External-brand invoices forwarded to Ole Eivind (oleeivind@livid.no) with the short Norwegian note and the auto-sent disclaimer.
3. Official invoices and credit notes addressed to Livid Jeans Unipessoal forwarded to Patrícia at HK Consulting (pfaisca@hkconsulting.pt) with the short English note and the auto-sent disclaimer (invoice routing step 7c; Kriss, second confirmation 2026-10-23).
Any other recipient is never a system auto-send.

# Guardrails on auto-send (when a class has earned it)
- Scheduled 15 minutes ahead and listed in the brief; Kriss can cancel.
- At most **20** auto-sent emails per day, and 1 per recipient per thread per day.
- Only 07:00–20:00 Oslo time; otherwise held as a draft until 07:00.
- Every sent email is logged in `kb/log.md`: class, level, rule, recipient domain, thread link. No body text.

# Kill switch
Kriss says **"stop sending"** (any chat): the assistant creates a Gmail draft with subject `[STOP-SENDING]` and no recipient. While that draft exists, every agent (cloud run, brief chat, Mac agent, other chats) treats every class and the system auto-sends as `draft`: nothing is sent or forwarded. Kriss lifts it by saying so; the draft is deleted and the change logged. Every agent checks for the draft before any send.

# Earning and losing autonomy
- **Promotion:** a class may move up one level after a track record — at least 20 drafts in that class sent by Kriss with no or trivial edits over at least 2 weeks (measured draft vs sent, [KB sync](/email/kb-sync.md)). The agent **proposes** it in the weekly review with the evidence; Kriss approves with a second confirmation; logged.
- **Demotion (automatic):** one level down for that class when Kriss materially edits, retracts or corrects an auto-sent email, or a recipient reacts badly. Logged and flagged in the next brief.
- Hard blocks and `draft`-only classes are never promoted.

# Source / history
Build brief "Sending email" + Kriss's answers in step 5b (2026-10-23): sensitive classes draft-only (he sends himself), daily cap 20, invoice forwards and Ole Eivind notices recorded as system auto-sends.
