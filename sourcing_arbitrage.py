from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourcingOption:
    country: str
    duty_rate_pct: float
    logistics_cost_usd: float


@dataclass(frozen=True)
class ArbitrageDecision:
    best_country: str
    estimated_total_cost_usd: float
    rationale: str


def choose_best_sourcing(
    base_value_usd: float,
    option_a: SourcingOption,
    option_b: SourcingOption,
) -> ArbitrageDecision:
    base = max(0.0, float(base_value_usd))

    def total_cost(opt: SourcingOption) -> float:
        return base * (1.0 + max(0.0, opt.duty_rate_pct) / 100.0) + max(0.0, opt.logistics_cost_usd)

    cost_a = total_cost(option_a)
    cost_b = total_cost(option_b)

    if cost_a <= cost_b:
        return ArbitrageDecision(
            best_country=option_a.country,
            estimated_total_cost_usd=cost_a,
            rationale=f"Lower projected landed cost than {option_b.country} by ${cost_b - cost_a:,.2f}.",
        )
    return ArbitrageDecision(
        best_country=option_b.country,
        estimated_total_cost_usd=cost_b,
        rationale=f"Lower projected landed cost than {option_a.country} by ${cost_a - cost_b:,.2f}.",
    )


if __name__ == "__main__":
    decision = choose_best_sourcing(
        100000,
        SourcingOption(country="VN", duty_rate_pct=5.0, logistics_cost_usd=4200),
        SourcingOption(country="MX", duty_rate_pct=2.0, logistics_cost_usd=6800),
    )
    print(decision)
