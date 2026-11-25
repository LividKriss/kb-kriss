# Morning brief — instructions for the Claude Code scheduled task (part B)

The scheduled task's prompt only says: *"Follow docs/brief-run.md in /Users/kristoffer/kb-kriss."* All instructions live here; the rules live in the KB docs this file points to. Runs weekdays 07:30 on Kriss's MacBook Air (the Mac with the Gmail token and the Mac agent), in a Claude Code chat he works through by voice (Wispr) or typing.

This file only says how the run is set up and in what order. What to do with each email is in `kb/email/daily-run.md` (part B) and the docs it links; how to recommend is in `../livid-kb/AGENTS.md` §7a; what may be written without asking is in §5a there. Where this file and a KB doc disagree, the KB doc wins; say so in the brief.

## 0. Setup
- Working folder: `/Users/kristoffer/kb-kriss`; the company KB is `/Users/kristoffer/livid-kb`. Both are local, so read and write them directly. Find docs with `python3 ../livid-kb/tools/kb_find.py --kb both <terms>`, never by reading whole folders.
- Tools, loaded in **one** tool search: the Gmail connector (search, read, label, drafts), Loom, Threadflow, Runway. Load Claude in Chrome only for the payments check or a step that needs it. Never Superhuman, Adobe or Google Drive in this run.
- Gmail script, for everything the connector can't do (attachments, drafts with attachments, forwards, closing threads, sending an approved draft): `scripts/email/gt <command> …` (a wrapper around `gmail_tool.py` with the venv python; see `scripts/email/gt --help`). Brief state: `scripts/email/bs …`. Thread state and decision ledger: `python3 scripts/email/ledger.py …`. Run each as a plain command (no pipes), so the allowlist in `.claude/settings.json` lets the unattended run use it. Files go in the run's scratch folder, never in a repo.
- Chrome only for PowerOffice, Webshipper, Shopify, Altinn, Digipost and sites without a connector. Use the Chrome on this Mac.
- Connector missing after one retry → say so on the status line and carry on without it.

## 1. Token use
The general rules are in `kb/notes/model-routing.md`; this section applies them to the brief.
- This chat runs on **Opus 5.5, medium effort**. It composes the brief, talks with Kriss, executes approved items and writes the KB.
- **Thread state first.** `ledger.py thread-get --open` gives part A's line per open thread. Only threads whose latest mail is newer than their line, or that have no line, go to readers. Everything else is presented from its line, which saves most of the reading.
- Bulk work goes to **Sonnet subagents** defined in `.claude/agents/` (fresh context, never a fork), in parallel:
  - **Thread readers** (`thread-reader`, ~10–15 threads each, only threads that need reading): one line per thread, including whether Kriss already handled it.
  - **Investigators** (`item-investigator`, one per item or per small group of related items): for each Urgent, Reply, Action, Payments or Waiting item whose answer depends on a system or document. They check Loom, Threadflow, Runway and documents (read-only), and return a recommendation, confidence and grounds.
  - **Task preparers** (`task-preparer`): one per `AI/Task` thread.
  - **Payments checker** (`payments-checker`): checks every payment row against the supplier ledger in PowerOffice (Chrome). It runs in the background. **The brief never waits for it**: when it reports, post a short *Payments update* in the chat.
- Give each subagent only what it needs (its thread ids, the one or two KB doc paths, the return format). Read only the returned lines, never a subagent's transcript.

## 2. Run
1. Read `AGENTS.md`, `../livid-kb/AGENTS.md` (§5a, §7a, §8), `kb/email/daily-run.md` (part B), `kb/email/brief.md`, `kb/email/send-policy.md`, `kb/email/signature.md` and `kb/voice/general.md`. Read the rest (labels, urgency, task triggers, actions, Person notes) when a step needs it.
2. Check for a `[STOP-SENDING]` draft, today's part A entry in `kb/log.md` (missing → say so and offer to run the labelling), and unapplied `[KB-inbox]` drafts.
3. `ledger.py thread-get --open`, then list the open inbox threads and their labels; split them into "state is current" and "needs reading". Start the subagents from section 1 (payments checker in the background).
3a. **PrintCollect check** (task-triggers rule 9): search `in:anywhere from:bestilling@printcollect.no newer_than:14d`, group by order number, and look each up in Loom (`list_orders` customer Eplehuset, customer reference). Any number without a Loom order → relabel `+INBOX +AI/Task`, prepare it per the PrintCollect Process, and make it the first row of the brief.
3b. **Close before presenting** (`daily-run.md` part B step 1b): `scripts/email/gt done <thread>…` and `ledger.py thread-close <thread>…` for everything the systems show settled; list each with its evidence on the *Closed for you* line. Items only "handled by Kriss" (sent mail, History) go in the High block (approval mode).
3c. **Brief state:** `scripts/email/bs status <thread_id>…` for every candidate row → leave out `hidden` items, put `still-open` items on the *Still open* line (unless the deadline is two days or less away), show `full` items as rows; cap at 20 numbered items. After presenting: `bs shown <thread_id>…` for every full row. "later 5 fri" → `bs later <thread_id> <date>`; "reopen 5" → `gt label <msg_id> +INBOX +AI/<its label>` for a closed item, `bs reopen <thread_id>` for a hidden or still-open one. `bs prune` once per brief.
3d. **Drafts going stale:** drafts in Reply/Urgent threads older than 5 days go in that section, each with a recommendation. "drop 7" → delete that draft (Gmail connector `delete_draft`) and `done` the thread.
3e. **Write back the state:** one `ledger.py thread-set` line per presented thread, with the recommendation, confidence and grounds as shown.
4. Present the brief exactly as `kb/email/brief.md` lays it out. Approval mode: nothing in the High block is done until Kriss says so.
5. Wait for Kriss and work through his replies per `daily-run.md` part B steps 3–4. Mechanics:
   - **"ok high"** = do every High item (except any he names): closes, task executions, voucher forwards. It never sends email; each send needs "send <n>" on that shown draft. Then report what was done, item by item.
   - Drafts: replies through `gt reply-draft` (attaches nothing unless `--keep`/`--attach`); forwards through `gt forward-draft` (real files only, never inline signature images). If a draft was made with the Gmail connector instead, run `gt clean-draft <draft_id>` right after: the connector copies the quoted message's inline images (logos, screenshots) as attachments. `send-draft` refuses a draft that still has them. Show the full text in the chat.
   - Disclaimer and sign-off per `kb/email/signature.md`. A draft the assistant will send carries the **reviewed** disclaimer; a draft Kriss sends himself carries none.
   - Sending: only after Kriss approves that specific shown draft ("send 3"), and only with `gt send-draft <draft_id>`. The connector's send, reply and forward are blocked in this repo.
   - **Closing:** `send-draft` closes the thread itself (open labels off, `AI/Waiting` if the text asks something, archived and read; `--waiting` / `--no-waiting` override the guess, `--keep-open` skips it). Every item Kriss settles without a send → `gt done <thread_id>` right away (`--waiting` if it now waits on someone) and `ledger.py thread-close`. Never leave a settled item for tomorrow's brief.
   - **Record answers:** one `ledger.py decision-add` line per answered item (`daily-run.md` part B step 3c).
   - **Write the KB as you go:** facts and decisions from his answers go into the right docs at once, with no question (`daily-run.md` part B step 4); standing instructions go to their Rule or Process, and you say which doc.
   - Approved tasks ("do 3", or High via "ok high"): execute here (Opus) per the Process. Dry run first, then the real write.
6. Finish with a short list: done, still open, KB written (count), and the gaps that forced a Low recommendation today.
