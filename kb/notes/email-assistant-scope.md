---
type: Decision
title: Email assistant — scope
description: Which mailbox, how much history and which languages the email assistant and its backfill cover.
owner: kriss
tier: personal
status: stable
generated:
  by: human:kriss
  at: 2026-10-22T14:30:00+02:00
verified:
  - by: human:kriss
    at: 2026-10-22T14:30:00+02:00
stale_after: 2027-10-22
---

# Context
Scope decisions from the kb-kriss build brief, confirmed at step 1.

# Decision
- **Mailbox:** Kriss's work Gmail (kristoffer@livid.no) only. Private email accounts are out of scope.
- **History:** headers for 3 years; full content for the last 12 months, extended to 3 years for key contacts only.
- **Language:** KB written in English; drafts in whatever language the thread uses.
- **Person notes** written by an agent start as `draft` and become `stable` when Kriss has reviewed them (bulk confirmation is fine).

# Alternatives considered
Including private accounts; full content for 3 years for everyone (too much third-party data for little gain).

# Consequences
Backfill scripts in `scripts/email/` respect these limits. A draft Person note blocks auto-send to that person (see the send policy once written).

# Affects
`AGENTS.md` §4 (status of Person notes); `email/send-policy.md` and `email/daily-run.md` when written.
