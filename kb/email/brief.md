---
type: Rule
title: Morning brief format
description: How the morning brief is laid out in its chat — short summary, then one table per section, numbered so Kriss can act by number.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-10-23T20:00:00+02:00
applies_to: all
---

# Applies to
Part B of the [daily run](/email/daily-run.md), and the midday sweep (part D: summary line, Tasks, new Urgent only).

# Rules
**Language and length:** English, short. **At most 20 numbered items**; whatever does not fit goes on the *Still open* line. The whole brief fits on about one screen; details come when Kriss asks ("tell me more about 3"). Numbers run through the whole brief (1, 2, 3 … not per section), so "send 2, 5" is unambiguous. Each row links the Gmail thread.

**Layout, in this order (leave out empty sections):**

0. **Closed for you** — one line, before the summary: what the brief closed itself before presenting (paid reminders the PowerOffice check found, tasks already done in Loom or Threadflow, Waiting threads that have been answered, Action alerts the system shows resolved), e.g. "Closed for you: EC Dahls 19620 (paid), Lisama 1463 task (done), 3 Waiting (answered)". Each with a short number so "reopen 5" undoes it.
1. **Summary** — one line: `Urgent 3 · Tasks 2 · Reply 5 · Action 2 · Invoices 4 · Payments due 3 · Waiting 1 · HR 2 · FYI 18 · Noise 41`, then one sentence on the single most important thing today.
2. **Urgent** — table:

   | # | From | What | Why now / deadline | Draft ready |
   |---|---|---|---|---|
   | 1 | Lisama (Delfina) | Proforma PO-00141, prepayment to release fabric | Shipment held until paid; ETD Fri | ✓ confirm payment date · [link] |

2b. **Tasks** — email-triggered tasks ([task triggers](/email/task-triggers.md)), one row per task: `# · Trigger (T-no) · Source · Proposal · Flags / waiting for`. Proposal = what will be created, short (e.g. "Loom immediate order, door Tromsø, TEE L 2 · XL 1"; "SH: Kuroki 26-1641 → Lisama, 2 lines, sea, BL …"). Flags = shortfalls, price/qty differences, missing documents or tracking, drafts to third parties. Kriss approves with "do 3"; ask more with "more on 3".
   - **T4 garment shipments:** under the row, the block from the [Process](kb://livid/production/processes/garment-shipments-from-manufacturers.md): header, *What ships*, *Price control* (MO price vs invoice price per line, difference × qty, proposed accept/reject) and *Decisions needed*, each decision numbered on with the brief ("accept 6, reject 7"). No shipment is created while a price difference is undecided.
   - **T5 sample shipments:** one row per manufacturer: matched SR lines → in transit with carrier and tracking, plus counts of already-in-transit, unmatched and overdue lines.

3. **Reply** — same columns, minus deadline when there is none; similar emails batched into one row ("3 wholesale restock requests — Retro, Bulifa, Modo").
4. **Needs action** — notifications that ask for something done: `# · Source · What it asks · Suggested handling`. Ends with the question "How should I handle these kinds going forward?" for any kind without a rule yet.
5. **Invoices** — first *Forwarded automatically since the last brief* (`Supplier · Doc no · Amount · Entity`, no numbers; for checking), then *Need your OK* (`# · Supplier · Doc no · Amount · Entity · Why not automatic`). Source for the automatic list: the Mac attachment agent's `kb/log.md` entries. A manufacturer invoice there without an MO shipment in Threadflow gets ⚠ and a task number ([task triggers](/email/task-triggers.md) rule 8). One line: customs documents filed / still waiting.
6. **Payments due** — `Supplier · Amount · Due · Reminder no.` (no numbering needed unless an action is proposed). Before a reminder is listed, check the supplier ledger in PowerOffice; if already paid, archive it and leave it out. If PowerOffice can't be reached, mark the row "not checked in PO". VWC (The Vintage Wholesale Company) INV-0200 GBP 4,500 is paid (Kriss, 2026-10-26).
7. **Waiting** — overdue threads: `# · Who · Asked on · Nudge draft`.
8. **FYI** — up to 8 one-liners, most relevant first; "+N more" if longer. Noise: count only (list on request).
8b. **Still open** — one line: items already shown in **two** briefs without an answer from Kriss, as `n · who – what` separated by "·" (e.g. "Still open (6): Octa leather claim · Emonkey cost prices · …"). An item comes back as a full row only when new mail arrives in its thread or its deadline is two days or less away. Kriss can still act on them by name or number.
8c. **Drafts going stale** — drafts in the inbox unsent for more than 5 days: `# · Who · Draft age · send / rewrite / drop`. "drop" deletes the draft and closes the thread.
9. **KB** — what part A changed (notes created/updated) and proposals waiting for a yes (voice, livid-kb), one line each.
10. **Close** — "Reply with numbers, e.g. *do 2 · send 1, 4 · forward 7–9 · more on 2*."

**Documents:** when a row's thread has a `[Doc]` draft, add its key facts in the row (e.g. "PL: 3 ctn, ETD 30.10") and offer the full summary on request. "Proposed for Livid KB" lines from `[Doc]` drafts go in the KB section for a yes.

**Drafts for approval:** before Kriss is asked to approve sending, every draft is shown in the chat — its full text where practical, and always at least the Gmail link to the draft (Kriss, morning brief 2026-11-06).

**Rows:** who = person (organization); what = the ask in ≤ 10 words; why = the deadline or consequence; draft = ✓ + its direction in ≤ 8 words, or "decision needed: …". Amounts with currency. No email body text beyond that.

**HR:** count only, never names of the matter beyond "HR matter (n)": the number of threads labelled `AI/HR` since the last brief (they are archived once labelled; NAV deadlines are Urgent and stay in the inbox).

**Decisions are remembered:** "skip", "handled", "no action" → the thread is closed (`gmail_tool.py done`); "later 5 fri" → item 5 is hidden until that date (brief state, `docs/brief-run.md`). The brief never asks about the same thread again unless new mail has arrived in it or a hidden item's date has come.

# Exceptions
- If part A failed or did not run, say so above the summary and offer to run it now.
- When there is nothing urgent, say "Nothing urgent" in the summary line.

# Examples

# Source / history
Kriss, 2026-11-17: the inbox kept building and settled items were asked about again: *Closed for you*, *Still open* after two briefs, at most 20 items, stale drafts, remembered decisions, HR counted then archived.
Kriss, 2026-11-09: T4 price-control block and T5 rows in Tasks; ⚠ on forwarded manufacturer invoices without an MO shipment.
Kriss, 2026-10-23: first test run was plain bullets; wants more structure, tables where useful, still short, and the brief as a new Cowork chat he can work through by voice or typing.
