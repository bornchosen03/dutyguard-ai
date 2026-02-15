#!/usr/bin/env python3
"""Simple batch processor for pilot batches.

Moves any JSON files from `backend/data/pilot_batches` to `backend/data/review_queue`
and creates an audit entry. Intended as a lightweight utility for processing queued
pilot onboarding files.

Usage:
    python3 scripts/process_pilot_batches.py
"""
from pathlib import Path
import json
import time
import hashlib

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "backend" / "data"
PILOT_DIR = DATA_DIR / "pilot_batches"
REVIEW_DIR = DATA_DIR / "review_queue"
AUDIT_PATH = DATA_DIR / "audit_trail.jsonl"

PILOT_DIR.mkdir(parents=True, exist_ok=True)
REVIEW_DIR.mkdir(parents=True, exist_ok=True)


def _append_audit(event_type: str, payload: dict):
    previous = ""
    if AUDIT_PATH.exists():
        with AUDIT_PATH.open("r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            if lines:
                try:
                    previous = json.loads(lines[-1]).get("event_hash", "")
                except Exception:
                    previous = ""
    event = {
        "event_type": event_type,
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "previous_hash": previous,
        "payload": payload,
    }
    event_hash = hashlib.sha256(json.dumps(event, sort_keys=True).encode("utf-8")).hexdigest()
    event["event_hash"] = event_hash
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def process_once():
    moved = 0
    for path in sorted(PILOT_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Skipping {path.name}: failed to parse JSON: {exc}")
            continue
        # construct review ticket id
        ticket_id = f"pilot_{int(time.time())}_{path.stem}"
        ticket = {
            "id": ticket_id,
            "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "open",
            "source": "pilot_batch",
            "payload": data,
        }
        out_path = REVIEW_DIR / f"{ticket_id}.json"
        out_path.write_text(json.dumps(ticket, indent=2), encoding="utf-8")
        _append_audit("pilot_batch_processed", {"ticket_id": ticket_id, "source_file": path.name})
        path.unlink()
        moved += 1
        print(f"Processed {path.name} -> {out_path.name}")
    if moved == 0:
        print("No pilot batches to process.")


if __name__ == "__main__":
    process_once()
