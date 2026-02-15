#!/bin/zsh
# Restart backend server if not running
PORT=8080
VENV="/Users/bthrax/DutyGuard-AI/backend/.venv-fastapi/bin"
APP="app.main:app"
LOG="/Users/bthrax/DutyGuard-AI/backend/uvicorn.log"

if ! lsof -i :$PORT | grep LISTEN > /dev/null; then
    echo "Backend not running. Restarting..."
    nohup $VENV/uvicorn $APP --host 0.0.0.0 --port $PORT > $LOG 2>&1 &
else
    echo "Backend already running."
fi
