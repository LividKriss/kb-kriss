---
type: Decision
title: Model and token routing for the assistant
description: Which Claude model and effort each kind of assistant work runs on, when to hand work to Sonnet subagents, and the habits that keep token use down; read at the start of every task.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-11-06T14:00:00+01:00
---

# Context
In early November 2026 the weekly usage limit was being reached: the 06:47 email run was rejected by the 7-day limit and finished only partly on 5 and 6 November. Most usage came from Opus doing routine reading: hourly Mac agent runs that found nothing, and morning and midday chats that read every thread themselves with every connector loaded.

# Decision
**Default split:** Sonnet does the reading, sorting and rule-following; Opus 5.5 at medium effort does judgment, conversation with Kriss and anything new.

| Work | Model | How |
|---|---|---|
| 06:47 email run (part A, cloud) | Sonnet | Default model in the cloud; KB sync and drafts in Sonnet subagents (`docs/routine.md`) |
| Mac attachment agent (part C) | Sonnet | `--model sonnet` in `scripts/email/mac_agent.sh`; skipped when Gmail shows nothing new |
| Morning brief (part B) | Opus, medium | Sonnet subagents read threads, prepare tasks, check payments (`docs/brief-run.md`) |
| Midday sweep (part D) | Sonnet | Kriss switches the chat to Opus before a task that needs judgment (`docs/midday-run.md`) |
| Bilagsmottak: refresh, triage, buckets with **stable** rules, the text-only check | Sonnet | Subagents `bilag-worker` and `bilag-checker` in livid-kb |
| Bilagsmottak: Q bucket, **draft**-rule buckets, first-use verification, review, posting | Opus, medium | The orchestrating chat |
| Mechanical runs: Z-report import fixes, gift cards, weekly report data, UPS DDP audit, customs filing, night runs | Sonnet | Started on Sonnet; Opus only when a case falls outside the doc |
| Writing or changing KB rules and processes, sensitive emails, month-end close, budget analysis | Opus, medium | |

**Habits for every task:**
1. **Subagents for bulk reading.** More than about 5 threads, documents or vouchers to read → Sonnet subagents with fresh context (never a fork). Each gets only its items, the one or two KB doc paths it needs and a return format, and returns one line per item. Read the returned lines, never the transcript.
2. **APIs and scripts before Chrome.** Connectors and `scripts/email/gmail_tool.py` first; Chrome only where no API exists, reading page text rather than screenshots.
3. **Load little.** One tool search for the connectors the task needs; find KB docs with `kb_find.py` and open 1–5 of them; never bulk-read folders.
4. **One task per chat.** Start a new chat for an unrelated task rather than continuing a long one.
5. **Escalate, don't default up.** A Sonnet run that meets something its docs don't cover stops and flags it for an Opus chat instead of guessing.

# Alternatives considered
- Everything on Opus: simplest, but it hit the weekly limit.
- Everything on Sonnet: cheapest, but weaker on judgment calls, drafting in Kriss's voice for sensitive mail, and rule writing.
- Moving the morning and midday chats to the cloud: same token use, but the cloud can't reach the Gmail token for attachments or Chrome on the Mac.

# Consequences
- Run instructions name their model: `docs/routine.md`, `docs/mac-agent.md`, `docs/brief-run.md`, `docs/midday-run.md`.
- Subagent definitions with `model: sonnet` live in `.claude/agents/` in kb-kriss (email) and livid-kb (bilagsmottak).
- `kb-router` points every task here.
- Check with the explain-usage skill after the first week of the new setup, and adjust this table.

# Affects
`docs/routine.md`, `docs/brief-run.md`, `docs/midday-run.md`, `docs/mac-agent.md`, `.claude/agents/` in both repos, livid-kb `.claude/skills/kb-router/SKILL.md` and `.claude/skills/bilagsmottak/workflow.md`.
