from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class PrecedentRecord:
    title: str
    source: str
    topic: str
    summary: str
    confidence: float


_DEFAULT_PRECEDENTS: List[PrecedentRecord] = [
    PrecedentRecord(
        title="HQ H312345 — Functional unit classification",
        source="CBP CROSS",
        topic="classification",
        summary="Composite goods are classified by essential character and principal function.",
        confidence=0.81,
    ),
    PrecedentRecord(
        title="HQ H301010 — Lithium battery treatment",
        source="CBP CROSS",
        topic="battery",
        summary="Battery assemblies may shift heading based on integration level and principal use.",
        confidence=0.77,
    ),
    PrecedentRecord(
        title="WTO valuation note — transaction value limits",
        source="WTO guidance",
        topic="valuation",
        summary="Declared value must reflect arms-length transaction value and includable adjustments.",
        confidence=0.71,
    ),
]


class PrecedentAgent:
    def __init__(self, records: Iterable[PrecedentRecord] | None = None):
        self.records = list(records) if records is not None else list(_DEFAULT_PRECEDENTS)

    def search(self, query: str, top_k: int = 3) -> list[PrecedentRecord]:
        q = (query or "").strip().lower()
        if not q:
            return self.records[:top_k]

        ranked: list[tuple[int, PrecedentRecord]] = []
        for record in self.records:
            text = " ".join([record.title, record.topic, record.summary]).lower()
            score = sum(1 for token in q.split() if token and token in text)
            ranked.append((score, record))

        ranked.sort(key=lambda x: (x[0], x[1].confidence), reverse=True)
        return [item[1] for item in ranked[:top_k]]


if __name__ == "__main__":
    agent = PrecedentAgent()
    for result in agent.search("lithium battery classification"):
        print(f"- {result.title} [{result.source}] ({result.confidence:.2f})")
