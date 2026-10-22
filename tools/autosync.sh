#!/bin/bash
# Background auto-sync for kb-kriss (build phase). Not a KB tool: agents must not edit it.
#
# Run by launchd every few minutes (see tools/install_autosync.sh). Each run:
#   1. skips if nothing changed, or if a file changed in the last minute (an agent is mid-write);
#   2. commits everything, using the entries added to kb/log.md as the commit message;
#   3. pulls (rebase) and pushes to origin.
# On failure, commits stay local and the next run retries. If it keeps failing for
# 30 minutes, a macOS notification says so. Log: ~/Library/Logs/kb-kriss-autosync.log

main() {
  set -u
  export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
  export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8   # launchd runs with the C locale; log entries contain æøå

  REPO="$(cd "$(dirname "$0")/.." && pwd -P)"
  QUIET_MINUTES=1
  NOTIFY_AFTER_MINUTES=30

  cd "$REPO" || exit 1
  # The home folder is itself a git repo; never let `git add -A` run against the wrong one.
  [ "$(git rev-parse --show-toplevel 2>/dev/null)" = "$REPO" ] || { log "not the kb-kriss repo: $REPO"; exit 1; }

  FAIL_MARK="$REPO/.git/autosync-failing"
  NOTIFIED_MARK="$REPO/.git/autosync-notified"

  [ -e .git/rebase-merge ] || [ -e .git/rebase-apply ] && fail "a rebase is in progress; resolve it by hand"

  dirty=$(git status --porcelain)
  ahead=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo 0)
  [ -z "$dirty" ] && [ "$ahead" = 0 ] && { recovered; exit 0; }

  if [ -n "$dirty" ]; then
    recent=$(find . -path ./.git -prune -o -type f ! -name .DS_Store -mmin -"$QUIET_MINUTES" -print -quit)
    [ -n "$recent" ] && exit 0   # still being written; next run picks it up

    git add -A || fail "git add failed"
    commit_staged || fail "git commit failed"
  fi

  out=$(git pull --rebase --quiet 2>&1) || {
    [ -e .git/rebase-merge ] || [ -e .git/rebase-apply ] && git rebase --abort
    fail "pull failed: $out"
  }
  out=$(git push --quiet 2>&1) || fail "push failed: $out"

  log "pushed $(git log -1 --format='%h %s')"
  recovered
}

commit_staged() {
  # New log.md entries are the commit message (AGENTS.md §5); fall back to a file list.
  local entries subject body files n
  entries=$(git diff --cached -U0 -- kb/log.md | sed -n 's/^+- //p')
  files=$(git diff --cached --name-only)
  n=$(printf '%s\n' "$files" | grep -c .)
  if [ -n "$entries" ]; then
    subject=$(printf '%s\n' "$entries" | head -1 | sed 's/\*\*//g')
    [ ${#subject} -gt 72 ] && subject="${subject:0:71}…"
    body=$(printf '%s\n' "$entries" | sed 's/^/- /')
  else
    subject="Auto-sync: $n file(s) changed"
    body=""
  fi
  body=$(printf '%s\n\nFiles:\n%s' "$body" "$(printf '%s\n' "$files" | sed 's/^/  /')")
  git commit --quiet -m "$subject" -m "$body"
}

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  log "ERROR $*"
  [ -e "$FAIL_MARK" ] || touch "$FAIL_MARK"
  if [ ! -e "$NOTIFIED_MARK" ] && [ -n "$(find "$FAIL_MARK" -mmin +"$NOTIFY_AFTER_MINUTES")" ]; then
    notify "kb-kriss is not syncing to GitHub. See ~/Library/Logs/kb-kriss-autosync.log"
    touch "$NOTIFIED_MARK"
  fi
  exit 1
}

recovered() {
  [ -e "$NOTIFIED_MARK" ] && notify "kb-kriss is syncing to GitHub again."
  rm -f "$FAIL_MARK" "$NOTIFIED_MARK"
}

notify() {
  osascript -e "display notification \"$1\" with title \"kb-kriss sync\"" >/dev/null 2>&1
}

main "$@"
