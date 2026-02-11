#!/usr/bin/env bash
set -euo pipefail

# Start development servers: backend (uvicorn reload) and frontend (vite dev)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[dev] Working directory: $ROOT"

echo "[dev] Starting backend (uvicorn --reload) on 127.0.0.1:8000"
cd "$ROOT/backend"
source .venv/bin/activate 2>/dev/null || true
pkill -f "uvicorn app.main:app" || true
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &

echo "[dev] Starting frontend (vite) on 5173"
cd "$ROOT/frontend"
npm install --legacy-peer-deps
npm run dev -- --port 5173 --host 127.0.0.1
