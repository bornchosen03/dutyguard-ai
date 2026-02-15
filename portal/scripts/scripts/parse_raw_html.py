#!/usr/bin/env python3
"""Lightweight parser for saved USITC raw HTML files.

Uses Python's built-in HTMLParser to extract table rows (tr/td/th) without
external dependencies. Prints summaries and writes CSVs if rows are found.
"""
import csv
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import List


class TableHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_tr = False
        self.in_td = False
        self.current_td = ""
        self.current_row: List[str] = []
        self.rows: List[List[str]] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            self.in_table = True
        elif tag == "tr" and self.in_table:
            self.in_tr = True
            self.current_row = []
        elif tag in ("td", "th") and self.in_tr:
            self.in_td = True
            self.current_td = ""

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "table":
            self.in_table = False
        elif tag == "tr":
            if self.in_tr:
                if any(cell.strip() for cell in self.current_row):
                    self.rows.append(list(self.current_row))
                self.current_row = []
            self.in_tr = False
        elif tag in ("td", "th"):
            if self.in_td:
                self.current_row.append(self.current_td.strip())
            self.in_td = False

    def handle_data(self, data):
        if self.in_td:
            self.current_td += data


def parse_file(path: Path) -> List[List[str]]:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    parser = TableHTMLParser()
    parser.feed(txt)
    return parser.rows


def write_csv(path: Path, rows: List[List[str]]):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(r)


def main(paths: List[str]):
    root = Path("knowledge_base")
    for p in paths:
        fp = Path(p)
        if not fp.exists():
            print(f"[skip] {fp} not found")
            continue
        print(f"\n[inspect] {fp}")
        rows = parse_file(fp)
        print(f"  tables found rows: {len(rows)}")
        if rows:
            sample = rows[:3]
            for i, r in enumerate(sample, 1):
                print(f"    row {i}: {r}")
            out_csv = root / (fp.stem + ".parsed.csv")
            write_csv(out_csv, rows)
            print(f"  -> wrote parsed CSV: {out_csv}")
        else:
            # if no rows, print snippets where <table> appears to help debugging
            txt = fp.read_text(encoding="utf-8", errors="ignore")
            idx = txt.lower().find("<table")
            if idx >= 0:
                start = max(0, idx - 200)
                end = min(len(txt), idx + 2000)
                print("  <table> snippet:\n" + txt[start:end])
            else:
                print("  no <table> tag found in file")


if __name__ == "__main__":
    args = sys.argv[1:] or ["knowledge_base/raw_usitc_0101.html", "knowledge_base/raw_usitc_8471.html", "knowledge_base/raw_usitc_8703.html"]
    main(args)
