from __future__ import annotations

from typing import Any

from chemical_agent import ChemicalReader


def placeholder() -> str:
    return "chemical_expert: ready"


def analyze_text(text: str) -> dict[str, Any]:
    reader = ChemicalReader()
    purity = reader.extract_purity(text)
    advisory = reader.infer_tariff_advisory(text)
    return {
        "purity": purity,
        "tariff_advisory": advisory,
    }
