#!/usr/bin/env python3
"""
Validate proxies listed in the file referenced by `PROXY_LIST_FILE` env or
`.env`. Writes valid proxies (http/https) to `backend/proxies.valid.txt`.

This is a lightweight health-check: each proxy is used to fetch
https://httpbin.org/ip with a short timeout. Proxies that return a 200 are
kept. Commented lines and non-http(s) schemes are ignored.
"""

import os
import sys
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROXY_FILE = ROOT / "backend" / "proxies.txt"
OUTPUT_FILE = ROOT / "backend" / "proxies.valid.txt"


def load_env_file(path: Path):
    env = {}
    if path.exists():
        for ln in path.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def main() -> int:
    # prefer explicit env var
    proxy_file = os.environ.get("PROXY_LIST_FILE")
    if not proxy_file:
        # try .env
        env_path = ROOT / ".env"
        if env_path.exists():
            env = load_env_file(env_path)
            proxy_file = env.get("PROXY_LIST_FILE")
    if not proxy_file:
        proxy_file = str(DEFAULT_PROXY_FILE)

    proxy_path = Path(proxy_file)
    if not proxy_path.exists():
        print(f"No proxy list found at {proxy_path}; nothing to validate.")
        # ensure output file is removed
        try:
            if OUTPUT_FILE.exists():
                OUTPUT_FILE.unlink()
        except Exception:
            pass
        return 0

    lines = [l.strip() for l in proxy_path.read_text(encoding="utf-8").splitlines()]
    candidates = [l for l in lines if l and not l.startswith("#")]
    print(f"Found {len(candidates)} proxy candidates in {proxy_path}")

    valid = []
    for p in candidates:
        # only test http(s) proxies in this lightweight checker
        if not (p.startswith("http://") or p.startswith("https://")):
            print(f"Skipping non-http(s) proxy scheme: {p}")
            continue
        try:
            proxies = {"http": p, "https": p}
            print(f"Testing proxy: {p}")
            r = requests.get("https://httpbin.org/ip", timeout=6, proxies=proxies)
            if r.status_code == 200:
                print(f"  -> OK")
                valid.append(p)
            else:
                print(f"  -> HTTP {r.status_code}")
        except Exception as e:
            print(f"  -> Failed: {e}")
        # be polite and avoid hammering
        time.sleep(0.2)

    if valid:
        OUT = "\n".join(valid) + "\n"
        OUTPUT_FILE.write_text(OUT, encoding="utf-8")
        print(f"Wrote {len(valid)} valid proxies to {OUTPUT_FILE}")
    else:
        if OUTPUT_FILE.exists():
            OUTPUT_FILE.unlink()
        print("No valid proxies found")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
