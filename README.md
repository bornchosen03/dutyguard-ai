# DutyGuard AI - Automated Duty Recovery Engine

**Global Tariff Audit Engine** for automated customs duty recovery, trade compliance analysis, and tariff optimization.

## Project Structure

```
DutyGuard-AI/
├── backend/                 # FastAPI (Python) API
├── frontend/                # React dashboard (Vite + TypeScript)
├── docs/                    # Documentation and guides
└── README.md
```

## Features

- **Automated Duty Recovery**: Recover overpaid customs duties through systematic audits
- **Trade Compliance**: Validate shipments against global tariff rules
- **Tariff Optimization**: Find duty-saving routes and classifications
- **Batch Processing**: Process thousands of shipments in minutes
- **Real-time Alerts**: Immediate notifications on compliance violations

## Local Development

### Prerequisites
- Python 3.10+ (for backend)
- Node.js 18+ (for frontend)
- PostgreSQL or SQLite
- Redis (optional, for queue processing)

### Quick Start

Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Run dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port ${PORT:-8000}
```

Frontend (Vite + React)

```bash
cd frontend
npm install
npm run dev
```

### API Endpoints (examples)

- `GET /` - Root welcome message
- `GET /health` - Health check
- `POST /api/classify` - Classification with confidence, legal citations, and optional review ticket
- `GET /api/sources` - Authoritative tariff/compliance source registry
- `GET /api/reviews` - List review tickets
- `GET /api/reviews/{review_id}` - Review ticket detail
- `POST /api/reviews/{review_id}/decision` - Approve/reject review ticket with audit event
- `GET /api/classification-report/{review_id}` - Customer-facing “why this classification” report payload
- `POST /api/pilot/onboard` - Pilot intake for customer entries
- `GET /api/pilot/prioritize/{batch_id}` - Top recoverable opportunities ranked by potential recovery
- `POST /api/pilot/claim-packet/{batch_id}` - Generate claim packet JSON + audit event
- `GET /api/metrics/summary` - Review and packet generation operational metrics

### One-command Validation

Run the full release gate (restart/build + smoke + tests + health):

```bash
bash scripts/release_check.sh
```

This script executes:

- `scripts/run_all.sh`
- `scripts/smoke_check.sh`
- `pytest backend/tests/test_api.py -q`
- `GET /health` final check

### Sales Pack PDF

Generate a customer-facing pitch PDF:

```bash
/Users/bthrax/DutyGuard-AI/backend/.venv-fastapi/bin/python scripts/generate_customer_pitch_pdf.py
```

Output file:

- `docs/DutyGuard_First_Customer_Pitch.pdf`

## Environment Configuration

Create `.env` file in `backend/` (example in `backend/.env.example`):

```
PORT=8000
DATABASE_URL="sqlite:///./dev.db"
SECRET_KEY="your_jwt_secret"
```

### Contact Notifications (optional)

To email your team when a new Contact Us form is submitted, set:

```bash
DUTYGUARD_NOTIFY_EMAIL_TO="ops@yourcompany.com"
DUTYGUARD_NOTIFY_EMAIL_FROM="noreply@yourcompany.com"
DUTYGUARD_SMTP_HOST="smtp.yourprovider.com"
DUTYGUARD_SMTP_PORT="587"
DUTYGUARD_SMTP_USERNAME="smtp-user"
DUTYGUARD_SMTP_PASSWORD="smtp-password"
DUTYGUARD_SMTP_STARTTLS="1"
DUTYGUARD_SMTP_SSL="0"
```

If these are not configured, intake submissions still work and are stored locally in `backend/data/intakes/`.

## Technology Stack

- **Backend**: Python, FastAPI, Uvicorn
- **Frontend**: React, Vite, TypeScript
- **Database**: PostgreSQL or SQLite
- **Queue**: Redis (optional)
- **Auth**: JWT (recommended)

## Documentation

See `/docs` for:
- Architecture overview
- API documentation
- Deployment guides
- Configuration reference

---

### Fees

- The industry standard is a Contingency Fee ranging from 15% to 30% of the recovered funds.


**Note**: If you prefer a different backend (Node.js/Nest/Express) or frontend (Next.js), tell me and I can re-scaffold accordingly.
