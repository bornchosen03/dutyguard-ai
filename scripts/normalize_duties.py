#!/usr/bin/env python3
"""Normalize duty tokens into structured columns.

Reads `knowledge_base/live_tariffs.canonical.with_duties.csv` and writes
`knowledge_base/live_tariffs.canonical.with_duties.normalized.csv` with
additional parsed columns for `general_rate`, `special_rate` and `column2_rate`.

This is a best-effort parser intended to extract common patterns like:
- percent: "3.4%" -> value=3.4, unit="%", type="percent"
- cents per kg: "31.4¢/kg" -> value=31.4, unit="¢/kg", type="specific"
- dollar per unit: "$1.03/kg" -> value=1.03, unit="$ / kg", type="specific"
- Free -> type="free"

Usage: python3 scripts/normalize_duties.py
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

IN_PATH = Path("knowledge_base/live_tariffs.canonical.with_duties.csv")
OUT_PATH = Path("knowledge_base/live_tariffs.canonical.with_duties.normalized.csv")

csv.field_size_limit(10 * 1024 * 1024)

PERCENT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*%")
CENTS_PER_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*¢\s*/\s*([^\s,;]+)")
DOLLAR_PER_RE = re.compile(r"\$\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*([^\s,;]+)")
NUMBER_PER_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*/\s*([^\s,;]+)")

def parse_rate(token: str) -> dict:
    token = (token or "").strip()
    out = {"raw": token, "value": None, "unit": None, "type": None}
    if not token:
        out["type"] = "empty"
        return out
    lower = token.lower()
    if "free" in lower:
        out["type"] = "free"
        out["value"] = 0.0
        out["unit"] = "free"
        return out

    m = PERCENT_RE.search(token)
    if m:
        out.update({"type": "percent", "value": float(m.group(1)), "unit": "%"})
        return out

    m = CENTS_PER_RE.search(token)
    if m:
        out.update({"type": "specific", "value": float(m.group(1)), "unit": f"¢/{m.group(2)}"})
        return out

    m = DOLLAR_PER_RE.search(token)
    if m:
        out.update({"type": "specific", "value": float(m.group(1)), "unit": f"$/{m.group(2)}"})
        return out

    m = NUMBER_PER_RE.search(token)
    if m:
        out.update({"type": "specific", "value": float(m.group(1)), "unit": f"/{m.group(2)}"})
        return out

    # Try to extract a plain number (fallback)
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", token)
    if m:
        out.update({"type": "numeric", "value": float(m.group(1)), "unit": None})
        return out

    out["type"] = "unknown"
    return out


def normalize_row(row: dict) -> dict:
    for col in ("general_rate", "special_rate", "column2_rate"):
        parsed = parse_rate(row.get(col, ""))
        row[f"{col}_value"] = parsed["value"]
        row[f"{col}_unit"] = parsed["unit"]
        row[f"{col}_type"] = parsed["type"]
        row[f"{col}_raw"] = parsed["raw"]
    return row


def main() -> int:
    if not IN_PATH.exists():
        print(f"Input file not found: {IN_PATH}", file=sys.stderr)
        return 2

    with IN_PATH.open("r", newline="", encoding="utf-8") as inf:
        reader = csv.DictReader(inf)
        rows = list(reader)
        if not rows:
            print("No rows found in input CSV.")

    # Prepare output fieldnames: existing + new parsed fields
    base_fields = reader.fieldnames or []
    extra = []
    for col in ("general_rate", "special_rate", "column2_rate"):
        extra += [f"{col}_value", f"{col}_unit", f"{col}_type", f"{col}_raw"]

    out_fields = list(base_fields) + extra

    parsed_count = 0
    fail_count = 0
    with OUT_PATH.open("w", newline="", encoding="utf-8") as outf:
        writer = csv.DictWriter(outf, fieldnames=out_fields)
        writer.writeheader()
        for r in rows:
            nr = normalize_row(r.copy())
            # simple success heuristic: any parsed type not unknown/empty
            if any(nr.get(f"{c}_type") not in ("unknown", "empty") for c in ("general_rate", "special_rate", "column2_rate")):
                parsed_count += 1
            else:
                fail_count += 1
            writer.writerow(nr)

    print(f"Wrote normalized CSV: {OUT_PATH} rows: {len(rows)} parsed_count: {parsed_count} fail_count: {fail_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
