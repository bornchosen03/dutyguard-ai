#!/usr/bin/env bash
set -euo pipefail

# Build frontend and start backend (serves static assets)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[start] Working directory: $ROOT"

echo "[start] Installing frontend dependencies (safe, uses legacy-peer-deps)"
cd "$ROOT/frontend"

# Only attempt npm install/build if `npm` is available in PATH. This avoids
# failing under launchd where users often run Node via nvm and npm isn't on the
# default PATH.
if command -v npm >/dev/null 2>&1; then
	npm install --legacy-peer-deps
	echo "[start] Building frontend (production)"
	npm run build
else
	echo "[start] npm not found in PATH; skipping frontend install/build"
fi

echo "[start] Starting backend (uvicorn) on 127.0.0.1:8080"
cd "$ROOT/backend"

# Prefer the FastAPI venv if present; fall back to the default venv.
if [ -d ".venv-fastapi" ]; then
	source .venv-fastapi/bin/activate
	if python -c "import fastapi" >/dev/null 2>&1; then
		echo "[start] Using backend venv: .venv-fastapi"
		if ! python -c "import multipart" >/dev/null 2>&1; then
			echo "[start] Installing backend dependency: python-multipart"
			pip install python-multipart
		fi
	else
		deactivate || true
	fi
fi

if ! python -c "import fastapi" >/dev/null 2>&1; then
	# Ensure backend venv and dependencies exist
	if [ ! -d ".venv" ]; then
		echo "[start] Creating backend venv (.venv)"
		python3 -m venv .venv
	fi

	source .venv/bin/activate
	echo "[start] Using backend venv: .venv"
	python -m pip install --upgrade pip >/dev/null 2>&1 || true

	if ! python -c "import fastapi" >/dev/null 2>&1; then
		echo "[start] Installing backend dependencies"
		pip install -r requirements.txt
	fi
fi

# ensure logs dir
mkdir -p "$ROOT/logs"

pkill -f "uvicorn app.main:app" || true
nohup uvicorn app.main:app --host 127.0.0.1 --port 8080 --log-level info > "$ROOT/logs/backend.log" 2>&1 &

echo "[start] Backend started (logs: $ROOT/logs/backend.log)"
sleep 0.5
echo "[start] Showing last 20 lines of backend log:"
tail -n 20 "$ROOT/logs/backend.log" || true

echo "[start] Done. Visit http://127.0.0.1:8080/"
