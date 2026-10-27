---
type: Rule
title: Signature and AI disclaimer on mail the assistant sends
description: How email written by the assistant ends — Kriss's own sign-off, then his Gmail signature; the AI disclaimer only on mail sent without his prior review.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-10-27T13:00:00+01:00
applies_to: all
---

# Applies to
Every email the assistant writes for Kriss: emails it sends, replies to or forwards on his behalf, and every Gmail draft it creates, in any chat or session.

# Rules
1. Body ends with Kriss's usual sign-off from the [voice profile](/voice/general.md): "All the best," / "Vennlig hilsen," + "Kristoffer" (casual mail: just "Kristoffer"). **No "Kjell Odne" sign-off** (Kriss, 2026-10-23).
2. **Disclaimer only on mail sent without Kriss's prior review** (`auto-send` and the system auto-sends in the [send policy](/email/send-policy.md)), in small grey text after the sign-off (HTML: `<p style="font-size:11px;color:#888">…</p>`), in the language of the email:
   - Norwegian: *Denne e-posten ble generert av Kristoffer sin AI assistent. Innholdet er sendt ut automatisk basert på regler og ikke gjennomgått.*
   - English: *This message was prepared by Kristoffer's AI assistant. It was automatically sent without human review based on automation rules.*

   **No disclaimer** on drafts or on anything Kriss has seen and approved (`draft`, `send-after-approval`): those go out as his own mail (Kriss, 2026-10-27).
3. Then Kriss's existing Gmail signature, unchanged.
4. Replies keep the thread's quoted history.
5. Today only the system auto-sends (Ole Eivind, HK Consulting) carry the disclaimer; PowerOffice voucher forwards go to a system address and need none.
6. When sending through the Gmail integration, set `includeSignature: true` so the Gmail signature is appended (after the disclaimer, where there is one).

# Exceptions

# Examples

# Source / history
Brief (Signature), changed by Kriss 2026-10-23. 2026-10-26: Kriss extended the disclaimer to all drafts after an approved send went out without it. 2026-10-27: Kriss reversed that: the reviewed variant is dropped; the disclaimer is only for mail sent without his prior review.
