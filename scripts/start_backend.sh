#!/usr/bin/env bash
set -euo pipefail

# Starts the backend (uvicorn) with the correct PYTHONPATH and logs.
# Usage: ./scripts/start_backend.sh [--port 8080]

PORT=${1:-8080}
BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
BACKEND_DIR="$BASE_DIR/portal/backend/backend"
LOGFILE="$BACKEND_DIR/uvicorn.log"

echo "Starting backend from $BACKEND_DIR (logs -> $LOGFILE)"
cd "$BACKEND_DIR"

# Kill any running uvicorn instances for this app
pkill -f "uvicorn app.main" || true

# Start uvicorn with PYTHONPATH pointing to backend dir so the `app` package imports
nohup env PYTHONPATH="$BACKEND_DIR" uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --reload > "$LOGFILE" 2>&1 &
echo $!
