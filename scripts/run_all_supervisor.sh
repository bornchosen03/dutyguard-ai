#!/usr/bin/env bash
# Supervisor to keep scripts/run_all.py running as a background task.
# Usage: ./scripts/run_all_supervisor.sh start|stop|status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$REPO_ROOT/backend/data/run_all.pid"
LOG_FILE="$REPO_ROOT/backend/data/run_all.supervisor.log"
RUN_CMD="python3 $REPO_ROOT/scripts/run_all.py --interval 3600 --retry 1 --continue-on-failure"

start() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" >/dev/null 2>&1; then
    echo "Supervisor: run_all already running (PID $(cat $PID_FILE))"
    exit 0
  fi
  echo "Supervisor: starting run_all with nohup"
  nohup $RUN_CMD > "$REPO_ROOT/backend/data/run_all.background.log" 2>&1 &
  echo $! > "$PID_FILE"
  echo "Supervisor: started (PID $(cat $PID_FILE))" | tee -a "$LOG_FILE"
}

stop() {
  if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    echo "Supervisor: stopping PID $pid"
    kill "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "Supervisor: stopped" | tee -a "$LOG_FILE"
  else
    echo "Supervisor: not running"
  fi
}

status() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" >/dev/null 2>&1; then
    echo "Supervisor: run_all is running (PID $(cat $PID_FILE))"
  else
    echo "Supervisor: run_all is not running"
  fi
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  status)
    status
    ;;
  *)
    echo "Usage: $0 start|stop|status"
    exit 2
    ;;
esac
