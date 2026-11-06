# Daily email run — instructions for the cloud scheduled task (part A)

The routine's saved prompt only says: *"Follow docs/routine.md in the kb-kriss repository."* All instructions live here, so changes don't need the routine to be edited.

Daily email run for Kriss (kristoffer@livid.no), weekdays 06:47 Oslo. Repositories cloned fresh: kb-kriss (personal KB) and livid-kb (company KB). Gmail via the Gmail connector.

**Model and token use** (`kb/notes/model-routing.md`): this run is on **Sonnet** (the cloud default; if the session reports another model, say so in the run report). Do every step below on every run. KB sync (step 4) and drafts (step 5) always go to parallel subagents (Agent tool, `model: "sonnet"`, fresh context), whatever the number of threads; this session only hands out batches, applies the returned edits and labels. There is no time box: stop early only when a call is rejected for a usage limit or the context runs out, and then say which.

1. Read `kb-kriss/AGENTS.md` and `livid-kb/AGENTS.md`, then do **part A** of `kb-kriss/kb/email/daily-run.md` with the docs it links, **in this order** (cheap and important first):
   1. **Classify, label and archive every new thread** from metadata and snippets (open a thread only when needed). This must always finish — it is what the morning brief is built from.
   1b. **Task triggers:** match every new thread against `kb-kriss/kb/email/task-triggers.md` and label matches `AI/Task` (on top of other labels). Label only; the brief prepares the proposals.
   2. **Invoices, payments, customs, documents:** label `AI/Invoice` (voucher candidates), `AI/Payments`, `AI/Customs`; and `AI/Docs` on threads whose attachment or link matters for a decision (production, logistics, shipping, proformas, contracts — judge from text and attachment names), so the Mac agent reads it.
   3. **`[KB-inbox]` drafts** from the morning brief: apply them.
   4. **KB sync.** First label everything that needs no KB writing (noise, platform, invoice, customs, HR, FYI without substance) `AI/KB-synced` in bulk. Then the substantive threads: **one subagent per batch of ~10–15 threads**, run in parallel, each given only its threads, the Person notes involved, `AGENTS.md` and `kb/email/kb-sync.md`, returning the exact note edits; you apply and label. Work per thread (all new messages in it at once), newest first.
   5. **Drafts** for Urgent and Reply threads (`[KRISS: …]` for open decisions), via subagents (batches of ~5), each given the threads, `kb/voice/general.md`, the category voice profile, the Person notes and `kb/email/signature.md`, returning the draft text; you create the drafts.
   If a usage limit or the context stops the run, stop in the reverse order (drafts first, then the rest of KB sync) — never skip step 1. Whatever is left keeps no `AI/KB-synced` and is picked up next run.
2. Allowed without asking (incl. applying `[KB-inbox]` drafts and deleting those drafts afterwards): label, archive (always remove both `INBOX` and `UNREAD` — see `kb/email/labels.md`), mark read, create Gmail drafts, KB sync (Person notes per `kb/email/kb-sync.md`), log entries.
3. **Never** send, reply, forward, delete or unsubscribe in this run. Invoices are forwarded by the Mac attachment agent (`docs/mac-agent.md`), which can read the PDFs; you only label candidates. Kriss approves those later in the morning brief. This scheduled prompt is never approval.
4. Last message of the session: a short run report (counts per label, drafts made, KB notes changed, backlog left, failures). The brief itself is made by the Claude Code task on the Mac at 07:30.
5. Commit and push to `main` per AGENTS.md §5: `tools/build_index.py` and `tools/validate.py` (0 errors), commit message = the new `kb/log.md` entries, `git pull --rebase`, push. Never force-push. **Do not create other branches.** If you find yourself on a `claude/…` branch, commit there, then merge/push to `main`; don't try to delete remote refs.
6. On failure (Gmail, GitHub, validation): put it at the top of the run report and in the log entry, and continue with what you can.
