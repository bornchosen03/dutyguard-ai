#!/usr/bin/env bash
set -euo pipefail

# Helper to create a Python virtualenv for FastAPI/pydantic development.
# It will try to find python3.11 or python3.12; if not found, it will report and exit.

PY_CANDIDATES=(python3.11 python3.12 python3.10 python3)
PY=""
for p in "${PY_CANDIDATES[@]}"; do
  if command -v "$p" >/dev/null 2>&1; then
    PY="$p"
    break
  fi
done

if [ -z "$PY" ]; then
  echo "No suitable Python found (tried: ${PY_CANDIDATES[*]}). Install Python 3.11/3.12 and retry." >&2
  exit 1
fi

echo "Using Python: $PY"

VENV_DIR="$(pwd)/backend/.venv-fastapi"
echo "Creating virtualenv at: $VENV_DIR"

"$PY" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel

REQ_FILE="$(pwd)/backend/requirements.fastapi.txt"
if [ ! -f "$REQ_FILE" ]; then
  cat > "$REQ_FILE" <<'REQ'
fastapi
uvicorn[standard]
python-dotenv
pydantic
REQ
  echo "Wrote sample requirements to $REQ_FILE"
fi

pip install -r "$REQ_FILE"

echo "FastAPI virtualenv prepared in $VENV_DIR. Activate with:"
echo "  source $VENV_DIR/bin/activate"
