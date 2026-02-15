#!/usr/bin/env python3
"""
Orchestration runner for DutyGuard-AI pipeline.

Runs (in order):
- `python3 scraper.py`
- `python3 scripts/import_htsdata.py`
- `./scripts/alert_on_fallbacks.sh backend/data/intake_notifications.jsonl 5`
- `set -a && source .env && set +a && ./scripts/release_check.sh`

Features:
- Runs steps sequentially, captures logs
- Retries steps configurable times
- Optional interval loop to auto-run next (cron-like)
- Posts a small summary to `ALERT_WEBHOOK_URL` if set in `.env`

Usage:
  ./scripts/run_all.py --once
  ./scripts/run_all.py --interval 3600   # run every hour

"""

import argparse
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "backend" / "data"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "run_all.log"
ENV_PATH = ROOT / ".env"

STEPNAMES = [
    "validate_proxies",
    "scraper",
    "import_htsdata",
    "alert_on_fallbacks",
    "release_check",
]

COMMANDS = {
    "validate_proxies": [sys.executable, str(ROOT / "scripts" / "validate_proxies.py")],
    "scraper": [sys.executable, str(ROOT / "scraper.py")],
    "import_htsdata": [sys.executable, str(ROOT / "scripts" / "import_htsdata.py")],
    "alert_on_fallbacks": ["./scripts/alert_on_fallbacks.sh", "backend/data/intake_notifications.jsonl", "5"],
    "release_check": ["/bin/bash", "-lc", "set -a && source .env && set +a && ./scripts/release_check.sh"],
}


def load_env():
    env = os.environ.copy()
    if ENV_PATH.exists():
        with ENV_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def now_iso():
    return datetime.utcnow().isoformat() + "Z"


def log(msg: str):
    ts = now_iso()
    s = f"[{ts}] {msg}\n"
    print(s, end="")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(s)


def run_cmd(cmd, env, retry=0, timeout=None):
    attempt = 0
    last_exc = None
    while attempt <= retry:
        attempt += 1
        try:
            log(f"Running: {cmd}")
            if isinstance(cmd, str):
                proc = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True, env=env, timeout=timeout)
            else:
                proc = subprocess.run(cmd, check=False, capture_output=True, text=True, env=env, timeout=timeout)

            out = proc.stdout or ""
            err = proc.stderr or ""
            log(f"Exit {proc.returncode} stdout:\n{out.strip()[:2000]}")
            if err.strip():
                log(f"stderr:\n{err.strip()[:2000]}")
            if proc.returncode == 0:
                return True, proc.returncode, out, err
            last_exc = RuntimeError(f"Exit {proc.returncode}")
        except Exception as e:
            last_exc = e
            log(f"Exception running command: {e}")
        # backoff before retrying
        if attempt <= retry:
            backoff = 1 + attempt * 2
            log(f"Retrying in {backoff}s (attempt {attempt}/{retry})")
            time.sleep(backoff)
    return False, getattr(last_exc, 'code', 1), "", str(last_exc)


def summarize_and_notify(env, results):
    # Build a small JSON payload
    payload = {
        "timestamp": now_iso(),
        "results": results,
    }
    webhook = env.get("ALERT_WEBHOOK_URL")
    if webhook:
        try:
            import requests
            r = requests.post(webhook, json=payload, timeout=10)
            log(f"Posted summary to webhook {webhook} -> {r.status_code}")
        except Exception as e:
            log(f"Failed to post webhook: {e}")
    else:
        log("No ALERT_WEBHOOK_URL configured; skipping webhook.")


def run_once(retry, timeout, continue_on_failure: bool = False):
    env = load_env()
    # If configured, prefer the PDF fallback pipeline instead of hitting the live
    # USITC site which may return error pages or be gated from this network.
    if env.get("FORCE_PDF_FALLBACK", "0").lower() in ("1", "true", "yes"):
        log("FORCE_PDF_FALLBACK enabled — running PDF fallback pipeline instead of scraper")
        # Replace the scraper command with a shell pipeline that runs the
        # PDF parsing pipeline and copies the canonical-with-duties CSV to
        # the expected live CSV path so downstream steps can continue.
        COMMANDS["scraper"] = [
            "/bin/bash",
            "-lc",
            (
                "python3 scripts/download_parse_finalcopy.py && "
                "python3 scripts/parse_finalcopy_normalized.py && "
                "python3 scripts/filter_pdf_candidates.py && "
                "python3 scripts/reconcile_tariffs.py && "
                "python3 scripts/produce_canonical_csv.py && "
                "python3 scripts/extract_duties.py && "
                "python3 scripts/merge_duties_into_canonical.py && "
                "cp knowledge_base/live_tariffs.canonical.with_duties.csv knowledge_base/live_tariffs.csv || true"
            ),
        ]
    # Log proxy list file if set so runs are traceable
    proxy_file = env.get("PROXY_LIST_FILE")
    if proxy_file:
        log(f"Using proxy list file: {proxy_file}")
    results = {}
    for step in STEPNAMES:
        cmd = COMMANDS[step]
        ok, code, out, err = run_cmd(cmd, env, retry=retry, timeout=timeout)
        results[step] = {"ok": ok, "exit_code": code}
        # After validating proxies, if a valid output exists, point the
        # scraper at the validated list so it only uses healthy proxies.
        if step == "validate_proxies" and ok:
            valid_path = ROOT / "backend" / "proxies.valid.txt"
            if valid_path.exists() and valid_path.read_text(encoding="utf-8").strip():
                env["PROXY_LIST_FILE"] = str(valid_path)
                log(f"Using validated proxy list: {valid_path}")
        if not ok:
            log(f"Step failed: {step}; {'continuing' if continue_on_failure else 'halting'} pipeline.")
            if not continue_on_failure:
                break
    summarize_and_notify(env, results)
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--interval", type=int, default=0, help="If set >0, re-run pipeline every N seconds")
    p.add_argument("--retry", type=int, default=1, help="Per-step retry count on failure")
    p.add_argument("--timeout", type=int, default=None, help="Per-step timeout in seconds")
    p.add_argument("--once", action="store_true", help="Run once and exit")
    p.add_argument("--continue-on-failure", action="store_true", help="Continue pipeline even if a step fails")
    args = p.parse_args()

    log("Starting run_all orchestration")
    if args.once or args.interval <= 0:
        run_once(args.retry, args.timeout, continue_on_failure=args.continue_on_failure)
        log("run_all finished (once)")
        return

    try:
        while True:
            log(f"Scheduled run: interval={args.interval}s")
            run_once(args.retry, args.timeout, continue_on_failure=args.continue_on_failure)
            log(f"Sleeping for {args.interval}s")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log("Interrupted; exiting")


if __name__ == '__main__':
    main()
