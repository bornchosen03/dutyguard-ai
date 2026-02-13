#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FORCE_RESTART="${FORCE_RESTART:-1}"
FORCE_FRONTEND_BUILD="${FORCE_FRONTEND_BUILD:-1}"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/backend/.venv-fastapi/bin/python}"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "[release] Python executable not found: $PYTHON_BIN"
  exit 1
fi

echo "[release] Step 1/4: Restart stack"
FORCE_RESTART="$FORCE_RESTART" FORCE_FRONTEND_BUILD="$FORCE_FRONTEND_BUILD" bash scripts/run_all.sh

echo "[release] Step 2/4: Smoke check"
bash scripts/smoke_check.sh

echo "[release] Step 3/4: Backend tests"
"$PYTHON_BIN" -m pytest backend/tests/test_api.py -q

echo "[release] Step 4/4: Final health"
curl -fsS http://127.0.0.1:8080/health

echo
 echo "[release] ✅ Release check passed"
