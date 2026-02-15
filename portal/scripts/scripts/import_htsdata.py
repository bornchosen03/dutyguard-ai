#!/usr/bin/env python3
"""Import and normalize a user-provided HTS CSV into the project's live_tariffs.csv

Usage: python scripts/import_htsdata.py

This script will:
- backup existing `knowledge_base/live_tariffs.csv` to `knowledge_base/live_tariffs.previous.csv`
- read `knowledge_base/htsdata.csv`
- write `knowledge_base/live_tariffs.csv` with the same metadata header used by the scraper
- call `scraper.diff_and_alert` to detect changes and write `knowledge_base/tariff_alerts.json`
"""
from pathlib import Path
import csv
import shutil
import json
import hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "knowledge_base"
KB.mkdir(parents=True, exist_ok=True)

SRC = KB / "htsdata.csv"
LIVE = KB / "live_tariffs.csv"
PREV = KB / "live_tariffs.previous.csv"

def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat()

def _csv_escape(value: str) -> str:
    value = value or ""
    if any(ch in value for ch in [",", "\n", "\r", '"']):
        return '"' + value.replace('"', '""') + '"'
    return value

def import_csv():
    if not SRC.exists():
        print(f"[import] Source not found: {SRC}")
        return 2

    if LIVE.exists():
        shutil.copy2(LIVE, PREV)
        print(f"[import] Backed up existing LIVE CSV to {PREV}")

    rows = []
    with SRC.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        for r in reader:
            # skip completely empty rows
            if not any(cell.strip() for cell in r):
                continue
            rows.append([cell.strip() for cell in r])

    # Build output rows with meta header then padded columns up to 8
    header = [
        "_meta_source",
        "_meta_hs_prefix",
        "_meta_fetched_at_utc",
        "col_1",
        "col_2",
        "col_3",
        "col_4",
        "col_5",
        "col_6",
        "col_7",
        "col_8",
    ]

    out_rows = [header]
    fetched_at = _utc_now_iso()

    for r in rows:
        # Attempt to infer hs_prefix from first column if it looks numeric
        hs_prefix = ""
        if len(r) >= 1 and r[0].replace('.', '').isdigit():
            hs_prefix = r[0]
        padded = list(r)[:8]
        while len(padded) < 8:
            padded.append("")
        out_rows.append(["IMPORT", hs_prefix, fetched_at, *padded])

    csv_bytes = "\n".join([",".join([_csv_escape(c) for c in row]) for row in out_rows]).encode("utf-8")
    LIVE.write_bytes(csv_bytes)
    print(f"[import] Wrote {LIVE} ({len(out_rows)-1} data rows)")

    # Use local scraper.diff_and_alert to compute diff and alerts
    try:
        import sys
        # Ensure repo root is on sys.path so local modules import reliably
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        import scraper
        prev_path = PREV if PREV.exists() else None
        alert = scraper.diff_and_alert(prev_path, LIVE)
        print("[import] diff_and_alert result:", json.dumps(alert, indent=2))
    except Exception as e:
        print("[import] Warning: unable to run scraper.diff_and_alert:", e)

    return 0

if __name__ == '__main__':
    raise SystemExit(import_csv())
