#!/bin/zsh
# Auto-update backend code from git
cd /Users/bthrax/DutyGuard-AI/backend
if git pull | grep -q 'Already up to date.'; then
    echo "No updates found."
else
    echo "Updates applied. Restarting backend..."
    nohup /Users/bthrax/DutyGuard-AI/backend/.venv-fastapi/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080 > /Users/bthrax/DutyGuard-AI/backend/uvicorn.log 2>&1 &
fi
