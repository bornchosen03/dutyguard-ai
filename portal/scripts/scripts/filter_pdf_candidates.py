#!/usr/bin/env python3
"""Filter noisy PDF-extracted tariff candidates.

Reads: `knowledge_base/live_tariffs.from_pdf.csv`
Writes: `knowledge_base/live_tariffs.from_pdf.filtered.csv` (and copies to original)

Heuristics applied:
 - Drop rows whose description is very short (< 3 words)
 - Drop rows whose description contains common footer/header noise
 - Drop rows where description is mostly digits or contains many CAS-like entries
 - Deduplicate on (hs6, normalized description)
"""
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IN_CSV = ROOT / 'knowledge_base' / 'live_tariffs.from_pdf.csv'
OUT_CSV = ROOT / 'knowledge_base' / 'live_tariffs.from_pdf.filtered.csv'

NOISE_PATTERNS = [
    re.compile(p, re.I) for p in [
        r"harmonized tariff schedule",
        r"goods provided for",
        r"compiler's note",
        r"con\.$",
        r"provided for in subheading",
        r"for purposes of",
        r"\bpage\b",
    ]
]


def is_mostly_digits(s: str) -> bool:
    s2 = re.sub(r"\D", "", s)
    if not s2:
        return False
    return (len(s2) / max(1, len(s))) > 0.6


def normalize_desc(s: str) -> str:
    s = s or ''
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def should_drop(desc: str) -> bool:
    if not desc:
        return True
    nd = normalize_desc(desc)
    words = nd.split()
    if len(words) < 3:
        return True
    for p in NOISE_PATTERNS:
        if p.search(nd):
            return True
    if is_mostly_digits(nd):
        return True
    # drop lines like "9823.04.01 9823.04.02 ..."
    if re.match(r"^(\d[\d\.\s,-]+)$", nd):
        return True
    return False


def main():
    if not IN_CSV.exists():
        print(f"Input CSV not found: {IN_CSV}")
        return 2

    csv.field_size_limit(10 * 1024 * 1024)

    kept = []
    seen = set()
    total = 0

    with IN_CSV.open('r', encoding='utf-8', errors='ignore') as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        for r in rows:
            total += 1
            hs = (r.get('hs6') or '').strip()
            desc = normalize_desc(r.get('description') or r.get('raw_block') or '')
            if should_drop(desc):
                continue
            key = (hs, re.sub(r"\W+", " ", desc).strip().lower())
            if key in seen:
                continue
            seen.add(key)
            kept.append({'hs6': hs, 'description': desc, 'raw_block': r.get('raw_block','')})

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['hs6','description','raw_block'])
        writer.writeheader()
        for r in kept:
            writer.writerow(r)

    # overwrite original to make downstream tools simple
    IN_CSV.unlink()
    OUT_CSV.rename(IN_CSV)

    print(f"Filtered {total} -> {len(kept)} rows; wrote {IN_CSV}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
