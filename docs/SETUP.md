DutyGuard AI — Setup & Run

This file documents the current local setup and quick run instructions.

Overview

- Frontend: Vite + React. Production build is in `frontend/dist/`.
- Backend: Minimal ASGI app at `backend/app/main.py` served by Uvicorn on 127.0.0.1:8080.
- Scripts: `scripts/start.sh`, `scripts/dev.sh`, `scripts/install_launchd_with_path.sh`, `scripts/setup_fastapi_env.sh`.

Run (production-like)

1. Build frontend:

```zsh
cd frontend
npm install --legacy-peer-deps
npm run build
```

2. Start backend (serves built `dist/` on port 8080):

```zsh
cd /path/to/DutyGuard-AI
./scripts/start.sh
```

3. Verify:

```zsh
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/health
```

Development

- Backend (reload): `./scripts/dev.sh`
- Frontend dev server: in `frontend/` run `npm run dev`

FastAPI / pydantic helper

`./scripts/setup_fastapi_env.sh` creates `backend/.venv-fastapi` and behaves as follows:
- If Python 3.11 or 3.12 is detected: attempts to install `fastapi`, `pydantic`, `uvicorn[standard]`, and `python-dotenv`.
- Otherwise (e.g., Python 3.13): it installs only minimal backend deps (`uvicorn`, `python-dotenv`) and prints instructions to install the full requirements later.

Notes on pydantic-core

- pydantic-core may require building native extensions (Rust) if prebuilt wheels are not available for your Python version. To avoid local build issues either:
  - Use Python 3.11 or 3.12 where wheels are commonly available, or
  - Install Rust toolchain (`rustup`) so pydantic-core can be built from source.

LaunchAgent (macOS)

Install the LaunchAgent that runs `scripts/start.sh` at login (installer sets PATH to include common Node locations):

```zsh
./scripts/install_launchd_with_path.sh
```

Logs: `~/Library/Logs/com.dutyguard-ai.server.out.log` and `.err.log`

Cleanup & Git

- `.gitignore` added to exclude `node_modules/`, `frontend/dist/`, `backend/.venv*`, and `logs/`.
- Tracked `frontend/node_modules` was removed from the index.

If you'd like: I can try to rewrite git history to fully remove the old node_modules commit (destructive), or I can add a small README update file — tell me which.
