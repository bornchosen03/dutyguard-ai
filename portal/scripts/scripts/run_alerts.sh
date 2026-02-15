#!/usr/bin/env zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Prefer the FastAPI venv if present (matches scripts/start.sh behavior)
if [[ -x "$ROOT/.venv-fastapi/bin/python" ]]; then
  PY="$ROOT/.venv-fastapi/bin/python"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="python3"
fi

echo "Running GuardDuty Alert Agent…"
"$PY" "$ROOT/alerts.py"
