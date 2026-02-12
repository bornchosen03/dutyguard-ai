#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

pick_port() {
  local preferred="$1"
  local port="$preferred"
  # Find the next free port starting at preferred.
  while lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; do
    port=$((port + 1))
  done
  echo "$port"
}

# Prefer backend venv-fastapi if present (consistent with start.sh)
if [ -d "$ROOT/backend/.venv-fastapi" ]; then
  source "$ROOT/backend/.venv-fastapi/bin/activate"
elif [ -d "$ROOT/backend/.venv" ]; then
  source "$ROOT/backend/.venv/bin/activate"
fi

python -m pip install --upgrade pip >/dev/null 2>&1 || true
pip install -r "$ROOT/requirements.dashboard.txt"

export STREAMLIT_BROWSER_GATHER_USAGE_STATS="false"
export STREAMLIT_TELEMETRY_DISABLED="1"

PORT="${DASHBOARD_PORT:-8501}"
PORT="$(pick_port "$PORT")"

exec streamlit run "$ROOT/dashboard.py" --server.port "$PORT" "$@"
