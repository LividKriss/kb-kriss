---
type: Decision
title: Kjell Odne (Mission Control) — never changes its own code; retired 2026-10-23
description: The rule Kriss set on 2026-10-11 that the earlier email assistant Kjell Odne must never modify its own repository, and the fact that Kjell was decommissioned on 2026-10-23; read if an old note or repo mentions Kjell or Mission Control.
owner: kriss
tier: personal
status: draft
generated:
  by: claude/sonnet-5.5
  at: 2026-11-19T09:15:00+01:00
---

# Context
Before the KB-based email assistant, Kriss ran an assistant called Kjell Odne, built as the web application Mission Control (repo `LividKriss/mission-control`, local clone `~/Documents/Kjell Odne/mission-control`). It read the CFO's Gmail over the Gmail API only, so `invoice@lividjeans.com` reached it by forwarding (see livid-kb `systems/invoice-inbox.md`). It could propose changes in Threadflow and Loom that Kriss approved in an Approvals view. On 2026-10-11 a safety audit found the coding worker could write pull requests that loosen its own limits.

# Decision
Decided by Kriss on 2026-10-11: Kjell (through Mission Control's coding worker) must never code, merge or deploy changes to its own repository, even with Kriss's approval. Mission Control changes are made only by Claude Code sessions on the Mac, deployed by Kriss with a passkey from "Deploy changes from main". Kjell keeps an always-current description of how he works and may only suggest improvements as text. For Kjell coding other repos (Loom, Threadflow, Origio) the recommendation was to pause it until the worker is sandboxed and then allow pull requests only, with Kriss merging; Kriss had not decided that.

Kjell Odne was decommissioned on 2026-10-23 (teardown runbook in the repo). Threadflow's approval layer was removed the same day and Loom replaced its proposal system with a native agent interface (see livid-kb `systems/threadflow.md`).

# Alternatives considered
- Approving each self-change with one passkey tap: rejected because the diff summary is phone-sized and the deploy warnings miss several safety files.

# Consequences
- Moot for new work since 2026-10-23; keep the rule in mind if an assistant ever gets write access to its own configuration or code.

# Affects
Source: Claude memory notes kjell-no-self-modification (2026-10-11), kjell-invoice-mailbox (2026-10-10), kjell-odne-threadflow-approvals (2026-10-23). See also `kb://kriss/notes/kb-repos-and-gmail-setup.md`.
