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
| `AI/PO-forwarded` | Voucher forwarded to PowerOffice | message |
| `AI/Filed` | Customs document saved in the customs folder | message |
| `AI/KB-synced` | Message processed by [KB sync](/email/kb-sync.md) | message |

- Only one of Urgent / Reply / Waiting / FYI / Noise per thread at a time; the run moves it as the thread changes. Kriss's reply removes Urgent/Reply (and adds Waiting if he asked something).
- **Archived = done** (removed from the inbox). The run never deletes, never marks spam, never unsubscribes without asking.
- No per-category labels: the contact category lives in the Person note.
- Ignore old labels (`[Superhuman]/…`, `Kjell Odne/Done`, `Invoices`, Kriss's manual labels); never remove them.

# Exceptions

# Examples

# Source / history
Kriss chose a new small AI/ set (2026-10-23).
