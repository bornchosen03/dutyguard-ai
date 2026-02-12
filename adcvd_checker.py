from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdCvdResult:
    hs_code: str
    origin_country: str
    risk_level: str
    notes: str


_HIGH_RISK_PREFIXES = ("7208", "7209", "7210", "7306", "7601", "7606")


def check_ad_cvd_risk(hs_code: str, origin_country: str) -> AdCvdResult:
    code = (hs_code or "").replace(".", "").strip()
    origin = (origin_country or "").upper().strip()

    high_risk_origin = origin in {"CN", "RU"}
    product_risk = any(code.startswith(prefix) for prefix in _HIGH_RISK_PREFIXES)

    if high_risk_origin and product_risk:
        return AdCvdResult(
            hs_code=hs_code,
            origin_country=origin,
            risk_level="high",
            notes="Potential AD/CVD exposure; verify scope rulings and case-specific cash deposit rates.",
        )
    if high_risk_origin or product_risk:
        return AdCvdResult(
            hs_code=hs_code,
            origin_country=origin,
            risk_level="medium",
            notes="Partial AD/CVD signal; run product scope and producer-specific checks.",
        )

    return AdCvdResult(
        hs_code=hs_code,
        origin_country=origin,
        risk_level="low",
        notes="No immediate AD/CVD pattern in MVP rules.",
    )


if __name__ == "__main__":
    print(check_ad_cvd_risk("7208.38", "CN"))
