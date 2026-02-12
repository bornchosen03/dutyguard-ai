#!/usr/bin/env bash
set -euo pipefail

FILE_PATH="${1:-backend/data/intake_notifications.jsonl}"
MAX_ENTRIES="${2:-1000}"

if [ ! -f "$FILE_PATH" ]; then
  echo "[prune] File not found: $FILE_PATH"
  exit 0
fi

LINE_COUNT=$(wc -l < "$FILE_PATH" | tr -d ' ')
if [ "$LINE_COUNT" -le "$MAX_ENTRIES" ]; then
  echo "[prune] No pruning needed ($LINE_COUNT <= $MAX_ENTRIES)."
  exit 0
fi

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP="$FILE_PATH.$TIMESTAMP.bak"

cp "$FILE_PATH" "$BACKUP"

tail -n "$MAX_ENTRIES" "$BACKUP" > "$FILE_PATH.tmp"

mv "$FILE_PATH.tmp" "$FILE_PATH"

echo "[prune] Pruned $FILE_PATH: kept last $MAX_ENTRIES of $LINE_COUNT entries. Backup: $BACKUP"
exit 0
