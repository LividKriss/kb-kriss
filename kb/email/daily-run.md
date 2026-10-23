---
type: Process
title: Daily email run
description: The weekday morning run of Kriss's email assistant — label, route invoices, sync the KB, draft replies, follow up, and give Kriss a priority brief to approve from.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-10-23T10:00:00+02:00
autonomy: execute-with-approval
---

# Purpose
Kriss starts the day with an inbox that holds only what needs him, ready drafts, a brief in a Cowork chat he can work through by voice or typing, and a KB that knows what happened yesterday. Nothing is sent or forwarded without his approval of that item (until [send policy](/email/send-policy.md) says otherwise).

# Trigger
Three parts:
- **A. Processing** — Claude cloud scheduled task (routine) "Daily email run", weekdays **06:47** Oslo. Unattended. Instructions: `docs/routine.md`.
- **C. Mac attachment agent** — Claude Code on Kriss's Mac, hourly while awake (`docs/mac-agent.md`): reads invoice PDFs, forwards clear cases to PowerOffice (+ Ole Eivind for external brands), files customs documents, and reads documents/links on `AI/Docs` threads into `[Doc]` summary drafts and the KB. The cloud can't read attachments.
- **B. Morning brief** — Cowork scheduled task, weekdays **07:30** Oslo: opens a **new Cowork chat** with the brief ([brief format](/email/brief.md)); Kriss goes through it by voice or typing and gives instructions.
Also on request ("morning run", "go through my email").

# Inputs
- Gmail: search (incl. sent and archived), read, label, archive, create drafts; send, reply and forward **only after Kriss's approval in part B**.
- Both KBs (read; write per AGENTS.md §5): `kb-kriss/AGENTS.md`, `livid-kb/AGENTS.md`, this doc and the docs it links.

# Steps — A. Processing (unattended)
1. **Load** both AGENTS.md, this doc, [urgency](/email/urgency.md), [labels](/email/labels.md), [actions](/email/actions.md), [KB sync](/email/kb-sync.md), [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md).
2. **Collect** new mail since the last run (2-day overlap; skip messages already labelled `AI/KB-synced`): inbox, archived, sent, and mail to invoice@.
3. **Classify and label** each thread per urgency and labels. Remove labels the thread has outgrown.
4. **Invoices and customs:** label voucher candidates `AI/Invoice` (the **Mac attachment agent**, part C, reads the PDFs, forwards clear cases and notifies Ole Eivind for external brands); ordinary payment reminders → `AI/Payments`; customs documents → `AI/Customs` (the Mac job files them and relabels `AI/Filed`).
5. **KB sync — every run** (all new messages, incl. Kriss's own sent mail), after classification. Bulk-label messages that need no KB writing; substantive threads in parallel batches (see `docs/routine.md`). If the run must be cut short, stop drafts first, then KB sync — never classification; the backlog carries over via the missing `AI/KB-synced` label.
6. **Follow-ups:** Kriss's sent questions → `AI/Waiting`; overdue Waiting threads (3 working days; 2 for production/payment) → nudge drafts.
7. **Drafts** for Urgent and Reply threads per [actions](/email/actions.md). Where the answer depends on Kriss's decision, still draft it with the open point marked `[KRISS: …]` and state the decision needed — a draft with one open point beats no draft.
8. **Archive** FYI, Noise and handled invoice mail.
8b. **KB inbox:** apply every draft with subject `[KB-inbox]` (written by the morning brief at Kriss's instruction) per AGENTS.md §5 — Person notes and notes directly; rules, voice and livid-kb changes count as confirmed by Kriss for that item (second-confirmation items excepted: list those in the run report instead). Log each, then delete the draft.
9. **Close:** short run report as the session's last message (counts, failures); `kb/log.md` entry; `tools/build_index.py`, `tools/validate.py` (0 errors); commit and push to `main` (AGENTS.md §5). No other branches.

# Steps — B. Morning brief (interactive, Cowork)
1. Read the labels, the `[Doc]` summary drafts from the Mac agent, and the drafts part A left (`AI/Urgent`, `AI/Reply`, `AI/Action`, `AI/Payments`, `AI/Invoice`, `AI/Waiting`, `AI/Customs`, `AI/HR` count), the last run report in `kb/log.md`, and the Person notes involved. If part A did not run today, say so first and offer to run it now.
2. Present the brief per [brief format](/email/brief.md).
3. Work through it with Kriss: open threads in full on request, check systems, revise drafts, and do what he approves — send (with the reviewed disclaimer, [signature](/email/signature.md)), forward vouchers (`AI/PO-forwarded`), archive, relabel. Nothing sent or forwarded without his approval of that item in this chat, and only up to the level the [send policy](/email/send-policy.md) allows (sensitive classes: leave as a draft for him to send himself). Check for a `[STOP-SENDING]` draft first.
4. Capture his instructions: new rules (e.g. how to handle an Action kind), corrections to Person notes, things to remember. The brief chat runs in the cloud and cannot write the KB, so it saves each as a **Gmail draft with subject `[KB-inbox] <short title>`**, no recipient, body = the instruction in Kriss's words + "confirmed by Kriss in the morning brief <date>" + the KB doc it concerns. Part A applies them the next morning.
5. End with what was done and what is still open.

# Decision rules
- Gmail is the system of record; archived = done.
- Until Superhuman is retired, its auto-archive can hide mail — always search all mail, never only the inbox.
- Low confidence about class, facts or tone → draft and say so; never send.

# Checks
- Every new message is labelled or listed as failed; every voucher is forwarded, skipped with a reason, or flagged.
- No mail sent or forwarded without an approval in this session.

# Output
Labelled and archived mail, Gmail drafts, filed customs documents, the brief, KB updates, a log entry.

# Escalation
Gmail or a KB unreachable, validation errors, or anything the docs don't cover → stop that part, say so at the top of the brief.

# Examples

# Open questions
- Superhuman retirement date (go-live).
