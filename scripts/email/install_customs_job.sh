#!/bin/bash
# Installs (or reinstalls) the launchd job that files customs documents every 30 minutes
# while the Mac is awake (scripts/email/file_customs.py). Run once on Kriss's Mac.
set -eu
LABEL=no.livid.kb-kriss-customs
REPO="$(cd "$(dirname "$0")/../.." && pwd -P)"
PY="$HOME/Library/Application Support/kb-kriss/venv/bin/python"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/kb-kriss-customs.log"
[ -x "$PY" ] || { echo "venv python not found: $PY" >&2; exit 1; }
"$PY" -m pip install --quiet pypdf
mkdir -p "$(dirname "$PLIST")" "$(dirname "$LOG")"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$PY</string><string>$REPO/scripts/email/file_customs.py</string></array>
  <key>StartInterval</key><integer>1800</integer>
  <key>RunAtLoad</key><true/>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
PL
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL (every 30 min while awake). Log: $LOG"
