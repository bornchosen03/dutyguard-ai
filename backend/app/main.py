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
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .tariff_logic import router as tariff_logic_router


ROOT_DIR = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE_DIR = (ROOT_DIR / "knowledge_base").resolve()
ALERTS_JSON_PATH = (KNOWLEDGE_BASE_DIR / "tariff_alerts.json").resolve()


BASE_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = (BASE_DIR / ".." / "frontend" / "dist").resolve()
DATA_DIR = (BASE_DIR / "data").resolve()
UPLOADS_DIR = (DATA_DIR / "uploads").resolve()
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

INTAKES_DIR = (DATA_DIR / "intakes").resolve()
INTAKES_DIR.mkdir(parents=True, exist_ok=True)


app = FastAPI(title="DutyGuard-AI", version="0.1.0")


def _parse_allowed_origins(value: str) -> list[str]:
    raw = (value or "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [part.strip() for part in raw.split(",") if part.strip()]


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


def _safe_name(name: str) -> str:
    name = name.strip().replace("\x00", "")
    return os.path.basename(name) or "upload.bin"


@app.post("/api/tariff-files")
async def upload_tariff_file(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = _safe_name(file.filename or "upload.bin")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    sha256 = hashlib.sha256(content).hexdigest()
    stored_name = f"{int(time.time())}_{sha256[:12]}_{filename}"
    stored_path = UPLOADS_DIR / stored_name
    stored_path.write_bytes(content)

    return {
        "id": sha256,
        "filename": filename,
        "storedName": stored_name,
        "bytes": len(content),
    }


@app.get("/api/tariff-files")
def list_tariff_files() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(UPLOADS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
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
def download_tariff_file(stored_name: str):
    stored_name = _safe_name(stored_name)
    path = (UPLOADS_DIR / stored_name).resolve()
    if UPLOADS_DIR not in path.parents:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path)


@app.post("/api/intake")
async def submit_intake(
    company: str = Form(""),
    name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    message: str = Form(""),
    files: list[UploadFile] | None = None,
) -> dict[str, Any]:
    """Client intake + contact submission.

    Stores a JSON record and saves uploaded files under `backend/data/intakes/`.
    """

    now = int(time.time())
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

    return {"ok": True, "id": intake_id, "storedFiles": stored_files}


@app.get("/api/alerts")
def get_alerts() -> dict[str, Any]:
    """Expose latest alert agent output to the UI/dashboard."""

    if not ALERTS_JSON_PATH.exists():
        return {
            "ok": False,
            "message": "Alerts file not found. Run ./scripts/run_scraper.sh then ./scripts/run_alerts.sh",
            "path": str(ALERTS_JSON_PATH),
        }
    try:
        return json.loads(ALERTS_JSON_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "message": f"Failed to read alerts JSON: {exc}", "path": str(ALERTS_JSON_PATH)}


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
