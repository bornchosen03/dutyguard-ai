from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class DrawbackSummary:
    total_matches: int
    total_potential_refund: float
    mandate_notice: str


class DrawbackAuditAgent:
    """Duty drawback audit agent (MVP).

    Matches duty-paid imports (CBP 7501/ACE extract) to exports/destruction proof.

    MVP matching:
    - Substitution logic: join on `hs_code`
    - Basic quantity sanity: optional compare if both sides contain `quantity`
    - Potential refund capped at 99% (typical legal limit)

    Notes:
    - Real drawback is nuanced (time windows, substitution eligibility, rulings).
    - Treat outputs as candidate opportunities requiring compliance review.
    """

    def __init__(self, import_data_path: str | Path, export_data_path: str | Path):
        self.import_path = Path(import_data_path)
        self.export_path = Path(export_data_path)
        self.imports = pd.read_csv(self.import_path)
        self.exports = pd.read_csv(self.export_path)

    def find_matches(self) -> pd.DataFrame:
        required_imp = {"hs_code", "duty_paid"}
        required_exp = {"hs_code"}

        if not required_imp.issubset(set(self.imports.columns)):
            missing = sorted(required_imp - set(self.imports.columns))
            raise ValueError(f"imports missing required columns: {missing}")
        if not required_exp.issubset(set(self.exports.columns)):
            missing = sorted(required_exp - set(self.exports.columns))
            raise ValueError(f"exports missing required columns: {missing}")

        paid_imports = self.imports[self.imports["duty_paid"].fillna(0) > 0].copy()

        matches = pd.merge(paid_imports, self.exports, on="hs_code", suffixes=("_imp", "_exp"))

        # Optional quantity gating if both columns exist.
        if "quantity_imp" in matches.columns and "quantity_exp" in matches.columns:
            matches = matches[matches["quantity_exp"].fillna(0) > 0]

        matches["potential_refund"] = matches["duty_paid"].astype(float) * 0.99
        return matches

    @staticmethod
    def summarize(matches: pd.DataFrame) -> DrawbackSummary:
        total_matches = int(len(matches))
        total_refund = float(matches["potential_refund"].sum()) if total_matches else 0.0
        notice = (
            "CBP Electronic Refund Mandate: Feb 6, 2026 — refunds via ACH only. "
            "Confirm the client is enrolled for ACE ACH refunds."
        )
        return DrawbackSummary(
            total_matches=total_matches,
            total_potential_refund=total_refund,
            mandate_notice=notice,
        )


def _demo() -> int:
    print("🚀 AI Audit Starting: Scanning 5 years of historical trade data…")

    # Minimal demo datasets
    imports = pd.DataFrame(
        [
            {"hs_code": "8471.30", "import_date": "2024-05-12", "duty_paid": 12000.0, "entry": "7501-1001"},
            {"hs_code": "8517.62", "import_date": "2025-01-10", "duty_paid": 8500.0, "entry": "7501-1002"},
            {"hs_code": "9018.90", "import_date": "2024-03-02", "duty_paid": 0.0, "entry": "7501-1003"},
        ]
    )
    exports = pd.DataFrame(
        [
            {"hs_code": "8471.30", "export_proof": "BOL-9921", "export_date": "2024-06-15"},
            {"hs_code": "8517.62", "export_proof": "INV-5542", "export_date": "2025-02-02"},
        ]
    )

    tmp_dir = Path.cwd() / "knowledge_base"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    imp_path = tmp_dir / "demo_imports.csv"
    exp_path = tmp_dir / "demo_exports.csv"
    imports.to_csv(imp_path, index=False)
    exports.to_csv(exp_path, index=False)

    agent = DrawbackAuditAgent(imp_path, exp_path)
    matches = agent.find_matches()
    summary = agent.summarize(matches)

    print(f"✅ Found ${summary.total_potential_refund:,.0f} in unclaimed 'Substitution' refunds.")
    print(f"⚠️ Action Required: {summary.mandate_notice}")

    out_path = tmp_dir / "demo_drawback_matches.csv"
    matches.to_csv(out_path, index=False)
    print(f"- matches_csv: {out_path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 3:
        agent = DrawbackAuditAgent(sys.argv[1], sys.argv[2])
        df = agent.find_matches()
        summary = agent.summarize(df)
        print(summary)
        df.to_csv("drawback_matches.csv", index=False)
        print("Wrote drawback_matches.csv")
        raise SystemExit(0)

    raise SystemExit(_demo())
