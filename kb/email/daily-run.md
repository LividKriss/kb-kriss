---
type: Process
title: Daily email run
description: The weekday runs of Kriss's email assistant — label, route invoices, prepare email-triggered tasks, sync the KB, draft replies, follow up, a morning brief and a midday task sweep to approve from.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/opus-5.5
  at: 2026-10-23T10:00:00+02:00
autonomy: execute-with-approval
---

# Purpose
Kriss starts the day with an inbox that holds only what needs him, ready drafts, a brief in a chat he can work through by voice or typing, and a KB that knows what happened yesterday. Nothing is sent or forwarded without his approval of that item (until [send policy](/email/send-policy.md) says otherwise).

# Trigger
Four parts:
- **A. Processing** — two Claude cloud routines, unattended (instructions: `docs/routine.md`; split 2026-11-26 because the single run kept stopping after classification): **"Email sort"** weekdays **06:47 and 15:47** Oslo (steps 1–4, 8 and 3c; ends only when its completeness searches return nothing) and **"Email KB sync and drafts"** weekdays **07:02** (steps 5–7b and 8b).
- **C. Mac attachment agent** — Claude Code on Kriss's Mac, hourly while awake (`docs/mac-agent.md`): reads invoice PDFs, forwards clear cases to PowerOffice (+ Ole Eivind for external brands), files customs documents, and reads documents/links on `AI/Docs` threads into `[Doc]` summary drafts and the KB. The cloud can't read attachments.
- **B. Morning brief** — Claude Code scheduled task on Kriss's MacBook Air, weekdays **07:30** Oslo (instructions: `docs/brief-run.md`): opens a **new chat** with the brief ([brief format](/email/brief.md)); Kriss goes through it by voice or typing and gives instructions. Moved from Cowork 2026-11-06.
- **D. Afternoon sweep** — Claude Code scheduled task on Kriss's MacBook Air, weekdays **16:00** Oslo (instructions: `docs/afternoon-run.md`), after the 15:47 sort run: opens a new chat with tasks, new urgent mail and the rest of the day's mail, and ends at inbox zero (Steps — D). Replaced the 12:00 midday sweep on 2026-11-26; that task had silently dropped out of the scheduler.
Also on request ("morning run", "go through my email", "afternoon sweep", "inbox zero").

# Inputs
- Gmail: search (incl. sent and archived), read, label, archive, create drafts; send, reply and forward **only after Kriss's approval in part B**.
- Both KBs (read; write per AGENTS.md §5): `kb-kriss/AGENTS.md`, `livid-kb/AGENTS.md`, this doc and the docs it links.

