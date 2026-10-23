---
type: Rule
title: Signature and AI disclaimer on mail the assistant sends
description: How email sent by the assistant ends — Kriss's own sign-off, the AI disclaimer (reviewed or auto-sent, Norwegian or English), then his Gmail signature.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-10-23T20:30:00+02:00
applies_to: all
---

# Applies to
Every email the assistant sends or replies to on Kriss's behalf. Not Gmail drafts Kriss sends himself — those go out as his own mail with no disclaimer.

# Rules
1. Body ends with Kriss's usual sign-off from the [voice profile](/voice/general.md): "All the best," / "Vennlig hilsen," + "Kristoffer" (casual mail: just "Kristoffer"). **No "Kjell Odne" sign-off** (Kriss, 2026-10-23).
2. Then the disclaimer in small grey text (HTML: `<p style="font-size:11px;color:#888">…</p>`), in the language of the email:

| | Reviewed by Kriss (send-after-approval) | Sent automatically (auto-send) |
|---|---|---|
| Norwegian | Denne e-posten ble generert av Kristoffer sin AI assistent. Kristoffer har sett over og godkjent innholdet. | Denne e-posten ble generert av Kristoffer sin AI assistent. Innholdet er sendt ut automatisk basert på regler og ikke gjennomgått. |
| English | This message was prepared by Kristoffer's AI assistant and reviewed by him before sending. | This message was prepared by Kristoffer's AI assistant. It was automatically sent without human review based on automation rules. |

3. Then Kriss's existing Gmail signature, unchanged.
4. Replies keep the thread's quoted history.
5. Until `email/send-policy.md` allows auto-send, only the **reviewed** variant is used.

# Exceptions

# Examples

# Source / history
Brief (Signature), changed by Kriss 2026-10-23.
