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
2. **Money at risk:** service suspension or a suspension warning, debt collection/inkasso, final notices, failed or returned payments, rent reminders. Ordinary payment reminders are **not** urgent: they go in the brief's grouped **Payments due** block.
3. **Authorities, bank and advisor deadlines:** Altinn, Skatteetaten, NAV, SSB, Tolletaten notices with a deadline; bank KYC (account blocked if missed); Eksfin/credit-line renewals; auditor deadlines; **any advisor or lawyer deadline, even when Kriss is only in cc** (a trademark deadline lapsed on 2026-10-21 that way).
4. **Board/owners and landlords** asking Kriss for something (`board-owner`, `landlord`).
5. **Operational blockers:** a store that cannot trade, customer escalations from support, and system alerts that are critical, a failed deploy, a quota at 100 %, or still unresolved after 24 hours. Other system alerts (sync warnings, re-route failures) are FYI; repeated alerts in one thread count once.

**AI/Reply** — Kriss should answer, not today-critical. Listed in this order:
1. Management and design colleagues: the general manager/board, CDMO, distribution and design leads — e.g. [Arnt](/people/arnt-david-eriksen.md), [Ole Eivind](/people/ole-eivind-siggerud.md), [Charlie](/people/charlie-selvig.md), [Jens Olav](/people/jens-olav-dankertsen.md), [Christopher](/people/christopher-stangeby.md).
2. Key wholesale customers (`wholesale-customer`), 3PL clients (`3pl-client`) and advisors (`advisor`: auditor, accountant, bank, lawyers) asking for something.
3. Everyone else with a real question or request to Kriss.

**AI/FYI** — no reply needed: Kriss in cc, status updates, confirmations, receipts of things already handled, internal announcements.

**Noise** (label AI/Noise, archive): newsletters and marketing (incl. suppliers' marketing), cold sales outreach from senders Kriss has never replied to, system notifications (sign-in alerts, carrier tracking, SaaS updates, Superhuman reminders) **unless they signal a failure** — then Urgent 5.

**Action-needed notifications** (label AI/Action) — system or authority notifications that ask for something to be done, e.g. a new employee in Samesystem (→ create in PowerOffice), NAV inntektsmelding, SSB reporting in Altinn. Never let these go silent: the brief lists them under **Needs action** and asks Kriss how to handle each kind. His answer becomes a rule here or a proposed livid-kb process, so the kind can later be automated.

**HR** (label AI/HR) — payslips, pay errors, expense claims, sick-leave/NAV notices, payroll-budget alerts, employee matters. Shown in the brief as a count only; urgent only for NAV deadlines; never summarised beyond "HR matter", never written to the KB.

**Invoice mail** follows [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md); once forwarded or filed it is archived. Reminders and collection notices are not vouchers: they go through the rules above (usually Urgent 2).

**Confirmed by Kriss in the 2026-10-26 brief:**
- Replit notifications (e.g. "Republish your projects"): Noise.
- PowerOffice "Pending Vouchers for Approval" reminders: Noise, archive; no Needs-action row (handled in PowerOffice).
- Quickship Logistics invoice mail: not a voucher (they send EHF); archive, never forward.
- Loom "Store stock sync: N problem(s) need attention": FYI and archived, never Urgent, even when unresolved over 24 hours. The brief keeps one open reminder line that the stock sync problem still needs fixing.
- Samesystem weekly "Ændrede / oprettede ansatte" mail: "Ingen endringer" → Noise, archive. New, starting or departing employees → AI/Action ("handle in PowerOffice"). No names in the KB.

**Confirmed by Kriss in the 2026-10-28 brief:**
- Resend "100% of your daily quota": FYI, archive, no Needs-action row. Keep a count; if it happens often (several times a month), propose upgrading the plan in the brief. (Supersedes Urgent 5 for quota mails.)
- Adobe "forespørsel om Adobe-applikasjoner som må gjennomgås": Noise, archive, no Needs-action row.
- PowerOffice "unpaid invoices on your client": archive, no Needs-action row.
- Altinn/Skatteetaten/Digipost notices: once Kriss has done an Altinn/Digipost round, the notices it covered are archived; only notices that arrived after the last round go under Needs action.

# Exceptions
- A message that fits Urgent but where Kriss has already acted (his reply is later in the thread) → not urgent.
- When unsure between two levels, pick the higher and say why in one line.

# Examples

# Source / history
Interview with Kriss, step 5 (2026-10-23). Dry-run fixes confirmed by Kriss (2026-10-23): grouped payment reminders, alerts as FYI, HR class, advisor deadlines in cc, action-needed notifications. Signals seen in the step 4 backfill: UPS collections/suspensions, bank KYC, Eksfin, rent reminders, Altinn/NAV/SSB, auditor reminders.
