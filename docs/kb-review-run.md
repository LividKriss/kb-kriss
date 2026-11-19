# Weekly KB review — instructions for the Claude Code scheduled task

The scheduled task's prompt only says: *"Follow docs/kb-review-run.md in /Users/kristoffer/kb-kriss."* Runs Fridays 13:00 on Kriss's MacBook Air, as a chat he answers by number. What the review covers is set in `../livid-kb/AGENTS.md` §8; this file says how to run it. Where they disagree, AGENTS.md wins.

**Model:** Opus 5.5, medium effort (it proposes rule and autonomy changes). Bulk reading (log entries, docs past `stale_after`, TODO lists) goes to Sonnet subagents that return one line per item.

**Unattended part (before Kriss answers):** read, count and write knowledge only. Never change a Rule, Process, Policy, `autonomy`, `status` or a permission before he answers.

## Run
1. Read `AGENTS.md`, `../livid-kb/AGENTS.md` (§5a, §6, §7a, §8) and `kb/notes/model-routing.md`.
2. **Gather** (in parallel where possible):
   - *Written this week:* `kb/log.md` in both repos since last Friday, counted per kind and per doc type.
   - *Ledger:* `python3 scripts/email/ledger.py stats --days 7` and `--days 28`; `ledger.py repeats`; `ledger.py uses <path>` for every `draft` Process or Rule named in this week's decisions (`docs` field).
   - *Gaps:* KB gaps named in this week's Low recommendations (the brief chats' closing lines, decision `reason` fields), and new `TODO(` lines added this week (`git log -p` is not available to agents; compare against last week's review entry in `kb/log.md`, or search for TODOs with this week's dates).
   - *Stale:* docs whose `stale_after` has passed, and `TODO(…): conflict` lines (`grep -rn "conflict —" ../livid-kb/kb kb`).
   - *Friction:* permission denials, failed or cut-short runs, and steps Kriss had to do by hand this week. Sources: run reports in `kb/log.md`; the scheduled tasks' runs (list them and read only the last messages of the brief, midday and email-run sessions); the routine's run list for the cloud run.
   - *Questions:* open `TODO(cfo)` items that blocked a decision this week, most frequent first.
3. **Compact** the data files: `ledger.py compact`.
4. **Present** in this order, numbered through, at most 25 items:
   1. *Summary:* knowledge written (count, top 5), decisions recorded and agreement rate (High / Medium / Low), runs OK or failed.
   2. *Instruction proposals:* each repeated decision as a proposed Rule or Process change: doc path, before/after in one or two lines, the cases. "ok 3" writes it.
   3. *Stable proposals:* draft docs with ≥3 accepted uses and no corrections: doc, uses, last case. "ok 5" sets stable (this is the second confirmation; add `verified` and `stale_after`, log as **Approval**).
   4. *Autonomy proposals* (only when §8's thresholds are met): the kind, the numbers, what agents would then do first and report after. Needs "yes, second confirmation" in Kriss's words.
   5. *Gaps that blocked decisions*, ranked: each with the doc it belongs in and the question that would close it. Kriss answers here, or says "interview" to save it for the next interview session.
   6. *Stale and conflicts:* re-verify (yes / update / retire) per doc.
   7. *Friction and fixes:* each with a proposed fix (a doc change, a permission, a script); permissions need a second confirmation.
   8. *Shadow period* (while it lasts): whether to end it for the High block, based on the week's High agreement rate.
5. Work through Kriss's answers: write what he approves (log each: **Update** or **Approval**), answer facts straight into the KB, and record each answer in the ledger (`kind: kb-review`).
6. After writing: `python3 tools/build_index.py` and `python3 tools/validate.py` in each repo changed (0 errors). Finish with one log entry in `kb/log.md`: **Update** Weekly KB review <date>, with what was approved, what was deferred, and the agreement rate.
