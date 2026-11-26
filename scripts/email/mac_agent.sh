#!/bin/bash
# One run of the Mac attachment agent (docs/mac-agent.md): headless Claude Code with only the
# permissions the job needs. Run hourly by launchd (install_mac_agent.sh), or by hand:
#   scripts/email/mac_agent.sh          real run
#   scripts/email/mac_agent.sh --dry    nothing forwarded, labelled, filed or logged in the KB
#   scripts/email/mac_agent.sh --force  real run even when the gate finds nothing new
# Token use: runs on Sonnet (MODEL below). A real run first checks Gmail without Claude and
# skips (logs SKIP) when nothing the agent handles has changed since the last finished run:
# no new mail with a document (PDF/Excel/CSV/Word or a transfer link) and the same set of
# AI/Invoice, AI/Docs and AI/Customs messages. Housekeeping runs once a day from this script;
# the inbox clean-up (gmail_tool.py inbox-cleanup) runs every time, before the gate.
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
MODEL="${MAC_AGENT_MODEL:-sonnet}"
GATE="$APP/mac-agent-gate"                # fingerprint of the AI/Invoice|Docs|Customs set after the last run
HOUSEKEPT="$APP/mac-agent-housekept"      # date of the last daily housekeeping
DRY=0; FORCE=0
case "${1:-}" in --dry) DRY=1 ;; --force) FORCE=1 ;; esac

stamp() { date "+%Y-%m-%d %H:%M"; }

# --- Failure alert (Kriss, 2026-11-26): a failing agent must never be silent again. While runs fail,
# $ALERT holds: first failure, latest failure, reason. The morning brief shows it on its status line
# (docs/brief-run.md step 2), and a macOS notification goes out at most every 3 hours.
ALERT="$APP/mac-agent-alert"
fail_alert() {
  local reason="${1//\"/}" first
  first=$(sed -n 1p "$ALERT" 2>/dev/null); [ -n "$first" ] || first="$(stamp)"
  printf '%s\n%s\n%s\n' "$first" "$(stamp)" "$reason" > "$ALERT"
  if [ $(( $(date +%s) - $(cat "$ALERT.notified" 2>/dev/null || echo 0) )) -ge 10800 ]; then
    /usr/bin/osascript -e "display notification \"$reason (see docs/mac-agent.md, Login)\" with title \"Mac email agent failing since $first\" sound name \"Basso\"" >/dev/null 2>&1
    date +%s > "$ALERT.notified"
  fi
}
clear_alert() { rm -f "$ALERT" "$ALERT.notified"; }

[ -x "$CLAUDE" ] || { echo "$(stamp) FAIL claude CLI not found ($CLAUDE)" >> "$LOG"; fail_alert "claude CLI not found"; exit 1; }

# --- Login (Kriss, 2026-11-26): the agent uses its own long-lived token from `claude setup-token`, kept in
# the Keychain (service kb-kriss-claude-token), not the interactive CLI login, which expired on 22.11 and
# stopped every run for four days. Without the Keychain item it falls back to the interactive login.
TOKEN=$(/usr/bin/security find-generic-password -s kb-kriss-claude-token -w 2>/dev/null)
[ -n "$TOKEN" ] && export CLAUDE_CODE_OAUTH_TOKEN="$TOKEN"
unset TOKEN
HEALTHY="$APP/mac-agent-login-ok"         # date of the last successful daily login check

RUNS="$APP/cache/mac-agent"
mkdir -p "$RUNS" "$DOCS" "$(dirname "$LOG")"
LOCK="$RUNS/.lock"
mkdir "$LOCK" 2>/dev/null || { echo "$(stamp) SKIP previous run still going" >> "$LOG"; exit 0; }
RUN="$RUNS/run-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN"
trap 'rm -rf "$RUN" "$LOCK"' EXIT

# `python`/`python3` resolve to the venv (Gmail libs, pypdf), so the allow rules need no quoted path.
export PATH="$VENV:/usr/bin:/bin:/usr/sbin:/sbin"
export KB_AGENT_UNATTENDED=1   # gmail_tool.py send-draft refuses in this run
LAST=$(cat "$STATE" 2>/dev/null || echo $(( $(date +%s) - 86400 )))
cd "$REPO"

