#!/bin/bash
# One run of the Mac attachment agent (docs/mac-agent.md): headless Claude Code with only the
# permissions the job needs. Run hourly by launchd (install_mac_agent.sh), or by hand:
#   scripts/email/mac_agent.sh          real run
#   scripts/email/mac_agent.sh --dry    nothing forwarded, labelled, filed or logged in the KB
# Invoice PDFs and notes go in a per-run folder under the cache (outside the repo), removed at the end;
# AI/Docs documents go in docs/<threadId>/ and stay 14 days (gmail_tool.py housekeep).
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd -P)"
APP="$HOME/Library/Application Support/kb-kriss"
VENV="$APP/venv/bin"
DOCS="$APP/docs"
LOG="$HOME/Library/Logs/kb-kriss-mac-agent.log"
STATE="$APP/mac-agent-last-run"           # epoch seconds of the last real run that finished
CLAUDE="${CLAUDE_BIN:-$(command -v claude || echo "$HOME/.local/bin/claude")}"
DRY=0; [ "${1:-}" = "--dry" ] && DRY=1

stamp() { date "+%Y-%m-%d %H:%M"; }
[ -x "$CLAUDE" ] || { echo "$(stamp) FAIL claude CLI not found ($CLAUDE)" >> "$LOG"; exit 1; }

RUNS="$APP/cache/mac-agent"
mkdir -p "$RUNS" "$DOCS" "$(dirname "$LOG")"
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
  MODE="DRY RUN: KB_AGENT_DRY=1 is set, so gmail_tool.py forward/label/draft/delete-draft/housekeep and file_customs.py only print what they would do. Run them exactly as in a real run (downloads still happen). Do not edit any file in the repo. End with a report: (1) a table of what you would forward (to PowerOffice and to Ole Eivind, with the note) and what you would leave for the brief and why; (2) what you would file as customs; (3) per AI/Docs thread: the [Doc] draft you would write (full text), and the KB updates you would make (Person note lines) or propose for livid-kb; (4) what housekeeping would delete."
else
  MODE="REAL RUN."
fi

PROMPT="Follow docs/mac-agent.md in $REPO. $MODE
Per-run temp folder (invoice PDFs, note and draft-body files): $RUN
Documents folder for AI/Docs threads: $DOCS/<threadId>/ (gmail_tool.py attachments/fetch write there).
Last finished run: $(date -r "$LAST" "+%Y-%m-%d %H:%M") (Gmail search: after:$LAST).
Commands: python scripts/email/gmail_tool.py ... (see its --help), python scripts/email/file_customs.py, python3 ../livid-kb/tools/kb_find.py ..., python3 tools/build_index.py, python3 tools/validate.py. Links: gmail_tool.py fetch for files; WebFetch only to read a public page. Never sign in anywhere.
Read every PDF before you forward or file it (gmail_tool.py text, or Read for scans); never match a document on its subject alone.
Your last line must be one summary line for the run log: counts forwarded / to Ole Eivind / filed / left for the brief, suppliers, entity. No amounts."

ALLOWED=(
  "Read" "Glob" "Grep"
  "Bash(python scripts/email/gmail_tool.py:*)"
  "Bash(python scripts/email/file_customs.py)"
  "Bash(python scripts/email/file_customs.py --dry)"
  "Bash(python3 ../livid-kb/tools/kb_find.py:*)"
  "Bash(python3 tools/build_index.py)"
  "Bash(python3 tools/validate.py)"
  "WebFetch"
  "Edit(/$RUN/**)"
)
[ $DRY = 1 ] || ALLOWED+=("Edit(/$REPO/kb/log.md)" "Edit(/$REPO/kb/index.md)" "Edit(/$REPO/kb/people/**)")

cd "$REPO"
echo "$(stamp) START $([ $DRY = 1 ] && echo dry || echo real)" >> "$LOG"
OUT="$RUN/out.txt"
"$CLAUDE" -p "$PROMPT" \
  --permission-mode dontAsk \
  --allowedTools "${ALLOWED[@]}" \
  --add-dir "$HOME/livid-kb" "$RUN" "$DOCS" \
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
