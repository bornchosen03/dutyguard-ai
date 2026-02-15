# Streamlit Community Cloud Deploy

Streamlit Community Cloud can only deploy apps that are in a **GitHub repository**.

If Streamlit shows:

> Unable to deploy — The app’s code is not connected to a remote GitHub repository

…it means this repo has no GitHub remote configured (or the code is not pushed).

## 1) Put this repo on GitHub

1) Create a new GitHub repo (example: `DutyGuard-AI`).

2) In this folder, add the remote and push:

```zsh
cd /Users/bthrax/DutyGuard-AI

git remote add origin https://github.com/<YOUR_USER>/<YOUR_REPO>.git

git branch -M main

git push -u origin main
```

If you already have a remote, verify:

```zsh
git remote -v
```

## 2) Deploy the Streamlit dashboard

In Streamlit Community Cloud:

- **Repository:** select your GitHub repo
- **Branch:** `main`
- **Main file path:** `dashboard.py`
- **Python version:** 3.13 (or whatever Streamlit supports at deploy time)

Streamlit Cloud installs dependencies from the repo-root `requirements.txt`.

## 3) Configure secrets / env vars

The dashboard calls the backend API. In Streamlit Cloud, you must host the backend elsewhere and point the dashboard to it.

Set an environment variable in Streamlit Cloud settings:

- `DUTYGUARD_API_BASE`: e.g. `https://your-backend.example.com`

If not set, it defaults to `http://127.0.0.1:8080` (local only).

## 4) Notes

- Streamlit Cloud will **not** automatically run the FastAPI backend.
- Deploy backend separately (Render/Fly/AWS/etc), then connect via `DUTYGUARD_API_BASE`.

## 5) Backend deploy on Render (recommended)

This repo includes a `render.yaml` that deploys the FastAPI backend as a Render Web Service.

1) Go to Render → **New +** → **Blueprint**

2) Select the GitHub repo: `bornchosen03/dutyguard-ai`

3) Render will detect `render.yaml` and propose creating `dutyguard-api`.

4) Click **Apply** to deploy.

After it deploys, you’ll get a public URL like:

- `https://dutyguard-api-xxxx.onrender.com`

Verify it:

- `https://dutyguard-api-xxxx.onrender.com/health`

Then set Streamlit Cloud secrets:

- `DUTYGUARD_API_BASE = "https://dutyguard-api-xxxx.onrender.com"`
