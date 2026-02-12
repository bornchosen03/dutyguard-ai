"""Standalone demo: Global Tariff Intelligence Engine v1.0

This file mirrors the requested FastAPI demo so you can run it directly:

```zsh
python3 -m pip install fastapi uvicorn pydantic
python3 main.py
```

Note: The main application used by this repo is `backend/app/main.py`.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Global Tariff Intelligence Engine v1.0")


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
    engineering_tip: Optional[str]
    total_landed_cost: float


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


@app.post("/classify", response_model=TariffResponse)
async def classify_product(product: ProductSpecs) -> TariffResponse:
    agent = TariffAgent(product)
    material_context = agent.analyze_materials()

    suggested_code = "8471.30.01"
    duty_percent = 0.05

    return TariffResponse(
        suggested_hs_code=suggested_code,
        duty_rate=f"{duty_percent * 100}%",
        reasoning_manifesto=[
            f"Analyzed {material_context} based on GRI 1.",
            "Cross-referenced intended use: " + product.intended_use,
            "Matched material threshold: Steel at " + str(product.materials.get("steel", 0)),
        ],
        risk_score=0.15,
        engineering_tip=agent.get_engineering_tip(suggested_code),
        total_landed_cost=agent.calculate_landed_cost(duty_percent),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
