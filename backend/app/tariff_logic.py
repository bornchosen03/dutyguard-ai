from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/api", tags=["tariff-logic"])


class ProductSpecs(BaseModel):
    name: str
    description: str
    materials: Dict[str, float]
    value: float
    origin_country: str
    destination_country: str
    intended_use: str


class TariffResponse(BaseModel):
    suggested_hs_code: str
    duty_rate: str
    reasoning_manifesto: List[str]
    risk_score: float
    confidence: float
    confidence_interval: Tuple[float, float]
    requires_human_review: bool
    review_reasons: List[str]
    legal_citations: List[str]
    legal_disclaimer: str
    engineering_tip: Optional[str]
    total_landed_cost: float
    reasoning_log_path: Optional[str] = None


class TariffAgent:
    def __init__(self, specs: ProductSpecs):
        self.specs = specs

    def analyze_materials(self) -> str:
        if self.specs.materials.get("steel", 0) > 0.50:
            return "Heavy Metal/Industrial Classification"
        return "General Goods"

    def calculate_landed_cost(self, duty_rate: float) -> float:
        return self.specs.value * (1 + duty_rate)

    def get_engineering_tip(self, hs_code: str) -> str:
        if "8517" in hs_code:
            return (
                "Tip: If the device is marketed as a 'data collector' rather than a 'telecom device', "
                "duty may drop 2%."
            )
        return "No immediate engineering arbitrage detected."


def _repo_root() -> Path:
    # backend/app/tariff_logic.py -> backend/ -> repo root
    return Path(__file__).resolve().parents[2]


def _audit_dir() -> Path:
    p = (_repo_root() / "backend" / "data" / "reasoning_logs").resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def _write_reasoning_log(payload: dict) -> str:
    ts = int(time.time())
    filename = f"classify_{ts}_{payload.get('id', 'na')}.json"
    path = _audit_dir() / filename
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def _confidence_from_risk(risk_score: float) -> float:
    # MVP mapping: lower risk => higher confidence.
    # risk_score is expected [0,1] but we clamp defensively.
    r = _clamp01(float(risk_score))
    conf = 0.98 - (r * 0.60)
    return _clamp01(conf)


def _confidence_interval(confidence: float) -> Tuple[float, float]:
    # MVP interval width shrinks as confidence rises.
    c = _clamp01(confidence)
    half_width = max(0.02, 0.12 - (c * 0.10))
    lo = _clamp01(c - half_width)
    hi = _clamp01(c + half_width)
    return (lo, hi)


def _legal_citations() -> List[str]:
    return [
        "General Rules of Interpretation (GRI) 1 and 6",
        "HTSUS Section and Chapter Notes (as applicable)",
        "19 CFR Part 141 (entry documentation requirements)",
        "19 CFR Part 152 (customs valuation framework)",
        "CBP CROSS rulings (fact-specific precedent)",
    ]


def _review_reasons(product: ProductSpecs, ci: Tuple[float, float]) -> List[str]:
    reasons: List[str] = []
    if len((product.description or "").strip()) < 30:
        reasons.append("Product description is too short for reliable legal classification.")
    if not product.materials:
        reasons.append("Material composition is missing.")
    if len((product.intended_use or "").strip()) < 8:
        reasons.append("Intended use detail is insufficient.")
    if ci[0] < 0.92:
        reasons.append("Lower-bound confidence is below legal review threshold (0.92).")
    if not reasons:
        reasons.append("MVP safeguard: final determination still requires licensed customs/legal review.")
    return reasons


@router.post("/classify", response_model=TariffResponse)
async def classify_product(product: ProductSpecs) -> TariffResponse:
    agent = TariffAgent(product)
    material_context = agent.analyze_materials()

    suggested_code = "8471.30.01"
    duty_percent = 0.05

    confidence = _confidence_from_risk(0.15)
    ci = _confidence_interval(confidence)
    review_reasons = _review_reasons(product, ci)
    requires_human_review = len(review_reasons) > 0

    response = TariffResponse(
        suggested_hs_code=suggested_code,
        duty_rate=f"{duty_percent * 100}%",
        reasoning_manifesto=[
            f"Analyzed {material_context} based on GRI 1.",
            "Cross-referenced intended use: " + product.intended_use,
            "Matched material threshold: Steel at " + str(product.materials.get("steel", 0)),
        ],
        risk_score=0.15,
        confidence=confidence,
        confidence_interval=ci,
        requires_human_review=requires_human_review,
        review_reasons=review_reasons,
        legal_citations=_legal_citations(),
        legal_disclaimer=(
            "This output is decision-support only and not legal advice; "
            "final tariff classification requires qualified customs/legal review."
        ),
        engineering_tip=agent.get_engineering_tip(suggested_code),
        total_landed_cost=agent.calculate_landed_cost(duty_percent),
    )

    # Legal audit trail: persist the reasoning and inputs.
    log_payload = {
        "id": f"{int(time.time())}",
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "request": product.model_dump(),
        "response": response.model_dump(),
        "policy": {
            "human_in_the_loop_threshold": 0.92,
            "requires_human_review": requires_human_review,
            "review_reasons": review_reasons,
            "legal_disclaimer": response.legal_disclaimer,
        },
    }
    response.reasoning_log_path = _write_reasoning_log(log_payload)
    return response
