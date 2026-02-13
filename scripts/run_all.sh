#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FORCE_RESTART="${FORCE_RESTART:-0}"

backend_healthy() {
	curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null 2>&1
}

dashboard_running() {
	pgrep -f "streamlit run .*dashboard.py" >/dev/null 2>&1
}

if [ "$FORCE_RESTART" != "1" ]; then
	if backend_healthy && dashboard_running; then
		echo "[run_all] Fast path: backend and dashboard already running"
		echo "[run_all] Set FORCE_RESTART=1 to force full restart"
		echo "[run_all] Health check:"
		curl -sS http://127.0.0.1:8080/health || true
		echo
		exit 0
	fi

	if backend_healthy && ! dashboard_running; then
		echo "[run_all] Backend already healthy; starting only dashboard"
		nohup ./scripts/run_dashboard.sh --server.headless true --server.address 127.0.0.1 >/dev/null 2>&1 &
		sleep 0.5
		echo "[run_all] Health check:"
		curl -sS http://127.0.0.1:8080/health || true
		echo
		echo "[run_all] Dashboard launch requested (background)"
		exit 0
	fi
fi

echo "[run_all] Starting GuardDuty backend+frontend…"
./scripts/start.sh

echo "[run_all] Starting Streamlit dashboard…"
# Runs in background; runner auto-selects an available port starting at 8501.
if dashboard_running; then
	echo "[run_all] Dashboard already running; skipping new launch"
else
	nohup ./scripts/run_dashboard.sh --server.headless true --server.address 127.0.0.1 >/dev/null 2>&1 &
fi

sleep 0.5

echo "[run_all] Health check:"
curl -sS http://127.0.0.1:8080/health || true

echo
echo "[run_all] Tip: dashboard prints its URL in terminal logs if run foreground."
