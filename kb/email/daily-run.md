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
Kriss starts the day with an empty-but-for-what-needs-him inbox, ready drafts, an approval list, and a KB that knows what happened yesterday. Nothing is sent or forwarded without his approval of that item (until [send policy](/email/send-policy.md) says otherwise).

# Trigger
Scheduled, weekdays **06:45** Oslo time. Also on request ("morning run", "go through my email").

# Inputs
- Gmail: search (incl. sent and archived), read, label, archive, create drafts; send, reply and forward **only after approval**.
- Both KBs (read; write per AGENTS.md §5): `kb-kriss/AGENTS.md`, `livid-kb/AGENTS.md`, this doc and the docs it links.
- Customs folder (Google Drive) for customs documents.

# Steps
1. **Load** both AGENTS.md, this doc, [urgency](/email/urgency.md), [labels](/email/labels.md), [actions](/email/actions.md), [KB sync](/email/kb-sync.md), [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md). Check the kill switch in the send policy (once it exists).
2. **Collect** new mail since the last run (2-day overlap; skip messages already labelled `AI/KB-synced`): inbox, archived, sent, and mail to invoice@.
3. **Classify and label** each thread per urgency and labels. Remove labels the thread has outgrown.
4. **Invoices and customs:** run invoice routing — vouchers into the approval batch; customs documents filed and labelled `AI/Filed`.
5. **KB sync** (all new messages, incl. Kriss's own sent mail).
6. **Follow-ups:** Kriss's sent questions → `AI/Waiting`; overdue Waiting threads (3 working days; 2 for production/payment) → nudge drafts.
7. **Drafts** for Urgent and Reply threads per [actions](/email/actions.md).
8. **Archive** FYI, Noise and handled invoice mail.
9. **Brief** (in the run's session; Kriss gets a notification):
   1. Two-line summary.
   2. Urgent — one line each: who, what, why urgent, draft direction (not the text).
   3. Reply — same, grouped: similar emails batched.
   4. Invoice batch — supplier · document no · amount · entity · reason; customs documents filed.
   5. Waiting — overdue items and nudge drafts.
   6. FYI — one line each. Noise — count.
   7. KB digest — notes created/updated, proposals (voice, livid-kb) waiting for a yes.
   Numbered so Kriss can answer "send 1, 3; forward 1–7; skip 4".
10. **After Kriss answers:** send approved drafts with the reviewed disclaimer ([signature](/email/signature.md)), forward approved vouchers (`AI/PO-forwarded`), archive the threads, move labels, log. Anything not approved stays as a draft.
11. **Close:** `kb/log.md` entry (counts, KB changes; no bodies), `tools/build_index.py`, `tools/validate.py` (0 errors).

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
- Hosting: scheduled task in Claude's cloud (KBs cloned from GitHub, pushed back) vs on Kriss's Mac — decided in step 5/6.
- Superhuman retirement date (go-live).
