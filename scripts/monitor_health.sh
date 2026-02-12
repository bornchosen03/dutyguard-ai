#!/usr/bin/env bash
set -euo pipefail

API_BASE="${1:-http://127.0.0.1:8080}"

check_endpoint() {
  local url="$1"
  local name="$2"
  if curl -fsS "$url" >/dev/null; then
    echo "[ok] $name -> $url"
  else
    echo "[fail] $name -> $url"
    return 1
  fi
}

check_endpoint "$API_BASE/health" "health"
check_endpoint "$API_BASE/api/alerts" "alerts"

echo "Monitor check complete."
