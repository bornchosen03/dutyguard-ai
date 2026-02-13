#!/usr/bin/env python3
"""Reconcile `knowledge_base/live_tariffs.csv` with `knowledge_base/live_tariffs.from_pdf.csv`.

Outputs:
 - `knowledge_base/live_tariffs.merged.csv` : existing rows annotated with PDF match info
 - `knowledge_base/tariff_reconcile_report.txt` : short human-readable summary

Algorithm (heuristic):
 - Normalize HS codes by removing non-digits and taking first 6 digits.
 - Match PDF rows (hs6) to existing rows by normalized code.
 - Annotate existing rows with `pdf_description` and `pdf_match` flags.
 - Append PDF-only rows at the end with `_meta_source=PDF`.
"""
import csv
import json
import re
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
EXISTING = ROOT / 'knowledge_base' / 'live_tariffs.csv'
PDF_SRC = ROOT / 'knowledge_base' / 'live_tariffs.from_pdf.csv'
OUT_MERGED = ROOT / 'knowledge_base' / 'live_tariffs.merged.csv'
REPORT = ROOT / 'knowledge_base' / 'tariff_reconcile_report.txt'


def norm_hs(code: str) -> str | None:
    if not code:
        return None
    digits = re.sub(r"\D", "", code)
    if len(digits) < 6:
        return None
    return digits[:6]


def extract_code_from_row(r: dict) -> str | None:
    """Search all columns in a CSV row dict for the first tariff-like token."""
    token_re = re.compile(r"(\d{1,2}(?:\.\d{2}){1,2}|\d{4,8})")
    for v in r.values():
        if not isinstance(v, str):
            continue
        m = token_re.search(v)
        if m:
            digits = re.sub(r"\D", "", m.group(1))
            if len(digits) >= 6:
                return digits[:6]
            if len(digits) >= 4:
                return digits[:4]
    return None


def load_pdf_map():
    pdf_map = {}
    if not PDF_SRC.exists():
        print(f"No PDF-derived CSV at {PDF_SRC}")
        return pdf_map
    # increase CSV field size limit to handle large raw_block fields
    try:
        csv.field_size_limit(10 * 1024 * 1024)
    except Exception:
        try:
            csv.field_size_limit(sys.maxsize)
        except Exception:
            pass
    with PDF_SRC.open('r', encoding='utf-8', errors='ignore') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            hs = r.get('hs6') or r.get('hs')
            if not hs:
                continue
            hs6 = norm_hs(hs)
            if not hs6:
                continue
            pdf_map.setdefault(hs6, []).append(r)
    return pdf_map


def find_pdf_entries_for_hs(hs6: str, pdf_map: dict):
    """Find PDF entries for a given normalized hs6.

    Strategy:
      1. Exact 6-digit match
      2. Match by 4-digit prefix (collect all pdf entries whose key startswith hs4)
    """
    if not hs6:
        return None
    # try exact 6-digit
    if hs6 in pdf_map:
        return pdf_map[hs6]
    # try 4-digit
    hs4 = hs6[:4]
    candidates = []
    for k, v in pdf_map.items():
        if k.startswith(hs4):
            candidates.extend(v)
    if candidates:
        return candidates
    # try 2-digit chapter
    hs2 = hs6[:2]
    for k, v in pdf_map.items():
        if k.startswith(hs2):
            candidates.extend(v)
    return candidates if candidates else None


def main():
    pdf_map = load_pdf_map()
    existing_rows = []
    fieldnames = None
    existing_hs_set = set()

    if not EXISTING.exists():
        print(f"Existing CSV missing: {EXISTING}")
        return 2

    with EXISTING.open('r', encoding='utf-8', errors='ignore') as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        # add annotation columns
        if 'pdf_match' not in fieldnames:
            fieldnames += ['pdf_match', 'pdf_description', 'description_differs']
        for r in reader:
            # try to extract a tariff code from any column of the existing CSV row
            hs_candidate = extract_code_from_row(r)
            hs6 = None
            if hs_candidate and len(hs_candidate) >= 6:
                hs6 = hs_candidate[:6]
            elif hs_candidate and len(hs_candidate) == 4:
                # expand 4-digit to 6-digit prefix by padding with zeros for matching
                hs6 = hs_candidate.ljust(6, '0')
            r['_norm_hs6'] = hs6
            if hs6:
                existing_hs_set.add(hs6)
            # attach pdf info if present
            pdf_entries = find_pdf_entries_for_hs(hs6, pdf_map) if hs6 else None
            if pdf_entries:
                # use the first PDF description
                pdf_desc = pdf_entries[0].get('description','')
                r['pdf_match'] = '1'
                r['pdf_description'] = pdf_desc
                # compare description to best-effort existing description column (col_3)
                existing_desc = (r.get('col_3') or '')
                r['description_differs'] = '1' if existing_desc and pdf_desc and existing_desc.strip() != pdf_desc.strip() else '0'
            else:
                r['pdf_match'] = '0'
                r['pdf_description'] = ''
                r['description_differs'] = '0'
            existing_rows.append(r)

    # PDF-only entries
    pdf_only = []
    # Use hierarchical matching to find pdf-only keys: keys that do not match any existing hs6 by 6-digit or 4-digit prefix
    matched_pdf_keys = set()
    for r in existing_rows:
        nh = r.get('_norm_hs6')
        if nh:
            # if there are any pdf entries matching this existing normalized HS6 (or hs4 prefix), mark those pdf keys as matched
            hits = find_pdf_entries_for_hs(nh, pdf_map)
            if hits:
                # determine which pdf_map keys were used
                for k in pdf_map.keys():
                    if k.startswith(nh[:4]):
                        matched_pdf_keys.add(k)

    for hs6, entries in pdf_map.items():
        if hs6 in matched_pdf_keys:
            continue
        # create a synthetic row for each PDF entry (use first entry)
        first = entries[0]
        new_row = {k: '' for k in fieldnames}
        new_row['_norm_hs6'] = hs6
        new_row['pdf_match'] = '0'
        new_row['pdf_description'] = first.get('description','')
        new_row['description_differs'] = '0'
        # place key fields in likely columns
        new_row['col_1'] = hs6
        new_row['col_3'] = first.get('description','')
        new_row['_meta_source'] = 'PDF'
        pdf_only.append(new_row)

    merged = existing_rows + pdf_only

    # write merged CSV
    with OUT_MERGED.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in merged:
            # remove internal keys
            out = {k: (v if v is not None else '') for k,v in r.items() if k in fieldnames}
            writer.writerow(out)

    # simple report
    total_existing = len(existing_rows)
    total_pdf = sum(len(v) for v in pdf_map.values())
    matched = sum(1 for r in existing_rows if r.get('pdf_match') == '1')
    pdf_only_count = len(pdf_only)

    report = {
        'total_existing_rows': total_existing,
        'total_pdf_rows': total_pdf,
        'matched_existing_with_pdf': matched,
        'pdf_only_new_entries': pdf_only_count,
    }

    with REPORT.open('w', encoding='utf-8') as fh:
        fh.write(json.dumps(report, indent=2))

    print('Wrote merged CSV:', OUT_MERGED)
    print('Wrote report:', REPORT)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
