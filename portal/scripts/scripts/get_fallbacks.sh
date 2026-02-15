#!/usr/bin/env bash
set -euo pipefail

ADMIN_URL="${1:-http://127.0.0.1:8080/admin/intake-notifications}"
FILE="${2:-backend/data/intake_notifications.jsonl}"

if [ -n "${DUTYGUARD_ADMIN_KEY:-}" ]; then
  echo "[get_fallbacks] Using admin endpoint: $ADMIN_URL"
  curl -fsS -H "x-admin-key: ${DUTYGUARD_ADMIN_KEY}" "$ADMIN_URL" || {
    echo "[get_fallbacks] Failed to fetch admin endpoint" >&2
    exit 1
  }
  exit 0
fi

if [ ! -f "$FILE" ]; then
  echo "[get_fallbacks] File not found: $FILE"
  exit 0
fi

if command -v jq >/dev/null 2>&1; then
  tail -n 20 "$FILE" | jq -R -s 'split("\n") | map(select(. != "") | fromjson)'
else
  echo "[get_fallbacks] jq not found — printing raw last 20 lines"
  tail -n 20 "$FILE"
fi
