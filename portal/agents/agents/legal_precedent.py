from __future__ import annotations

from precedent_agent import PrecedentAgent, PrecedentRecord


def placeholder() -> str:
    return "legal_precedent: ready"


def search_precedent(query: str, top_k: int = 3) -> list[PrecedentRecord]:
    return PrecedentAgent().search(query=query, top_k=top_k)
