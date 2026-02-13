#!/usr/bin/env python3
"""Run scraper for a small batch of HS prefixes and save per-prefix CSV + alert.

Usage: ./scripts/run_scraper_batch.py
"""
import asyncio
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

from scraper import fetch_usitc_tariff_data


ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "knowledge_base"
KB.mkdir(parents=True, exist_ok=True)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def _csv_escape(value: str) -> str:
    value = value or ""
    if any(ch in value for ch in [",", "\n", "\r", '"']):
        return '"' + value.replace('"', '""') + '"'
    return value


async def run_prefix(hs_prefix: str) -> dict:
    result = await fetch_usitc_tariff_data(hs_prefix)

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
    for r in result.rows:
        padded = list(r)[:8]
        while len(padded) < 8:
            padded.append("")
        out_rows.append([result.source, result.hs_prefix, result.fetched_at_utc, *padded])

    csv_bytes = "\n".join([",".join([_csv_escape(c) for c in row]) for row in out_rows]).encode("utf-8")
    csv_path = KB / f"live_tariffs_{hs_prefix}.csv"
    csv_path.write_bytes(csv_bytes)

    alert = {
        "source": result.source,
        "hs_prefix": result.hs_prefix,
        "fetched_at_utc": result.fetched_at_utc,
        "row_count": len(result.rows),
        "csv_path": str(csv_path),
        "csv_sha256": _sha256_bytes(csv_bytes),
        "checked_at_utc": _utc_now_iso(),
    }

    alert_path = KB / f"tariff_alert_{hs_prefix}.json"
    alert_path.write_text(json.dumps(alert, indent=2), encoding="utf-8")

    print(f"Saved {csv_path} ({alert['row_count']} rows), alert -> {alert_path}")
    return {"hs_prefix": hs_prefix, "row_count": alert["row_count"], "csv": str(csv_path), "alert": str(alert_path)}


async def main() -> int:
    prefixes = ["0101", "8471", "8703"]
    results = []
    for p in prefixes:
        try:
            res = await run_prefix(p)
            results.append(res)
        except Exception as e:
            print(f"Error fetching {p}: {e}")

    print("\nBatch complete. Summary:")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
