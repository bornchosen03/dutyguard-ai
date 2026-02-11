#!/usr/bin/env bash
set -euo pipefail

# Installs a launchd agent to run scripts/start.sh at login and keep it alive.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.dutyguard-ai.server.plist"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$ROOT/logs"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.dutyguard-ai.server</string>
    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>$ROOT/scripts/start.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$ROOT/logs/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>$ROOT/logs/launchd.err.log</string>
    <key>WorkingDirectory</key>
    <string>$ROOT</string>
  </dict>
</plist>
EOF

echo "Wrote $PLIST"

# Reload the agent
launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"

echo "Loaded LaunchAgent: com.dutyguard-ai.server"
echo "You can view logs at: $ROOT/logs/launchd.out.log and $ROOT/logs/launchd.err.log"
