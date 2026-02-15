#!/usr/bin/env python3
"""Produce a canonical merged HTS CSV from `live_tariffs.merged.csv`.

Rules:
 - Normalize HS key from `col_1` if present, otherwise from `_norm_hs6`.
 - Prefer rows that are not `_meta_source=PDF` (i.e., existing/import rows).
 - If multiple rows for same HS, pick the preferred one; otherwise first seen.

Writes: `knowledge_base/live_tariffs.canonical.csv`
"""
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IN_MERGED = ROOT / 'knowledge_base' / 'live_tariffs.merged.csv'
OUT_CANON = ROOT / 'knowledge_base' / 'live_tariffs.canonical.csv'


def norm_from_row(r):
    # try _norm_hs6
    v = r.get('_norm_hs6') or ''
    if v:
        return re.sub(r"\D", "", v)[:6]
    # try col_1
    v = r.get('col_1') or ''
    v = re.sub(r"\D", "", v)
    if len(v) >= 6:
        return v[:6]
    if len(v) == 4:
        return v.ljust(6, '0')
    return None


def main():
    if not IN_MERGED.exists():
        print('Merged CSV missing:', IN_MERGED)
        return 2

    with IN_MERGED.open('r', encoding='utf-8', errors='ignore') as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    chosen = {}
    for r in rows:
        key = norm_from_row(r)
        if not key:
            continue
        prefer_existing = (r.get('_meta_source') or '').upper() != 'PDF'
        if key not in chosen:
            chosen[key] = r
            chosen[key]['_chosen_reason'] = 'first'
            continue
        # if current chosen is PDF and this row is existing, replace
        cur = chosen[key]
        cur_pdf = (cur.get('_meta_source') or '').upper() == 'PDF'
        if cur_pdf and prefer_existing:
            chosen[key] = r
            chosen[key]['_chosen_reason'] = 'prefer_existing'

    # write canonical CSV
    out_fields = fieldnames + ['_chosen_reason'] if '_chosen_reason' not in fieldnames else fieldnames
    with OUT_CANON.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=out_fields)
        writer.writeheader()
        for k, r in sorted(chosen.items()):
            row = {fn: r.get(fn, '') for fn in out_fields}
            writer.writerow(row)

    print('Wrote canonical CSV:', OUT_CANON, 'rows:', len(chosen))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
