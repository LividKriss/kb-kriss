---
type: Rule
title: Signature and AI disclaimer on mail the assistant sends
description: How email written by the assistant ends — Kriss's own sign-off, the AI disclaimer on every email the assistant sends (reviewed or auto-sent), then his Gmail signature.
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
2. **Disclaimer on every email the assistant sends, replies to or forwards** — only email Kriss sends himself goes without (Kriss, 2026-11-04). Small grey text after the sign-off (HTML: `<p style="font-size:11px;color:#888">…</p>`), in the language of the email:
   - **Reviewed** — `send-after-approval` (Kriss approved that email before it went out):
     - Norwegian: *Denne e-posten ble skrevet og sendt av Kristoffer sin AI-assistent etter hans gjennomgang.*
     - English: *This message was prepared and sent by Kristoffer's AI assistant after his review.*
   - **Auto-sent** — `auto-send` and the system auto-sends in the [send policy](/email/send-policy.md):
     - Norwegian: *Denne e-posten ble generert av Kristoffer sin AI assistent. Innholdet er sendt ut automatisk basert på regler og ikke gjennomgått.*
     - English: *This message was prepared by Kristoffer's AI assistant. It was automatically sent without human review based on automation rules.*

   **Never as normal text** (Kriss, 2026-11-12): the disclaimer is always the small grey HTML paragraph, never part of the normal body formatting. A draft the assistant will send must have an HTML body with that styled paragraph, not a plain-text-only body. `gmail_tool.py` styles a disclaimer paragraph in a plain-text note automatically (reply-draft, forward-draft, forward). Before sending, check that the disclaimer renders small and grey.
   **Drafts:** a Gmail draft that Kriss will send himself (`draft` level) carries no disclaimer. A draft the assistant will send after his approval gets the reviewed disclaimer before it is sent.
   Exception: voucher forwards to PowerOffice system addresses (`@faktura.poweroffice.net`) need none.
   Enforced in Claude Code by `scripts/email/gmail_tool.py send-draft`, which refuses a draft without one of these texts; the Gmail connector's send, reply and forward are blocked in kb-kriss (`.claude/settings.json`). In Cowork, by the `email-disclaimer-guard` plugin.
3. Then Kriss's existing Gmail signature, unchanged.
4. Replies keep the thread's quoted history.
5. When sending through the Gmail integration, set `includeSignature: true` so the Gmail signature is appended (after the disclaimer, where there is one).

# Exceptions

# Examples

# Source / history
2026-11-12: Kriss saw disclaimers going out as normal text. Cause: `gmail_tool.py` rendered a plain-text note's disclaimer as an ordinary paragraph (two forwards to Arnt that day). The script now styles it, and this rule says so.
Brief (Signature), changed by Kriss 2026-10-23. 2026-10-26: Kriss extended the disclaimer to all drafts after an approved send went out without it. 2026-10-27: Kriss reversed that: the reviewed variant is dropped; the disclaimer is only for mail sent without his prior review. 2026-11-04: Kriss reinstated it (second confirmation): every email the assistant sends carries a disclaimer, reviewed or auto-sent; only mail he sends himself goes without. Trigger: the Pio insights request went out without one.
