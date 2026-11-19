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
1. **Find:** messages since the last successful run (12-hour overlap, see [daily run](/email/daily-run.md) step 2) without `AI/KB-synced` — in the inbox, in Sent, and archived mail (Superhuman's auto-archive must not hide anything). Work per **message**, so a new reply in an old thread is picked up.
2. **Skip without writing** (label only): noise, platform senders, invoice mail, private contacts, HR and employee matters (AGENTS.md §2.3).
3. **Per remaining message, update the Person note(s)** of the other party (look up by email):
   - History: one dated line if something mattered (agreement, decision, order, dispute, change). Routine traffic adds nothing.
   - Open threads: add new unresolved threads; close those Kriss's message resolved.
   - "How Kriss communicates" only if a lasting difference shows.
4. **No Person note yet:** create a draft note when Kriss has now replied in ≥ 2 threads with that person within 12 months (step 3 threshold), or the person is `board-owner`, `landlord`, `advisor` or `3pl-client` and Kriss wrote to them. Otherwise nothing.
5. **Sent by Kriss himself:**
   - If the assistant had a draft in that thread: compare draft vs sent. A meaningful edit (tone, length, content, language) → **propose** a Voice Profile change or a Person-note override in the brief (Voice Profiles need Kriss's confirmation). Trivial edits → count only.
   - Otherwise: keep the message as a voice sample reference (thread link only, no text) for the monthly voice review.
6. **Company facts** (payment terms, invoice channel, entity, lead times, contacts, a new customer or supplier, agreed plans and dates, what a counterpart confirmed or disputed) → **write them into livid-kb now** (Kriss, 2026-11-19; livid-kb AGENTS.md §5a): the right Organization, System or Reference doc, as a dated line with the thread link as source. A new organization with real business traffic gets a draft Organization doc. Facts only: what the email says, never what you conclude. A fact that contradicts the doc → `TODO(cfo): conflict — …` and a line in the brief. A fact that implies a way of working ("always send X to Y") is recorded as a fact; the instruction change is proposed in the brief under *KB → Needs your yes*.
7. Label each processed message `AI/KB-synced`; add the changes to `kb/log.md` in each repo written (one short line per doc) and to the brief's KB digest.
8. **Close quiet open threads** (daily, `scripts/email/kb_close_threads.py` on the Mac): an Open threads bullet whose Gmail thread is archived and has had no mail for 14 days moves to History as "Closed, no mail since <date>: <subject>". Bullets without a thread link are left alone. Logged in `kb/log.md`.
9. **Same day:** whenever a chat closes a thread (a send, `done`, a task executed), it updates that thread's Open threads line in the Person note right away (close it, or say what it now waits for); it does not wait for the next run.

# Decision rules
- Personal vs company: AGENTS.md §1 test. About an individual → here; about an organization → livid-kb (written directly, step 6).
- Third-party minimum (AGENTS.md §2): role, relationship, history, open threads, how to communicate. Nothing about health, family, private life, character, HR.

# Checks
- No message newer than the window lacks `AI/KB-synced` after the run, except ones listed as failed.
- `tools/validate.py`: 0 errors.

# Output
Updated Person notes, a log entry, the KB digest lines, proposals (voice, livid-kb) in the brief.

# Escalation
Unclear identity (same name, new address) or possible HR content → don't write; ask in the brief. A fact that contradicts a livid-kb doc → conflict TODO in that doc (step 6) and a line in the brief.

# Examples

# Open questions
- Monthly voice review: how many samples per category before a profile change is proposed (start: 10 meaningful edits or 30 own-written mails).
