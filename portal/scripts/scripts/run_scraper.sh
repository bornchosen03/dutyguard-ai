#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Optional: use the backend venv-fastapi if present for a consistent python.
if [ -d "$ROOT/backend/.venv-fastapi" ]; then
  source "$ROOT/backend/.venv-fastapi/bin/activate"
elif [ -d "$ROOT/backend/.venv" ]; then
  source "$ROOT/backend/.venv/bin/activate"
fi

python -m pip install --upgrade pip >/dev/null 2>&1 || true
pip install -r "$ROOT/requirements.scraper.txt"

python "$ROOT/scraper.py"
