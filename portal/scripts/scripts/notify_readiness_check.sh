#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[notify] Checking SMTP environment variables..."
MISSING=0
for key in DUTYGUARD_NOTIFY_EMAIL_TO DUTYGUARD_NOTIFY_EMAIL_FROM DUTYGUARD_SMTP_HOST DUTYGUARD_SMTP_PORT DUTYGUARD_SMTP_USERNAME DUTYGUARD_SMTP_PASSWORD; do
  if [ -z "${!key:-}" ]; then
    echo "[notify] missing: $key"
    MISSING=1
  else
    echo "[notify] set: $key"
  fi
done

echo "[notify] Submitting test intake..."
RESP="$(curl -sS -X POST http://127.0.0.1:8080/api/intake \
  -F 'company=Notification Check Co' \
  -F 'name=Ops User' \
  -F 'email=ops@example.com' \
  -F 'message=Notification readiness check' \
  -F 'website=')"

echo "$RESP"

if echo "$RESP" | grep -q '"notificationSent":true'; then
  echo "[notify] ✅ Email notification is working"
  exit 0
fi

if [ "$MISSING" -eq 1 ]; then
  echo "[notify] ⚠️ Notification not sent because SMTP env vars are incomplete"
else
  echo "[notify] ⚠️ Notification not sent; verify SMTP credentials/provider settings"
fi

exit 0
