# AGENTS.md — kb-kriss (Kriss's personal knowledge base)

Read this file and `../livid-kb/AGENTS.md` before reading or changing anything here. **Everything in livid-kb's AGENTS.md applies unless this file says otherwise.** Where they differ, this file wins inside this repo; company processes, rules and policies still win over personal notes for how work is done.

`kb/` is an OKF v0.2 bundle with the extensions in `schema/`. Owner of every doc: `kriss`. Tier of every doc: `personal` (readable by the owner only).

## 1. What belongs here

People and relationships, how Kriss writes (voice), email assistant rules and processes, Kriss's areas, things he asked to remember, and his decisions.

**Personal vs company — one test:** *would a colleague doing this task need it if Kriss were away?*
- Yes → company: propose it for `livid-kb` via its feedback protocol (§6 there); write only after Kriss confirms.
- No → here.
- About an organization → company. About an individual person → here.
- Ambiguous → ask Kriss with a one-line choice.

Every save proposal names its destination: "Save to Livid KB → `organizations/suppliers/ups.md`" or "Saved to your notes → `people/jane-doe.md`". Never copy a fact into both KBs; link instead.

## 2. Ground rules (in addition to livid-kb §1)

1. **No raw email in any repo.** Only distilled notes. Raw messages fetched for processing live in `~/Library/Application Support/kb-kriss/cache/` (outside the repo) and are deleted after each pass.
2. **Minimal notes about third parties.** Only what helps work: role, relationship, history, open threads, how to communicate. Never health, family, private life, opinions about the person's character, or anything you wouldn't be comfortable showing them.
3. **Employees: work context only.** Nothing HR-related (performance, absence, salary, conflicts).
4. **Email address is the only contact detail stored.** It is the lookup key, unique across `people/`. No phone numbers, home addresses etc.
5. **Sending is governed by `kb/email/send-policy.md`.** Nothing is sent, forwarded or deleted outside what it allows. Until that doc exists and is stable, nothing is sent. When in doubt: draft, don't send.
6. Names of individuals are allowed here (unlike livid-kb's "roles, not people"), within rules 2–4.

## 3. Layout

```
schema/     types.yaml (types, categories, kb_roots) · domains.yaml (foundations)
templates/  one template per type
tools/      validate.py · build_index.py · kblib.py (copied from livid-kb, extended) · autosync (do not edit)
scripts/email/   Gmail API scripts (backfill, daily). Secrets never in the repo.
kb/
  people/   Person — one per contact, file name = kebab-case full name
  voice/    Voice Profile — general.md + one per contact category
  email/    Rule / Process — triage, labels, actions, send policy, signature, daily run
  areas/    Area — Kriss's ongoing responsibilities and projects
  notes/    Note (things to remember) · Decision (decisions and why)
```

No domains; the five foundations are fixed in `schema/domains.yaml`.

## 4. Frontmatter

Same common fields as livid-kb (`type, title, description, owner, tier, status, generated`, plus `verified`/`stale_after` when stable). `owner: kriss`, `tier: personal`. No `domain`, no `entities`.

| Type | Extra required | Notes |
|---|---|---|
| Person | `emails` (list), `category` | `organization`: `kb://livid/organizations/...` (optional for private/consumer) |
| Voice Profile | `applies_to` | a category, a list of categories, or `all` |
| Rule | `applies_to` | category / list / `all` / path |
| Process | `autonomy` | |
| Area, Note, Decision | — | |

**Categories** (Person `category`, `applies_to`): see `schema/types.yaml` → `categories`.

**Cross-repo links:** `kb://livid/<path>` (company) and `kb://kriss/<path>` (this KB), both relative to the bundle root. Use them in bodies and in `organization`. The validator resolves `kb://livid/` against `../livid-kb/kb/` when that folder is present and warns on broken links.

**Person body:** Who · Relationship · How Kriss communicates with them (only where it overrides the category voice) · History (dated bullets, newest first, short) · Open threads (with Gmail thread links) · Links.

**Status:** new Person notes are `draft` until Kriss has looked at them; he can confirm in bulk. Routine updates (History, Open threads) do not change status.

## 5. Update rules (differs from livid-kb §5–6)

- **Without asking:** create and update Person notes, voice *examples*, and Notes. Every change gets a `kb/log.md` entry, and Kriss gets a **daily digest** of what changed.
- **Show → confirm → write** (livid-kb rules): Voice Profile text, Rules, Processes, Areas, Decisions, and anything with `autonomy`.
- **Second explicit confirmation:** changing `autonomy`, setting a Voice Profile/Rule/Process `stable`, any send-policy change, adding a type or category, deleting a doc.
- **"Forget X"** → delete the line or doc and log it as **Removal** (no confirmation beyond the request itself; the log entry says what was removed, not its content).
- Saving works as in livid-kb: auto-sync (launchd `no.livid.kb-kriss-autosync`) commits and pushes; the new `kb/log.md` entries become the commit message. Agents never run Git and never edit `tools/autosync.sh` / `tools/install_autosync.sh`.
- After writing: `python3 tools/build_index.py`, then `python3 tools/validate.py`; fix all errors.

## 6. Using this KB

- Locate docs with `python3 ../livid-kb/tools/kb_find.py --kb personal|company|both <terms>` instead of reading folders.
- Email work: follow `kb/email/daily-run.md` and the rules it links; respect `autonomy` and the send policy.
- Drafting: thread + Person note + Voice Profile (category, then person override) + relevant livid-kb docs. Drafts go in the language of the thread.
