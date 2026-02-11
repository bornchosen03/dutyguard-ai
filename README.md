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

## Environment Configuration

Create `.env` file in `backend/` (example in `backend/.env.example`):

```
PORT=8000
DATABASE_URL="sqlite:///./dev.db"
SECRET_KEY="your_jwt_secret"
```

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

**Note**: If you prefer a different backend (Node.js/Nest/Express) or frontend (Next.js), tell me and I can re-scaffold accordingly.
