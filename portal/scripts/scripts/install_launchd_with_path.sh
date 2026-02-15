#!/usr/bin/env bash
set -euo pipefail

# Install a LaunchAgent that runs scripts/start.sh on user login
# This version injects a PATH that includes the user's node/npm location

NAME="com.dutyguard-ai.server"
PLIST="$HOME/Library/LaunchAgents/$NAME.plist"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_SH="$SCRIPT_DIR/../scripts/start.sh"

# Find node/npm bin dir if available
NODE_BIN="$(command -v node || true)"
NPM_BIN="$(command -v npm || true)"

if [ -n "$NODE_BIN" ]; then
  NODE_DIR="$(dirname "$NODE_BIN")"
else
  NODE_DIR=""
fi

if [ -n "$NPM_BIN" ]; then
  NPM_DIR="$(dirname "$NPM_BIN")"
else
  NPM_DIR=""
fi

# Build PATH to include common locations plus found node/npm
PATH_ENTRIES=("$HOME/.nvm/versions/node/$(node -v 2>/dev/null  || true)/bin" "/usr/local/bin" "/opt/homebrew/bin" "$NODE_DIR" "$NPM_DIR" "$HOME/.npm-global/bin")
FINAL_PATH=""
for p in "${PATH_ENTRIES[@]}"; do
  if [ -n "$p" ] && [ -d "$p" ]; then
    if [ -z "$FINAL_PATH" ]; then
      FINAL_PATH="$p"
    else
      FINAL_PATH="$FINAL_PATH:$p"
    fi
  fi
done

# Fallback to /usr/local/bin and /opt/homebrew/bin and /usr/bin
if [ -z "$FINAL_PATH" ]; then
  FINAL_PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin"
fi

echo "Writing LaunchAgent plist to $PLIST (PATH includes: $FINAL_PATH)"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>$NAME</string>
    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>-lc</string>
      <string>\"$START_SH\"</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/$NAME.out.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/$NAME.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>$FINAL_PATH</string>
    </dict>
  </dict>
</plist>
EOF

# Load the LaunchAgent
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load -w "$PLIST"

echo "LaunchAgent installed and loaded: $PLIST"
