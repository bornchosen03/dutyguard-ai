from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClientProfile:
    name: str
    annual_import_value_usd: float
    hs_prefixes: tuple[str, ...] = ()


# Example config; replace with real client values.
CLIENTS: tuple[ClientProfile, ...] = (
    ClientProfile(name="ExampleCo", annual_import_value_usd=1_000_000.0, hs_prefixes=("8471",)),
)


# If you have a known baseline duty rate for a portfolio, you can use it for rough deltas.
# Otherwise, the alert agent will still run and report data changes.
BASELINE_DUTY_RATE_PCT: float | None = None