# --- Gate (no Claude, no tokens): only start Claude when there is something to do. ---
GT="python scripts/email/gmail_tool.py"
NEW_Q="after:$LAST -in:sent -in:drafts {filename:pdf filename:xlsx filename:xls filename:csv filename:docx filename:doc wetransfer dropbox drive.google.com}"
LABEL_Q="label:ai-invoice OR label:ai-docs OR label:ai-customs"
fingerprint() ( set -o pipefail; $GT list "$LABEL_Q" --max 500 2>/dev/null | python -c 'import sys,json,hashlib; print(hashlib.sha1(" ".join(sorted(json.loads(l)["id"] for l in sys.stdin if l.strip())).encode()).hexdigest())' )

# Inbox clean-up every run (docs/mac-agent.md step 0b) — a plain script call, no Claude: closes threads
# whose latest message is Kriss's, fixes conflicting class labels, archives FYI/Noise/Waiting leftovers.
if [ $DRY = 1 ]; then
  $GT inbox-cleanup --dry 2>&1 | tail -n 40
else
  CLEAN=$($GT inbox-cleanup 2>&1); CLEAN_RC=$?
  printf '%s\n' "$CLEAN" | grep -v '^inbox-cleanup:' | sed 's/^/    /' >> "$LOG"
  echo "$(stamp) CLEANUP rc=$CLEAN_RC $(printf '%s\n' "$CLEAN" | tail -n 1)" >> "$LOG"
fi

if [ $DRY = 0 ]; then
  # Daily housekeeping (docs/mac-agent.md step 5) — a plain script call, once per day.
  if [ "$(cat "$HOUSEKEPT" 2>/dev/null)" != "$(date +%F)" ]; then
    $GT housekeep >> "$LOG" 2>&1 && date +%F > "$HOUSEKEPT"
    # Quiet open threads in Person notes → History (kb/email/kb-sync.md step 8); auto-sync commits it.
    python scripts/email/kb_close_threads.py 2>&1 | tail -n 1 | sed "s/^/$(stamp) /" >> "$LOG"
  fi
  # Daily login check — a one-word Haiku call, so an expired login is caught on quiet days too, when the
  # gate below would otherwise skip Claude and hide it. Fails → alert and stop (the real run would fail too).
  if [ "$(cat "$HEALTHY" 2>/dev/null)" != "$(date +%F)" ]; then
    PING=$(cd "$RUN" && "$CLAUDE" -p "Reply with the single word OK." --model haiku --permission-mode dontAsk \
      --setting-sources project --strict-mcp-config --no-session-persistence 2>&1); PING_RC=$?
    if [ $PING_RC = 0 ]; then
      date +%F > "$HEALTHY"; echo "$(stamp) LOGIN ok ($([ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && echo token || echo interactive login))" >> "$LOG"
    else
      REASON=$(printf '%s\n' "$PING" | tail -n 1 | cut -c1-90)
      echo "$(stamp) LOGIN FAIL rc=$PING_RC $REASON" >> "$LOG"; fail_alert "Claude login failed: $REASON"; exit 1
    fi
  fi
  if [ $FORCE = 0 ]; then
    NEW=$($GT list "$NEW_Q" --max 20 2>/dev/null); NEW_RC=$?
    FP=$(fingerprint); FP_RC=$?
    if [ $NEW_RC = 0 ] && [ $FP_RC = 0 ] && [ -n "$FP" ] && [ -z "$NEW" ] && [ "$FP" = "$(cat "$GATE" 2>/dev/null)" ]; then
      echo "$(stamp) SKIP nothing new (no document mail since $(date -r "$LAST" "+%H:%M"), labelled set unchanged)" >> "$LOG"
      exit 0
    fi
    # Any Gmail error → fall through and run Claude (fail open).
  fi
fi

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

echo "$(stamp) START $([ $DRY = 1 ] && echo dry || echo real) ($MODEL)" >> "$LOG"
OUT="$RUN/out.txt"
"$CLAUDE" -p "$PROMPT" \
  --model "$MODEL" \
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
  if [ $RC = 0 ]; then
    clear_alert
    date +%s > "$STATE"
    FP=$(fingerprint) && [ -n "$FP" ] && echo "$FP" > "$GATE"   # state after this run's own relabelling
  fi
  if [ $RC != 0 ]; then
    sed 's/^/    /' "$OUT" | tail -n 40 >> "$LOG"
    fail_alert "run failed: $(tail -n 1 "$OUT" | cut -c1-90)"
  fi
fi
exit $RC
