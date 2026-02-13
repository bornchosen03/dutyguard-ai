#!/usr/bin/env python3
"""Parse `knowledge_base/finalCopy.txt` into a normalized CSV of HS6 entries.

This is a heuristic parser: it finds numeric tariff codes in the text (with or
without dots), normalizes them to a 6-digit HS code, and groups the following
lines as the description/notes until the next code is encountered.

Output: `knowledge_base/live_tariffs.from_pdf.csv` with columns:
  - hs6: first 6 digits of the found code
  - description: joined description text (single-line, trimmed)
  - raw_block: the original text block captured (multi-line)

Run: `python3 scripts/parse_finalcopy_normalized.py`
"""
import csv
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IN_TXT = ROOT / "knowledge_base" / "finalCopy.txt"
OUT_CSV = ROOT / "knowledge_base" / "live_tariffs.from_pdf.csv"


def find_code_token(s: str):
    # Find tokens like 0406.20.48 or 98230401 or 9823.04.01 etc.
    # Return normalized 6-digit HS (first six digits) or None
    token_re = re.compile(r"(\d{1,2}(?:\.\d{2}){1,2}|\d{6,8})")
    m = token_re.search(s)
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    if len(digits) < 6:
        return None
    hs6 = digits[:6]
    return hs6


def parse_blocks(lines):
    blocks = []
    current = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            # preserve blank lines in block as newline markers
            if current is not None:
                current['raw_lines'].append('')
            continue

        code = find_code_token(line)
        if code:
            # start a new block
            if current is not None:
                blocks.append(current)
            # description is remainder of line after the match
            # find where match ends
            m = re.search(r"(\d{1,2}(?:\.\d{2}){1,2}|\d{6,8})", line)
            desc_part = line[m.end():].strip() if m else ''
            current = {
                'hs6': code,
                'raw_lines': [line],
                'desc_parts': [desc_part] if desc_part else []
            }
        else:
            if current is None:
                # skip preface text until first code
                continue
            current['raw_lines'].append(line)
            current['desc_parts'].append(line)

    if current is not None:
        blocks.append(current)

    return blocks


def normalize_description(desc_parts):
    # Join parts, collapse whitespace and trim
    txt = '\n'.join(p for p in desc_parts if p)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


def main():
    if not IN_TXT.exists():
        print(f"Missing input text: {IN_TXT}. Run the PDF extractor first.")
        return 2

    with IN_TXT.open('r', encoding='utf-8', errors='ignore') as fh:
        lines = fh.readlines()

    print(f"Parsing {len(lines)} lines from {IN_TXT}")
    blocks = parse_blocks(lines)
    print(f"Found {len(blocks)} candidate blocks")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open('w', newline='', encoding='utf-8') as outfh:
        writer = csv.DictWriter(outfh, fieldnames=['hs6', 'description', 'raw_block'])
        writer.writeheader()
        for b in blocks:
            hs6 = b['hs6']
            description = normalize_description(b.get('desc_parts', []))
            raw_block = '\n'.join(b.get('raw_lines', []))
            writer.writerow({'hs6': hs6, 'description': description, 'raw_block': raw_block})

    print(f"Wrote normalized CSV: {OUT_CSV}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
