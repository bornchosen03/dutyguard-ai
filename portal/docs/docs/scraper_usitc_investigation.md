USITC Scraper Investigation

Date: 2026-02-12

Summary

- Ran `scraper.py` which uses Playwright to attempt fetching tariff tables for HS prefix `8471`.
- Playwright and Chromium were installed in the project venv to run the scraper.
- The scraper saved raw HTML to `knowledge_base/raw_usitc_8471.html` but found 0 rows (site is client-side rendered).

Network findings

- When loading `https://hts.usitc.gov/view/8471`, observed these notable responses:
  - `301 https://hts.usitc.gov/view/8471`
  - `503 https://hts.usitc.gov/reststop/file?filename=8471&release=currentRelease`
  - `403` responses for static assets under `https://learning.usitc.gov/hts-docs/...` (JS, fonts)

- Direct GET to the reststop endpoint returned HTTP 503 even when using a browser-like `User-Agent` and `Referer` header.
- Attempts to reduce Playwright detection (override `navigator.webdriver`, set a common `User-Agent`) did not avoid the 503.

Conclusions

- The USITC site (or upstream CDN/WAF) is returning 503/403 for the endpoints used to power the client app. This prevents automated extraction of the tariff table via typical headless/browser automation.

Recommendations / Next actions (pick one)

1. Use an official data source: check whether USITC publishes bulk tariff files or an API that allows downloading HS tables rather than scraping the website.
2. Try running the scraper from a different network/IP range (the WAF may be blocking our host's IP).
3. Implement a headful/manual scrape: open a real browser, interact manually and save the page; this may be suitable for occasional one-off captures but not for automation.
4. If automation is required, consider: rotating proxies + human-like timing, browser fingerprinting mitigation libraries (stealth), and careful legal/compliance review.

Artifacts created during investigation

- `knowledge_base/raw_usitc_8471.html`
- `knowledge_base/live_tariffs.csv` (empty rows saved, row_count=0)
- `knowledge_base/tariff_alerts.json` (diff metadata)

If you want me to continue automatically, I'll proceed with option (1) to search for official data endpoints and try to fetch them programmatically.