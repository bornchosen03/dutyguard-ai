#!/usr/bin/env python3
"""Capture network requests/responses when loading a USITC HS page.

Saves JSON responses and large text responses to `knowledge_base/network_{hs}.jsonl`.
"""
import asyncio
import json
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright


OUT_DIR = Path("knowledge_base")
OUT_DIR.mkdir(parents=True, exist_ok=True)


async def capture(hs_prefix: str) -> int:
    url = f"https://hts.usitc.gov/view/{hs_prefix}"
    out_file = OUT_DIR / f"network_{hs_prefix}.jsonl"
    print("Capturing network for:", url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        captured = []

        async def on_response(response):
            try:
                req = response.request
                r = {
                    "url": response.url,
                    "status": response.status,
                    "request_method": req.method,
                    "request_url": req.url,
                    "resource_type": req.resource_type,
                    "headers": dict(response.headers),
                }

                # Try to parse JSON bodies
                ctype = response.headers.get("content-type", "").lower()
                body: Any = None
                if "application/json" in ctype:
                    try:
                        body = await response.json()
                        r["body_type"] = "json"
                        r["body"] = body
                    except Exception:
                        r["body_type"] = "json_failed"
                else:
                    text = await response.text()
                    if len(text) > 800:
                        r["body_type"] = "text"
                        r["body_snippet"] = text[:2000]
                captured.append(r)
                # append to file incrementally
                with out_file.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(r) + "\n")
            except Exception as e:
                print("on_response error:", e)

        page.on("response", on_response)

        # also capture console for hints
        page.on("console", lambda msg: print(f"[console] {msg.type}: {msg.text}"))

        await page.goto(url, wait_until="networkidle")
        # wait a bit for late XHRs
        await page.wait_for_timeout(2000)

        await browser.close()

    print("Saved network captures to", str(out_file))
    return 0


if __name__ == "__main__":
    import sys

    prefix = sys.argv[1] if len(sys.argv) > 1 else "8471"
    raise SystemExit(asyncio.run(capture(prefix)))
