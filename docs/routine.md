# Daily email run — instructions for the cloud scheduled tasks (part A)

Part A is **two cloud routines**, each with one job, so neither can end "partial" (Kriss, 2026-11-26). Their saved prompts only name a section of this file, so changes don't need the routines to be edited:

| Routine | When (Oslo, weekdays) | Prompt | Job |
|---|---|---|---|
| **Email sort** | 06:47 and 15:47 | *"Follow section A1 of docs/routine.md in the kb-kriss repository."* | Classify, label and archive every new thread; task triggers; invoice/customs/docs labels; thread state |
| **Email KB sync and drafts** | 07:02 | *"Follow section A2 of docs/routine.md in the kb-kriss repository."* | `[KB-inbox]` drafts, KB sync, follow-ups, drafts, stale sweep |

Why the split: from 20.11 to 26.11 the single run (on Sonnet) did only the classification, judged that "partial", and ended by itself after 2–4 minutes with no limit reported; it also searched only `in:inbox`, so customs and invoice mail that a Gmail filter keeps out of the inbox was never labelled. The full runs before that (on Opus) searched all mail since the last run and took about 11 minutes.

Repositories cloned fresh: kb-kriss (personal KB) and livid-kb (company KB). Gmail via the Gmail connector. Both runs are on **Sonnet** (`kb/notes/model-routing.md`); if the session reports another model, say so in the run report.

## Rules for both routines
- Read `kb-kriss/AGENTS.md`, `livid-kb/AGENTS.md` and `kb-kriss/kb/email/daily-run.md` (part A) first, then the docs your section names.
- **Every step in your section is done on every run.** The run ends early **only** when a tool call is rejected for a usage limit or the context runs out; then quote that error at the top of the run report. Ending early for any other reason ("to keep it short", "time", "no bodies read") is a **failed run**. There is no time box.
- **Page through every search** (`pageSize` 50, follow `nextPageToken` until there is none).
- Allowed without asking (incl. applying `[KB-inbox]` drafts and deleting those drafts afterwards): label, archive (always remove both `INBOX` and `UNREAD`, `kb/email/labels.md`), mark read, create Gmail drafts, KB sync (Person notes, and company knowledge in livid-kb per `kb/email/kb-sync.md` step 6 and livid-kb AGENTS.md §5a), thread-state lines in `data/`, log entries. Instruction changes (Rules, Processes) are never written by these runs: list them in the run report for the brief.
- **Never** send, reply, forward, delete or unsubscribe. Invoices are forwarded by the Mac attachment agent (`docs/mac-agent.md`), which can read the PDFs; you only label candidates. A scheduled prompt is never approval.
- **Run report** (last message) starts with one checklist line per step of your section: `1 ✓ … · 2 ✓ … · 3 ✗ <quoted error>`, then counts per label, drafts made, KB notes and livid-kb docs changed, backlog left, failures, and the model. The same checklist goes into the `kb/log.md` entry, which begins `**Update** Email sort (cloud <date> <HH:MM>)` or `**Update** Email KB sync (cloud <date>)`.
- Commit and push to `main` per AGENTS.md §5, **in each repo the run changed** (kb-kriss including `data/`; livid-kb when company knowledge was written): `tools/build_index.py` and `tools/validate.py` (0 errors), commit message = the new `kb/log.md` entries, `git pull --rebase`, push. Never force-push. **Do not create other branches.** If you find yourself on a `claude/…` branch, commit there, then push that commit to `main`; don't push the `claude/…` branch itself and don't try to delete remote refs.
- On failure (Gmail, GitHub, validation): put it at the top of the run report and in the log entry, and continue with what you can.

## A1. Email sort (06:47 and 15:47)
Read also: `kb/email/urgency.md`, `labels.md`, `task-triggers.md`, and livid-kb `finance/bookkeeping/processes/invoice-routing.md` (steps 1–2 only, to recognise vouchers and customs documents).

