---
type: Rule
title: Morning brief format
description: How the morning brief is laid out — a decision queue grouped by confidence, each item with a recommendation and its grounds, numbered so Kriss can settle most of it with one word.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-11-19T09:00:00+01:00
applies_to: all
---

# Applies to
Part B of the [daily run](/email/daily-run.md), and the afternoon sweep (part D: summary line, then only the sections that have items, then *Rest* and the inbox-zero finish).

# Rules
**What the brief is:** a decision queue, not an inbox digest. Every numbered item arrives **already checked and investigated**, with a recommendation, a confidence (High, Medium or Low) and the grounds, following livid-kb AGENTS.md §7a. Kriss should be able to settle the High block with one word and most of the rest with a number and a word.

**Language and length:** English, short. **At most 20 numbered items** in total; what does not fit goes on the *Still open* line. Numbers run through the whole brief, so "ok 3, 7" is unambiguous. Each item links its Gmail thread. Grounds are short references (`KB: urgency.md (draft)` · `TF: SH-00180 exists` · `prec: 2× close` · `sent 18.11`), never prose.

**Layout, in this order (leave out empty sections):**

0. **Status line**: did part A run, any `[STOP-SENDING]` draft, and whether the PowerOffice payments check is still running (its results are added when they come; the brief never waits for it).
1. **Closed for you**: one line listing what the brief closed before presenting, each with its evidence in a few words (e.g. "Bube 0017 (paid 14.11, PO ledger) · Frameless task (SH-00180/181 exist)"), and a short number so "reopen 5" undoes it.
2. **Summary**: one line of counts (`High 6 · Medium 5 · Low 4 · Payments 9 · Waiting 3 · FYI 18 · Noise 41`), then one sentence on the most important thing today.
3. **High: will do on "ok high"**: `# · Item (who, what) · Action · Grounds`. Actions: close or archive (with evidence it is settled), execute a prepared task, file or forward a voucher per its Process. Kriss can exclude items: "ok high except 4". **Sending email is never part of "ok high":** a recommended send shows the full draft text and waits for "send 3" on that email ([send policy](/email/send-policy.md)), until the send policy itself is changed.
4. **Medium: recommend**: `# · Item · Recommendation · Why not High` (e.g. "rule is draft", "first time", "PDF not read"). Drafts are linked, and shown in full when the recommendation is to send.
5. **Low: your decision**: `# · Item · Options, and my lean if the grounds support one · KB gap` (the doc or policy that would let this be answered next time).
6. **Tasks**: email-triggered tasks ([task triggers](/email/task-triggers.md)) sit in the block their confidence puts them in, with the Process's extra blocks kept under the row:
   - **T4 garment shipments:** header, *What ships*, *Price control* (MO price vs invoice price per line, difference × qty, proposed accept/reject), *Decisions needed* (numbered with the brief). No shipment is created while a price difference is undecided.
   - **T5 sample shipments:** one row per manufacturer: matched SR lines → in transit with carrier and tracking; counts of already in transit, unmatched and overdue.
