#!/usr/bin/env bash
set -euo pipefail

# Usage: alert_on_fallbacks.sh [file] [threshold]
# Optional env: ALERT_WEBHOOK_URL - POSTs a JSON payload to this URL when threshold exceeded

# Determine repository root (two levels up from this script: scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# If a repo-root .env exists, export its variables so child processes see them.
if [ -f "$REPO_ROOT/.env" ]; then
  echo "[alert] Loading environment from $REPO_ROOT/.env"
  set -a
  # shellcheck disable=SC1090
  source "$REPO_ROOT/.env"
  set +a
fi

FILE="${1:-backend/data/intake_notifications.jsonl}"
THRESHOLD="${2:-10}"
WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"

if [ ! -f "$FILE" ]; then
  echo "[alert] Fallback file not found: $FILE"
  exit 0
fi

COUNT=$(wc -l < "$FILE" | tr -d ' ')
echo "[alert] $COUNT fallback entries in $FILE (threshold=$THRESHOLD)"
if [ "$COUNT" -ge "$THRESHOLD" ]; then
  echo "[alert] ⚠️ Threshold exceeded: $COUNT >= $THRESHOLD"

  # Gather a small sample (last 5 entries) for context
  SAMPLE=$(tail -n 5 "$FILE" | jq -s '.' 2>/dev/null || tail -n 5 "$FILE" | sed -e ':a' -e 'N' -e '$!ba' -e 's/\n/\\n/g')

  if [ -n "$WEBHOOK_URL" ]; then
    echo "[alert] Sending webhook to $WEBHOOK_URL"
    PAYLOAD=$(jq -n --arg file "$FILE" --argjson count "$COUNT" --argjson threshold "$THRESHOLD" --arg sample "$SAMPLE" '{file: $file, count: $count, threshold: $threshold, sample: $sample}')
    if curl -sS -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$WEBHOOK_URL"; then
      echo "[alert] Webhook delivered"
    else
      echo "[alert] Webhook delivery failed"
    fi
  else
    echo "[alert] No webhook configured (set ALERT_WEBHOOK_URL to enable) — skipping POST"
  fi

  exit 2
fi

echo "[alert] OK"
exit 0
