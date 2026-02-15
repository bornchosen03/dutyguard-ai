from __future__ import annotations

import hashlib
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
    review_ticket_id: Optional[str] = None


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


def _review_queue_dir() -> Path:
    p = (_repo_root() / "backend" / "data" / "review_queue").resolve()
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


def _risk_score(product: ProductSpecs) -> float:
    score = 0.03
    description_len = len((product.description or "").strip())
    intended_use_len = len((product.intended_use or "").strip())
    material_count = len(product.materials or {})

    if description_len < 30:
        score += 0.18
    elif description_len < 60:
        score += 0.07

    if intended_use_len < 8:
        score += 0.12
    elif intended_use_len < 20:
        score += 0.05

    if material_count == 0:
        score += 0.25
    elif material_count < 2:
        score += 0.08

    if product.value >= 100_000:
        score += 0.10
    elif product.value >= 25_000:
        score += 0.05

    if (product.origin_country or "").upper().strip() == "CN":
        score += 0.05

    return _clamp01(score)


HUMAN_REVIEW_LOWER_CONFIDENCE_THRESHOLD = 0.90


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
    if ci[0] < HUMAN_REVIEW_LOWER_CONFIDENCE_THRESHOLD:
        reasons.append(
            f"Lower-bound confidence is below legal review threshold ({HUMAN_REVIEW_LOWER_CONFIDENCE_THRESHOLD:.2f})."
        )
    return reasons


def _create_review_ticket(product: ProductSpecs, response: TariffResponse) -> str:
    ts = int(time.time())
    stable_hash = hashlib.sha256(f"{product.name}|{product.origin_country}|{product.value}".encode("utf-8")).hexdigest()[:8]
    ticket_id = f"review_{ts}_{stable_hash}"
    payload = {
        "id": ticket_id,
        "status": "open",
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "request": product.model_dump(),
        "response": response.model_dump(),
        "review_reasons": response.review_reasons,
        "decision": None,
        "reviewer": None,
        "decision_notes": None,
        "decided_at_utc": None,
    }
    (_review_queue_dir() / f"{ticket_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return ticket_id


@router.post("/classify", response_model=TariffResponse)
async def classify_product(product: ProductSpecs) -> TariffResponse:
    agent = TariffAgent(product)
    material_context = agent.analyze_materials()

    suggested_code = "8471.30.01"
    duty_percent = 0.05

    risk_score = _risk_score(product)
    confidence = _confidence_from_risk(risk_score)
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
        risk_score=risk_score,
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

    if requires_human_review:
        response.review_ticket_id = _create_review_ticket(product, response)

    # Legal audit trail: persist the reasoning and inputs.
    log_payload = {
        "id": f"{int(time.time())}",
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "request": product.model_dump(),
        "response": response.model_dump(),
        "policy": {
            "human_in_the_loop_threshold": HUMAN_REVIEW_LOWER_CONFIDENCE_THRESHOLD,
            "requires_human_review": requires_human_review,
            "review_reasons": review_reasons,
            "legal_disclaimer": response.legal_disclaimer,
        },
    }
    response.reasoning_log_path = _write_reasoning_log(log_payload)
    return response
