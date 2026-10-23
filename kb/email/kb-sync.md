---
type: Process
title: KB sync from email
description: How every new incoming and sent message in Kriss's work Gmail — including replies he writes himself — updates the Person notes, voice samples and (by proposal) livid-kb.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-10-23T10:00:00+02:00
autonomy: execute
---

# Purpose
The KB never misses context because a reply was written by Kriss in Gmail (or Superhuman, or on his phone) rather than by the assistant. Done = every new message since the last run carries `AI/KB-synced`, and the KB reflects it.

# Trigger
Every [daily run](/email/daily-run.md) (step 5 of the run). Weekly (Monday run): a sweep of the last 8 days for messages still without `AI/KB-synced`, in case a run was missed.

# Inputs
- Gmail: search incoming **and sent** mail (`in:sent`), read messages, add labels.
- Both KBs: Person notes (`people/`), Voice Profiles (`voice/`), livid-kb Organizations.

# Steps
1. **Find:** messages newer than the last run (overlap 2 days) without `AI/KB-synced` — in the inbox, in Sent, and archived mail (Superhuman's auto-archive must not hide anything). Work per **message**, so a new reply in an old thread is picked up.
2. **Skip without writing** (label only): noise, platform senders, invoice mail, private contacts, HR and employee matters (AGENTS.md §2.3).
3. **Per remaining message, update the Person note(s)** of the other party (look up by email):
   - History: one dated line if something mattered (agreement, decision, order, dispute, change). Routine traffic adds nothing.
   - Open threads: add new unresolved threads; close those Kriss's message resolved.
   - "How Kriss communicates" only if a lasting difference shows.
4. **No Person note yet:** create a draft note when Kriss has now replied in ≥ 2 threads with that person within 12 months (step 3 threshold), or the person is `board-owner`, `landlord`, `advisor` or `3pl-client` and Kriss wrote to them. Otherwise nothing.
5. **Sent by Kriss himself:**
   - If the assistant had a draft in that thread: compare draft vs sent. A meaningful edit (tone, length, content, language) → **propose** a Voice Profile change or a Person-note override in the brief (Voice Profiles need Kriss's confirmation). Trivial edits → count only.
   - Otherwise: keep the message as a voice sample reference (thread link only, no text) for the monthly voice review.
6. **Company facts** (payment terms, invoice channel, entity, lead times, a new customer or supplier) → propose for livid-kb in the brief, naming the target doc. Written only after Kriss confirms.
7. Label each processed message `AI/KB-synced`; add the changes to `kb/log.md` (one entry per run) and to the brief's KB digest.

# Decision rules
- Personal vs company: AGENTS.md §1 test. About an individual → here; about an organization → livid-kb (proposal).
- Third-party minimum (AGENTS.md §2): role, relationship, history, open threads, how to communicate. Nothing about health, family, private life, character, HR.

# Checks
- No message newer than the window lacks `AI/KB-synced` after the run, except ones listed as failed.
- `tools/validate.py`: 0 errors.

# Output
Updated Person notes, a log entry, the KB digest lines, proposals (voice, livid-kb) in the brief.

# Escalation
Unclear identity (same name, new address), possible HR content, or a fact that contradicts a livid-kb doc → don't write; ask in the brief.

# Examples

# Open questions
- Monthly voice review: how many samples per category before a profile change is proposed (start: 10 meaningful edits or 30 own-written mails).
