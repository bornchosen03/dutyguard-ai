from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class WarRoomSignal:
    name: str
    severity: str
    impact: str
    recommendation: str


@dataclass(frozen=True)
class WarRoomReport:
    generated_at_utc: str
    signals: list[WarRoomSignal]


def build_war_room_report(alert_payload: dict | None = None, include_defaults: bool = True) -> WarRoomReport:
    signals: list[WarRoomSignal] = []

    if include_defaults:
        signals.extend(
            [
                WarRoomSignal(
                    name="Tariff volatility",
                    severity="medium",
                    impact="Margin compression risk on exposed SKUs.",
                    recommendation="Run weekly landed-cost scenario modeling and lock supplier fallback lanes.",
                ),
                WarRoomSignal(
                    name="Compliance workload",
                    severity="high",
                    impact="Higher chance of filing inconsistencies under rapid policy changes.",
                    recommendation="Prioritize HS code review queue and human review for low-confidence classifications.",
                ),
            ]
        )

    if isinstance(alert_payload, dict):
        msg = str(alert_payload.get("message", "")).lower()
        if "changed" in msg or bool(alert_payload.get("changed")):
            signals.append(
                WarRoomSignal(
                    name="Live tariff change detected",
                    severity="high",
                    impact="Potential immediate cost and compliance impact.",
                    recommendation="Trigger client notifications and refresh classification/rate mappings.",
                )
            )

    return WarRoomReport(
        generated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        signals=signals,
    )


def as_rows(report: WarRoomReport) -> list[dict[str, str]]:
    return [
        {
            "name": signal.name,
            "severity": signal.severity,
            "impact": signal.impact,
            "recommendation": signal.recommendation,
        }
        for signal in report.signals
    ]


if __name__ == "__main__":
    report = build_war_room_report({"changed": True, "message": "tariff table changed"})
    print(report.generated_at_utc)
    for row in as_rows(report):
        print(f"- [{row['severity']}] {row['name']}: {row['recommendation']}")
