#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/backend/.venv-fastapi/bin/python}"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "[smoke] Python not found at: $PYTHON_BIN"
  exit 1
fi

echo "[smoke] Checking health endpoint..."
HEALTH="$(curl -fsS --max-time 3 "$BASE_URL/health")"
echo "[smoke] /health => $HEALTH"

echo "[smoke] Running API smoke flow (classify + pilot + metrics)..."
"$PYTHON_BIN" - <<'PY'
import json
import urllib.request

base = "http://127.0.0.1:8080"

def post(path, payload):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def get(path):
    req = urllib.request.Request(base + path, method="GET")
    with urllib.request.urlopen(req, timeout=8) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

summary = {}

status, body = post("/api/classify", {
    "name": "Smoke check sample",
    "description": "short",
    "materials": {},
    "value": 120000,
    "origin_country": "CN",
    "destination_country": "US",
    "intended_use": "qa",
})
summary["classify"] = {"status": status, "review_ticket_id": body.get("review_ticket_id")}

status, onboard = post("/api/pilot/onboard", {
    "customer_name": "Smoke Test Imports",
    "entries": [
        {
            "sku": "SM-100",
            "description": "Industrial controller module",
            "import_value": 100000,
            "current_duty_rate": 0.08,
            "suggested_duty_rate": 0.04,
            "confidence": 0.93,
        }
    ],
})
batch_id = onboard.get("batch_id")
summary["pilot_onboard"] = {"status": status, "batch_id": batch_id}

status, prioritize = get(f"/api/pilot/prioritize/{batch_id}")
summary["pilot_prioritize"] = {
    "status": status,
    "total_potential_recovery": prioritize.get("total_potential_recovery"),
}

status, packet = post(f"/api/pilot/claim-packet/{batch_id}", {})
summary["claim_packet"] = {"status": status, "packet_id": packet.get("packet_id")}

status, metrics = get("/api/metrics/summary")
summary["metrics"] = {
    "status": status,
    "reviews_total": metrics.get("reviews", {}).get("total"),
    "claim_packets_generated": metrics.get("claim_packets_generated"),
}

print(json.dumps(summary, indent=2))
PY

echo "[smoke] Smoke check completed successfully"
