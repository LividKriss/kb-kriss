# Step 4 — Backfill pass 2 (content): brief for Claude Code

Read first: `docs/brief.md` (step 4 + ground rules), `docs/progress.md` (all decisions so far), `AGENTS.md` here and `~/livid-kb/AGENTS.md`. This file adds the details for step 4. Where it is silent, the brief and AGENTS.md decide.

**Goal:** draft Person notes for the step-4 contacts, draft Voice Profiles from Kriss's sent mail, and one batch of livid-kb proposals. Stop at the checkpoint (⏸) for Kriss's review. Then delete the cache.

## 0. Inputs and scope

- Contacts: `cache/step3/contacts.csv`, rows with `step4=yes` (235 on 2026-10-23). Kriss's review answers in `review/corrections.json` apply (category, org, merged addresses, notes).
- Window: last **12 months** for everyone; **3 years** for the top ~50, ranked by threads Kriss replied in over 3 years. List the top 50 in the checkpoint report.
- Gmail API, `gmail.readonly` (unchanged). Fetch `threads.get(format=full)` only for threads that include a step-4 contact. Same pacing as `fetch_headers.py` (per-user quota, back off on 403/429), resumable.
- **Never fetch or read** the excluded employee-case threads (progress.md, Employee matters), private contacts, or anything already dropped as noise or platform.
- Raw bodies only in `~/Library/Application Support/kb-kriss/cache/content/`. Scripts in `scripts/email/` (committed, no addresses or names hard-coded). Nothing raw in either repo.

## 1. Prepare text (script, before any reading)

Per message keep: date, from, to/cc, subject, and the body with quoted replies, signatures, disclaimers and HTML removed. Truncate each body to ~2,000 characters. Attachments: names only, never content. Write one compact file per contact. This keeps reading cheap. Parallel subagents per batch of contacts are fine; each gets only its contacts' files, `AGENTS.md`, the Person template and this section's rules.

## 2. Person notes (`kb/people/`)

- One file per person, `kebab-case-full-name.md`, from `templates/person.md`. Disambiguate same names with the organization (`ana-silva-rangel.md`).
- Frontmatter: `emails` = every address of that person (incl. merged private ones; unique across all notes), `category` from the review, `organization` = `kb://livid/organizations/<kind>/<id>.md`. If the org doc doesn't exist yet, use the path proposed in the livid-kb batch (§4) — the validator will warn until the batch is approved; list those in the report. `status: draft`, `generated.by: claude-code/<model>`.
- Body, short (aim ≤ 40 lines):
  - **Who:** role and organization.
  - **Relationship:** what they and Kriss work on together, since when.
  - **How Kriss communicates with them:** only where it differs from the category voice (language, formality, tone, typical length).
  - **History:** dated bullets, newest first, one line each, ~5–10 that matter (orders, disputes, agreements, changes). No routine traffic.
  - **Open threads:** only unresolved ones from the last ~60 days, with link `https://mail.google.com/mail/u/0/#all/<threadId>`.
  - **Links:** organization, related people/areas.
- **Never write** (AGENTS.md §2): health, family, private life, opinions about character, anything you wouldn't show the person; for colleagues nothing HR (performance, absence, salary, conflicts) — work context only; former staff = "former staff" + role, nothing about why they left; no phone numbers, addresses or other contact details besides email; no amounts that are personal (salaries, private payments).
- **Company facts go to livid-kb, not the Person note** (test: would a colleague need it if Kriss were away?). E.g. payment terms, invoice channel, which entity an org deals with, a supplier's lead times → collect in the §4 batch. The Person note may link to the org doc instead.
- Every note created → one `kb/log.md` **Creation** entry per batch (count + categories, no names of third parties beyond what the files themselves show). Person notes may be created without asking (AGENTS.md §5), but all stay `draft` until Kriss's review.

## 3. Voice profiles (`kb/voice/`)

- Source: Kriss's **sent** mail in the last 12 months, sampled per category of recipient (~40 messages per category where available; skip one-word replies and forwards without text). Also note language per thread.
- Profiles: `general.md` (`applies_to: all`) plus one per category with enough material; fold thin categories into `general.md` and say so. Expected at least: colleague, supplier, manufacturer, wholesale-customer, advisor, landlord, board-owner, 3pl-client.
- Each profile (template `templates/voice-profile.md`): summary; language (Norwegian vs English and when he switches); formality and length; greeting and sign-off; typical phrasing; **what he never does**; **3–5 short real examples** — Kriss's own words only, with other people's names, companies, amounts and details replaced by placeholders.
- Voice Profiles need confirmation (AGENTS.md §5): **do not write them to `kb/voice/` yet.** Put the drafts in the checkpoint report. On Kriss's OK, write them as `draft`; `stable` needs his second confirmation.

## 4. livid-kb batch (proposal only — do not write to livid-kb)

One file `cache/step4/livid-kb-batch.md` for Kriss, grouped so he can approve per group:
1. **New Organizations** — start with those linked to step-4 people (needed for `organization` links), then the rest of the 153 proposals from step 3. Per org: proposed path (`organizations/<kind>/<id>.md`), `kind`, entity, `email_domains`, one-line who/relationship, Channels if known. Customers and manufacturers go in `customers/` and `manufacturers/` (empty today).
2. **Changes to existing orgs:** new `email_domains` (list in progress.md), Texgoios → Mill-Tex rename, Eplehuset as customer (plus supplier), garment factories in `suppliers/` → `manufacturers/` (Stork Texteis, Lisama, Mill-Tex, Afonso, Dia Exemplar, Officocta) incl. every link that must change.
3. **Company facts** found while reading (target doc + one line + source thread).
4. **Ideas** (e.g. Eplehuset/PrintCollect orders → Loom) for a later livid-kb process.
After Kriss approves, write per livid-kb AGENTS.md (templates, log entry per group, `build_index.py`, `validate.py`). Moves = rename + update links; a deletion or type change needs a second confirmation there.

## 5. Checkpoint ⏸ — report for Kriss

A local HTML page (like step 3; never uploaded) with:
1. Counts: Person notes written by category; contacts skipped and why; notes whose `organization` waits for the batch.
2. **Voice profile drafts** — Kriss reviews these carefully; they drive every draft.
3. **10 Person notes for spot-check**, random but spread over categories (at least 2 colleagues, 2 suppliers/manufacturers, 1 advisor/board).
4. The livid-kb batch (§4).
5. Anything you were unsure about (category conflicts, merged identities, possible HR/private content you left out).
Run `tools/build_index.py` and `tools/validate.py` (0 errors) before the checkpoint.

## 6. After Kriss's review

- Apply corrections. Corrections that are rules (e.g. "never mention X") → propose a line in AGENTS.md or the template.
- Write the voice profiles (draft) after OK; set reviewed Person notes `stable` only if Kriss says so (bulk is fine; add `verified` + `stale_after`).
- Write the approved livid-kb batch.
- **Delete** `~/Library/Application Support/kb-kriss/cache/` (content and headers) and `review/corrections.json`; confirm in the log.
- Update `docs/progress.md` (status, decisions, anything step 5 needs: e.g. senders/topics that looked urgent, authorities seen) and add the `kb/log.md` entries. Next step (5) runs in Cowork.
