# Change log

## 2026-10-23

- **Creation** Added docs/step4.md: detailed brief for step 4 (content backfill: Person notes, voice profiles, livid-kb batch, checkpoint, cache deletion).

## 2026-10-22

- **Update** Schema `schema/types.yaml`: added contact category `3pl-client` (brands Livid does warehouse fulfilment for) and marked the category list confirmed. Why: step 3 backfill review; none of the existing categories fit 3PL clients. Confirmed by Kriss twice (step 3 review + second confirmation).
- **Creation** Added docs/brief.md (build brief) and docs/progress.md (status after steps 0–2, decisions, handoff for step 3 in Claude Code).
- **Approval** Decision `notes/email-assistant-scope.md`: work Gmail only; headers 3 yrs, content 12 months (3 yrs key contacts); KB English, drafts in thread language; agent-written Person notes start as draft. Confirmed by Kriss (step 1).
- **Creation** Step 1 scaffold: AGENTS.md, schema (types Person, Voice Profile, Rule, Process, Area, Note, Decision; tier personal; owner kriss; contact categories; kb:// roots), templates, tools copied from livid-kb and extended (owners, categories, kb:// links, unique emails, phone-number warning), email-assistant skill.