# Steps — A. Processing (unattended)
1. **Load** both AGENTS.md, this doc, [urgency](/email/urgency.md), [labels](/email/labels.md), [actions](/email/actions.md), [task triggers](/email/task-triggers.md), [KB sync](/email/kb-sync.md), [invoice routing](kb://livid/finance/bookkeeping/processes/invoice-routing.md).
2. **Collect** (page through **all** search results, 50 per page, until there is no next page) new mail since the **last successful run** (take its time from the latest daily-run entry in `kb/log.md`, minus 12 hours of overlap; never a fixed 2 days, so Monday reaches back to Friday's run and a missed run leaves no gap; skip messages already labelled `AI/KB-synced`): inbox, archived, sent, and mail to invoice@. **Plus, every run: every thread still in the inbox without one of the AI class labels (Urgent, Reply, Waiting, FYI, Noise, Action, HR, Invoice, Payments, Task, Docs, Docs-read), whatever its age**, so nothing that slipped a window stays unclassified (Kriss, 2026-11-01).
3. **Classify and label** each thread per urgency and labels. Remove labels the thread has outgrown.
3b. **Task triggers:** match every new thread against [task triggers](/email/task-triggers.md), **including its Exceptions**; label matches `AI/Task` (on top of any other label). Label only; the brief prepares the proposals.
3c. **Thread state** (Kriss, 2026-11-19): for every thread this run leaves in the inbox with an open class (Urgent, Reply, Action, Task, Payments, Invoice, Waiting), append one line with `scripts/email/ledger.py thread-set` containing: who, the ask (≤12 words), latest state, deadline, draft id, `last_msg_at`, a `kind` slug, and, where the KB alone supports one, a preliminary recommendation with confidence and grounds (livid-kb AGENTS.md §7a). This run has the Loom and Threadflow connectors and may check them for a recommendation (read-only); it cannot reach PowerOffice or attachments, so a recommendation that needs those is `conf: L` with "needs system check". HR threads get "HR matter" only, no who or ask. Add `handled` evidence when Kriss's own sent mail (any thread) or a KB History line shows the item settled. The brief re-reads only threads whose mail is newer than their state line.
4. **Invoices and customs:** label voucher candidates `AI/Invoice` (the **Mac attachment agent**, part C, reads the PDFs, forwards clear cases and notifies Ole Eivind for external brands); ordinary payment reminders → `AI/Payments`; customs documents → `AI/Customs` (the Mac job files them and relabels `AI/Filed`).
5. **KB sync — every run** (all new messages, incl. Kriss's own sent mail), after classification. Bulk-label messages that need no KB writing; substantive threads in parallel batches (see `docs/routine.md`). If the run must be cut short, stop drafts first, then KB sync — never classification; the backlog carries over via the missing `AI/KB-synced` label.
6. **Follow-ups:** Kriss's sent questions → `AI/Waiting`; overdue Waiting threads (3 working days; 2 for production/payment) → nudge drafts. Before treating a Waiting thread as unanswered, look for the reply in other threads too ([actions](/email/actions.md), AI/Waiting).
7. **Drafts** for Urgent and Reply threads per [actions](/email/actions.md). Where the answer depends on Kriss's decision, still draft it with the open point marked `[KRISS: …]` and state the decision needed — a draft with one open point beats no draft.
7b. **Stale sweep:** inbox threads labelled Reply, Action or Payments whose latest message is older than 10 days are listed in the brief under a short *Stale* line (one line each, suggested action), so Kriss can archive or act (Kriss, 2026-11-01). Exits that need no word from him are in step 8; carry-over of unanswered items is the brief's *Still open* line (Kriss, 2026-11-17).
8. **Archive** (remove `INBOX` + `UNREAD`) FYI, Noise, Waiting, HR (once labelled; counted in the brief; NAV deadlines are Urgent and stay), handled invoice/customs mail, a payment reminder superseded by a newer reminder from the same supplier, and every thread whose latest message is Kriss's own send/reply (not a voucher forward to PowerOffice, which only swaps `AI/Invoice` for `AI/PO-forwarded`). The Mac agent's hourly inbox clean-up does the same between runs. Also sweep already-archived AI-labelled threads that are still unread and mark them read.
8b. **KB inbox:** apply every draft with subject `[KB-inbox]` (written from a chat without access to the repos, e.g. on the phone) per AGENTS.md §5 — knowledge directly; rules, voice and livid-kb instruction changes count as confirmed by Kriss for that item (second-confirmation items excepted: list those in the run report instead). Log each, then delete the draft.
9. **Close:** short run report as the session's last message (counts, failures, the model it ran on); `kb/log.md` entry in each repo it changed; `tools/build_index.py`, `tools/validate.py` (0 errors) in each; commit and push to `main` (AGENTS.md §5), kb-kriss including `data/`. No other branches.

# Steps — B. Morning brief (interactive, Claude Code on the Mac)
1. Read the labels, the `[Doc]` summary drafts from the Mac agent, and the drafts part A left (`AI/Urgent`, `AI/Task`, `AI/Reply`, `AI/Action`, `AI/Payments`, `AI/Invoice`, `AI/Waiting`, `AI/Customs`, `AI/HR` count), the last run report in `kb/log.md`, and the thread state (`ledger.py thread-get --open`). Only threads with mail newer than their state line, or with no state line, are read again. If part A did not run today, say so first and offer to run it now.
1b. **Close what is already settled** before presenting, and list it under *Closed for you* with its evidence ([brief format](/email/brief.md)). Settled means one of these, checked in this run:
   - a payment reminder the payments check finds paid in PowerOffice;
   - an `AI/Task` thread already done in the system (task-triggers rule 6);
   - an `AI/Waiting` thread whose counterpart has answered (in the thread or another one, [actions](/email/actions.md));
   - an `AI/Action` alert the system shows resolved (e.g. a Loom Webshipper issue now shipped);
   - an item Kriss has already dealt with: his own sent mail in any thread, or a KB History line, shows it done (e.g. the claim already made to the supplier). In approval mode ([brief format](/email/brief.md), Exceptions) these are **not** closed before presenting; they are listed as High "close" items for his word.

   Close = `scripts/email/gt done <thread>`, then `ledger.py thread-close`. Apply the brief state: leave out hidden ("later") items until their date, and move items shown twice without an answer to *Still open*.
2. **Investigate and recommend** (livid-kb AGENTS.md §7a; Kriss, 2026-11-19): every remaining item is checked before it is shown, not after Kriss asks.
   - `AI/Task` threads: follow the Process their [task trigger](/email/task-triggers.md) row names up to the proposal (systems, dry run, `[Doc]` summaries / documents).
   - Every other Urgent, Reply, Action, Payments and Waiting item whose answer depends on a system or document (Loom orders and stock, Threadflow MOs, POs, shipments and samples, PowerOffice ledgers, Runway, an attachment): look it up and put the result in the row.
   - Each item gets a recommendation, a confidence and grounds. Precedent comes from `ledger.py repeats` and History lines; payment rows follow the payment-priority policy and the dated holds in the KB, or are Low where the KB holds neither.
   - The PowerOffice payments check runs alongside and **never holds the brief back**: present without it and add the results when they come.
   - Then present the brief per [brief format](/email/brief.md).
3. Work through it with Kriss: open threads in full on request, check systems, revise drafts, and do what he approves — execute approved tasks ("do 3") per their Process, then archive the thread and remove `AI/Task`; send (with the reviewed disclaimer, [signature](/email/signature.md)), forward vouchers (`AI/PO-forwarded`), archive, relabel. Everything sent, forwarded or decided as no-action in the brief is archived and marked read right away. Nothing sent or forwarded without his approval of that item in this chat, and only up to the level the [send policy](/email/send-policy.md) allows (sensitive classes: leave as a draft for him to send himself). Check for a `[STOP-SENDING]` draft first. **Attachments** (reading, re-attaching, forwarding only some files, drafts with files) go through `scripts/email/gmail_tool.py` on the Mac, not Chrome. **Browser work** (PowerOffice, Webshipper, Digipost, Altinn): the Chrome on the Mac the chat runs on. All other email work goes through the Gmail connector, never Superhuman, not even as a fallback. Sending an approved draft: `gmail_tool.py send-draft` (it refuses without the disclaimer or while `[STOP-SENDING]` exists). An instruction like "write to X" means: create a Gmail draft and show its full text in the chat; it is not approval. Send only after Kriss explicitly approves that specific shown draft ("send 1, 3"); when in doubt, ask. (Kriss, 2026-10-26: the brief had sent 4 emails straight from instructions, which he did not count as approval.)
3b. **Close as you go:** every item Kriss settles is closed in the same chat: a send through `send-draft` closes itself; "skip", "handled", "no action", a task executed, a reminder already paid → `scripts/email/gt done <thread>` (`--waiting` if it now waits on someone) and `ledger.py thread-close`; "later <date>" → brief state. Then update the Person note's Open threads for that thread right away. Nothing settled is left for tomorrow's brief.
3c. **Record each answer** in the decision ledger (`ledger.py decision-add`): the item's kind, a `decision_key`, the recommendation and confidence shown, Kriss's answer (`agree`, `changed`, `rejected`, `later`), the decision and his reason in a few words, and the KB docs the recommendation rested on.
4. **Write what was learned now, in this chat** (both repos are local; livid-kb AGENTS.md §5a, §8):
   - **Facts and decisions** (what is the case, what Kriss decided and why, e.g. "Manteco PO-00168 payment on hold, 18.11, cash") go straight into the right doc as dated lines (Organization or Person History, a system record, a Reference doc), with no question to Kriss. They are listed in the next brief's KB digest.
   - **Standing instructions** Kriss states ("from now on…") are written to the Rule or Process they concern; say which doc in the chat.
   - **Repeated decisions** that `ledger.py repeats` shows at least twice with none against are proposed as a rule under *KB → Needs your yes*.
   - `[KB-inbox]` drafts are only for chats that cannot reach the repos.
5. **Inbox zero:** end with `bs inbox`; every thread ends as done, waiting, later or keep ([brief format](/email/brief.md), Inbox zero; Kriss, 2026-11-26). Then say what was done and what is still open (later and keep, with dates).

# Steps — D. Afternoon sweep (Claude Code on the Mac, 16:00)
1. Load as part B step 1, but only what the sweep needs: both AGENTS.md, this doc, [task triggers](/email/task-triggers.md), [labels](/email/labels.md), [brief format](/email/brief.md), [send policy](/email/send-policy.md), and the Processes the matches need. Check for `[STOP-SENDING]`, and that the 15:47 sort run logged a full checklist (missing or ✗ → classify today's unlabelled mail here, metadata only).
2. `bs due`, then take the inbox as the sort run left it. Threads already settled in the systems are closed as in part B step 1b.
3. Prepare `AI/Task` threads to the proposal and look up what new Urgent items depend on (as part B step 2). Other new Reply and Action items get a short recommendation from their snippet and thread state; no drafts unless Kriss asks.
4. Present: one summary line, *Tasks*, *New urgent*, *New since the morning* (numbered, short), *Rest* with its default, and the inbox line. Nothing at all and an empty inbox → one line "Inbox zero, nothing new since the morning" and stop.
5. Work through it with Kriss exactly as part B step 3 (approval per item, drafts shown in full, send only after approval), and finish with the inbox-zero step (part B step 5).

# Decision rules
- Gmail is the system of record; archived (and read) = done.
- Until Superhuman is retired, its auto-archive can hide mail — always search all mail, never only the inbox.
- Low confidence about class, facts or tone → draft and say so; never send.

# Checks
- Every new message is labelled or listed as failed; every voucher is forwarded, skipped with a reason, or flagged.
- No mail sent or forwarded without an approval in this session.

# Output
Labelled and archived mail, Gmail drafts, filed customs documents, the brief, KB updates, a log entry.

# Escalation
Gmail or a KB unreachable, validation errors, or anything the docs don't cover → stop that part, say so at the top of the brief.

# Examples

# Open questions
- Superhuman retirement date (go-live).
