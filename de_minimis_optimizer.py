from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParcelPlan:
    order_value_usd: float
    threshold_usd: float
    eligible: bool
    recommendation: str


def evaluate_de_minimis(order_value_usd: float, threshold_usd: float = 800.0) -> ParcelPlan:
    value = max(0.0, float(order_value_usd))
    threshold = max(0.0, float(threshold_usd))
    eligible = value <= threshold

    if eligible:
        rec = "Eligible under current threshold; keep invoice and parcel-level documentation audit-ready."
    else:
        rec = (
            "Above threshold; route through formal entry workflow and pre-validate HS code + declared value."
        )

    return ParcelPlan(order_value_usd=value, threshold_usd=threshold, eligible=eligible, recommendation=rec)


if __name__ == "__main__":
    print(evaluate_de_minimis(725.0))
    print(evaluate_de_minimis(1200.0))
