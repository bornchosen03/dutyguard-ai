#!/usr/bin/env bash
set -euo pipefail

# Build frontend and start backend (serves static assets)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[start] Working directory: $ROOT"

echo "[start] Installing frontend dependencies (safe, uses legacy-peer-deps)"
cd "$ROOT/frontend"
npm install --legacy-peer-deps

echo "[start] Building frontend (production)"
npm run build

echo "[start] Starting backend (uvicorn) on 127.0.0.1:8080"
cd "$ROOT/backend"
source .venv/bin/activate 2>/dev/null || true

# ensure logs dir
mkdir -p "$ROOT/logs"

pkill -f "uvicorn app.main:app" || true
nohup uvicorn app.main:app --host 127.0.0.1 --port 8080 --log-level info > "$ROOT/logs/backend.log" 2>&1 &

echo "[start] Backend started (logs: $ROOT/logs/backend.log)"
sleep 0.5
echo "[start] Showing last 20 lines of backend log:"
tail -n 20 "$ROOT/logs/backend.log" || true

echo "[start] Done. Visit http://127.0.0.1:8080/"
