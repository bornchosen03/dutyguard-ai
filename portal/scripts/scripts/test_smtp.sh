#!/usr/bin/env bash
# Test SMTP / notification flow by POSTing an intake to the running backend.
# If SMTP is configured, backend will try to send email; otherwise fallback is recorded.
# Optionally provide an admin key in $DUTYGUARD_ADMIN_KEY to retrieve the fallback entries.

set -euo pipefail

BASE_URL=${BASE_URL:-http://127.0.0.1:8080}
ADMIN_KEY=${DUTYGUARD_ADMIN_KEY:-}

echo "[test_smtp] Posting a test intake to $BASE_URL/api/intake"

response=$(curl -sS -w "\n%{http_code}" -X POST "$BASE_URL/api/intake" \
  -F "company=SMTP Test Co" \
  -F "name=Ops User" \
  -F "email=ops@example.com" \
  -F "phone=+10000000000" \
  -F "message=SMTP live test" \
  -F "website=")

body=$(echo "$response" | sed '$d')
code=$(echo "$response" | tail -n1)

echo "HTTP $code"
echo "$body" | jq -C . || echo "$body"

if [ -n "$ADMIN_KEY" ]; then
  echo
  echo "Fetching last 10 fallback notifications using admin key..."
  curl -sS -H "x-admin-key: $ADMIN_KEY" "$BASE_URL/admin/intake-notifications?lines=10" | jq -C . || true
else
  echo
  echo "No DUTYGUARD_ADMIN_KEY provided; to inspect fallback logs set DUTYGUARD_ADMIN_KEY and re-run this script."
fi

echo "done"