1. **Since when:** the time of the last `Email sort (cloud …)` entry in `kb/log.md` (or, before the first one, the last `Daily email run (cloud …)` entry), **minus 12 hours**. Call it `SINCE` (a Unix timestamp; Gmail's `after:` takes one).
2. **Collect, with exactly these Gmail searches** (all pages each):
   - S1 `after:SINCE -in:drafts -in:chats` — **all mail, not only the inbox**: archived, filtered (e.g. the `Invoices` filter label for customs and carrier mail), sent and mail to invoice@.
   - S2 `in:inbox -label:AI-Urgent -label:AI-Reply -label:AI-Waiting -label:AI-FYI -label:AI-Noise -label:AI-Action -label:AI-HR -label:AI-Invoice -label:AI-Payments -label:AI-Task -label:AI-Docs -label:AI-Docs-read -label:AI-Later` — every unclassified inbox thread, whatever its age.
   Work per thread (union of S1 and S2). Skip a thread when its newest message is older than its AI class label's last change (nothing new in it).
3. **Classify, label and archive** each thread per urgency and labels, from metadata and snippets (open a thread only when needed). Remove labels the thread has outgrown. Archive FYI, Noise, Waiting, HR (NAV deadlines are Urgent and stay), a payment reminder superseded by a newer one from the same supplier, and every thread whose latest message is Kriss's own (not a voucher forward). Already-archived mail found by S1 gets its label and stays archived unless it is Urgent, Reply, Action, Task or Payments.
4. **Task triggers:** match every thread against `task-triggers.md`, **including its Exceptions**; label matches `AI/Task` on top of other labels. **Hard rule:** mail from bestilling@printcollect.no always gets `AI/Task` and stays in the inbox; never FYI/Noise/archived (rule 9).
5. **Invoices, payments, customs, documents:** label `AI/Invoice` **on top of the thread's class label** (voucher candidates: invoice, credit note, receipt, collection notice, wherever the mail is, also inside a claim, reminder or colleague's forward), `AI/Payments` (ordinary reminders), `AI/Customs` (UPS «Innførsel/Utførsel/Rekalkulerte fortollinger», DHL «Tolldeklaration», FedEx «Godkjente deklarasjoner», Cargo Linea «Tollkvittering»), and `AI/Docs` on threads whose attachment or link matters for a decision (production, logistics, shipping, proformas, contracts; judge from text and attachment names), so the Mac agent reads them.
6. **Thread state** (`daily-run.md` part A step 3c): one `python3 scripts/email/ledger.py thread-set` call **per batch, with all its lines in one heredoc and nothing else in that command**, one line per thread left in the inbox with an open class, built from what this run already read. Include `handled` evidence where Kriss's own sent mail shows the item done.
7. **Completeness check — the run is not done until both return nothing:** S2 again, and S3 `after:SINCE -in:sent -in:drafts -in:chats -label:AI-Urgent -label:AI-Reply -label:AI-Waiting -label:AI-FYI -label:AI-Noise -label:AI-Action -label:AI-HR -label:AI-Invoice -label:AI-Payments -label:AI-Task -label:AI-Docs -label:AI-Docs-read -label:AI-Customs -label:AI-Filed -label:AI-PO-forwarded -label:AI-Later`. Anything they return: classify it (back to step 3), then check again. Put the two final counts in the checklist line (`7 ✓ S2 0 · S3 0`).
8. Log entry, commit and push (rules above). No KB sync and no drafts in this routine; A2 does them.

## A2. Email KB sync and drafts (07:02)
Read also: `kb/email/kb-sync.md`, `actions.md`, `kb/voice/general.md`, `kb/email/signature.md`.

1. **Check A1 ran today** (an `Email sort (cloud <today>` entry in `kb/log.md` after `git pull`). If it is missing, do A1 first, in full, then continue.
2. **`[KB-inbox]` drafts** from the brief: apply them per AGENTS.md §5, log each, delete the draft.
3. **KB sync** (`kb-sync.md`), for every thread with mail in the last 14 days and no `AI/KB-synced` label (search `newer_than:14d -label:AI-KB-synced -in:drafts -in:chats`, all pages). First label everything that needs no KB writing (noise, platform, invoice, customs, HR, FYI without substance) `AI/KB-synced` in bulk. Then the substantive threads: **one subagent per batch of ~10–15 threads**, in parallel (Agent tool, `model: "sonnet"`, fresh context), each given only its threads, the Person notes involved, both `AGENTS.md` (livid-kb §5a) and `kb/email/kb-sync.md`, returning the exact edits; you apply them and label `AI/KB-synced`. Newest first.
4. **Follow-ups** (`daily-run.md` step 6): Kriss's sent questions → `AI/Waiting`; overdue Waiting threads (3 working days; 2 for production/payment) → nudge drafts, after looking for the reply in other threads too.
5. **Drafts** for Urgent and Reply threads without a current draft (`[KRISS: …]` for open decisions), via subagents (batches of ~5), each given the threads, `kb/voice/general.md`, the category voice profile, the Person notes and `kb/email/signature.md`, returning the draft text; you create the drafts. **No stray attachments:** a connector `create_draft` with `replyToMessageId` copies the quoted message's inline images as attachments. Right after each such draft, call `update_draft` with its `draftId` and the same `subject`, no `attachments` (tested 2026-11-17).
6. **Stale sweep** (`daily-run.md` step 7b): list inbox threads labelled Reply, Action or Payments whose latest message is older than 10 days in the run report and log entry, one line each with a suggested action.
7. Log entry, commit and push (rules above). The brief itself is made by the Claude Code task on the Mac at 07:30.
