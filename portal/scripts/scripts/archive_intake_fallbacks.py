#!/usr/bin/env python3
"""Archive the intake fallback JSONL file after alerts are sent.

Usage: python3 scripts/archive_intake_fallbacks.py [path/to/intake_notifications.jsonl]

This moves the file to `backend/data/intake_notifications.YYYYmmddTHHMMSS.jsonl`
and leaves an empty file at the original path so new fallbacks accumulate.
"""
from pathlib import Path
from datetime import datetime
import shutil
import sys


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('backend/data/intake_notifications.jsonl')
    if not src.exists():
        print(f"Source file does not exist: {src}")
        return 2

    dest_dir = src.parent
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    dest = dest_dir / f"intake_notifications.{ts}.jsonl"

    # Move the file atomically
    shutil.move(str(src), str(dest))
    # Create an empty placeholder file with same permissions
    src.touch()

    print(f"Archived {src} -> {dest}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
