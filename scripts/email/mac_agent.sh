#!/bin/bash
# One run of the Mac attachment agent (docs/mac-agent.md): headless Claude Code with only the
# permissions the job needs. Run hourly by launchd (install_mac_agent.sh), or by hand:
#   scripts/email/mac_agent.sh          real run
#   scripts/email/mac_agent.sh --dry    nothing forwarded, labelled, filed or logged in the KB
# Raw mail and PDFs go in a per-run folder under the cache (outside the repo), removed at the end.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd -P)"
APP="$HOME/Library/Application Support/kb-kriss"
VENV="$APP/venv/bin"
LOG="$HOME/Library/Logs/kb-kriss-mac-agent.log"
STATE="$APP/mac-agent-last-run"           # epoch seconds of the last real run that finished
CLAUDE="${CLAUDE_BIN:-$(command -v claude || echo "$HOME/.local/bin/claude")}"
DRY=0; [ "${1:-}" = "--dry" ] && DRY=1

stamp() { date "+%Y-%m-%d %H:%M"; }
[ -x "$CLAUDE" ] || { echo "$(stamp) FAIL claude CLI not found ($CLAUDE)" >> "$LOG"; exit 1; }

RUNS="$APP/cache/mac-agent"
mkdir -p "$RUNS" "$(dirname "$LOG")"
LOCK="$RUNS/.lock"
mkdir "$LOCK" 2>/dev/null || { echo "$(stamp) SKIP previous run still going" >> "$LOG"; exit 0; }
RUN="$RUNS/run-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN"
trap 'rm -rf "$RUN" "$LOCK"' EXIT

# `python`/`python3` resolve to the venv (Gmail libs, pypdf), so the allow rules need no quoted path.
export PATH="$VENV:/usr/bin:/bin:/usr/sbin:/sbin"
LAST=$(cat "$STATE" 2>/dev/null || echo $(( $(date +%s) - 86400 )))
if [ $DRY = 1 ]; then
  export KB_AGENT_DRY=1
  MODE="DRY RUN: KB_AGENT_DRY=1 is set, so gmail_tool.py forward/label and file_customs.py only print what they would do. Run them exactly as in a real run. Do not edit kb/log.md. End with a table of what you would forward (to PowerOffice and to Ole Eivind, with the note), what you would file, and what you would leave for the brief and why."
else
  MODE="REAL RUN."
fi

PROMPT="Follow docs/mac-agent.md in $REPO. $MODE
Per-run temp folder (PDFs, note files): $RUN
Last finished run: $(date -r "$LAST" "+%Y-%m-%d %H:%M") (Gmail search: after:$LAST).
Commands: python scripts/email/gmail_tool.py ..., python scripts/email/file_customs.py, python3 ../livid-kb/tools/kb_find.py ..., python3 tools/build_index.py, python3 tools/validate.py.
Your last line must be one summary line for the run log: counts forwarded / to Ole Eivind / filed / left for the brief, suppliers, entity. No amounts."

ALLOWED=(
  "Read" "Glob" "Grep"
  "Bash(python scripts/email/gmail_tool.py:*)"
  "Bash(python scripts/email/file_customs.py)"
  "Bash(python scripts/email/file_customs.py --dry)"
  "Bash(python3 ../livid-kb/tools/kb_find.py:*)"
  "Bash(python3 tools/build_index.py)"
  "Bash(python3 tools/validate.py)"
  "Edit(/$RUN/**)"
)
[ $DRY = 1 ] || ALLOWED+=("Edit(/$REPO/kb/log.md)" "Edit(/$REPO/kb/index.md)")

cd "$REPO"
echo "$(stamp) START $([ $DRY = 1 ] && echo dry || echo real)" >> "$LOG"
OUT="$RUN/out.txt"
"$CLAUDE" -p "$PROMPT" \
  --permission-mode dontAsk \
  --allowedTools "${ALLOWED[@]}" \
  --add-dir "$HOME/livid-kb" "$RUN" \
  --setting-sources project \
  --strict-mcp-config \
  --no-session-persistence \
  > "$OUT" 2>&1
RC=$?
if [ $DRY = 1 ]; then
  cat "$OUT"                                   # the full table, for the person who ran it
  echo "$(stamp) DRY rc=$RC $(tail -n 1 "$OUT")" >> "$LOG"
else
  echo "$(stamp) rc=$RC $(tail -n 1 "$OUT")" >> "$LOG"
  [ $RC = 0 ] && date +%s > "$STATE"
  [ $RC = 0 ] || sed 's/^/    /' "$OUT" | tail -n 40 >> "$LOG"
fi
exit $RC
