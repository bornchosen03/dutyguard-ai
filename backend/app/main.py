"""Backend API + SPA static hosting.

Serves the built frontend from `frontend/dist` and provides API endpoints:

- GET `/health`
- POST `/api/tariff-files` (upload)
- GET `/api/tariff-files` (list)

Run with:

`uvicorn app.main:app --host 127.0.0.1 --port 8080`
"""

from __future__ import annotations

import hashlib
import json
import os
import smtplib
import threading
import time
from email.message import EmailMessage
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .tariff_logic import router as tariff_logic_router


ROOT_DIR = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE_DIR = (ROOT_DIR / "knowledge_base").resolve()
ALERTS_JSON_PATH = (KNOWLEDGE_BASE_DIR / "tariff_alerts.json").resolve()


BASE_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = (BASE_DIR / ".." / "frontend" / "dist").resolve()
DATA_DIR = (BASE_DIR / "data").resolve()
UPLOADS_DIR = (DATA_DIR / "uploads").resolve()
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

REVIEW_QUEUE_DIR = (DATA_DIR / "review_queue").resolve()
REVIEW_QUEUE_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_TRAIL_PATH = (DATA_DIR / "audit_trail.jsonl").resolve()

PILOT_BATCHES_DIR = (DATA_DIR / "pilot_batches").resolve()
PILOT_BATCHES_DIR.mkdir(parents=True, exist_ok=True)

CLAIM_PACKETS_DIR = (DATA_DIR / "claim_packets").resolve()
CLAIM_PACKETS_DIR.mkdir(parents=True, exist_ok=True)

INTAKES_DIR = (DATA_DIR / "intakes").resolve()
INTAKES_DIR.mkdir(parents=True, exist_ok=True)

NOTIFICATIONS_FALLBACK_PATH = (DATA_DIR / "intake_notifications.jsonl").resolve()

_intake_rate_lock = threading.Lock()
_intake_rate_buckets: dict[str, list[float]] = {}


app = FastAPI(title="DutyGuard-AI", version="0.1.0")

# Startup check: log a clear warning when notification SMTP/notify-to is not configured.
def _notifications_configured() -> bool:
    notify_to = os.getenv("DUTYGUARD_NOTIFY_EMAIL_TO", "").strip()
    smtp_host = os.getenv("DUTYGUARD_SMTP_HOST", "").strip()
    return bool(notify_to and smtp_host)


@app.on_event("startup")
def _startup_checks() -> None:
    if not _notifications_configured():
        print("[startup] WARNING: Notification SMTP or notify-to is not configured.")
        print("[startup] Set DUTYGUARD_NOTIFY_EMAIL_TO and DUTYGUARD_SMTP_HOST to enable email notifications.")


SOURCE_REGISTRY = [
    {
        "id": "htsus_usitc",
        "name": "Harmonized Tariff Schedule (USITC)",
        "url": "https://hts.usitc.gov/",
        "authority": "United States International Trade Commission",
        "purpose": "Primary tariff schedule for U.S. import classification and duty rates.",
        "update_cadence": "Published revisions",
    },
    {
        "id": "cbp_cross",
        "name": "CBP CROSS Rulings",
        "url": "https://rulings.cbp.gov/home",
        "authority": "U.S. Customs and Border Protection",
        "purpose": "Fact-specific customs ruling precedents for classification and valuation interpretation.",
        "update_cadence": "Continuous",
    },
    {
        "id": "federal_register",
        "name": "Federal Register",
        "url": "https://www.federalregister.gov/",
        "authority": "Office of the Federal Register",
        "purpose": "Official publication for federal rules, notices, and policy changes affecting trade.",
        "update_cadence": "Daily",
    },
]


class ReviewDecision(str, Enum):
    approved = "approved"
    rejected = "rejected"


class ReviewDecisionRequest(BaseModel):
    decision: ReviewDecision
    reviewer: str
    decision_notes: str = ""


