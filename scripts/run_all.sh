#!/usr/bin/env bash
set -euo pipefail

# run_all: perform an end-to-end development run locally
# - Run backend pip-audit
# - Run backend pytest
# - Start backend server (background)
# - Run frontend npm install + audit
# - Build frontend production assets

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
BACKEND_DIR="$ROOT_DIR/portal/backend/backend"
FRONTEND_DIR="$ROOT_DIR/portal/frontend/customer-portal"

echo "[run_all] Starting backend pip-audit"
cd "$BACKEND_DIR"
python3 -m pip_audit --format json || true

echo "[run_all] Running backend tests"
cd "$ROOT_DIR"
PYTHONPATH=portal python3 -m pytest -q backend/backend/tests || true

echo "[run_all] Starting backend server"
"$ROOT_DIR/scripts/start_backend.sh"

echo "[run_all] Installing frontend dependencies and running audit"
cd "$FRONTEND_DIR"
npm ci --no-audit --no-fund
npm audit --json || true

echo "[run_all] Building frontend"
npm run build --silent

echo "[run_all] Finished. Backend: http://127.0.0.1:8080  Frontend built at $FRONTEND_DIR/dist"
