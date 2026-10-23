---
type: Rule
title: Email urgency and priority
description: What makes an incoming email urgent, reply-needed, FYI or noise, and in which order the morning brief lists them.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-10-23T10:00:00+02:00
applies_to: all
---

# Applies to
Every incoming message in Kriss's work Gmail handled by the [daily run](/email/daily-run.md). Labels: [labels](/email/labels.md). What happens next: [actions](/email/actions.md).

# Rules
**AI/Urgent** — needs Kriss today. In this order:
1. **Production (top priority):** payments needed to release shipments of materials or goods (proformas, prepayment requests, a forwarder or customs hold waiting for payment); clarification questions about production directed at Kriss; anything blocking production or a shipment (customs holds, delayed fabric, missing documents).
2. **Money at risk:** service suspension, debt collection/inkasso, final reminders, failed or returned payments, payment demands with a deadline.
3. **Authorities and bank deadlines:** Altinn, Skatteetaten, NAV, SSB, Tolletaten notices with a deadline; bank KYC (account blocked if missed); Eksfin/credit-line renewals; auditor deadlines.
4. **Board/owners and landlords** asking Kriss for something (`board-owner`, `landlord`).
5. **Operational blockers:** system sync failures (Sitoo/Cin7/Shopify/Loom), a store that cannot trade, customer escalations from support.

**AI/Reply** — Kriss should answer, not today-critical. Listed in this order:
1. Management and design colleagues: the general manager/board, CDMO, distribution and design leads — e.g. [Arnt](/people/arnt-david-eriksen.md), [Ole Eivind](/people/ole-eivind-siggerud.md), [Charlie](/people/charlie-selvig.md), [Jens Olav](/people/jens-olav-dankertsen.md), [Christopher](/people/christopher-stangeby.md).
2. Key wholesale customers (`wholesale-customer`), 3PL clients (`3pl-client`) and advisors (`advisor`: auditor, accountant, bank, lawyers) asking for something.
3. Everyone else with a real question or request to Kriss.

**AI/FYI** — no reply needed: Kriss in cc, status updates, confirmations, receipts of things already handled, internal announcements.

**Noise** (label AI/Noise, archive): newsletters and marketing (incl. suppliers' marketing), cold sales outreach from senders Kriss has never replied to, system notifications (sign-in alerts, carrier tracking, SaaS updates, Superhuman reminders) **unless they signal a failure** — then Urgent 5.

**Invoice mail** follows [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md); once forwarded or filed it is archived. Reminders and collection notices are not vouchers: they go through the rules above (usually Urgent 2).

# Exceptions
- A message that fits Urgent but where Kriss has already acted (his reply is later in the thread) → not urgent.
- HR or employee-case mail: summarised only as "HR matter from <name>"; label Urgent or Reply, never written to the KB.
- When unsure between two levels, pick the higher and say why in one line.

# Examples

# Source / history
Interview with Kriss, step 5 (2026-10-23). Signals seen in the step 4 backfill: UPS collections/suspensions, bank KYC, Eksfin, rent reminders, Altinn/NAV/SSB, auditor reminders.
