# Afternoon sweep — instructions for the Claude Code scheduled task (part D)

The scheduled task's prompt only says: *"Follow docs/afternoon-run.md in /Users/kristoffer/kb-kriss."* Runs weekdays 16:00 on Kriss's MacBook Air, after the 15:47 cloud sort run (`docs/routine.md` A1). The rules are in `kb/email/daily-run.md` (part D) and the docs it links. Setup, tools and sending mechanics are the same as in `docs/brief-run.md`, sections 0 and 2 step 5. Replaced the 12:00 midday sweep on 2026-11-26 (Kriss: every day should end at inbox zero).

## Token use
The general rules are in `kb/notes/model-routing.md`.
- This chat runs on **Sonnet 5.5**. The sort run has already labelled the day's mail, so the sweep reads thread state and snippets, not whole threads.
- Open a thread only to confirm a task match, build a proposal or answer Kriss.
- When Kriss approves something with a judgment call in it (a shortfall, a price or quantity difference, a draft to a third party), prepare it here. If the case is unclear, say so and suggest he switches this chat to Opus before executing.

## Run
1. Read `AGENTS.md`, `kb/email/daily-run.md` (part D), `kb/email/task-triggers.md`, `kb/email/brief.md` (the layout, *Rest* and *Inbox zero*) and `kb/email/send-policy.md`. Read the Processes only for today's matches.
2. Check for a `[STOP-SENDING]` draft, today's `Email sort (cloud <today> 15:…)` entry in `kb/log.md` (missing or ✗ → run S2 and S3 from `docs/routine.md` A1 with `scripts/email/gt list` and classify what they return, metadata only), and the Mac agent alert (`docs/brief-run.md` step 2).
3. `scripts/email/bs due`. **PrintCollect check:** as `docs/brief-run.md` step 3a; any PrintCollect order number without a Loom order is the first task.
4. Prepare and present per `daily-run.md` part D steps 2–4, using the brief's state tools (`bs status`, `bs shown`, `ledger.py`) as the brief does (`docs/brief-run.md` steps 3b–3e).
5. Work through Kriss's replies as in `docs/brief-run.md` section 2 step 5.
6. **Inbox zero:** `docs/brief-run.md` section 2 step 6. Finish with a short list: done, still open (later and keep, with dates), and the `bs inbox` line.
