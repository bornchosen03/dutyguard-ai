#!/usr/bin/env bash
set -euo pipefail

# Build frontend and start backend (serves static assets)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[start] Working directory: $ROOT"

# If a project .env file exists, source it and export variables so services
# started by this script inherit the environment (useful for SMTP, admin key, etc.)
if [ -f "$ROOT/.env" ]; then
	echo "[start] Loading environment from $ROOT/.env"
	# shellcheck disable=SC1090
	set -a
	. "$ROOT/.env"
	set +a
fi

# Warn when notify/SMTP env vars missing to avoid silent fallbacks.
echo "[start] Checking notification environment..."
missing=0
for v in DUTYGUARD_NOTIFY_EMAIL_TO DUTYGUARD_SMTP_HOST DUTYGUARD_SMTP_PORT; do
	if [ -z "${!v:-}" ]; then
		echo "[start] WARNING: $v is not set. Intake notifications may fallback to JSONL."
		missing=1
	fi
done
if [ "$missing" -eq 0 ]; then
	echo "[start] Notification environment looks OK"
fi

# Fast mode defaults:
# - skip frontend npm install unless explicitly forced
# - skip frontend build if dist already exists unless explicitly forced
SKIP_FRONTEND_INSTALL="${SKIP_FRONTEND_INSTALL:-1}"
FORCE_FRONTEND_BUILD="${FORCE_FRONTEND_BUILD:-0}"

echo "[start] Installing frontend dependencies (safe, uses legacy-peer-deps)"
cd "$ROOT/frontend"

# Only attempt npm install/build if `npm` is available in PATH. This avoids
# failing under launchd where users often run Node via nvm and npm isn't on the
# default PATH.
if command -v npm >/dev/null 2>&1; then
	if [ "$SKIP_FRONTEND_INSTALL" = "0" ]; then
		echo "[start] Running npm install --legacy-peer-deps"
		npm install --legacy-peer-deps
	else
		echo "[start] Skipping npm install (set SKIP_FRONTEND_INSTALL=0 to force)"
	fi

	if [ "$FORCE_FRONTEND_BUILD" = "1" ] || [ ! -f "$ROOT/frontend/dist/index.html" ]; then
		echo "[start] Building frontend (production)"
		npm run build
	else
		echo "[start] Skipping frontend build (dist exists; set FORCE_FRONTEND_BUILD=1 to force)"
	fi
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

backend_healthy() {
	curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null 2>&1
}

healthy=0
for _ in $(seq 1 20); do
	if backend_healthy; then
		healthy=1
		echo "[start] Backend health check: OK"
		break
	fi
	sleep 0.25
done

if [ "$healthy" -ne 1 ]; then
	echo "[start] Backend health check: FAILED"
	echo "[start] Showing last 40 lines of backend log:"
	tail -n 40 "$ROOT/logs/backend.log" || true
	exit 1
fi

echo "[start] Showing last 20 lines of backend log:"
tail -n 20 "$ROOT/logs/backend.log" || true

echo "[start] Done. Visit http://127.0.0.1:8080/"
