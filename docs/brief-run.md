# Morning brief — instructions for the Claude Code scheduled task (part B)

The scheduled task's prompt only says: *"Follow docs/brief-run.md in /Users/kristoffer/kb-kriss."* All instructions live here; the rules live in the KB docs this file points to. Runs weekdays 07:30 on Kriss's MacBook Air (the Mac with the Gmail token and the Mac agent), in a Claude Code chat he works through by voice (Wispr) or typing.

This file only says how the run is set up and in what order. What to do with each email is in `kb/email/daily-run.md` (part B) and the docs it links. Where this file and a KB doc disagree, the KB doc wins; say so in the brief.

## 0. Setup
- Working folder: `/Users/kristoffer/kb-kriss`; the company KB is `/Users/kristoffer/livid-kb`. Both are local, so read them directly. Find docs with `python3 ../livid-kb/tools/kb_find.py --kb both <terms>`, never by reading whole folders.
- Tools, loaded in **one** tool search: the Gmail connector (search, read, label, drafts), Loom, Threadflow. Load Claude in Chrome only when a step below needs it. Never Superhuman, Adobe, Runway or Google Drive in this run.
- Gmail script, for everything the connector can't do (attachments, drafts with attachments, forwards, sending an approved draft): `"$HOME/Library/Application Support/kb-kriss/venv/bin/python" scripts/email/gmail_tool.py …` (see its `--help`). Files go in the run's scratch folder, never in a repo.
- Chrome only for PowerOffice, Webshipper, Shopify, Altinn, Digipost and sites without a connector. Use the Chrome on this Mac.
- Connector missing after one retry → say so at the top of the brief and carry on without it.

## 1. Token use
The general rules are in `kb/notes/model-routing.md`; this section applies them to the brief.
- This chat runs on **Opus 5.5, medium effort**. It composes the brief, talks with Kriss and executes approved items.
- Bulk reading goes to **Sonnet subagents** defined in `.claude/agents/` (fresh context, never a fork), running in parallel:
  - **Thread readers** (`thread-reader`; split by label group, about 10–15 threads each): each reads its threads to the latest message (`kb/email/actions.md`) and returns one line per thread: thread id, Gmail link, who, the ask in 10 words or fewer, its latest state, deadline, and whether a draft exists.
  - **Task preparers** (`task-preparer`): one per `AI/Task` thread. Each reads `kb/email/task-triggers.md` and the Process its row names, checks Loom or Threadflow (read and dry run only), reads the `[Doc]` draft or the documents (gmail_tool.py), and returns the proposal row with its flags.
  - **Payments checker** (`payments-checker`): one subagent checks every Payments-due row against the supplier ledger in PowerOffice (Chrome) and returns paid or open for each.
- Give each subagent only what it needs: its thread ids, the one or two KB doc paths, and the return format. Read only the returned lines, never a subagent's transcript.
- Open a thread in this chat only when Kriss asks about it or before drafting a reply to it.

## 2. Run
1. Read `AGENTS.md`, `../livid-kb/AGENTS.md`, `kb/email/daily-run.md` (part B), `kb/email/brief.md`, `kb/email/send-policy.md`, `kb/email/signature.md` and `kb/voice/general.md`. Read the rest (labels, urgency, task triggers, actions, Person notes) when a step needs it.
2. Check for a `[STOP-SENDING]` draft, today's part A entry in `kb/log.md` (missing → say so and offer to run the labelling), and unapplied `[KB-inbox]` drafts.
3. Start the subagents from section 1 in parallel. Close tasks that are already done (`task-triggers.md` rule 6).
3b. **Close before presenting** (`daily-run.md` part B step 1b): `gmail_tool.py done <thread>` for what the subagents found settled (paid in PowerOffice, task done in the system, Waiting answered, Action resolved); list them on the *Closed for you* line.
3c. **Brief state** (`scripts/email/brief_state.py`, run with the venv python): `status <thread_id>…` for every candidate row → leave out `hidden` items, put `still-open` items on the *Still open* line (unless the deadline is two days or less away), show `full` items as rows; cap at 20 numbered items. After presenting: `shown <thread_id>…` for every full row. "later 5 fri" → `later <thread_id> <date>`; "reopen 5" → put the thread back: `gmail_tool.py label <msg_id> +INBOX +AI/<its label>` for a closed item, `brief_state.py reopen <thread_id>` for a hidden or still-open one. `prune` once per brief.
3d. **Drafts going stale:** drafts in Reply/Urgent threads older than 5 days go in that section. "drop 7" → delete that draft (Gmail connector `delete_draft`) and `done` the thread.
4. Present the brief exactly as `kb/email/brief.md` lays it out.
5. Wait for Kriss and work through his replies per `daily-run.md` part B steps 3–4. Mechanics:
   - Drafts: replies through `gmail_tool.py reply-draft` (attaches nothing unless `--keep`/`--attach`); forwards through `forward-draft` (real files only, never inline signature images). If a draft was made with the Gmail connector instead, run `gmail_tool.py clean-draft <draft_id>` right after: the connector copies the quoted message's inline images (logos, screenshots) as attachments. `send-draft` refuses a draft that still has them. Show the full text in the chat.
   - Disclaimer and sign-off per `kb/email/signature.md`. A draft the assistant will send carries the **reviewed** disclaimer; a draft Kriss sends himself carries none.
   - Sending: only after Kriss approves that shown draft, and only with `gmail_tool.py send-draft <draft_id>`. The connector's send, reply and forward are blocked in this repo.
   - **Closing:** `send-draft` closes the thread itself (open labels off, `AI/Waiting` if the text asks something, archived and read; `--waiting` / `--no-waiting` override the guess, `--keep-open` skips it). Every item Kriss settles without a send ("done", "skip", "handled", "no action", a task executed, a reminder already paid) → `gmail_tool.py done <thread_id>` right away (`--waiting` if it now waits on someone). Never leave a settled item for tomorrow's brief. Kriss's own replies from Gmail or his phone are closed hourly by the Mac agent's inbox clean-up.
   - Approved tasks ("do 3"): execute here (Opus) per the Process. Dry run first, then the real write.
6. Finish with a short list: done, still open.