class PilotEntry(BaseModel):
    sku: str
    description: str
    import_value: float
    current_duty_rate: float
    suggested_duty_rate: float
    confidence: float


class PilotOnboardRequest(BaseModel):
    customer_name: str
    entries: list[PilotEntry]


def _parse_allowed_origins(value: str) -> list[str]:
    raw = (value or "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [part.strip() for part in raw.split(",") if part.strip()]


def _load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _append_audit_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    previous_hash = ""
    if AUDIT_TRAIL_PATH.exists():
        lines = AUDIT_TRAIL_PATH.read_text(encoding="utf-8").splitlines()
        if lines:
            previous_hash = json.loads(lines[-1]).get("event_hash", "")

    event = {
        "event_type": event_type,
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "previous_hash": previous_hash,
        "payload": payload,
    }
    event_hash = hashlib.sha256(json.dumps(event, sort_keys=True).encode("utf-8")).hexdigest()
    event["event_hash"] = event_hash

    with AUDIT_TRAIL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    return event


def _smtp_int(value: str, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _rate_limit_exceeded(key: str, now_ts: float, max_requests: int, window_seconds: int) -> bool:
    cutoff = now_ts - float(window_seconds)
    with _intake_rate_lock:
        bucket = _intake_rate_buckets.setdefault(key, [])
        bucket[:] = [ts for ts in bucket if ts >= cutoff]
        if len(bucket) >= max_requests:
            return True
        bucket.append(now_ts)
        return False


def _append_notification_fallback(payload: dict[str, Any]) -> bool:
    try:
        with NOTIFICATIONS_FALLBACK_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
        return True
    except Exception as exc:
        print(f"[intake] Fallback notification write failed: {exc}")
        return False


def _send_intake_notification(intake_payload: dict[str, Any], stored_files: list[dict[str, Any]]) -> tuple[bool, str]:
    notify_to = os.getenv("DUTYGUARD_NOTIFY_EMAIL_TO", "").strip()
    if not notify_to:
        fallback_ok = _append_notification_fallback(
            {
                "mode": "fallback",
                "reason": "missing_notify_to",
                "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "intake_id": intake_payload.get("id"),
                "company": intake_payload.get("company"),
                "email": intake_payload.get("email"),
                "files": stored_files,
            }
        )
        return fallback_ok, "fallback"

    smtp_host = os.getenv("DUTYGUARD_SMTP_HOST", "").strip()
    if not smtp_host:
        fallback_ok = _append_notification_fallback(
            {
                "mode": "fallback",
                "reason": "missing_smtp_host",
                "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "intake_id": intake_payload.get("id"),
                "company": intake_payload.get("company"),
                "email": intake_payload.get("email"),
                "files": stored_files,
            }
        )
        return fallback_ok, "fallback"

    smtp_port = _smtp_int(os.getenv("DUTYGUARD_SMTP_PORT", "587"), 587)
    smtp_username = os.getenv("DUTYGUARD_SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("DUTYGUARD_SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("DUTYGUARD_NOTIFY_EMAIL_FROM", smtp_username or "noreply@dutyguard.local").strip()
    use_ssl = _bool_env("DUTYGUARD_SMTP_SSL", False)
    use_starttls = _bool_env("DUTYGUARD_SMTP_STARTTLS", True)

    message = EmailMessage()
    message["Subject"] = f"[DutyGuard] New contact request: {intake_payload.get('company', 'Unknown')}"
    message["From"] = smtp_from
    message["To"] = notify_to

    files_summary = "\n".join(
        [f"- {item.get('filename')} ({item.get('bytes', 0)} bytes)" for item in stored_files]
    ) or "- None"

    body = (
        "New contact submission received.\n\n"
        f"Reference: {intake_payload.get('id')}\n"
        f"Created: {intake_payload.get('created_at_utc')}\n"
        f"Company: {intake_payload.get('company')}\n"
        f"Name: {intake_payload.get('name')}\n"
        f"Email: {intake_payload.get('email')}\n"
        f"Phone: {intake_payload.get('phone')}\n\n"
        "Message:\n"
        f"{intake_payload.get('message')}\n\n"
        "Files:\n"
        f"{files_summary}\n"
    )
    message.set_content(body)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as client:
                if smtp_username:
                    client.login(smtp_username, smtp_password)
                client.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as client:
                if use_starttls:
                    client.starttls()
                if smtp_username:
                    client.login(smtp_username, smtp_password)
                client.send_message(message)
        return True, "email"
    except Exception as exc:
        print(f"[intake] Email notification failed: {exc}")
        fallback_ok = _append_notification_fallback(
            {
                "mode": "fallback",
                "reason": "smtp_send_failed",
                "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "intake_id": intake_payload.get("id"),
                "company": intake_payload.get("company"),
                "email": intake_payload.get("email"),
                "files": stored_files,
                "error": str(exc),
            }
        )
        return fallback_ok, "fallback"


_allowed_origins = _parse_allowed_origins(os.getenv("DUTYGUARD_ALLOWED_ORIGINS", "*"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tariff_logic_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "DutyGuard-AI API",
        "health": "/health",
        "alerts": "/api/alerts",
        "classify": "/api/classify",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/sources")
def list_sources() -> dict[str, Any]:
    return {
        "ok": True,
        "sources": SOURCE_REGISTRY,
        "legal_disclaimer": "Source links are references only; legal determinations require qualified human review.",
    }


def _safe_name(name: str) -> str:
    name = name.strip().replace("\x00", "")
    return os.path.basename(name) or "upload.bin"


def _sanitize_user_key(raw: str) -> str:
    cleaned = "".join(ch for ch in (raw or "").strip() if ch.isalnum() or ch in {"-", "_", "."})
    return cleaned[:64] or "anonymous"


def _resolve_user_key(request: Request) -> str:
    from_query = request.query_params.get("user", "")
    from_header = request.headers.get("x-user-key", "")
    return _sanitize_user_key(from_query or from_header or "anonymous")


def _user_uploads_dir(user_key: str) -> Path:
    user_dir = (UPLOADS_DIR / user_key).resolve()
    if UPLOADS_DIR not in user_dir.parents:
        raise HTTPException(status_code=400, detail="Invalid user scope")
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


@app.get("/api/reviews")
def list_reviews() -> dict[str, Any]:
    tickets: list[dict[str, Any]] = []
    for path in sorted(REVIEW_QUEUE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        ticket = _load_json_file(path)
        tickets.append(
            {
                "id": ticket.get("id"),
                "status": ticket.get("status"),
                "created_at_utc": ticket.get("created_at_utc"),
                "review_reasons": ticket.get("review_reasons", []),
            }
        )
    return {"ok": True, "count": len(tickets), "tickets": tickets}


@app.get("/api/reviews/{review_id}")
def get_review(review_id: str) -> dict[str, Any]:
    path = (REVIEW_QUEUE_DIR / f"{_safe_name(review_id)}.json").resolve()
    if REVIEW_QUEUE_DIR not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Review ticket not found")
    return {"ok": True, "ticket": _load_json_file(path)}


@app.post("/api/reviews/{review_id}/decision")
def review_decision(review_id: str, payload: ReviewDecisionRequest) -> dict[str, Any]:
    path = (REVIEW_QUEUE_DIR / f"{_safe_name(review_id)}.json").resolve()
    if REVIEW_QUEUE_DIR not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Review ticket not found")

    ticket = _load_json_file(path)
    if ticket.get("status") != "open":
        raise HTTPException(status_code=400, detail="Review already finalized")

    ticket["status"] = payload.decision.value
    ticket["reviewer"] = payload.reviewer
    ticket["decision_notes"] = payload.decision_notes
    ticket["decision"] = payload.decision.value
    ticket["decided_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path.write_text(json.dumps(ticket, indent=2), encoding="utf-8")

    audit_event = _append_audit_event(
        "review_decision",
        {
            "review_id": review_id,
            "decision": payload.decision.value,
            "reviewer": payload.reviewer,
            "decision_notes": payload.decision_notes,
        },
    )

    return {"ok": True, "ticket": ticket, "audit_event": audit_event}


@app.get("/api/classification-report/{review_id}")
def classification_report(review_id: str) -> dict[str, Any]:
    path = (REVIEW_QUEUE_DIR / f"{_safe_name(review_id)}.json").resolve()
    if REVIEW_QUEUE_DIR not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Review ticket not found")

    ticket = _load_json_file(path)
    request = ticket.get("request", {})
    response = ticket.get("response", {})

    return {
        "ok": True,
        "report": {
            "ticket_id": ticket.get("id"),
            "status": ticket.get("status"),
            "product": request.get("name"),
            "origin_country": request.get("origin_country"),
            "destination_country": request.get("destination_country"),
            "suggested_hs_code": response.get("suggested_hs_code"),
            "duty_rate": response.get("duty_rate"),
            "confidence": response.get("confidence"),
            "confidence_interval": response.get("confidence_interval"),
            "why_this_classification": response.get("reasoning_manifesto", []),
            "review_reasons": ticket.get("review_reasons", []),
            "legal_citations": response.get("legal_citations", []),
            "legal_disclaimer": response.get("legal_disclaimer"),
        },
    }


@app.post("/api/pilot/onboard")
def pilot_onboard(payload: PilotOnboardRequest) -> dict[str, Any]:
    if not payload.entries:
        raise HTTPException(status_code=400, detail="At least one entry is required")

    batch_id = f"pilot_{int(time.time())}_{hashlib.sha256(payload.customer_name.encode('utf-8')).hexdigest()[:8]}"
    batch = {
        "id": batch_id,
        "customer_name": payload.customer_name,
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entries": [entry.model_dump() for entry in payload.entries],
    }
    (PILOT_BATCHES_DIR / f"{batch_id}.json").write_text(json.dumps(batch, indent=2), encoding="utf-8")
    return {"ok": True, "batch_id": batch_id, "entry_count": len(payload.entries)}


@app.get("/api/pilot/prioritize/{batch_id}")
def pilot_prioritize(batch_id: str) -> dict[str, Any]:
    path = (PILOT_BATCHES_DIR / f"{_safe_name(batch_id)}.json").resolve()
    if PILOT_BATCHES_DIR not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Pilot batch not found")

    batch = _load_json_file(path)
    opportunities: list[dict[str, Any]] = []
    for entry in batch.get("entries", []):
        import_value = float(entry.get("import_value", 0.0))
        current_rate = float(entry.get("current_duty_rate", 0.0))
        suggested_rate = float(entry.get("suggested_duty_rate", 0.0))
        potential_recovery = max(0.0, import_value * max(0.0, current_rate - suggested_rate))

        opportunities.append(
            {
                "sku": entry.get("sku"),
                "description": entry.get("description"),
                "import_value": import_value,
                "current_duty_rate": current_rate,
                "suggested_duty_rate": suggested_rate,
                "confidence": entry.get("confidence"),
                "potential_recovery": round(potential_recovery, 2),
            }
        )

    opportunities.sort(key=lambda item: item["potential_recovery"], reverse=True)
    top_10 = opportunities[:10]
    total_potential_recovery = round(sum(item["potential_recovery"] for item in opportunities), 2)

    return {
        "ok": True,
        "batch_id": batch_id,
        "customer_name": batch.get("customer_name"),
        "total_entries": len(opportunities),
        "top_opportunities": top_10,
        "total_potential_recovery": total_potential_recovery,
        "legal_disclaimer": "Opportunity ranking is decision support only and requires qualified customs/legal review.",
    }


@app.post("/api/pilot/claim-packet/{batch_id}")
def pilot_claim_packet(batch_id: str) -> dict[str, Any]:
    prioritized = pilot_prioritize(batch_id)
    packet_id = f"claim_{int(time.time())}_{hashlib.sha256(batch_id.encode('utf-8')).hexdigest()[:8]}"
    packet = {
        "id": packet_id,
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "batch_id": batch_id,
        "customer_name": prioritized.get("customer_name"),
        "top_opportunities": prioritized.get("top_opportunities", []),
        "summary": {
            "total_entries": prioritized.get("total_entries", 0),
            "total_potential_recovery": prioritized.get("total_potential_recovery", 0.0),
        },
        "legal_disclaimer": prioritized.get("legal_disclaimer"),
    }
    packet_path = CLAIM_PACKETS_DIR / f"{packet_id}.json"
    packet_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    _append_audit_event(
        "claim_packet_generated",
        {
            "packet_id": packet_id,
            "batch_id": batch_id,
            "customer_name": packet.get("customer_name"),
            "total_potential_recovery": packet["summary"]["total_potential_recovery"],
        },
    )

    return {"ok": True, "packet_id": packet_id, "path": str(packet_path), "packet": packet}


@app.get("/api/metrics/summary")
def metrics_summary() -> dict[str, Any]:
    open_count = 0
    approved_count = 0
    rejected_count = 0

    for path in REVIEW_QUEUE_DIR.glob("*.json"):
        if not path.is_file():
            continue
        ticket = _load_json_file(path)
        status = ticket.get("status")
        if status == "open":
            open_count += 1
        elif status == "approved":
            approved_count += 1
        elif status == "rejected":
            rejected_count += 1

    claim_packets = list(CLAIM_PACKETS_DIR.glob("*.json"))
    return {
        "ok": True,
        "reviews": {
            "open": open_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "total": open_count + approved_count + rejected_count,
        },
        "claim_packets_generated": len(claim_packets),
        "audit_trail_path": str(AUDIT_TRAIL_PATH),
    }


@app.post("/api/tariff-files")
async def upload_tariff_file(request: Request, file: UploadFile = File(...)) -> dict[str, Any]:
    user_key = _resolve_user_key(request)
    user_uploads_dir = _user_uploads_dir(user_key)
    filename = _safe_name(file.filename or "upload.bin")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    sha256 = hashlib.sha256(content).hexdigest()
    stored_name = f"{int(time.time())}_{sha256[:12]}_{filename}"
    stored_path = user_uploads_dir / stored_name
    stored_path.write_bytes(content)

    return {
        "id": sha256,
        "filename": filename,
        "storedName": stored_name,
        "bytes": len(content),
        "user": user_key,
    }


@app.get("/api/tariff-files")
def list_tariff_files(request: Request) -> list[dict[str, Any]]:
    user_key = _resolve_user_key(request)
    user_uploads_dir = _user_uploads_dir(user_key)
    items: list[dict[str, Any]] = []
    for path in sorted(user_uploads_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        items.append(
            {
                "storedName": path.name,
                "bytes": path.stat().st_size,
                "modified": int(path.stat().st_mtime),
            }
        )
    return items


@app.get("/api/tariff-files/{stored_name}")
def download_tariff_file(stored_name: str, request: Request):
    user_key = _resolve_user_key(request)
    user_uploads_dir = _user_uploads_dir(user_key)
    stored_name = _safe_name(stored_name)
    path = (user_uploads_dir / stored_name).resolve()
    if user_uploads_dir not in path.parents:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path)


@app.post("/api/intake")
async def submit_intake(
    request: Request,
    company: str = Form(""),
    name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    message: str = Form(""),
    website: str = Form(""),
    files: list[UploadFile] | None = None,
) -> dict[str, Any]:
    """Client intake + contact submission.

    Stores a JSON record and saves uploaded files under `backend/data/intakes/`.
    """

    if website.strip():
        raise HTTPException(status_code=400, detail="Invalid submission")

    client_ip = (request.client.host if request.client and request.client.host else "unknown").strip().lower()
    email_key = email.strip().lower() or "anonymous"
    now_ts = time.time()

    if _rate_limit_exceeded(f"ip:{client_ip}", now_ts, max_requests=8, window_seconds=300):
        raise HTTPException(status_code=429, detail="Too many submissions, please try again later")
    if _rate_limit_exceeded(f"email:{email_key}", now_ts, max_requests=4, window_seconds=300):
        raise HTTPException(status_code=429, detail="Too many submissions, please try again later")

    now = int(now_ts)
    intake_id = f"intake_{now}_{hashlib.sha256(f'{company}|{email}|{now}'.encode('utf-8')).hexdigest()[:10]}"
    intake_dir = (INTAKES_DIR / intake_id).resolve()
    intake_dir.mkdir(parents=True, exist_ok=True)

    stored_files: list[dict[str, Any]] = []
    if files:
        for f in files:
            filename = _safe_name(f.filename or "upload.bin")
            content = await f.read()
            if not content:
                continue
            sha256 = hashlib.sha256(content).hexdigest()
            stored_name = f"{sha256[:12]}_{filename}"
            stored_path = intake_dir / stored_name
            stored_path.write_bytes(content)
            stored_files.append({"filename": filename, "storedName": stored_name, "bytes": len(content)})

    payload = {
        "id": intake_id,
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "company": company,
        "name": name,
        "email": email,
        "phone": phone,
        "message": message,
        "files": stored_files,
    }
    (intake_dir / "intake.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    email_sent, notification_mode = _send_intake_notification(payload, stored_files)

    return {
        "ok": True,
        "id": intake_id,
        "storedFiles": stored_files,
        "notificationSent": email_sent,
        "notificationMode": notification_mode,
    }


@app.get("/api/alerts")
def get_alerts() -> dict[str, Any]:
    """Expose latest alert agent output to the UI/dashboard."""

    if not ALERTS_JSON_PATH.exists():
        return {
            "ok": False,
            "message": "No alert data is available yet. Please check back shortly.",
            "path": str(ALERTS_JSON_PATH),
        }
    try:
        return json.loads(ALERTS_JSON_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "message": f"Failed to read alerts JSON: {exc}", "path": str(ALERTS_JSON_PATH)}


@app.get("/admin/intake-notifications")
def admin_intake_notifications(request: Request, lines: int = 50) -> dict[str, Any]:
    """Admin-only: Read the fallback intake notification log (JSONL).

    Protects access with an admin key provided via header `x-admin-key` or query `admin_key`.
    The admin key must match the `DUTYGUARD_ADMIN_KEY` environment variable.
    """
    admin_key = os.getenv("DUTYGUARD_ADMIN_KEY", "").strip()
    provided = (request.headers.get("x-admin-key") or request.query_params.get("admin_key") or "").strip()
    if not admin_key or provided != admin_key:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not NOTIFICATIONS_FALLBACK_PATH.exists():
        return {"ok": True, "entries": [], "path": str(NOTIFICATIONS_FALLBACK_PATH)}

    try:
        with NOTIFICATIONS_FALLBACK_PATH.open("r", encoding="utf-8") as f:
            lines_list = f.read().splitlines()
    except Exception as exc:
        return {"ok": False, "message": f"Failed to read notifications file: {exc}", "path": str(NOTIFICATIONS_FALLBACK_PATH)}

    # return the last `lines` entries (most recent last)
    entries_raw = lines_list[-int(lines) :] if lines_list else []
    entries: list[dict[str, Any]] = []
    for raw in entries_raw:
        try:
            entries.append(json.loads(raw))
        except Exception:
            # keep raw line when JSON parse fails
            entries.append({"raw": raw})

    return {"ok": True, "entries": entries, "count": len(entries)}


# Serve static frontend
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    if not DIST_DIR.exists():
        raise HTTPException(status_code=404, detail="Frontend not built")

    requested = (DIST_DIR / full_path).resolve()
    if DIST_DIR in requested.parents and requested.exists() and requested.is_file():
        return FileResponse(requested)

    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Not Found")
