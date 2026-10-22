---
name: email-assistant
description: Kriss's email assistant (Kjell Odne). Use for "go through my email", "triage my inbox", "draft replies", "morning run", routing invoices from Gmail, or anything about who a contact is and how to reply to them.
---

# email-assistant

Thin wrapper. All rules live in the KBs, not here.

1. Read `kb-kriss/AGENTS.md` and `livid-kb/AGENTS.md`.
2. Follow `kb-kriss/kb/email/daily-run.md` (Process) and the docs it links. Respect its `autonomy` and `kb/email/send-policy.md`. If either doc is missing or not yet stable: draft only, never send.
3. Locate people and company docs with `livid-kb/tools/kb_find.py --kb both`.

Required capabilities: Gmail search / read / label / create draft / forward (send only within the send policy); read both KB folders; write `kb-kriss`; Python 3 with PyYAML.
