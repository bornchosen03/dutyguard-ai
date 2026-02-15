import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright


async def main():
    hs = "8471"
    url = f"https://hts.usitc.gov/view/{hs}"
    out_dir = Path(__file__).resolve().parent.parent / "knowledge_base"
    out_dir.mkdir(parents=True, exist_ok=True)
    har_path = out_dir / f"usitc_{hs}.har"
    reqs_path = out_dir / f"usitc_{hs}_requests.json"

    reqs = []
    print(f"Capturing network activity for: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(record_har_path=str(har_path))
        page = await context.new_page()

        page.on("request", lambda r: reqs.append({"url": r.url, "method": r.method, "resource_type": r.resource_type}))

        await page.goto(url, wait_until="networkidle")
        # Wait a bit more for XHRs that may fire after load
        await page.wait_for_timeout(3000)

        await context.close()
        await browser.close()

    reqs_path.write_text(json.dumps(reqs, indent=2), encoding="utf-8")
    print("Wrote HAR to:", har_path)
    print("Wrote captured requests to:", reqs_path)

    # Summarize likely API/XHR endpoints
    candidates = [r for r in reqs if r.get("resource_type") in ("xhr", "fetch") or ("/api/" in r.get("url", "") or r.get("url", "").endswith('.json'))]
    print(f"Found {len(candidates)} candidate XHR/fetch requests:")
    for c in candidates[:20]:
        print(" -", c["method"], c["url"])


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
