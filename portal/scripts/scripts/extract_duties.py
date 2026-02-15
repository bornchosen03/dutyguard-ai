#!/usr/bin/env python3
"""Heuristically extract duty/rate columns from PDF-derived tariff blocks.

Reads: `knowledge_base/live_tariffs.from_pdf.csv`
Writes: `knowledge_base/live_tariffs.from_pdf.duties.csv`

Heuristics (best-effort):
 - Find percent rates (e.g. '1.6%', '6%') and cents/kg patterns (e.g. '1¢/kg')
 - If multiple rate-like tokens found, assign in order: general_rate, special_rate, column2_rate
 - Recognize 'Free' as a rate
 - Clean results to short strings
"""
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IN_CSV = ROOT / 'knowledge_base' / 'live_tariffs.from_pdf.csv'
OUT_CSV = ROOT / 'knowledge_base' / 'live_tariffs.from_pdf.duties.csv'

PERCENT_RE = re.compile(r"\b\d{1,2}(?:\.\d+)?\s*%")
CENTS_PER_KG_RE = re.compile(r"\d+(?:\.\d+)?\s*¢/?kg")
FREE_RE = re.compile(r"\bFree\b", re.I)


def find_rate_tokens(text: str):
    t = text or ''
    tokens = []
    # Free
    if FREE_RE.search(t):
        tokens.append('Free')
    # cents/kg
    for m in CENTS_PER_KG_RE.finditer(t):
        tokens.append(m.group(0).strip())
    # percent
    for m in PERCENT_RE.finditer(t):
        tokens.append(m.group(0).strip())
    # if none found, try to find patterns like '1¢/kg + 1.6%'
    if not tokens:
        m = re.search(r"(\d+\s*¢/?kg).*(\d{1,2}(?:\.\d+)?\s*%)", t)
        if m:
            tokens.extend([m.group(1).strip(), m.group(2).strip()])
    return tokens


def normalize_token(tok: str) -> str:
    return re.sub(r"\s+", " ", tok).strip()


def main():
    if not IN_CSV.exists():
        print('Input PDF-derived CSV not found:', IN_CSV)
        return 2

    csv.field_size_limit(10 * 1024 * 1024)
    out_rows = []
    with IN_CSV.open('r', encoding='utf-8', errors='ignore') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            hs = (r.get('hs6') or '').strip()
            desc = (r.get('description') or r.get('raw_block') or '').strip()
            tokens = find_rate_tokens(desc)
            tokens = [normalize_token(t) for t in tokens]
            general = tokens[0] if len(tokens) > 0 else ''
            special = tokens[1] if len(tokens) > 1 else ''
            column2 = tokens[2] if len(tokens) > 2 else ''
            out_rows.append({'hs6': hs, 'description': desc, 'general_rate': general, 'special_rate': special, 'column2_rate': column2})

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['hs6','description','general_rate','special_rate','column2_rate'])
        writer.writeheader()
        for row in out_rows:
            writer.writerow(row)

    print('Wrote duties CSV:', OUT_CSV, 'rows:', len(out_rows))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
