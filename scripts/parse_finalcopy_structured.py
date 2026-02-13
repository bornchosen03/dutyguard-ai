#!/usr/bin/env python3
"""
Simple heuristic parser to convert the naive PDF extraction
(`knowledge_base/finalcopy_extracted.csv`) into a structured CSV
with one HTS 6-digit heading per row and a combined description.

This is a pragmatic, best-effort approach that groups lines between
detected 6-digit HTS headings. It produces `knowledge_base/finalcopy_structured.csv`.
"""
import csv
import os
import re

WORKDIR = os.getcwd()
IN_CSV = os.path.join(WORKDIR, 'knowledge_base', 'finalcopy_extracted.csv')
OUT_CSV = os.path.join(WORKDIR, 'knowledge_base', 'finalcopy_structured.csv')

code_re = re.compile(r"\b(\d{6})\b")

if not os.path.exists(IN_CSV):
    print('Input CSV not found:', IN_CSV)
    raise SystemExit(1)

entries = []
current = None

with open(IN_CSV, newline='', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        line = (row.get('line') or '').strip()
        codes_field = row.get('codes') or ''
        # search for a 6-digit HS within the codes field first, then the line
        m = code_re.search(codes_field) or code_re.search(line)
        if m:
            code = m.group(1)
            # start a fresh entry
            if current:
                entries.append(current)
            current = {'hs6': code, 'description_lines': [line]}
        else:
            # append to current entry description if present
            if current:
                # avoid duplicating identical lines
                if line and (not current['description_lines'] or line != current['description_lines'][-1]):
                    current['description_lines'].append(line)
            else:
                # no current code — skip or accumulate (skip for now)
                continue

if current:
    entries.append(current)

# write structured CSV
with open(OUT_CSV, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=['hs6', 'description'])
    writer.writeheader()
    for e in entries:
        desc = ' '.join(e['description_lines'])
        writer.writerow({'hs6': e['hs6'], 'description': desc})

print('Wrote', len(entries), 'entries to', OUT_CSV)
