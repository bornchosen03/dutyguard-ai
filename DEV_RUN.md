**Development Run**

This document explains how to run the project locally and provides a simple `run_all` helper.

- **Start everything (recommended)**: from repo root:

```
./scripts/run_all.sh
```

This will run `pip-audit`, `pytest`, start the backend (backgrounded), run `npm ci` and `npm audit`, and build the frontend to `portal/frontend/customer-portal/dist`.

- **Start backend only**:

```
./scripts/start_backend.sh 8080
```

- **Notes**:
  - The backend must be started with `PYTHONPATH` pointing at `portal/backend/backend` (the helper script does this).
  - The `feat/upgrade-backend-deps` branch was cleaned of large binary PDFs before pushing to remote. A backup branch `backup/feat/upgrade-backend-deps` exists in this repo.
  - CI workflow (`.github/workflows/ci.yml`) runs `pip-audit`, `pytest`, `npm audit`, and `npm run build` on push/PR.
