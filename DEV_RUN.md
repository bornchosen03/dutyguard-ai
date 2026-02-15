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

- **Environment variables (examples)**: set these to enable email notifications and tune runtime limits.

```
# Notification / SMTP (example values)
export DUTYGUARD_NOTIFY_EMAIL_TO="devops@example.com"
export DUTYGUARD_NOTIFY_EMAIL_FROM="noreply@example.com"
export DUTYGUARD_SMTP_HOST="smtp.example.com"
export DUTYGUARD_SMTP_PORT="587"
export DUTYGUARD_SMTP_USERNAME="smtp-user"
export DUTYGUARD_SMTP_PASSWORD="s3cr3t"
export DUTYGUARD_SMTP_STARTTLS="true"   # or set DUTYGUARD_SMTP_SSL for SMTPS

# Security / runtime tuning (optional)
export DUTYGUARD_MAX_UPLOAD_BYTES="10485760"        # 10 MB default
export DUTYGUARD_MAX_TOTAL_INTAKE_BYTES="26214400"  # 25 MB default
export DUTYGUARD_FORCE_HTTPS="false"
```

Set these in your shell (e.g. `~/.zshenv`) or run them in the shell before starting the backend. If `DUTYGUARD_NOTIFY_EMAIL_TO` or `DUTYGUARD_SMTP_HOST` are not set, the server will fallback to writing notification payloads to `portal/backend/backend/data/intake_notifications.jsonl`.
