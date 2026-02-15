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

# Create sample requirements file if missing
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

# pydantic-core currently may not have wheels for Python 3.13 on some systems.
# If the chosen Python is 3.11 or 3.12, install full requirements. Otherwise
# install minimal runtime deps and print instructions.
PY_VER_STR="$($PY -c 'import sys; print("%s.%s" % (sys.version_info.major, sys.version_info.minor))')"
if [[ "$PY_VER_STR" == "3.11" || "$PY_VER_STR" == "3.12" ]]; then
  echo "Detected compatible Python ($PY_VER_STR). Installing full requirements..."
  pip install -r "$REQ_FILE"
  echo "FastAPI virtualenv prepared in $VENV_DIR. Activate with:"
  echo "  source $VENV_DIR/bin/activate"
else
  echo "Warning: detected Python $PY_VER_STR. pydantic-core may not have prebuilt wheels for this version."
  echo "Installing minimal backend dependencies (uvicorn, python-dotenv) into venv."
  pip install uvicorn[standard] python-dotenv
  echo
  echo "Created venv at $VENV_DIR with minimal backend dependencies."
  echo "To install full FastAPI + pydantic later, activate the venv and run:"
  echo "  source $VENV_DIR/bin/activate"
  echo "  pip install -r $REQ_FILE"
  echo
  echo "If that fails due to pydantic-core build errors, either use Python 3.11/3.12 or install Rust toolchain to build pydantic-core from source." 
fi
