---
type: Rule
title: Gmail labels used by the assistant
description: The small AI/ label set the daily run applies, what each means, and which labels it ignores.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-10-23T10:00:00+02:00
applies_to: all
---

# Applies to
Kriss's work Gmail. Applied by the [daily run](/email/daily-run.md) and [KB sync](/email/kb-sync.md).

# Rules
| Label | Meaning | Level |
|---|---|---|
| `AI/Urgent` | Needs Kriss today ([urgency](/email/urgency.md)) | thread |
| `AI/Reply` | Kriss should answer | thread |
| `AI/Waiting` | Kriss asked something and waits for an answer | thread |
| `AI/FYI` | No reply needed; archived | thread |
| `AI/Noise` | Newsletter, marketing, cold sales, notification; archived | thread |
| `AI/Action` | Notification that needs something done, no rule yet; listed under Needs action | thread |
| `AI/Task` | Matches a row in [task triggers](/email/task-triggers.md); a task in a Livid system is waiting; listed under Tasks | thread |
| `AI/HR` | HR matter; count only in the brief, never in the KB | thread |
| `AI/Invoice` | Voucher waiting for Kriss's approval to forward | thread |
| `AI/Payments` | Ordinary payment reminder; grouped in the brief | thread |
| `AI/PO-forwarded` | Voucher forwarded to PowerOffice | message |
| `AI/Docs` | Email points to a document/link worth reading; the Mac agent reads it | thread |
| `AI/Docs-read` | Document read; summary in a `[Doc]` draft | thread |
| `AI/Customs` | Customs document waiting to be filed (cloud run can't reach Drive) | message |
| `AI/Filed` | Customs document saved in the customs folder | message |
| `AI/KB-synced` | Message processed by [KB sync](/email/kb-sync.md) | message |

- Only one of Urgent / Reply / Waiting / FYI / Noise / Action / HR / Payments per thread at a time; the run moves it as the thread changes. Kriss's reply removes Urgent/Reply (and adds Waiting if he asked something).
- **Archived = done.** Archiving always means removing **both `INBOX` and `UNREAD`** from every message in the thread — Gmail's archive alone leaves mail unread. Done = archived **and** read.
- **Archive everything handled:** FYI, Noise, handled invoice/customs mail, every thread Kriss or the assistant has sent, replied to or forwarded (incl. Kriss's own forwards to PowerOffice), Waiting threads, and anything else that needs no action. Only Urgent, Reply, Action, Task, HR, Invoice, Payments, Docs and Docs-read stay in the inbox (and keep their unread state). The run never deletes, never marks spam, never unsubscribes without asking.
- `AI/Task` comes on top of the single label above (and of `AI/Invoice`/`AI/Customs`); it is removed when the task is done.
- No per-category labels: the contact category lives in the Person note.
- Ignore old labels (`[Superhuman]/…`, `Kjell Odne/Done`, `Invoices`, Kriss's manual labels); never remove them.

# Exceptions

# Examples

# Source / history
Kriss chose a new small AI/ set (2026-10-23). `AI/Task` added 2026-10-27.
