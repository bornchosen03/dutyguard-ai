#!/usr/bin/env python3
"""Merge duty columns from PDF duties CSV into the canonical HTS CSV.

Reads:
 - `knowledge_base/live_tariffs.canonical.csv`
 - `knowledge_base/live_tariffs.from_pdf.duties.csv`

Writes:
 - `knowledge_base/live_tariffs.canonical.with_duties.csv`

Behavior:
 - Map duties by `hs6` from the duties CSV (first entry wins).
 - For each canonical row, attempt to get hs6 (from `_norm_hs6` or `col_1` tokens).
 - Add columns `general_rate`, `special_rate`, `column2_rate` if missing.
 - Fill empty rate columns from duties map when available.
"""
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / 'knowledge_base' / 'live_tariffs.canonical.csv'
DUTIES = ROOT / 'knowledge_base' / 'live_tariffs.from_pdf.duties.csv'
OUT = ROOT / 'knowledge_base' / 'live_tariffs.canonical.with_duties.csv'


def norm_code_from_str(s: str) -> str | None:
    if not s:
        return None
    digits = re.sub(r"\D", "", s)
    if len(digits) >= 6:
        return digits[:6]
    if len(digits) == 4:
        return digits.ljust(6, '0')
    return None


def hs_from_row(r: dict) -> str | None:
    # prefer internal _norm_hs6
    v = (r.get('_norm_hs6') or '').strip()
    if v:
        return norm_code_from_str(v)
    # try common columns
    for key in ('col_1', 'col_4', 'col_3'):
        v = (r.get(key) or '').strip()
        h = norm_code_from_str(v)
        if h:
            return h
    # search all values
    token_re = re.compile(r"(\d{1,2}(?:\.\d{2}){1,2}|\d{4,8})")
    for v in r.values():
        if not isinstance(v, str):
            continue
        m = token_re.search(v)
        if m:
            digits = re.sub(r"\D", "", m.group(1))
            if len(digits) >= 6:
                return digits[:6]
            if len(digits) == 4:
                return digits.ljust(6, '0')
    return None


def load_duties_map():
    m = {}
    if not DUTIES.exists():
        return m
    with DUTIES.open('r', encoding='utf-8', errors='ignore') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            hs = (r.get('hs6') or '').strip()
            if not hs:
                continue
            if hs not in m:
                m[hs] = r
    return m


def main():
    duties_map = load_duties_map()
    if not CANON.exists():
        print('Canonical CSV not found:', CANON)
        return 2

    with CANON.open('r', encoding='utf-8', errors='ignore') as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    # ensure duty columns exist
    for c in ('general_rate', 'special_rate', 'column2_rate'):
        if c not in fieldnames:
            fieldnames.append(c)

    filled = 0
    total = 0
    for r in rows:
        total += 1
        hs = hs_from_row(r)
        if not hs:
            continue
        d = duties_map.get(hs)
        if not d:
            continue
        # fill missing columns
        for col in ('general_rate', 'special_rate', 'column2_rate'):
            if not (r.get(col) or '').strip():
                val = d.get(col) or d.get(col.replace('_rate','rate')) or d.get('general_rate') or ''
                if val:
                    r[col] = val
                    filled += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: (v if v is not None else '') for k, v in r.items()})

    print(f'Wrote {OUT} ({len(rows)} rows), filled {filled} duty fields from duties CSV')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
