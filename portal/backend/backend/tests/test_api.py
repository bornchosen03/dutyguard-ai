import io

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
    assert body.get("requires_human_review") is False
    assert body.get("review_ticket_id") in (None, "")

    assert isinstance(body.get("review_reasons"), list)
    assert len(body["review_reasons"]) == 0
    assert isinstance(body.get("legal_citations"), list)
    assert len(body["legal_citations"]) >= 1
    assert "not legal advice" in str(body.get("legal_disclaimer", "")).lower()


def test_classify_high_risk_creates_review_ticket() -> None:
    payload = {
        "name": "Risky sample",
        "description": "short",
        "materials": {},
        "value": 180000,
        "origin_country": "CN",
        "destination_country": "US",
        "intended_use": "test",
    }
    response = client.post("/api/classify", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body.get("requires_human_review") is True
    assert isinstance(body.get("review_reasons"), list)
    assert len(body["review_reasons"]) >= 1
    assert isinstance(body.get("review_ticket_id"), str)
    assert body["review_ticket_id"].startswith("review_")


def test_sources_and_metrics_endpoints() -> None:
    sources_response = client.get("/api/sources")
    assert sources_response.status_code == 200
    sources_body = sources_response.json()
    assert sources_body.get("ok") is True
    assert isinstance(sources_body.get("sources"), list)
    assert len(sources_body["sources"]) >= 3

    metrics_response = client.get("/api/metrics/summary")
    assert metrics_response.status_code == 200
    metrics_body = metrics_response.json()
    assert metrics_body.get("ok") is True
    assert "reviews" in metrics_body


def test_review_workflow_end_to_end() -> None:
    classify_payload = {
        "name": "Workflow sample",
        "description": "short",
        "materials": {},
        "value": 120000,
        "origin_country": "CN",
        "destination_country": "US",
        "intended_use": "qa",
    }
    classify_response = client.post("/api/classify", json=classify_payload)
    assert classify_response.status_code == 200
    classify_body = classify_response.json()
    review_id = classify_body.get("review_ticket_id")
    assert isinstance(review_id, str)

    list_response = client.get("/api/reviews")
    assert list_response.status_code == 200
    assert list_response.json().get("ok") is True

    get_response = client.get(f"/api/reviews/{review_id}")
    assert get_response.status_code == 200
    assert get_response.json().get("ticket", {}).get("id") == review_id

    decision_response = client.post(
        f"/api/reviews/{review_id}/decision",
        json={"decision": "approved", "reviewer": "qa-reviewer", "decision_notes": "Validated"},
    )
    assert decision_response.status_code == 200
    decision_body = decision_response.json()
    assert decision_body.get("ticket", {}).get("status") == "approved"
    assert "audit_event" in decision_body

    report_response = client.get(f"/api/classification-report/{review_id}")
    assert report_response.status_code == 200
    report_body = report_response.json().get("report", {})
    assert report_body.get("ticket_id") == review_id
    assert isinstance(report_body.get("why_this_classification"), list)


def test_pilot_onboarding_and_claim_packet() -> None:
    onboard_payload = {
        "customer_name": "Acme Imports",
        "entries": [
            {
                "sku": "A-100",
                "description": "Industrial controller module",
                "import_value": 100000,
                "current_duty_rate": 0.08,
                "suggested_duty_rate": 0.04,
                "confidence": 0.93,
            },
            {
                "sku": "B-200",
                "description": "Specialty component",
                "import_value": 50000,
                "current_duty_rate": 0.07,
                "suggested_duty_rate": 0.03,
                "confidence": 0.91,
            },
        ],
    }
    onboard_response = client.post("/api/pilot/onboard", json=onboard_payload)
    assert onboard_response.status_code == 200
    onboard_body = onboard_response.json()
    batch_id = onboard_body.get("batch_id")
    assert isinstance(batch_id, str)

    prioritize_response = client.get(f"/api/pilot/prioritize/{batch_id}")
    assert prioritize_response.status_code == 200
    prioritize_body = prioritize_response.json()
    assert prioritize_body.get("ok") is True
    assert isinstance(prioritize_body.get("top_opportunities"), list)

    packet_response = client.post(f"/api/pilot/claim-packet/{batch_id}")
    assert packet_response.status_code == 200
    packet_body = packet_response.json()
    assert packet_body.get("ok") is True
    assert isinstance(packet_body.get("packet_id"), str)


def test_alerts_endpoint_available() -> None:
    response = client.get("/api/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_intake_submission_success() -> None:
    response = client.post(
        "/api/intake",
        data={
            "company": "Acme Imports",
            "name": "Jane Smith",
            "email": "jane@acme.com",
            "phone": "+15551234567",
            "message": "Need a tariff exposure review for Q1 imports",
            "website": "",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("ok") is True
    assert isinstance(body.get("id"), str)
    assert body.get("notificationSent") is True
    assert body.get("notificationMode") in {"email", "fallback"}


def test_intake_honeypot_rejected() -> None:
    response = client.post(
        "/api/intake",
        data={
            "company": "Spam Co",
            "name": "Bot",
            "email": "bot@example.com",
            "message": "spam",
            "website": "https://spam.example.com",
        },
    )
    assert response.status_code == 400


def test_tariff_files_are_isolated_per_user() -> None:
    upload_response = client.post(
        "/api/tariff-files?user=alpha-user",
        files={"file": ("alpha.txt", io.BytesIO(b"alpha-content"), "text/plain")},
    )
    assert upload_response.status_code == 200
    stored_name = upload_response.json().get("storedName")
    assert isinstance(stored_name, str)

    list_alpha = client.get("/api/tariff-files?user=alpha-user")
    assert list_alpha.status_code == 200
    alpha_names = {item["storedName"] for item in list_alpha.json()}
    assert stored_name in alpha_names

    list_beta = client.get("/api/tariff-files?user=beta-user")
    assert list_beta.status_code == 200
    beta_names = {item["storedName"] for item in list_beta.json()}
    assert stored_name not in beta_names
