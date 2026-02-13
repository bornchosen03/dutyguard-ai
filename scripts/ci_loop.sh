#!/usr/bin/env bash
# Simple CI loop that runs the existing release_check.sh once (or repeatedly with interval).
# Usage:
#   ./scripts/ci_loop.sh         # run once
#   ./scripts/ci_loop.sh 60     # run every 60s until interrupted

set -euo pipefail

RELEASE_SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/scripts/release_check.sh"
if [ ! -x "$RELEASE_SCRIPT" ]; then
  echo "Release script not found or not executable: $RELEASE_SCRIPT" >&2
  exit 1
fi

INTERVAL=${1:-0}

run_once() {
  echo "[ci_loop] Running release check: $RELEASE_SCRIPT"
  bash "$RELEASE_SCRIPT"
}

if [ "$INTERVAL" -gt 0 ]; then
  echo "[ci_loop] Running in loop, interval=${INTERVAL}s — press Ctrl+C to stop"
  while true; do
    run_once || echo "[ci_loop] release_check failed; continuing"
    sleep "$INTERVAL"
  done
else
  run_once
fi
