# New Mac setup — handover for Claude Code

Paste this whole file into **Claude Code** (desktop app, Code tab) on the new Mac, with `~` (the home folder) as the working folder. Use Claude Code, not Cowork: this needs the real shell, SSH keys and launchd, which Cowork's sandbox can't reach.

## Goal

Make this Mac a second workstation for Kriss (CFO, Livid; GitHub account `LividKriss`, email `kristoffer@livid.no`):

1. Both knowledge bases cloned and syncing to GitHub automatically: `livid-kb` (company) and `kb-kriss` (personal).
2. The app repos cloned and ready to edit: Loom (ERP), Threadflow (production), Runway (finance/reporting).
3. Claude configured so Livid work here has the same KB context as on the first Mac.

Done = every check in *Verify* passes, and you report the results back to Kriss.

## Rules for this setup

- **No secrets.** Don't ask for, create or copy `.env` files, API keys, database URLs or tokens. The apps run on Replit, and their secrets stay there.
- **Don't install the Mac agent.** `kb-kriss/scripts/email/install_mac_agent.sh` (launchd `no.livid.kb-kriss-mac-agent`) and `install_customs_job.sh` must run on **one Mac only**, the first one. Otherwise emails get forwarded twice.
- **Don't edit** `tools/autosync.sh` or `tools/install_autosync.sh` in either KB repo.
- After setup, **nobody runs Git in the KB repos**. The sync job does it. Normal Git use in the app repos is fine.
- Kriss does anything in the browser (GitHub key upload, logins). Tell him exactly what to click or paste.

## Steps

### 1. Tools
- Command line tools: `xcode-select -p`. If that fails, run `xcode-select --install` and wait for Kriss to finish the installer.
- Node 22 and pnpm: check `node -v`. If it's missing, install Node 22 (Homebrew `brew install node@22`, or the nodejs.org installer, whichever Kriss prefers), then `corepack enable` so `pnpm` works.
- Python: the KB tools use `/usr/bin/python3` plus PyYAML: `python3 -m pip install --user pyyaml`.

### 2. GitHub access over SSH
All remotes use SSH (`git@github.com:LividKriss/...`).
- If there's no `~/.ssh/id_ed25519`, run `ssh-keygen -t ed25519 -C "kristoffer@livid.no"`. Let Kriss choose a passphrase or leave it empty; if he sets one, add `UseKeychain yes` / `AddKeysToAgent yes` for github.com in `~/.ssh/config`.
- `pbcopy < ~/.ssh/id_ed25519.pub`, then Kriss adds it at github.com → Settings → SSH and GPG keys → New SSH key (name it after this Mac).
- Test it: `ssh -T git@github.com` should greet `LividKriss`.

### 3. Clone the KB repos to these exact paths
Docs and scripts refer to `~/livid-kb` and `~/kb-kriss`, so use those paths.
```
git clone git@github.com:LividKriss/livid-kb.git ~/livid-kb
git clone git@github.com:LividKriss/kb-kriss.git ~/kb-kriss
```
In each repo: `git config user.name "Kristoffer Dagslott"` and `git config user.email kristoffer@livid.no`.

Check both: `python3 tools/validate.py` ends with `0 errors` (warnings are fine).

### 4. Install the sync job in both KB repos
```
~/livid-kb/tools/install_autosync.sh
~/kb-kriss/tools/install_autosync.sh
```
Every 3 minutes the job commits and pushes local changes, and pulls when there is nothing to push. Read `~/livid-kb/README.md` → *Auto-sync (build phase)* for how to check it.

### 5. Claude configuration
- Create `~/.claude/CLAUDE.md` with exactly this line (if the file already exists, add it):
  `For any Livid or personal-work task, use the kb-router skill.`
- The KB skills (`kb-router`, `kb-maintainer`, `bilagsmottak`, `z-rapport-import`, `email-assistant`) come with the repos in `.claude/skills/`. Account skills and connectors (PowerOffice, Gmail, Loom, Threadflow and so on) come with Kriss's claude.ai login. Ask Kriss to sign in to the Claude desktop app with the same account, and to check the connectors under Settings → Connectors.
- The first Mac also has personal design skills in `~/.claude/skills/` that aren't in any repo. Copy them only if Kriss wants them (AirDrop or a USB stick).

### 6. App repos
| Repo | Path | Package manager |
|---|---|---|
| `git@github.com:LividKriss/loom.git` | `~/Loom_Live` | pnpm (workspace) |
| `git@github.com:LividKriss/Threadflow2.git` | `~/Threadflow2` | npm (see `replit.md`) |
| `git@github.com:LividKriss/Runway.git` | `~/Runway` | pnpm (workspace) |

Clone each, set the same `user.name` / `user.email`, install dependencies, and run the typecheck (`pnpm typecheck` / `npm run check`, whichever the repo's `package.json` has). Don't try to start the apps: they need Replit's secrets. Local work means edit, typecheck, commit, push, and Replit deploys.

Older copies on the first Mac (`~/Documents/Loom`, `~/Documents/Threadflow`, `~/Documents/Threadflow2`) are **not** needed.

### Working on the app repos from two Macs
Unlike the KBs, these repos have no sync job:
- Run `git pull` before starting work on a Mac, and push before leaving it.
- Don't keep uncommitted work on the same branch on both Macs.
- Claude's worktree branches (`claude/...`) stay local unless pushed.

## Verify (report each to Kriss)
1. `ssh -T git@github.com` greets `LividKriss`.
2. `validate.py` shows 0 errors in both KB repos.
3. `launchctl print gui/$(id -u)/no.livid.kb-autosync | grep -E 'state|last exit'` and the same for `no.livid.kb-kriss-autosync`: loaded, last exit 0.
4. Sync round trip: ask Kriss to make any KB change on the first Mac (or wait for the next Mac agent/cloud run). Within about 5 minutes, `~/Library/Logs/livid-kb-autosync.log` (or `kb-kriss-autosync.log`) on this Mac shows `pulled …`.
5. `launchctl list | grep kb-kriss-mac-agent` returns **nothing** on this Mac.
6. All three app repos are cloned, dependencies installed, and typecheck passes (report any failures as-is; don't fix code as part of setup).
7. In a new Claude Code session in `~/livid-kb`, asking "what does kb-router do?" loads the KB skill.
