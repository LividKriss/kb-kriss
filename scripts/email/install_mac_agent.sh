#!/bin/bash
# Installs (or reinstalls) the launchd job that runs the Mac attachment agent every hour while the
# Mac is awake (scripts/email/mac_agent.sh, docs/mac-agent.md). Run once on Kriss's Mac, after a
# dry run (mac_agent.sh --dry) looked right. Replaces install_customs_job.sh: the agent runs
# file_customs.py itself, so the separate customs job is removed if it is there.
set -eu
LABEL=no.livid.kb-kriss-mac-agent
REPO="$(cd "$(dirname "$0")/../.." && pwd -P)"
PY="$HOME/Library/Application Support/kb-kriss/venv/bin/python"
CLAUDE="${CLAUDE_BIN:-$(command -v claude || echo "$HOME/.local/bin/claude")}"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/kb-kriss-mac-agent.log"
[ -x "$PY" ] || { echo "venv python not found: $PY" >&2; exit 1; }
[ -x "$CLAUDE" ] || { echo "claude CLI not found: $CLAUDE (install Claude Code and log in first)" >&2; exit 1; }
"$PY" -m pip install --quiet pypdf
mkdir -p "$(dirname "$PLIST")" "$(dirname "$LOG")"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$REPO/scripts/email/mac_agent.sh</string></array>
  <key>EnvironmentVariables</key>
  <dict><key>CLAUDE_BIN</key><string>$CLAUDE</string><key>HOME</key><string>$HOME</string></dict>
  <key>StartInterval</key><integer>3600</integer>
  <key>RunAtLoad</key><true/>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
PL
OLD=no.livid.kb-kriss-customs
launchctl bootout "gui/$(id -u)/$OLD" 2>/dev/null && rm -f "$HOME/Library/LaunchAgents/$OLD.plist" && echo "Removed $OLD" || true
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL (hourly while awake, runs now). Log: $LOG"
