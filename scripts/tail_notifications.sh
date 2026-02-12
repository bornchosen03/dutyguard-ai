#!/usr/bin/env bash
set -euo pipefail

FILE="${1:-backend/data/intake_notifications.jsonl}"
LINES="${2:-20}"

if [ ! -f "$FILE" ]; then
  echo "[tail_notifications] File not found: $FILE"
  exit 0
fi

echo "[tail_notifications] Showing last $LINES entries from $FILE"
if command -v jq >/dev/null 2>&1; then
  tail -n "$LINES" "$FILE" | jq -R -s 'split("\n") | map(select(. != "") | fromjson)'
else
  tail -n "$LINES" "$FILE"
fi

exit 0
