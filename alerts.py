from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


ROOT = Path(__file__).resolve().parent
KNOWLEDGE_BASE = ROOT / "knowledge_base"
KNOWLEDGE_BASE.mkdir(parents=True, exist_ok=True)

LIVE_TARIFFS_CSV = KNOWLEDGE_BASE / "live_tariffs.csv"
HISTORY_CSV = KNOWLEDGE_BASE / "tariff_history.csv"
ALERTS_JSON = KNOWLEDGE_BASE / "tariff_alerts.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_csv_rows(path: Path, max_rows: int = 50) -> list[list[str]]:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            rows.append([c.strip() for c in row])
    return rows


def _write_csv(path: Path, rows: Iterable[Iterable[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(list(row))


@dataclass(frozen=True)
class AlertResult:
    changed: bool
    checked_at_utc: str
    live_csv_sha256: Optional[str]
    history_csv_sha256: Optional[str]
    message: str


def diff_live_vs_history(live_csv: Path = LIVE_TARIFFS_CSV, history_csv: Path = HISTORY_CSV) -> AlertResult:
    if not live_csv.exists():
        return AlertResult(
            changed=False,
            checked_at_utc=_utc_now_iso(),
            live_csv_sha256=None,
            history_csv_sha256=_sha256_file(history_csv) if history_csv.exists() else None,
            message=f"Missing live tariffs CSV: {live_csv}",
        )

    live_hash = _sha256_file(live_csv)

    if not history_csv.exists():
        history_csv.write_bytes(live_csv.read_bytes())
        return AlertResult(
            changed=False,
            checked_at_utc=_utc_now_iso(),
            live_csv_sha256=live_hash,
            history_csv_sha256=live_hash,
            message=f"Initialized history from live CSV: {history_csv.name}",
        )

    history_hash = _sha256_file(history_csv)
    changed = history_hash != live_hash
    msg = "Tariff data changed" if changed else "No tariff data change detected"

    if changed:
        # Update history to the latest snapshot after detecting the diff.
        history_csv.write_bytes(live_csv.read_bytes())

    return AlertResult(
        changed=changed,
        checked_at_utc=_utc_now_iso(),
        live_csv_sha256=live_hash,
        history_csv_sha256=history_hash,
        message=msg,
    )


def build_alert_payload(result: AlertResult) -> dict:
    payload: dict = {
        "changed": result.changed,
        "checked_at_utc": result.checked_at_utc,
        "history_csv_sha256": result.history_csv_sha256,
        "live_csv_sha256": result.live_csv_sha256,
        "message": result.message,
    }

    if LIVE_TARIFFS_CSV.exists():
        payload["live_csv_path"] = str(LIVE_TARIFFS_CSV)
        payload["live_preview_rows"] = _read_csv_rows(LIVE_TARIFFS_CSV, max_rows=12)

    if HISTORY_CSV.exists():
        payload["history_csv_path"] = str(HISTORY_CSV)

    payload["recommendations"] = [
        "Review impacted HS chapters/prefixes and validate duty rates.",
        "Re-run landed cost for affected SKUs and flag margin breaches.",
        "Check for exclusions, quotas, or temporary suspensions.",
        "If exposure is high, evaluate tariff engineering and supplier re-sourcing options.",
    ]

    return payload


def write_alert(payload: dict, path: Path = ALERTS_JSON) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    result = diff_live_vs_history()
    payload = build_alert_payload(result)
    write_alert(payload)

    prefix = "⚠️" if result.changed else "✅"
    print(f"{prefix} {result.message}")
    print(f"- checked_at_utc: {result.checked_at_utc}")
    if result.history_csv_sha256 and result.live_csv_sha256:
        print(f"- history_sha256: {result.history_csv_sha256}")
        print(f"- live_sha256:    {result.live_csv_sha256}")
    print(f"- alert_json:     {ALERTS_JSON}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
