#!/usr/bin/env python3
import os
import requests
import re
import csv
import sys

URL = 'https://learning.usitc.gov/hts-docs/documents/finalCopy.pdf'
OUT_DIR = os.path.join(os.getcwd(), 'knowledge_base')
PDF_PATH = os.path.join(OUT_DIR, 'finalCopy.pdf')
TEXT_PATH = os.path.join(OUT_DIR, 'finalCopy.txt')
CSV_PATH = os.path.join(OUT_DIR, 'finalcopy_extracted.csv')

os.makedirs(OUT_DIR, exist_ok=True)

print('Downloading', URL)
resp = requests.get(URL, stream=True, timeout=60)
resp.raise_for_status()
with open(PDF_PATH, 'wb') as fh:
    for chunk in resp.iter_content(8192):
        if chunk:
            fh.write(chunk)
print('Saved PDF to', PDF_PATH)

from pdfminer.high_level import extract_text
try:
    text = extract_text(PDF_PATH)
except Exception as e:
    print('Failed to extract text from PDF:', e)
    sys.exit(2)

with open(TEXT_PATH, 'w', encoding='utf-8') as fh:
    fh.write(text)
print('Saved extracted text to', TEXT_PATH)

# Naive extraction: find lines that contain 4- or 6-digit HS-like codes and write them
pattern = re.compile(r"\b\d{4,6}\b")
lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
rows = []
for ln in lines:
    codes = pattern.findall(ln)
    if codes:
        rows.append({'codes': ' '.join(codes), 'line': ln})

with open(CSV_PATH, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=['codes', 'line'])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print('Wrote', len(rows), 'extracted lines to', CSV_PATH)
print('Done')
