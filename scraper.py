import asyncio
import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parent
KNOWLEDGE_BASE = ROOT / "knowledge_base"
KNOWLEDGE_BASE.mkdir(parents=True, exist_ok=True)

LIVE_TARIFFS_CSV = KNOWLEDGE_BASE / "live_tariffs.csv"
ALERTS_JSON = KNOWLEDGE_BASE / "tariff_alerts.json"


@dataclass(frozen=True)
class ScrapeResult:
    source: str
    hs_prefix: str
    rows: list[list[str]]
    fetched_at_utc: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def fetch_usitc_tariff_data(hs_code_prefix: str) -> ScrapeResult:
    """Fetches public tariff table rows from the US HTS site.

    This is a best-effort scraper (site markup can change). It uses Playwright
    to behave like a browser, which helps with sites that block simple requests.
    """

    hs_code_prefix = hs_code_prefix.strip().replace("/", "")
    if not hs_code_prefix:
        raise ValueError("hs_code_prefix is required")

    url = f"https://hts.usitc.gov/view/{hs_code_prefix}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"🔍 USITC: searching HS prefix: {hs_code_prefix}")
        await page.goto(url, wait_until="domcontentloaded")

        # The site layout changes over time; we try a couple selectors.
        await page.wait_for_timeout(800)

        table = None
        for selector in ["table", ".table", ".table-responsive table"]:
            table = await page.query_selector(selector)
            if table:
                break

        rows: list[list[str]] = []
        if table:
            tr_nodes = await table.query_selector_all("tr")
            for tr in tr_nodes:
                text = (await tr.inner_text()).strip()
                if not text:
                    continue
                # split on tabs/newlines; keep non-empty
                parts = [p.strip() for p in text.replace("\n", "\t").split("\t") if p.strip()]
                if len(parts) >= 2:
                    rows.append(parts)

        await browser.close()

    return ScrapeResult(
        source="USITC",
        hs_prefix=hs_code_prefix,
        rows=rows,
        fetched_at_utc=_utc_now_iso(),
    )


def _write_csv(path: Path, rows: Iterable[Iterable[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(list(row))


def save_to_intelligence_base(result: ScrapeResult) -> dict:
    """Save scraped rows to knowledge_base/live_tariffs.csv.

    Also writes a lightweight metadata header row at the top so downstream code
    can see source and timestamp.
    """

    header = [
        "_meta_source",
        "_meta_hs_prefix",
        "_meta_fetched_at_utc",
        "col_1",
        "col_2",
        "col_3",
        "col_4",
        "col_5",
        "col_6",
        "col_7",
        "col_8",
    ]

    out_rows: list[list[str]] = [header]
    for r in result.rows:
        padded = list(r)[:8]
        while len(padded) < 8:
            padded.append("")
        out_rows.append([result.source, result.hs_prefix, result.fetched_at_utc, *padded])

    csv_bytes = "\n".join([",".join([_csv_escape(c) for c in row]) for row in out_rows]).encode("utf-8")
    LIVE_TARIFFS_CSV.write_bytes(csv_bytes)

    meta = {
        "source": result.source,
        "hs_prefix": result.hs_prefix,
        "fetched_at_utc": result.fetched_at_utc,
        "row_count": len(result.rows),
        "csv_path": str(LIVE_TARIFFS_CSV),
        "csv_sha256": _sha256_bytes(csv_bytes),
    }

    print("✅ Knowledge Base Updated:", json.dumps(meta, indent=2))
    return meta


def _csv_escape(value: str) -> str:
    value = value or ""
    if any(ch in value for ch in [",", "\n", "\r", '"']):
        return '"' + value.replace('"', '""') + '"'
    return value


def diff_and_alert(previous_csv: Optional[Path], current_csv: Path) -> dict:
    """Very small diff scaffold.

    For now: if the CSV hash changed, write an alerts JSON file.
    Later: parse and compare specific duty-rate columns and trigger emails.
    """

    prev_hash = None
    if previous_csv and previous_csv.exists():
        prev_hash = _sha256_bytes(previous_csv.read_bytes())

    curr_hash = _sha256_bytes(current_csv.read_bytes())

    changed = prev_hash is not None and prev_hash != curr_hash
    alert = {
        "changed": changed,
        "previous_sha256": prev_hash,
        "current_sha256": curr_hash,
        "checked_at_utc": _utc_now_iso(),
    }

    ALERTS_JSON.write_text(json.dumps(alert, indent=2), encoding="utf-8")
    if changed:
        print("⚠️ Tariff data changed — alert written to", str(ALERTS_JSON))
    else:
        print("✅ No change detected — alert written to", str(ALERTS_JSON))

    return alert


async def main() -> int:
    hs_prefix = "8471"
    prev_tmp = None
    if LIVE_TARIFFS_CSV.exists():
        prev_tmp = KNOWLEDGE_BASE / "live_tariffs.previous.csv"
        prev_tmp.write_bytes(LIVE_TARIFFS_CSV.read_bytes())

    result = await fetch_usitc_tariff_data(hs_prefix)
    save_to_intelligence_base(result)
    diff_and_alert(prev_tmp, LIVE_TARIFFS_CSV)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
