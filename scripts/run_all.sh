#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[run_all] Starting GuardDuty backend+frontend…"
./scripts/start.sh

echo "[run_all] Starting Streamlit dashboard…"
# Runs in background; runner auto-selects an available port starting at 8501.
nohup ./scripts/run_dashboard.sh --server.headless true --server.address 127.0.0.1 >/dev/null 2>&1 &

sleep 0.5

echo "[run_all] Health check:"
curl -sS http://127.0.0.1:8080/health || true

echo
echo "[run_all] Tip: dashboard prints its URL in terminal logs if run foreground."
