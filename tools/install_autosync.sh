#!/bin/bash
# Installs (or reinstalls) the launchd job that runs tools/autosync.sh every 3 minutes.
# Run once on the Mac that holds the kb-kriss folder. Not a KB tool: agents must not edit it.
set -eu

LABEL=no.livid.kb-kriss-autosync
REPO="$(cd "$(dirname "$0")/.." && pwd -P)"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/kb-kriss-autosync.log"

# Commits need an explicit identity: launchd can't rely on git guessing one from the hostname.
git -C "$REPO" config user.name  >/dev/null || git -C "$REPO" config user.name  "$(id -F)"
git -C "$REPO" config user.email >/dev/null || { echo "set user.email first: git -C $REPO config user.email you@example.com" >&2; exit 1; }
git -C "$REPO" config core.quotepath false   # show æøå in file names as-is
chmod +x "$REPO/tools/autosync.sh"

mkdir -p "$(dirname "$PLIST")" "$(dirname "$LOG")"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$REPO/tools/autosync.sh</string></array>
  <key>StartInterval</key><integer>180</integer>
  <key>RunAtLoad</key><true/>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL (every 3 min). Log: $LOG"
