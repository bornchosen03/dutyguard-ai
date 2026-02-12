from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from typing import Any, Optional


_PURITY_RE = re.compile(r"(\d+\.?\d*)\s*(?:%|wt%|purity)\b", re.IGNORECASE)


@dataclass(frozen=True)
class TariffAdvice:
    code: str
    rate: str
    note: str


class ChemicalAgent:
    """Extracts key chemical attributes from OCR'd lab reports.

    MVP scope:
    - Parse text (already OCR'd)
    - Extract purity as a float percent

    Optional:
    - OCR an image via pytesseract if available

    This is not legal advice.
    """

    def __init__(self, ocr_text: str):
        self.text = ocr_text or ""

    @staticmethod
    def ocr_image(image_path: str) -> str:
        """Best-effort OCR via pytesseract.

        Requires:
        - `pip install pytesseract`
        - `tesseract` binary installed (macOS: `brew install tesseract`)
        """

        try:
            import pytesseract  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("pytesseract not installed. Run: pip install pytesseract") from exc

        if shutil.which("tesseract") is None:  # pragma: no cover
            raise RuntimeError("tesseract binary not found. On macOS: brew install tesseract")

        return pytesseract.image_to_string(image_path)

    def extract_purity(self) -> Optional[float]:
        """Uses regex to find purity levels.

        Examples:
        - "98.5% purity"
        - "98.5 wt%"
        - "Purity 98.5%"
        """

        match = _PURITY_RE.search(self.text)
        return float(match.group(1)) if match else None

    def get_tariff_advice(self, purity: Optional[float], hs_prefix: str) -> Optional[dict[str, Any]]:
        """Toy logic showing how purity can impact classification.

        Deep logic note: in real-world Chapter 29 classification, purity and
        chemical identity drive headings/subheadings; this is an MVP stub.
        """

        if purity is None:
            return None

        hs_prefix = (hs_prefix or "").strip()
        if hs_prefix == "2901":
            if purity >= 95.0:
                advice = TariffAdvice(code="2901.10.00", rate="Free", note="High purity alkane")
            else:
                advice = TariffAdvice(
                    code="2711.12.00",
                    rate="5.5%",
                    note="Mixed fuel grade - Lower purity increases tax.",
                )
            return {"code": advice.code, "rate": advice.rate, "note": advice.note}

        return None


if __name__ == "__main__":
    # --- VS CODE TEST ---
    # "96% Ethylene found in lab report"
    test_report = "Analysis Report: Batch 402, Ethylene Content: 96.2%, Impurities: 0.8%"
    agent = ChemicalAgent(test_report)
    purity = agent.extract_purity()
    print(f"Detected Purity: {purity}%")
    print(f"Advice: {agent.get_tariff_advice(purity, '2901')}")
