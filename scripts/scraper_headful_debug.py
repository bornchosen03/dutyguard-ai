import asyncio
from pathlib import Path
import json
from playwright.async_api import async_playwright

async def main():
    hs = "8471"
    url = f"https://hts.usitc.gov/view/{hs}"
    out_dir = Path(__file__).resolve().parent.parent / "knowledge_base"
    out_dir.mkdir(parents=True, exist_ok=True)
    har_path = out_dir / f"usitc_{hs}.headful.har"
    shot_path = out_dir / f"usitc_{hs}.headful.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(record_har_path=str(har_path))
        page = await context.new_page()
        print('Opening browser window (headful). You may see a window appear.')
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(5000)
        try:
            await page.screenshot(path=str(shot_path), full_page=True)
            print('Saved screenshot to', shot_path)
        except Exception as e:
            print('Screenshot failed:', e)
        await context.close()
        await browser.close()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
