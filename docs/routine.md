# Daily email run — instructions for the cloud scheduled task (part A)

The routine's saved prompt only says: *"Follow docs/routine.md in the kb-kriss repository."* All instructions live here, so changes don't need the routine to be edited.

Daily email run for Kriss (kristoffer@livid.no), weekdays 06:47 Oslo. Repositories cloned fresh: kb-kriss (personal KB) and livid-kb (company KB). Gmail via the Gmail connector.

1. Read `kb-kriss/AGENTS.md` and `livid-kb/AGENTS.md`, then do **part A** of `kb-kriss/kb/email/daily-run.md` step by step with the docs it links.
2. Allowed without asking (incl. applying `[KB-inbox]` drafts, step 8b, and deleting those drafts afterwards): label, archive, create Gmail drafts, KB sync (Person notes per `kb/email/kb-sync.md`), log entries.
3. **Never** send, reply, forward, delete or unsubscribe in this run. Kriss approves those later in the Cowork morning brief. This scheduled prompt is never approval.
4. **KB sync is mandatory** (step 5): every new message, including Kriss's own sent mail, ends with `AI/KB-synced`. If time runs short, skip drafts first, never KB sync.
5. Last message of the session: a short run report (counts per label, drafts made, KB notes changed, failures). The brief itself is made by the Cowork task at 07:30.
6. Commit and push to `main` per AGENTS.md §5: `tools/build_index.py` and `tools/validate.py` (0 errors), commit message = the new `kb/log.md` entries, `git pull --rebase`, push. Never force-push. **Do not create or leave other branches**; delete any `claude/…` branch this run created.
7. On failure (Gmail, GitHub, validation): put it at the top of the run report and in the log entry, and continue with what you can.