7. **Payments**: `# · Supplier · Amount · Due · Reminder no. · PO ledger (paid/open/checking) · Recommendation · Conf`. Recommendations follow the payment-priority policy and any dated holds in the KB; where the KB holds neither, the row is Low and says so. One row per supplier.
8. **Waiting**: overdue threads, as recommendations ("send nudge" with the draft, or "close: answered in <thread>").
9. **Invoices**: *Forwarded automatically since the last brief* (`Supplier · Doc no · Amount · Entity`, unnumbered, for checking; source: the Mac agent's `kb/log.md` entries; ⚠ and a task number for a manufacturer invoice with no MO shipment in Threadflow, [task triggers](/email/task-triggers.md) rule 8), then any that need Kriss, numbered in the blocks above. One line: customs documents filed / waiting.
10. **FYI**: up to 8 one-liners; "+N more". Noise: count only.
11. **Still open**: one line, `n · who – what · default` where *default* is what happens without an answer ("closes 26.11", "later Mon", "keep"). An item comes back as a full row only on new mail or a deadline two days or less away. "Stays" is no longer a default: an item that waits goes to *later* with a date.
11b. **Rest**: one line for every inbox thread that is not a numbered row or on *Still open* (beyond the 20-item cap, or nothing to decide): `Rest (n): who – what, … · default archive`. "ok rest" archives them all; "ok rest except Bogart" keeps that one as a row next time.
12. **Drafts going stale**: drafts unsent for more than 5 days: `# · Who · Age · recommendation (send / rewrite / drop)`.
13. **KB**: *Written since the last brief*: a count and up to 5 one-liners (knowledge flows without approval, livid-kb AGENTS.md §5a). *Needs your yes*: numbered instruction changes (rules from repeated decisions, process changes), each with its cases. *Gaps that blocked a decision today*: one line.
14. **Close**: "Reply e.g. *ok high · ok 7, 9 · 12 later 01.12 · 14: pay Friday · keep 5 · ok rest · more on 5*." Then the inbox line: `Inbox: n threads now · goal 0`.

**Inbox zero — the brief's finish line** (Kriss, 2026-11-26): the brief is done when the inbox is empty except for what Kriss chose to keep. Every thread in the inbox when the brief starts ends as one of:
- **done**: settled, sent or decided as no action → archived and read;
- **waiting**: waits on someone else → archived with `AI/Waiting` (the follow-up rule brings it back if nobody answers);
- **later**: put off to a date → archived and read with `AI/Later`, back in the inbox on that date (`bs later`, `bs due`);
- **keep**: Kriss wants it in the inbox unprocessed for now → stays, marked read (`bs keep`). Keep is for a handful of items, not a parking place: a thread kept three briefs in a row is asked about as "later or done?".

After Kriss's answers the brief runs `bs inbox`, asks once about anything left with a default ("12 left: 9 → archive, 3 → later Mon; ok?"), and ends on `inbox: 0 left (keep K)`. Approval mode is unchanged: nothing is archived, put off or closed without Kriss's word, except what the sort run already archives (FYI, Noise, Waiting, HR, threads whose last message is Kriss's own).

**Answers are recorded:** every numbered item's recommendation and Kriss's answer go into the decision ledger (`scripts/email/ledger.py decision-add`): `agree` when he accepts it as given, `changed` when he decides otherwise or edits it, `rejected`, `later`. Facts and decisions in his answers are written to the KB at once (livid-kb AGENTS.md §8).

**Decisions are remembered:** "skip", "handled", "no action" → the thread is closed (`gmail_tool.py done`); "later 5 fri" → archived with `AI/Later` and hidden until that date (brief state, `docs/brief-run.md`); "keep 5" → stays in the inbox, read. The brief never asks about the same thread again unless new mail has arrived in it or a hidden item's date has come.

**Documents:** a row whose thread has a `[Doc]` draft carries its key facts ("PL: 3 ctn, ETD 30.10"); the full summary on request.

**HR:** count only, "HR matter (n)". HR threads are archived once labelled; NAV deadlines are Urgent and stay.

# Exceptions
- If part A failed or did not run, say so on the status line and offer to run it now.
- Nothing in a block → leave the block out. Nothing at all → "Nothing needs you today" plus the Closed and KB lines.
- **Approval mode (standing; Kriss, 2026-11-19):** every action and every email waits for Kriss's word. Nothing in the High block is done before he says "ok high" or names the items. This changes only per kind of decision, when the weekly KB review proposes it with the ledger numbers (livid-kb AGENTS.md §8) and Kriss gives a second confirmation. Section 1 closes only what the system shows settled: paid in PowerOffice, done in Loom or Threadflow, answered by the counterpart, alert resolved. An item that looks **already handled by Kriss** (his sent mail, a KB History line) is not closed on that evidence alone; it goes in the High block as "close: handled <evidence>".

# Examples
- 18.11 brief, before this format: of 19 answers, none was "approve as drafted". 7 were "already handled, archive", 6 were "hold or later", 5 were "check X first" and 2–3 were dictated replies. That is why items are now checked and investigated before they are shown.

# Source / history
Kriss, 2026-11-26: inbox zero is the goal of every brief. After a full brief the inbox still held 73 threads (41 new since the 06:47 run, 30 left over from earlier briefs as held, later or past the 20-item cap). Added *Rest*, the four end states (done, waiting, later, keep) and the closing `bs inbox` check; *later* now archives. The afternoon sweep (16:00) uses the same finish line.
Kriss, 2026-11-19: brief v2 — decision queue with confidence and grounds, investigation before presenting, answers recorded in the decision ledger, knowledge written without approval, payments check never blocks the brief.
Kriss, 2026-11-17: the inbox kept building and settled items were asked about again: *Closed for you*, *Still open* after two briefs, at most 20 items, stale drafts, remembered decisions, HR counted then archived.
Kriss, 2026-11-09: T4 price-control block and T5 rows in Tasks; ⚠ on forwarded manufacturer invoices without an MO shipment.
Kriss, 2026-10-23: first test run was plain bullets; wants more structure, tables where useful, still short.
