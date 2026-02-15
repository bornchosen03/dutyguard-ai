#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/logs"
MAX_SIZE_MB="${MAX_SIZE_MB:-10}"
KEEP_FILES="${KEEP_FILES:-5}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$LOG_DIR"

rotate_one() {
  local file="$1"
  [ -f "$file" ] || return 0

  local size_mb
  size_mb=$(du -m "$file" | awk '{print $1}')

  if [ "$size_mb" -ge "$MAX_SIZE_MB" ]; then
    local base
    base="$(basename "$file")"
    local rotated="$LOG_DIR/${base}.${TIMESTAMP}.log"
    mv "$file" "$rotated"
    : > "$file"
    echo "[rotate] Rotated $base -> $(basename "$rotated") (${size_mb}MB)"
  else
    echo "[rotate] Kept $(basename "$file") (${size_mb}MB < ${MAX_SIZE_MB}MB)"
  fi
}

rotate_one "$LOG_DIR/backend.log"
rotate_one "$LOG_DIR/launchd.out.log"
rotate_one "$LOG_DIR/launchd.err.log"
rotate_one "$LOG_DIR/start.out"

# Keep only newest KEEP_FILES rotated logs per source
for stem in backend.log launchd.out.log launchd.err.log start.out; do
  ls -1t "$LOG_DIR/$stem".*.log 2>/dev/null | tail -n +$((KEEP_FILES + 1)) | xargs -I{} rm -f "{}" || true
done

echo "[rotate] Log rotation complete"
