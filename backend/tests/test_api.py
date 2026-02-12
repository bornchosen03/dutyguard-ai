from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


def test_classify_returns_legal_guardrails() -> None:
    payload = {
        "name": "Compliance sample",
        "description": "Lithium battery module for industrial equipment with aluminum enclosure",
        "materials": {"steel": 0.1, "aluminum": 0.45},
        "value": 5000,
        "origin_country": "CN",
        "destination_country": "US",
        "intended_use": "Commercial machine power subsystem",
    }
    response = client.post("/api/classify", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert "suggested_hs_code" in body
    assert "confidence_interval" in body
    assert body.get("requires_human_review") is True

    assert isinstance(body.get("review_reasons"), list)
    assert len(body["review_reasons"]) >= 1
    assert isinstance(body.get("legal_citations"), list)
    assert len(body["legal_citations"]) >= 1
    assert "not legal advice" in str(body.get("legal_disclaimer", "")).lower()


def test_alerts_endpoint_available() -> None:
    response = client.get("/api/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
