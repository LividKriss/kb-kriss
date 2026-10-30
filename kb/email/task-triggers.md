---
type: Rule
title: Email task triggers
description: Registry of email kinds that start a defined task in a Livid system — how to recognise each one and which livid-kb Process does the work; checked on every email run.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-10-27T13:00:00+01:00
applies_to: all
---

# Applies to
Every new thread in Kriss's work Gmail, in every run that reads mail: the 06:47 [daily run](/email/daily-run.md) (part A), the Mac attachment agent (part C), the 07:30 morning brief (part B) and the 12:00 midday sweep (part D).

# Rules
1. **Match** every new thread against the table below (sender, subject, content; attachments where the run can read them). A thread can match more than one row (an invoice is also a shipment trigger).
2. **Label** a match `AI/Task` ([labels](/email/labels.md)), in addition to any invoice/customs label. It stays in the inbox until the task is done, even after a PowerOffice forward.
3. **Prepare** in the unattended runs: read the systems involved and build the proposal the Process asks for (dry runs only, nothing created). No Loom or Threadflow connector in the run → label only; the brief prepares it.
4. **Present** in the brief or midday chat, section *Tasks* ([brief format](/email/brief.md)): one numbered row per task with the proposal and its flags.
5. **Execute** only up to the Process's `autonomy`. `execute-with-approval` = after Kriss approves that numbered task in the chat ("do 3"). Drafts to third parties the Process asks for follow the [send policy](/email/send-policy.md).
6. **Close:** when done, archive the thread (remove `INBOX` + `UNREAD`), remove `AI/Task`, and report what was created (order/shipment numbers). This applies whenever a task is executed in Loom, Threadflow or another system, in any chat, and the thread needs no reply: archive right away. Before listing an `AI/Task` thread as a task, check the system first (e.g. a Loom order with the PrintCollect order number as customer reference) and close it if already done (PrintCollect 21081 = LO-0084, fulfilled 27.10, still listed 28.10). Waiting on something (documents, tracking, stock) → keep `AI/Task` and say what it waits for.
7. **No row matches** but the email clearly asks for something done in a system → `AI/Action` as before, with "how should this be handled?". When Kriss gives the rule, write or update the livid-kb Process (via its feedback protocol) and add a row here.

# Registry

| # | Email kind | Recognise by | Process (does the work) | System | Autonomy |
|---|---|---|---|---|---|
| T1 | Eplehuset uniform order | From bestilling@printcollect.no, subject "PrintCollect - Eplehuset - <no>"; one email per order line, group by order number. Check spam too. | [PrintCollect uniform orders](kb://livid/sales/processes/printcollect-uniform-orders.md) | Loom | execute-with-approval |
| T3 | Modo weekly stock report | From edi@frontsystems.com, subject "Livid lager Moa", received on a **Monday**, CSV attachment `OnHandReportUTC-Livid lager Moa-*.csv` (covers Modo Moa and Modo Sentrum). Not the Sunday "BRAND WEEKLY STOCK REPORT – Modo … – Livid" mails: those are wrong, label `AI/Noise`. | [Modo auto-replenishment](kb://livid/sales/processes/modo-auto-replenishment.md) | Loom | execute-with-approval |
| T2 | Material shipment | Invoice, packing list or shipping notice from a material supplier (fabric mills, trims, labels; see the Process trigger). Not garments from manufacturers. Only items on a Threadflow PO get a shipment; the rest is forwarded and the task closed (see the Process, Decision rules). | [Material shipments from supplier invoices](kb://livid/production/processes/material-shipments-from-invoices.md) | Threadflow | execute-with-approval |

Adding a kind: one row here + a Process in livid-kb (or a link to the existing one). The how-to lives only in the Process.

# Exceptions
- T3 needs the CSV attachment: the cloud runs label by sender, subject and weekday only. The chat that prepares it (brief or midday sweep) fetches the CSV through the browser (Kriss's Gmail session). Having the Mac agent save it is possible but not set up. The proposal is always shown, also when below the Process threshold.
- T2 needs the PDFs, which only the Mac agent can read: the cloud runs label by sender/subject/attachment names, the Mac agent writes the `[Doc]` summary, and the chat that executes reads the documents before creating anything.

# Examples

# Source / history
Kriss, 2026-10-28: T3 added; the Monday Modo report had been labelled `AI/FYI` and archived by the run.
Kriss, 2026-10-27: tasks triggered by incoming email are to be registered so the morning brief and a 12:00 midday sweep pick them up; more kinds will be added.
